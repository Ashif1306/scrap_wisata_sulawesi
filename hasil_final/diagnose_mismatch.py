import pandas as pd

df = pd.read_csv('wisata_sulawesi_fixed.csv')

def find_mismatches(df):
    mismatches = []
    # Daftar kata kunci kabupaten
    kab_keywords = {
        'makassar': 'Kota Makassar',
        'maros': 'Kabupaten Maros',
        'gowa': 'Kabupaten Gowa',
        'jeneponto': 'Kabupaten Jeneponto',
        'takalar': 'Kabupaten Takalar',
        'bantaeng': 'Kabupaten Bantaeng',
        'bulukumba': 'Kabupaten Bulukumba',
        'sinjai': 'Kabupaten Sinjai',
        'bone': 'Kabupaten Bone',
        'soppeng': 'Kabupaten Soppeng',
        'wajo': 'Kabupaten Wajo',
        'sidrap': 'Kabupaten Sidenreng Rappang',
        'pinrang': 'Kabupaten Pinrang',
        'enrekang': 'Kabupaten Enrekang',
        'parepare': 'Kota Parepare',
        'barru': 'Kabupaten Barru',
        'pangkep': 'Kabupaten Pangkajene Dan Kepulauan',
        'palopo': 'Kota Palopo',
        'luwu': 'Kabupaten Luwu',
        'toraja': 'Kabupaten Tana Toraja',
        'manado': 'Kota Manado',
        'kendari': 'Kota Kendari',
        'gorontalo': 'Kabupaten Gorontalo',
        'palu': 'Kota Palu'
    }
    
    for idx, row in df.iterrows():
        alamat = str(row['alamat']).lower()
        kab_current = str(row['kabupaten']).lower()
        
        for kw, full_name in kab_keywords.items():
            if kw in alamat and kw not in kab_current:
                # Filter pengecualian
                if kw == 'luwu' and 'luwu' in kab_current: continue
                if kw == 'bone' and 'bone bolango' in kab_current: continue
                if kw == 'gorontalo' and 'gorontalo' in kab_current: continue
                if kw == 'konawe' and 'konawe' in kab_current: continue
                if kw == 'makassar' and ('maros' in kab_current or 'gowa' in kab_current): 
                    continue
                
                mismatches.append({
                    'idx': idx,
                    'nama': row['nama_wisata'],
                    'alamat': row['alamat'],
                    'kab_skrg': row['kabupaten'],
                    'kab_mungkin': full_name
                })
                break
    return mismatches

mismatches = find_mismatches(df)
print(f"Total: {len(mismatches)}")
for m in mismatches[:50]:
    print(f"{m['nama']} | {m['kab_skrg']} -> {m['kab_mungkin']} | {m['alamat'][:60]}")
