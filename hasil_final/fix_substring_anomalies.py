import pandas as pd
import re
import sys

# Atur encoding untuk stdout
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = 'wisata_sulawesi_lengkap.csv'
OUTPUT_FILE = 'wisata_sulawesi_lengkap.csv'

df = pd.read_csv(INPUT_FILE)
print(f"Total data awal: {len(df)}")

fixes = 0

for idx, row in df.iterrows():
    kab = str(row['kabupaten']).strip()
    alamat = str(row['alamat']).strip().lower()
    
    new_kab = kab
    
    if kab == 'Kabupaten Luwu':
        if 'luwu timur' in alamat or 'east luwu' in alamat:
            new_kab = 'Kabupaten Luwu Timur'
        elif 'luwu utara' in alamat or 'north luwu' in alamat:
            new_kab = 'Kabupaten Luwu Utara'
        elif 'palopo' in alamat:
            new_kab = 'Kota Palopo'
        elif 'bulukumba' in alamat or 'kalumeme' in alamat:
            new_kab = 'Kabupaten Bulukumba'
            
    elif kab == 'Kabupaten Bone':
        if 'bone bolango' in alamat:
            new_kab = 'Kabupaten Bone Bolango'
            
    elif kab == 'Kabupaten Gorontalo':
        if 'gorontalo utara' in alamat or 'north gorontalo' in alamat:
            new_kab = 'Kabupaten Gorontalo Utara'
            
    elif kab == 'Kabupaten Minahasa':
        if 'minahasa utara' in alamat or 'north minahasa' in alamat:
            new_kab = 'Kabupaten Minahasa Utara'
        elif 'minahasa selatan' in alamat or 'south minahasa' in alamat:
            new_kab = 'Kabupaten Minahasa Selatan'
        elif 'minahasa tenggara' in alamat or 'southeast minahasa' in alamat:
            new_kab = 'Kabupaten Minahasa Tenggara'
            
    elif kab == 'Kabupaten Bolaang Mongondow':
        if 'bolaang mongondow utara' in alamat or 'north bolaang mongondow' in alamat:
            new_kab = 'Kabupaten Bolaang Mongondow Utara'
        elif 'bolaang mongondow selatan' in alamat or 'south bolaang mongondow' in alamat:
            new_kab = 'Kabupaten Bolaang Mongondow Selatan'
        elif 'bolaang mongondow timur' in alamat or 'east bolaang mongondow' in alamat:
            new_kab = 'Kabupaten Bolaang Mongondow Timur'
            
    elif kab == 'Kabupaten Konawe':
        if 'konawe utara' in alamat or 'north konawe' in alamat:
            new_kab = 'Kabupaten Konawe Utara'
        elif 'konawe selatan' in alamat or 'south konawe' in alamat:
            new_kab = 'Kabupaten Konawe Selatan'
        elif 'konawe kepulauan' in alamat:
            new_kab = 'Kabupaten Konawe Kepulauan'
            
    elif kab == 'Kabupaten Buton':
        if 'buton utara' in alamat or 'north buton' in alamat:
            new_kab = 'Kabupaten Buton Utara'
        elif 'buton selatan' in alamat or 'south buton' in alamat:
            new_kab = 'Kabupaten Buton Selatan'
        elif 'buton tengah' in alamat or 'central buton' in alamat:
            new_kab = 'Kabupaten Buton Tengah'
            
    elif kab == 'Kabupaten Morowali':
        if 'morowali utara' in alamat or 'north morowali' in alamat:
            new_kab = 'Kabupaten Morowali Utara'
            
    elif kab == 'Kabupaten Banggai':
        if 'banggai kepulauan' in alamat:
            new_kab = 'Kabupaten Banggai Kepulauan'
        elif 'banggai laut' in alamat:
            new_kab = 'Kabupaten Banggai Laut'
            
    elif kab == 'Kabupaten Muna':
        if 'muna barat' in alamat or 'west muna' in alamat:
            new_kab = 'Kabupaten Muna Barat'
            
    elif kab == 'Kota Gorontalo':
        if 'kabupaten gorontalo' in alamat and 'kota gorontalo' not in alamat:
            # Need to be careful here, but usually if it says 'Gorontalo Regency' it's the Kabupaten
            if 'gorontalo regency' in alamat:
                new_kab = 'Kabupaten Gorontalo'
                
    if new_kab != kab:
        print(f"FIX: '{row['nama_wisata']}' -> {kab} diubah menjadi {new_kab} (Alamat: {row['alamat']})")
        df.at[idx, 'kabupaten'] = new_kab
        fixes += 1

print(f"\nSelesai! Total {fixes} kabupaten dikoreksi karena anomali substring.")

# Save both to fixed and lengkap so the dashboard gets the latest
df.to_csv('wisata_sulawesi_fixed.csv', index=False, encoding='utf-8-sig')
df.to_csv('wisata_sulawesi_lengkap.csv', index=False, encoding='utf-8-sig')
print("Disimpan ke wisata_sulawesi_fixed.csv dan wisata_sulawesi_lengkap.csv")
