"""Fix manual: Taman Kota Sengkang → Kabupaten Wajo"""
import pandas as pd
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Fix wisata_sulawesi_lengkap.csv
df = pd.read_csv('wisata_sulawesi_lengkap.csv')
idx = 883
print(f"Sebelum: [{idx}] {df.at[idx, 'nama_wisata']} | kab: {df.at[idx, 'kabupaten']} | prov: {df.at[idx, 'provinsi']}")
df.at[idx, 'kabupaten'] = 'Kabupaten Wajo'
df.at[idx, 'provinsi'] = 'Sulawesi Selatan'
print(f"Sesudah: [{idx}] {df.at[idx, 'nama_wisata']} | kab: {df.at[idx, 'kabupaten']} | prov: {df.at[idx, 'provinsi']}")
df.to_csv('wisata_sulawesi_lengkap.csv', index=False, encoding='utf-8-sig')

# Fix kabupaten_provinsi.csv
df_kab = pd.read_csv('kabupaten_provinsi.csv')
pid = df.at[idx, 'place_id']
mask = df_kab['place_id'] == pid
if mask.any():
    df_kab.loc[mask, 'kabupaten'] = 'Kabupaten Wajo'
    df_kab.loc[mask, 'provinsi'] = 'Sulawesi Selatan'
    df_kab.to_csv('kabupaten_provinsi.csv', index=False, encoding='utf-8')

print("Done!")
