import pandas as pd
import sys
sys.path.append('hasil_scrap')
from apply_bbox_fix import KAB_BBOX

df = pd.read_csv('hasil_final/wisata_sulawesi_lengkap.csv')
total = len(df)
out_of_bounds = []
missing_coords = 0

for i, row in df.iterrows():
    kab = str(row['kabupaten']).strip()
    lat, lon = row['lat'], row['long']
    if pd.isna(lat) or pd.isna(lon):
        missing_coords += 1
        continue
    if kab in KAB_BBOX:
        lmin, lmax, lnmin, lnmax = KAB_BBOX[kab]
        if not (lmin <= lat <= lmax and lnmin <= lon <= lnmax):
            out_of_bounds.append({
                'idx': i,
                'nama': row['nama_wisata'],
                'kab': kab,
                'prov': row['provinsi'],
                'lat': lat,
                'lon': lon,
                'alamat': str(row.get('alamat',''))
            })

print(f'Total data: {total}')
print(f'Missing coords: {missing_coords}')
print(f'Out of bbox: {len(out_of_bounds)}')
print()
for item in out_of_bounds[:30]:
    print(f"  [{item['idx']}] {item['nama']} | {item['kab']} | lat={item['lat']:.4f} lon={item['lon']:.4f}")
    print(f"       alamat: {item['alamat'][:80]}")
