"""
diagnose_nyasar.py — Cari data yang kabupatennya tidak cocok dengan koordinatnya.
Misalnya: kabupaten = "Kota Makassar" tapi koordinat jauh dari Makassar.
"""
import pandas as pd
import math
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Bounding box kasar tiap kabupaten/kota (lat_min, lat_max, lon_min, lon_max)
# Kota Makassar: sekitar -5.22 s/d -5.05, 119.35 s/d 119.55
BBOX = {
    "Kota Makassar": (-5.25, -5.00, 119.30, 119.55),
    "Kota Parepare": (-4.10, -3.95, 119.58, 119.68),
    "Kota Palopo": (-3.05, -2.90, 120.15, 120.25),
    "Kota Palu": (-1.00, -0.80, 119.80, 120.00),
    "Kota Manado": (1.40, 1.56, 124.78, 124.92),
    "Kota Gorontalo": (0.50, 0.60, 123.02, 123.10),
    "Kota Kendari": (-4.10, -3.90, 122.40, 122.65),
    "Kota Baubau": (-5.55, -5.40, 122.50, 122.70),
    "Kota Tomohon": (1.28, 1.38, 124.80, 124.90),
    "Kota Bitung": (1.40, 1.50, 125.10, 125.25),
    "Kota Kotamobagu": (0.70, 0.80, 124.28, 124.38),
}

# Centroid kasar tiap kabupaten (untuk estimasi jarak)
# Jika tidak ada bbox, pakai centroid + radius
CENTROID = {
    "Kota Makassar": (-5.14, 119.41),
    "Kota Parepare": (-4.01, 119.63),
    "Kota Palopo": (-2.99, 120.20),
    "Kota Palu": (-0.90, 119.89),
    "Kota Manado": (1.49, 124.84),
    "Kota Gorontalo": (0.54, 123.06),
    "Kota Kendari": (-3.97, 122.51),
    "Kota Baubau": (-5.47, 122.60),
    "Kota Tomohon": (1.32, 124.85),
    "Kota Bitung": (1.45, 125.18),
    "Kota Kotamobagu": (0.72, 124.32),
}

def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.asin(math.sqrt(a))

df = pd.read_csv('wisata_terkoreksi_geo.csv')

print("=" * 70)
print("DIAGNOSA: Data yang koordinatnya jauh dari kabupaten yang tercatat")
print("=" * 70)

# Untuk setiap kab/kota yang punya centroid, cek entri yang jauh
MAX_DISTANCE_KM = 40  # threshold: >40km dianggap nyasar

nyasar = []
for i, row in df.iterrows():
    kab = str(row['kabupaten']).strip()
    lat = row.get('lat')
    lon = row.get('long')
    
    if pd.isna(lat) or pd.isna(lon):
        continue
    
    if kab in CENTROID:
        clat, clon = CENTROID[kab]
        dist = haversine_km(lat, lon, clat, clon)
        if dist > MAX_DISTANCE_KM:
            nyasar.append({
                'idx': i,
                'nama': row['nama_wisata'],
                'kabupaten': kab,
                'lat': lat,
                'lon': lon,
                'jarak_km': round(dist, 1),
                'alamat': str(row.get('alamat', ''))[:80],
            })

# Juga cek semua kabupaten — cari yang koordinat-nya sangat jauh dari semua kab/kota di provinsi yang sama
# Simplified: just check Kota entries for now

nyasar.sort(key=lambda x: x['jarak_km'], reverse=True)

print(f"\nTotal data 'nyasar' (jarak > {MAX_DISTANCE_KM} km dari centroid kab/kota): {len(nyasar)}")
print()

for n in nyasar:
    print(f"  [{n['idx']:4d}] {n['nama'][:50]}")
    print(f"         kab: {n['kabupaten']} | jarak: {n['jarak_km']} km | lat: {n['lat']}, lon: {n['lon']}")
    print(f"         alamat: {n['alamat']}")
    print()
