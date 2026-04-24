import pandas as pd

df = pd.read_csv('wisata_sulawesi_cleaned_final.csv')
print(f"Total data: {len(df)}")
print(f"Kabupaten kosong: {df['kabupaten'].isna().sum()}")
print(f"Provinsi kosong : {df['provinsi'].isna().sum()}")
print()

mask_kab  = df['kabupaten'].isna() | (df['kabupaten'].astype(str).str.strip().isin(['', 'nan']))
mask_prov = df['provinsi'].isna()  | (df['provinsi'].astype(str).str.strip().isin(['', 'nan']))
mask      = mask_kab | mask_prov

print(f"Baris dengan kabupaten/provinsi kosong: {mask.sum()}")
print()
cols = ['nama_wisata', 'alamat', 'kabupaten', 'provinsi']
print(df[mask][cols].to_string(index=True))
