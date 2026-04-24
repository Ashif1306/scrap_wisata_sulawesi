import pandas as pd
import reverse_geocoder as rg
import numpy as np

def map_province(admin1):
    mapping = {
        'South Sulawesi': 'Sulawesi Selatan',
        'West Sulawesi': 'Sulawesi Barat',
        'Central Sulawesi': 'Sulawesi Tengah',
        'North Sulawesi': 'Sulawesi Utara',
        'South East Sulawesi': 'Sulawesi Tenggara',
        'Gorontalo': 'Gorontalo',
        'Bali': 'Bali',
        'East Java': 'Jawa Timur',
        'Jakarta': 'Daerah Khusus Ibukota Jakarta',
        'Maluku': 'Maluku',
        'North Maluku': 'Maluku Utara',
        'West Papua': 'Papua Barat'
    }
    # Return mapped or original if not in mapping but maybe close
    return mapping.get(admin1, admin1)

def fix_dataset_by_coord(file_path):
    print(f"Memproses {file_path}")
    df = pd.read_csv(file_path)
    
    # Kumpulkan lat, long menjadi list of tuples (lat, long)
    # Ensure they are floats
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
        print("Tidak ada koordinat valid.")
        return

    print(f"Melakukan reverse geocoding untuk {len(coords)} titik...")
    results = rg.search(coords)
    
    changes = 0
    for i, idx in enumerate(valid_idx):
        res = results[i]
        # rg.search returns a list of dicts. admin1 is province, admin2 is regency
        raw_prov = res.get('admin1', '')
        # Map English province name to Indonesian
        mapped_prov = map_province(raw_prov)
        
        current_prov = str(df.at[idx, 'provinsi']).strip()
        
        # If mapping gives us a known province and it's different from the dataset
        # We only care about fixing Sulawesi provinces mismatch mainly
        if mapped_prov in ['Sulawesi Selatan', 'Sulawesi Barat', 'Sulawesi Tengah', 'Sulawesi Utara', 'Sulawesi Tenggara', 'Gorontalo']:
            if current_prov != mapped_prov:
                df.at[idx, 'provinsi'] = mapped_prov
                changes += 1

    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"Selesai! {changes} provinsi telah diperbaiki berdasarkan koordinat (lat/long).\n")

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
