import pandas as pd
import re

def fix_dataset(file_path):
    print(f"Memproses {file_path}")
    df = pd.read_csv(file_path)
    
    provinsi_list = [
        'Sulawesi Selatan', 'Sulawesi Tenggara', 'Sulawesi Tengah', 
        'Sulawesi Utara', 'Sulawesi Barat', 'Gorontalo', 
        'Jawa Timur', 'Daerah Khusus Ibukota Jakarta', 'Jawa Barat', 'Bali'
    ]
    
    changes_provinsi = 0
    changes_kabupaten = 0
    
    for idx, row in df.iterrows():
        alamat = str(row['alamat']) if pd.notnull(row['alamat']) else ""
        
        # 1. Fix Provinsi
        found_prov = None
        for p in provinsi_list:
            if p.lower() in alamat.lower():
                found_prov = p
                break
        
        if found_prov and str(row['provinsi']) != found_prov:
            df.at[idx, 'provinsi'] = found_prov
            changes_provinsi += 1
            
        # 2. Fix Kabupaten
        match = re.search(r'(Kabupaten\s+[\w\s]+|Kab\.\s+[\w\s]+|Kota\s+[\w\s]+)(?=[,\n])', alamat)
        if match:
            found_kab = match.group(1).replace('Kab.', 'Kabupaten').strip()
            # Hindari jika menangkap 'Kota Jakarta' dsb
            if not found_kab.lower().startswith('kota selatan') and not found_kab.lower().startswith('kota utara'):
                if str(row['kabupaten']).lower() != found_kab.lower() and 'kecamatan' not in found_kab.lower():
                    df.at[idx, 'kabupaten'] = found_kab
                    changes_kabupaten += 1

    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"Selesai! {changes_provinsi} provinsi dan {changes_kabupaten} kabupaten telah diperbaiki.\n")

if __name__ == "__main__":
    files_to_fix = [
        'd:/semester6/mc_learning/scrapt_wisata/hasil_scrap/wisata_sulawesi_kategori_ai.csv',
        'd:/semester6/mc_learning/scrapt_wisata/hasil_final/wisata_sulawesi_lengkap.csv'
    ]
    for f in files_to_fix:
        try:
            fix_dataset(f)
        except Exception as e:
            print(f"Gagal memproses {f}: {e}")
