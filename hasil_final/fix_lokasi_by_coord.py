import pandas as pd
import reverse_geocoder as rg
import numpy as np
import re

def map_province(admin1):
    mapping = {
        'South Sulawesi': 'Sulawesi Selatan',
        'West Sulawesi': 'Sulawesi Barat',
        'Central Sulawesi': 'Sulawesi Tengah',
        'North Sulawesi': 'Sulawesi Utara',
        'South East Sulawesi': 'Sulawesi Tenggara',
        'Gorontalo': 'Gorontalo',
    }
    return mapping.get(admin1, admin1)

def format_kabupaten(admin2):
    # Reverse geocoder usually returns "Kota Makassar" or "Kabupaten Donggala"
    # But sometimes it might just be the name or something else.
    # We will just ensure it follows "Kota X" or "Kabupaten X".
    admin2 = str(admin2).strip()
    if not admin2:
        return ""
    if admin2.lower().startswith('kota '):
        return admin2
    elif admin2.lower().startswith('kabupaten '):
        return admin2
    else:
        # If it doesn't have "Kota" or "Kabupaten", assume it's Kabupaten
        return f"Kabupaten {admin2}"

def fix_dataset_by_coord(file_path):
    print(f"Memproses {file_path}")
    df = pd.read_csv(file_path)
    
    coords = []
    valid_idx = []
    
    for idx, row in df.iterrows():
        try:
            lat = float(row['lat'])
            lon = float(row['long'])
            if not np.isnan(lat) and not np.isnan(lon):
                coords.append((lat, lon))
                valid_idx.append(idx)
        except (ValueError, TypeError):
            pass

    if not coords:
        return

    results = rg.search(coords)
    
    changes_prov = 0
    changes_kab = 0
    
    for i, idx in enumerate(valid_idx):
        res = results[i]
        
        raw_prov = res.get('admin1', '')
        mapped_prov = map_province(raw_prov)
        
        raw_kab = res.get('admin2', '')
        mapped_kab = format_kabupaten(raw_kab)
        
        current_prov = str(df.at[idx, 'provinsi']).strip()
        current_kab = str(df.at[idx, 'kabupaten']).strip()
        
        # Update Provinsi if mismatched and it's one of Sulawesi provinces
        if mapped_prov in ['Sulawesi Selatan', 'Sulawesi Barat', 'Sulawesi Tengah', 'Sulawesi Utara', 'Sulawesi Tenggara', 'Gorontalo']:
            if current_prov != mapped_prov:
                df.at[idx, 'provinsi'] = mapped_prov
                changes_prov += 1
                
        # Always update Kabupaten if we found something sensible
        if mapped_kab and current_kab.lower() != mapped_kab.lower():
            df.at[idx, 'kabupaten'] = mapped_kab
            changes_kab += 1

    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"Selesai! {changes_prov} provinsi dan {changes_kab} kabupaten telah diperbaiki berdasarkan koordinat (lat/long).\n")

if __name__ == "__main__":
    files_to_fix = [
        'd:/semester6/mc_learning/scrapt_wisata/hasil_scrap/wisata_sulawesi_kategori_ai.csv',
        'd:/semester6/mc_learning/scrapt_wisata/hasil_final/wisata_sulawesi_lengkap.csv'
    ]
    for f in files_to_fix:
        try:
            fix_dataset_by_coord(f)
        except Exception as e:
            print(f"Gagal memproses {f}: {e}")
