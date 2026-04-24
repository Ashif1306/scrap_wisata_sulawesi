import pandas as pd

df = pd.read_csv('wisata_sulawesi_cleaned_final.csv')

# 1318 - Pemancingan Riboko Balla → Borongpa'la'la = Bulukumba
df.at[1318, 'kabupaten'] = 'Kabupaten Bulukumba'
df.at[1318, 'provinsi']  = 'Sulawesi Selatan'

# 2199 - LORONG WISATA SILVES → kabupaten sudah ada, tinggal provinsi
df.at[2199, 'provinsi']  = 'Sulawesi Selatan'

# 2215 - Air panas kelewaha → Lobu Dua ada di Bitung, Sulawesi Utara
df.at[2215, 'kabupaten'] = 'Kota Bitung'
df.at[2215, 'provinsi']  = 'Sulawesi Utara'

# 2427 - Kolam pemancingan keluarga H. Jafar → Empagae adalah wilayah di Sulawesi Selatan (Barru)
# Hapus Kabupaten Sambas (salah/Kalimantan), ganti ke Barru, Sulsel
df.at[2427, 'kabupaten'] = 'Kabupaten Barru'
df.at[2427, 'provinsi']  = 'Sulawesi Selatan'

df.to_csv('wisata_sulawesi_cleaned_final.csv', index=False, encoding='utf-8-sig')

# Verifikasi
mask_kab  = df['kabupaten'].isna() | (df['kabupaten'].astype(str).str.strip().isin(['', 'nan']))
mask_prov = df['provinsi'].isna()  | (df['provinsi'].astype(str).str.strip().isin(['', 'nan']))
print(f"Kabupaten kosong sisa: {mask_kab.sum()}")
print(f"Provinsi kosong sisa : {mask_prov.sum()}")
print("✓ Semua data lengkap!" if mask_kab.sum() == 0 and mask_prov.sum() == 0 else "Masih ada yang kosong.")
print()
print("Contoh data yang diperbaiki:")
print(df.loc[[1318, 2199, 2215, 2427], ['nama_wisata','kabupaten','provinsi']].to_string())
