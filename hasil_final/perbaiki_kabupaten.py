import pandas as pd
import re
import sys
import os

# Reconfigure stdout to handle unicode characters like checkmarks
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, 'wisata_sulawesi_lengkap.csv')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'wisata_sulawesi_fixed.csv')


df = pd.read_csv(INPUT_FILE)
original_kabupaten = df['kabupaten'].copy()
changes_log = []

# ============================================================
# 1. PERBAIKAN NAMA KABUPATEN YANG JELAS-JELAS SALAH/TYPO
# ============================================================

# Kota Bau-Bau -> Kota Baubau (standardisasi ejaan resmi)
mask = df['kabupaten'] == 'Kota Bau-Bau'
df.loc[mask, 'kabupaten'] = 'Kota Baubau'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kota Bau-Bau' -> 'Kota Baubau'")

# Kotamobagu -> Kota Kotamobagu
mask = df['kabupaten'] == 'Kotamobagu'
df.loc[mask, 'kabupaten'] = 'Kota Kotamobagu'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kotamobagu' -> 'Kota Kotamobagu'")

# ============================================================
# 2. PERBAIKAN KABUPATEN YANG SALAH TOTAL (BUKAN SULAWESI)
# ============================================================

# 'Kota Jakarta Selatan' - Pantai Wajo, berdasarkan koordinat (-5.49, 122.84) 
# dan provinsi=Sulawesi Tenggara -> Kabupaten Muna
mask = df['kabupaten'] == 'Kota Jakarta Selatan'
df.loc[mask, 'kabupaten'] = 'Kabupaten Muna'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kota Jakarta Selatan' -> 'Kabupaten Muna'")

# 'Kabupaten Province of Davao Oriental' -> Kabupaten Kepulauan Talaud
# (berdasarkan alamat: Miangas, Kabupaten Kepulauan Talaud)
mask = df['kabupaten'] == 'Kabupaten Province of Davao Oriental'
df.loc[mask, 'kabupaten'] = 'Kabupaten Kepulauan Talaud'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kabupaten Province of Davao Oriental' -> 'Kabupaten Kepulauan Talaud'")

# ============================================================
# 3. PERBAIKAN KABUPATEN PARSIAL/TIDAK LENGKAP
# ============================================================

# 'Kabupaten  Utara' (spasi ganda) -> Kabupaten Gorontalo Utara
# (berdasarkan alamat: Kabupaten Gorontalo Utara)
mask = df['kabupaten'] == 'Kabupaten  Utara'
df.loc[mask, 'kabupaten'] = 'Kabupaten Gorontalo Utara'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kabupaten  Utara' -> 'Kabupaten Gorontalo Utara'")

# ============================================================
# 4. PERBAIKAN KABUPATEN YANG SALAH (NAMA KECAMATAN/KELURAHAN DIJADIKAN KABUPATEN)
# ============================================================

# 'Kota Timur Tanamodindi Mantikulore' -> Kota Palu
# (berdasarkan alamat: Kota Palu, Sulawesi Tengah)
mask = df['kabupaten'] == 'Kota Timur Tanamodindi Mantikulore'
df.loc[mask, 'kabupaten'] = 'Kota Palu'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kota Timur Tanamodindi Mantikulore' -> 'Kota Palu'")

# 'Kota Pulu' -> Kabupaten Sigi (bukan Kota Palu)
# (berdasarkan alamat: Kabupaten Sigi, Sulawesi Tengah)
mask = df['kabupaten'] == 'Kota Pulu'
df.loc[mask, 'kabupaten'] = 'Kabupaten Sigi'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kota Pulu' -> 'Kabupaten Sigi'")

# 'Kota Jin' -> Kabupaten Gorontalo Utara
# (berdasarkan alamat: Kec. Atinggola, Kabupaten Gorontalo Utara)
mask = df['kabupaten'] == 'Kota Jin'
df.loc[mask, 'kabupaten'] = 'Kabupaten Gorontalo Utara'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kota Jin' -> 'Kabupaten Gorontalo Utara'")

# 'Kota Tentena' -> Kabupaten Poso
# (berdasarkan alamat: Kec. Pamona Utara, Kabupaten Poso)
mask = df['kabupaten'] == 'Kota Tentena'
df.loc[mask, 'kabupaten'] = 'Kabupaten Poso'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kota Tentena' -> 'Kabupaten Poso'")

# 'Kota Utara' -> Kabupaten Poso
# (berdasarkan alamat: Kec. Poso Kota Utara, Kabupaten Poso)
mask = df['kabupaten'] == 'Kota Utara'
df.loc[mask, 'kabupaten'] = 'Kabupaten Poso'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kota Utara' -> 'Kabupaten Poso'")

# 'Kota Menara' -> Kabupaten Minahasa Tenggara
# (berdasarkan alamat: Kec. Silian Raya, Kabupaten Minahasa Tenggara)
mask = df['kabupaten'] == 'Kota Menara'
df.loc[mask, 'kabupaten'] = 'Kabupaten Minahasa Tenggara'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] 'Kota Menara' -> 'Kabupaten Minahasa Tenggara'")

# ============================================================
# 5. PERBAIKAN BERDASARKAN NAMA WISATA / KOORDINAT SPESIFIK
# ============================================================

# TN Bantimurung Bulusaraung yang masuk ke Kabupaten Bone -> Kabupaten Maros
# (hanya yang place_id tertentu, bukan yang sudah benar di Maros)
mask = (df['nama_wisata'].str.contains('Bantimurung Bulusaraung', na=False)) & \
       (df['kabupaten'] == 'Kabupaten Bone')
df.loc[mask, 'kabupaten'] = 'Kabupaten Maros'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] TN Bantimurung Bulusaraung: 'Kabupaten Bone' -> 'Kabupaten Maros'")

# Cinta Souvenir Bantimurung: Kota Makassar -> Kabupaten Maros
# (alamat: Kalabbirang, Kec. Bantimurung -> Maros)
mask = (df['nama_wisata'] == 'Cinta Souvenir Bantimurung') & \
       (df['kabupaten'] == 'Kota Makassar')
df.loc[mask, 'kabupaten'] = 'Kabupaten Maros'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] Cinta Souvenir Bantimurung: 'Kota Makassar' -> 'Kabupaten Maros'")

# Tongkonan Buntu: Kabupaten Bone -> Kabupaten Toraja Utara
# (koordinat: -2.96085, 119.903415 -> area Toraja Utara)
mask = (df['nama_wisata'] == 'Tongkonan Buntu') & (df['kabupaten'] == 'Kabupaten Bone')
df.loc[mask, 'kabupaten'] = 'Kabupaten Toraja Utara'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] Tongkonan Buntu: 'Kabupaten Bone' -> 'Kabupaten Toraja Utara'")

# Tugu Adipura: Kota Kendari -> Kabupaten Konawe (berdasarkan alamat)
mask = (df['nama_wisata'] == 'Tugu Adipura') & (df['kabupaten'] == 'Kota Kendari')
df.loc[mask, 'kabupaten'] = 'Kabupaten Konawe'
n = mask.sum()
if n: changes_log.append(f"[{n} baris] Tugu Adipura: 'Kota Kendari' -> 'Kabupaten Konawe'")

# ============================================================
# 6. PERBAIKAN MASSAL: Kota Kendari -> kabupaten yang benar (berdasarkan alamat)
# ============================================================

def fix_kota_kendari(row):
    if row['kabupaten'] != 'Kota Kendari':
        return row['kabupaten']
    alamat = str(row['alamat']) if pd.notna(row['alamat']) else ''
    m = re.search(r'Kabupaten ([^,]+),', alamat)
    if m:
        return 'Kabupaten ' + m.group(1).strip()
    return row['kabupaten']  # tetap Kota Kendari jika tidak ada petunjuk lain

# Terapkan hanya jika alamat mengandung Kabupaten lain
kendari_mask = df['kabupaten'] == 'Kota Kendari'
new_vals = df[kendari_mask].apply(fix_kota_kendari, axis=1)
changed_indices = new_vals[new_vals != df.loc[kendari_mask, 'kabupaten']].index
df.loc[changed_indices, 'kabupaten'] = new_vals[changed_indices]
n = len(changed_indices)
if n: changes_log.append(f"[{n} baris] 'Kota Kendari' diperbaiki ke kabupaten yang sesuai alamat")

# ============================================================
# 7. SIMPAN HASIL
# ============================================================

df.drop(columns=['kab_from_alamat'], errors='ignore', inplace=True)
df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

# Hitung total perubahan
total_changed = (df['kabupaten'] != original_kabupaten).sum()

print("=" * 60)
print("LAPORAN PERBAIKAN DATA KABUPATEN")
print("=" * 60)
for log in changes_log:
    print(f"  ✓ {log}")
print()
print(f"Total baris yang diperbaiki : {total_changed}")
print(f"Total baris data            : {len(df)}")
print(f"Output disimpan ke          : {OUTPUT_FILE}")
print("=" * 60)