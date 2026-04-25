"""
fix_nyasar.py — Perbaiki data yang kabupatennya tidak cocok dengan koordinat.
Menggunakan reverse geocoding untuk menentukan kabupaten yang benar.
"""
import pandas as pd
import re
import time
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VALID_KAB_KOTA = [
    "Kota Makassar","Kota Palopo","Kota Parepare",
    "Kabupaten Bantaeng","Kabupaten Barru","Kabupaten Bone",
    "Kabupaten Bulukumba","Kabupaten Enrekang","Kabupaten Gowa",
    "Kabupaten Jeneponto","Kabupaten Kepulauan Selayar",
    "Kabupaten Luwu","Kabupaten Luwu Timur","Kabupaten Luwu Utara",
    "Kabupaten Maros","Kabupaten Pangkajene Dan Kepulauan",
    "Kabupaten Pinrang","Kabupaten Sidenreng Rappang",
    "Kabupaten Sinjai","Kabupaten Soppeng","Kabupaten Takalar",
    "Kabupaten Tana Toraja","Kabupaten Toraja Utara","Kabupaten Wajo",
    "Kabupaten Mamuju","Kabupaten Majene","Kabupaten Polewali Mandar",
    "Kabupaten Mamasa","Kabupaten Pasangkayu","Kabupaten Mamuju Tengah",
    "Kota Palu","Kabupaten Banggai","Kabupaten Banggai Kepulauan",
    "Kabupaten Banggai Laut","Kabupaten Buol","Kabupaten Donggala",
    "Kabupaten Morowali","Kabupaten Morowali Utara",
    "Kabupaten Parigi Moutong","Kabupaten Poso","Kabupaten Sigi",
    "Kabupaten Tojo Una-Una","Kabupaten Tolitoli",
    "Kota Manado","Kota Bitung","Kota Tomohon","Kota Kotamobagu",
    "Kabupaten Bolaang Mongondow","Kabupaten Bolaang Mongondow Selatan",
    "Kabupaten Bolaang Mongondow Timur","Kabupaten Bolaang Mongondow Utara",
    "Kabupaten Kepulauan Sangihe","Kabupaten Kepulauan Siau Tagulandang Biaro",
    "Kabupaten Kepulauan Talaud","Kabupaten Minahasa",
    "Kabupaten Minahasa Selatan","Kabupaten Minahasa Tenggara",
    "Kabupaten Minahasa Utara",
    "Kota Kendari","Kota Baubau",
    "Kabupaten Bombana","Kabupaten Buton","Kabupaten Buton Selatan",
    "Kabupaten Buton Tengah","Kabupaten Buton Utara",
    "Kabupaten Kolaka","Kabupaten Kolaka Timur","Kabupaten Kolaka Utara",
    "Kabupaten Konawe","Kabupaten Konawe Kepulauan",
    "Kabupaten Konawe Selatan","Kabupaten Konawe Utara",
    "Kabupaten Muna","Kabupaten Muna Barat","Kabupaten Wakatobi",
    "Kota Gorontalo","Kabupaten Boalemo","Kabupaten Bone Bolango",
    "Kabupaten Gorontalo Utara","Kabupaten Pohuwato","Kabupaten Gorontalo",
]
VALID_SORTED = sorted(VALID_KAB_KOTA, key=len, reverse=True)

KAB_TO_PROV = {
    "Kota Makassar":"Sulawesi Selatan","Kota Palopo":"Sulawesi Selatan","Kota Parepare":"Sulawesi Selatan",
    "Kabupaten Bantaeng":"Sulawesi Selatan","Kabupaten Barru":"Sulawesi Selatan","Kabupaten Bone":"Sulawesi Selatan",
    "Kabupaten Bulukumba":"Sulawesi Selatan","Kabupaten Enrekang":"Sulawesi Selatan","Kabupaten Gowa":"Sulawesi Selatan",
    "Kabupaten Jeneponto":"Sulawesi Selatan","Kabupaten Kepulauan Selayar":"Sulawesi Selatan",
    "Kabupaten Luwu":"Sulawesi Selatan","Kabupaten Luwu Timur":"Sulawesi Selatan","Kabupaten Luwu Utara":"Sulawesi Selatan",
    "Kabupaten Maros":"Sulawesi Selatan","Kabupaten Pangkajene Dan Kepulauan":"Sulawesi Selatan",
    "Kabupaten Pinrang":"Sulawesi Selatan","Kabupaten Sidenreng Rappang":"Sulawesi Selatan",
    "Kabupaten Sinjai":"Sulawesi Selatan","Kabupaten Soppeng":"Sulawesi Selatan","Kabupaten Takalar":"Sulawesi Selatan",
    "Kabupaten Tana Toraja":"Sulawesi Selatan","Kabupaten Toraja Utara":"Sulawesi Selatan","Kabupaten Wajo":"Sulawesi Selatan",
    "Kabupaten Mamuju":"Sulawesi Barat","Kabupaten Majene":"Sulawesi Barat","Kabupaten Polewali Mandar":"Sulawesi Barat",
    "Kabupaten Mamasa":"Sulawesi Barat","Kabupaten Pasangkayu":"Sulawesi Barat","Kabupaten Mamuju Tengah":"Sulawesi Barat",
    "Kota Palu":"Sulawesi Tengah","Kabupaten Banggai":"Sulawesi Tengah","Kabupaten Banggai Kepulauan":"Sulawesi Tengah",
    "Kabupaten Banggai Laut":"Sulawesi Tengah","Kabupaten Buol":"Sulawesi Tengah","Kabupaten Donggala":"Sulawesi Tengah",
    "Kabupaten Morowali":"Sulawesi Tengah","Kabupaten Morowali Utara":"Sulawesi Tengah",
    "Kabupaten Parigi Moutong":"Sulawesi Tengah","Kabupaten Poso":"Sulawesi Tengah","Kabupaten Sigi":"Sulawesi Tengah",
    "Kabupaten Tojo Una-Una":"Sulawesi Tengah","Kabupaten Tolitoli":"Sulawesi Tengah",
    "Kota Manado":"Sulawesi Utara","Kota Bitung":"Sulawesi Utara","Kota Tomohon":"Sulawesi Utara","Kota Kotamobagu":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow":"Sulawesi Utara","Kabupaten Bolaang Mongondow Selatan":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow Timur":"Sulawesi Utara","Kabupaten Bolaang Mongondow Utara":"Sulawesi Utara",
    "Kabupaten Kepulauan Sangihe":"Sulawesi Utara","Kabupaten Kepulauan Siau Tagulandang Biaro":"Sulawesi Utara",
    "Kabupaten Kepulauan Talaud":"Sulawesi Utara","Kabupaten Minahasa":"Sulawesi Utara",
    "Kabupaten Minahasa Selatan":"Sulawesi Utara","Kabupaten Minahasa Tenggara":"Sulawesi Utara","Kabupaten Minahasa Utara":"Sulawesi Utara",
    "Kota Kendari":"Sulawesi Tenggara","Kota Baubau":"Sulawesi Tenggara",
    "Kabupaten Bombana":"Sulawesi Tenggara","Kabupaten Buton":"Sulawesi Tenggara","Kabupaten Buton Selatan":"Sulawesi Tenggara",
    "Kabupaten Buton Tengah":"Sulawesi Tenggara","Kabupaten Buton Utara":"Sulawesi Tenggara",
    "Kabupaten Kolaka":"Sulawesi Tenggara","Kabupaten Kolaka Timur":"Sulawesi Tenggara","Kabupaten Kolaka Utara":"Sulawesi Tenggara",
    "Kabupaten Konawe":"Sulawesi Tenggara","Kabupaten Konawe Kepulauan":"Sulawesi Tenggara",
    "Kabupaten Konawe Selatan":"Sulawesi Tenggara","Kabupaten Konawe Utara":"Sulawesi Tenggara",
    "Kabupaten Muna":"Sulawesi Tenggara","Kabupaten Muna Barat":"Sulawesi Tenggara","Kabupaten Wakatobi":"Sulawesi Tenggara",
    "Kota Gorontalo":"Gorontalo","Kabupaten Boalemo":"Gorontalo","Kabupaten Bone Bolango":"Gorontalo",
    "Kabupaten Gorontalo Utara":"Gorontalo","Kabupaten Pohuwato":"Gorontalo","Kabupaten Gorontalo":"Gorontalo",
}

def reverse_geocode(lat, lon):
    from geopy.geocoders import Nominatim
    geolocator = Nominatim(user_agent="wisata_fix_nyasar_v1", timeout=10)
    location = geolocator.reverse(f"{lat}, {lon}", language="id")
    if location and location.raw:
        addr = location.raw.get('address', {})
        candidate = addr.get('county', '') or addr.get('city', '') or addr.get('town', '')
        if candidate:
            cl = candidate.lower()
            for kab in VALID_SORTED:
                kl = kab.lower()
                ks = kl.replace('kabupaten ', '').replace('kota ', '')
                if kl in cl or ks in cl or cl in kl:
                    return kab
    return None

# Data yang nyasar (dari diagnosa sebelumnya)
NYASAR_INDICES = {
    1342: {"nama": "Pantai Babana",                       "lat": -2.0916328, "lon": 119.1943106},
    744:  {"nama": "Tanjung Ngalo Mamuju",                 "lat": -2.8666905, "lon": 118.7693474},
    1008: {"nama": "Pantai Salopi",                        "lat": -3.5215298, "lon": 119.4929373},
    883:  {"nama": "Taman Kota Sengkang Kabupaten Wajo",   "lat": -4.1351913, "lon": 120.0283347},
    682:  {"nama": "Pantai Sarena",                        "lat": 1.4599273,  "lon": 125.2333494},
}

df = pd.read_csv('wisata_sulawesi_lengkap.csv')

print("=" * 70)
print("FIX DATA NYASAR — Perbaiki kabupaten berdasarkan koordinat")
print("=" * 70)

fixes = []
for idx, info in NYASAR_INDICES.items():
    print(f"\n[{idx}] {info['nama']}")
    print(f"  Koordinat: {info['lat']}, {info['lon']}")
    print(f"  Kab lama: {df.at[idx, 'kabupaten']}")
    
    kab_baru = reverse_geocode(info['lat'], info['lon'])
    if kab_baru:
        prov_baru = KAB_TO_PROV.get(kab_baru, '')
        print(f"  Kab baru: {kab_baru} ({prov_baru})")
        
        df.at[idx, 'kabupaten'] = kab_baru
        df.at[idx, 'provinsi'] = prov_baru
        fixes.append({'idx': idx, 'nama': info['nama'], 'lama': 'Kota Makassar', 'baru': kab_baru})
    else:
        print(f"  GAGAL reverse geocode!")
    
    time.sleep(1.2)

# Also fix in kabupaten_provinsi.csv
df_kab = pd.read_csv('kabupaten_provinsi.csv')
for f in fixes:
    idx = f['idx']
    pid = df.at[idx, 'place_id']
    mask = df_kab['place_id'] == pid
    if mask.any():
        df_kab.loc[mask, 'kabupaten'] = f['baru']
        df_kab.loc[mask, 'provinsi'] = KAB_TO_PROV.get(f['baru'], '')

print(f"\n{'=' * 70}")
print(f"Total diperbaiki: {len(fixes)}")
for f in fixes:
    print(f"  [{f['idx']}] {f['nama']}: {f['lama']} → {f['baru']}")

df.to_csv('wisata_sulawesi_lengkap.csv', index=False, encoding='utf-8-sig')
df_kab.to_csv('kabupaten_provinsi.csv', index=False, encoding='utf-8')
print(f"\nDisimpan ke wisata_sulawesi_lengkap.csv dan kabupaten_provinsi.csv")
print("=" * 70)
