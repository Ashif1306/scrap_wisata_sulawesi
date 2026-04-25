import pandas as pd

df = pd.read_csv('wisata_sulawesi_fixed.csv')

def find_missing_kab(df):
    missing = []
    for idx, row in df.iterrows():
        kab = str(row['kabupaten']).lower()
        kab_clean = kab.replace('kabupaten ', '').replace('kota ', '').strip()
        alamat = str(row['alamat']).lower()
        
        if kab_clean not in alamat:
            if kab_clean == 'pangkajene dan kepulauan' and 'pangkep' in alamat:
                continue
            if kab_clean == 'sidenreng rappang' and 'sidrap' in alamat:
                continue
            if kab_clean == 'bolaang mongondow' and 'bolmong' in alamat:
                continue
            if kab_clean == 'siau tagulandang biaro' and 'sitaro' in alamat:
                continue
                
            missing.append({
                'nama': row['nama_wisata'],
                'kab': row['kabupaten'],
                'alamat': row['alamat']
            })
    return missing

missing = find_missing_kab(df)
print(f"Total: {len(missing)}")
for m in missing:
    print(f"{m['nama']} | {m['kab']} | {m['alamat']}")
