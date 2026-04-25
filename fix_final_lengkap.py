"""
fix_final_lengkap.py
====================
Perbaikan final 2 lapis untuk wisata_sulawesi_lengkap.csv:
1. Perluas bounding box yang terlalu sempit untuk menampung area kepulauan
2. Perbaiki berdasarkan teks alamat fisik (lebih presisi dari bbox)
"""

import pandas as pd
import re
import sys
import math
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hasil_scrap'))
from apply_bbox_fix import KAB_TO_PROV

# ── BOUNDING BOX YANG DIPERLUAS (mencakup kepulauan) ──────────────
KAB_BBOX_EXT = {
    "Kota Makassar":                       (-5.27, -5.05, 119.34, 119.58),
    "Kabupaten Gowa":                       (-5.80, -4.80, 119.40, 120.50),
    "Kabupaten Maros":                      (-5.20, -4.60, 119.55, 120.15),
    "Kabupaten Pangkajene Dan Kepulauan":   (-4.95, -4.35, 119.35, 119.85),
    "Kabupaten Barru":                      (-4.65, -3.85, 119.60, 120.05),
    "Kabupaten Bone":                       (-5.10, -3.60, 119.75, 120.65),
    "Kabupaten Sinjai":                     (-5.45, -4.75, 119.85, 120.45),
    "Kabupaten Bulukumba":                  (-5.85, -5.10, 119.90, 120.60),
    "Kabupaten Bantaeng":                   (-5.75, -5.25, 119.70, 120.15),
    "Kabupaten Jeneponto":                  (-5.85, -5.35, 119.35, 120.05),
    "Kabupaten Takalar":                    (-5.65, -5.15, 119.30, 119.80),
    "Kabupaten Kepulauan Selayar":          (-7.30, -5.40, 120.00, 121.20),  # diperluas
    "Kabupaten Enrekang":                   (-3.90, -2.95, 119.55, 120.20),
    "Kabupaten Sidenreng Rappang":          (-4.35, -3.55, 119.70, 120.25),
    "Kabupaten Pinrang":                    (-4.45, -3.20, 119.35, 120.10),
    "Kabupaten Luwu":                       (-3.55, -2.40, 120.05, 120.65),
    "Kabupaten Luwu Utara":                 (-2.80, -2.25, 119.90, 120.75),
    "Kabupaten Luwu Timur":                 (-2.90, -2.05, 120.70, 121.90),
    "Kabupaten Tana Toraja":                (-3.50, -2.55, 119.45, 120.30),
    "Kabupaten Toraja Utara":               (-3.30, -2.55, 119.65, 120.35),
    "Kabupaten Soppeng":                    (-4.45, -3.75, 119.70, 120.25),
    "Kabupaten Wajo":                       (-4.35, -3.35, 119.85, 120.65),
    "Kota Parepare":                        (-4.08, -3.93, 119.58, 119.78),
    "Kota Palopo":                          (-3.08, -2.92, 120.16, 120.30),

    "Kabupaten Mamuju":                     (-2.80, -1.65, 118.70, 119.85),  # diperluas barat & selatan
    "Kabupaten Mamuju Tengah":              (-2.25, -1.55, 119.45, 120.05),
    "Kabupaten Pasangkayu":                 (-1.65, -0.75, 119.20, 120.05),
    "Kabupaten Majene":                     (-3.70, -2.95, 118.65, 119.35),  # diperluas barat
    "Kabupaten Polewali Mandar":            (-3.80, -3.15, 118.85, 119.65),
    "Kabupaten Mamasa":                     (-3.35, -2.55, 119.05, 119.85),

    "Kota Palu":                            (-1.05, -0.70, 119.75, 120.05),  # diperluas
    "Kabupaten Donggala":                   (-1.40,  0.55, 119.40, 120.25),
    "Kabupaten Sigi":                       (-2.00, -0.80, 119.50, 120.30),
    "Kabupaten Parigi Moutong":             (-1.00,  0.85, 119.85, 121.00),
    "Kabupaten Poso":                       (-2.10, -1.10, 120.10, 121.20),
    "Kabupaten Tojo Una-Una":               (-1.60, -0.05, 121.00, 122.40),
    "Kabupaten Banggai":                    (-2.10, -0.60, 121.75, 123.35),
    "Kabupaten Banggai Kepulauan":          (-2.40, -1.30, 122.60, 123.90),
    "Kabupaten Banggai Laut":              (-1.80, -0.70, 122.40, 123.30),
    "Kabupaten Morowali":                   (-3.30, -1.70, 121.30, 123.00),
    "Kabupaten Morowali Utara":             (-2.30, -0.85, 120.90, 122.30),
    "Kabupaten Tolitoli":                   (-1.05,  1.15, 120.25, 121.50),  # diperluas utara
    "Kabupaten Buol":                       (-0.10,  1.40, 120.80, 122.10),  # diperluas

    "Kota Manado":                          ( 1.38,  1.65, 124.70, 125.00),  # diperluas utara
    "Kota Bitung":                          ( 1.38,  1.65, 125.10, 125.35),  # diperluas
    "Kota Tomohon":                         ( 1.25,  1.48, 124.75, 124.98),
    "Kota Kotamobagu":                      ( 0.67,  0.77, 124.28, 124.40),
    "Kabupaten Minahasa":                   ( 1.00,  1.50, 124.55, 125.10),  # diperluas
    "Kabupaten Minahasa Utara":             ( 1.50,  1.95, 124.85, 125.30),  # diperluas utara
    "Kabupaten Minahasa Selatan":           ( 0.75,  1.25, 124.30, 124.95),  # diperluas
    "Kabupaten Minahasa Tenggara":          ( 0.55,  1.10, 124.55, 125.10),
    "Kabupaten Bolaang Mongondow":          ( 0.50,  1.10, 123.80, 124.80),
    "Kabupaten Bolaang Mongondow Utara":    ( 0.75,  1.30, 123.17, 123.90),  # diperluas utara
    "Kabupaten Bolaang Mongondow Selatan":  ( 0.30,  0.65, 123.65, 124.50),
    "Kabupaten Bolaang Mongondow Timur":    ( 0.50,  1.05, 124.30, 124.80),
    "Kabupaten Kepulauan Sangihe":          ( 2.60,  4.20, 125.20, 125.90),  # diperluas utara
    "Kabupaten Kepulauan Talaud":           ( 3.70,  5.60, 126.50, 127.30),  # diperluas sangat utara (Miangas)
    "Kabupaten Kepulauan Siau Tagulandang Biaro": (2.30, 2.90, 125.20, 125.70),  # diperluas

    "Kota Kendari":                         (-4.10, -3.90, 122.45, 122.65),
    "Kota Baubau":                          (-5.55, -5.38, 122.53, 122.78),  # diperluas
    "Kabupaten Konawe":                     (-4.40, -3.30, 121.80, 123.20),
    "Kabupaten Konawe Selatan":             (-4.90, -3.80, 121.70, 122.80),
    "Kabupaten Konawe Utara":               (-3.65, -2.50, 121.50, 122.70),
    "Kabupaten Konawe Kepulauan":           (-4.30, -3.75, 122.75, 123.25),  # diperluas
    "Kabupaten Kolaka":                     (-4.50, -3.50, 121.30, 122.15),  # diperluas barat
    "Kabupaten Kolaka Utara":               (-3.65, -2.60, 120.70, 121.90),  # diperluas barat
    "Kabupaten Kolaka Timur":               (-4.50, -3.60, 121.70, 122.35),
    "Kabupaten Bombana":                    (-5.45, -4.50, 121.40, 122.50),  # diperluas
    "Kabupaten Buton":                      (-5.75, -4.85, 122.35, 123.20),  # diperluas
    "Kabupaten Buton Utara":                (-5.05, -4.15, 122.65, 123.30),  # diperluas
    "Kabupaten Buton Tengah":               (-5.35, -4.85, 122.30, 122.90),
    "Kabupaten Buton Selatan":              (-5.70, -5.15, 122.35, 122.95),
    "Kabupaten Muna":                       (-5.35, -4.55, 122.00, 122.85),
    "Kabupaten Muna Barat":                 (-5.20, -4.60, 121.70, 122.35),
    "Kabupaten Wakatobi":                   (-6.30, -5.20, 123.30, 124.30),  # diperluas

    "Kota Gorontalo":                       ( 0.52,  0.63, 122.99, 123.11),
    "Kabupaten Gorontalo":                  ( 0.38,  0.82, 122.15, 123.20),  # diperluas
    "Kabupaten Gorontalo Utara":            ( 0.65,  1.05, 122.10, 123.20),  # diperluas
    "Kabupaten Bone Bolango":               ( 0.30,  0.80, 122.95, 123.50),
    "Kabupaten Boalemo":                    ( 0.35,  0.90, 121.95, 122.65),
    "Kabupaten Pohuwato":                   ( 0.38,  0.95, 121.10, 122.15),
}

# Mapping nama kab dari alamat → nama resmi (untuk perbaikan berbasis alamat)
VALID_KAB_KOTA = list(KAB_BBOX_EXT.keys())

def norm(s):
    return re.sub(r'\s+', ' ', str(s).strip().lower())

def parse_kab_dari_alamat(alamat):
    """Cari nama kabupaten paling panjang yang cocok dalam alamat."""
    al = str(alamat).lower()
    best = None
    best_len = 0
    for k in sorted(VALID_KAB_KOTA, key=len, reverse=True):
        if norm(k) in al:
            if len(k) > best_len:
                best = k
                best_len = len(k)
    return best

def point_to_bbox_distance(lat, lon, lmin, lmax, lnmin, lnmax):
    dx = max(lnmin - lon, 0, lon - lnmax)
    dy = max(lmin - lat, 0, lat - lmax)
    return math.sqrt(dx*dx + dy*dy)

def find_nearest_kab(lat, lon):
    min_dist = float('inf')
    best = None
    for kab, (lmin, lmax, lnmin, lnmax) in KAB_BBOX_EXT.items():
        dist = point_to_bbox_distance(lat, lon, lmin, lmax, lnmin, lnmax)
        if dist < min_dist:
            min_dist = dist
            best = kab
    return best, min_dist

# ── MAIN ──────────────────────────────────────────────────────────
file_path = 'd:/semester6/mc_learning/scrapt_wisata/hasil_final/wisata_sulawesi_lengkap.csv'
df = pd.read_csv(file_path)
print(f"Total data: {len(df)}")

fixes_alamat = 0
fixes_bbox = 0

for idx, row in df.iterrows():
    kab_asli = str(row['kabupaten']).strip()
    lat = row['lat']
    lon = row['long']

    if pd.isna(lat) or pd.isna(lon):
        continue

    # --- LAPIS 1: Cek apakah sudah masuk bbox diperluas ---
    in_bbox = False
    if kab_asli in KAB_BBOX_EXT:
        lmin, lmax, lnmin, lnmax = KAB_BBOX_EXT[kab_asli]
        if lmin <= lat <= lmax and lnmin <= lon <= lnmax:
            in_bbox = True

    if in_bbox:
        continue  # Sudah benar, skip

    # --- LAPIS 2: Coba parse dari alamat ---
    kab_dari_alamat = parse_kab_dari_alamat(row.get('alamat', ''))
    if kab_dari_alamat and kab_dari_alamat != kab_asli:
        # Validasi: apakah koordinat masuk bbox kabupaten dari alamat?
        if kab_dari_alamat in KAB_BBOX_EXT:
            lmin, lmax, lnmin, lnmax = KAB_BBOX_EXT[kab_dari_alamat]
            if lmin <= lat <= lmax and lnmin <= lon <= lnmax:
                print(f"[ALAMAT] {row['nama_wisata']}: {kab_asli} -> {kab_dari_alamat}")
                df.at[idx, 'kabupaten'] = kab_dari_alamat
                df.at[idx, 'provinsi'] = KAB_TO_PROV.get(kab_dari_alamat, row['provinsi'])
                fixes_alamat += 1
                continue

    # --- LAPIS 3: Snap ke bbox terdekat ---
    nearest, dist = find_nearest_kab(lat, lon)
    if nearest and nearest != kab_asli:
        print(f"[BBOX]   {row['nama_wisata']}: {kab_asli} -> {nearest} (dist={dist:.4f})")
        df.at[idx, 'kabupaten'] = nearest
        df.at[idx, 'provinsi'] = KAB_TO_PROV.get(nearest, row['provinsi'])
        fixes_bbox += 1

total_fixes = fixes_alamat + fixes_bbox
print(f"\n{'='*60}")
print(f"Fix dari alamat : {fixes_alamat}")
print(f"Fix dari bbox   : {fixes_bbox}")
print(f"Total fix       : {total_fixes}")

if total_fixes > 0:
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"Tersimpan ke {file_path}")

# Hitung sisa yang masih out of bbox
sisa = 0
for idx, row in df.iterrows():
    kab = str(row['kabupaten']).strip()
    lat, lon = row['lat'], row['long']
    if pd.isna(lat) or pd.isna(lon): continue
    if kab in KAB_BBOX_EXT:
        lmin, lmax, lnmin, lnmax = KAB_BBOX_EXT[kab]
        if not (lmin <= lat <= lmax and lnmin <= lon <= lnmax):
            sisa += 1
print(f"Sisa out-of-bbox: {sisa}")
