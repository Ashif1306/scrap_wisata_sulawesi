"""
=================================================================
PERBAIKAN KABUPATEN WISATA SULAWESI
=================================================================
Strategi (berlapis):
  1. Perbaikan typo / nama tidak standar
  2. Koreksi kabupaten di luar Sulawesi / jelas salah
  3. Perbaikan nama kecamatan/kelurahan yang dijadikan kabupaten
  4. OTOMATIS: ekstrak kabupaten dari kolom 'alamat' via regex
     dan update jika ditemukan nama valid yang BERBEDA dengan
     nilai saat ini.
  5. Perbaikan spesifik berdasarkan nama wisata / koordinat
=================================================================
"""

import pandas as pd
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(SCRIPT_DIR, 'wisata_sulawesi_lengkap.csv')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'wisata_sulawesi_fixed.csv')

# ── DAFTAR VALID ──────────────────────────────────────────────────────────────
VALID_KAB_KOTA = [
    # Sulawesi Selatan
    "Kota Makassar", "Kota Palopo", "Kota Parepare",
    "Kabupaten Bantaeng", "Kabupaten Barru", "Kabupaten Bone",
    "Kabupaten Bulukumba", "Kabupaten Enrekang", "Kabupaten Gowa",
    "Kabupaten Jeneponto", "Kabupaten Kepulauan Selayar",
    "Kabupaten Luwu", "Kabupaten Luwu Timur", "Kabupaten Luwu Utara",
    "Kabupaten Maros", "Kabupaten Pangkajene Dan Kepulauan",
    "Kabupaten Pinrang", "Kabupaten Sidenreng Rappang",
    "Kabupaten Sinjai", "Kabupaten Soppeng", "Kabupaten Takalar",
    "Kabupaten Tana Toraja", "Kabupaten Toraja Utara", "Kabupaten Wajo",
    # Sulawesi Barat
    "Kabupaten Mamuju", "Kabupaten Majene", "Kabupaten Polewali Mandar",
    "Kabupaten Mamasa", "Kabupaten Pasangkayu", "Kabupaten Mamuju Tengah",
    # Sulawesi Tengah
    "Kota Palu", "Kabupaten Banggai", "Kabupaten Banggai Kepulauan",
    "Kabupaten Banggai Laut", "Kabupaten Buol", "Kabupaten Donggala",
    "Kabupaten Morowali", "Kabupaten Morowali Utara",
    "Kabupaten Parigi Moutong", "Kabupaten Poso", "Kabupaten Sigi",
    "Kabupaten Tojo Una-Una", "Kabupaten Tolitoli",
    # Sulawesi Utara
    "Kota Manado", "Kota Bitung", "Kota Tomohon", "Kota Kotamobagu",
    "Kabupaten Bolaang Mongondow", "Kabupaten Bolaang Mongondow Selatan",
    "Kabupaten Bolaang Mongondow Timur", "Kabupaten Bolaang Mongondow Utara",
    "Kabupaten Kepulauan Sangihe", "Kabupaten Kepulauan Siau Tagulandang Biaro",
    "Kabupaten Kepulauan Talaud", "Kabupaten Minahasa",
    "Kabupaten Minahasa Selatan", "Kabupaten Minahasa Tenggara",
    "Kabupaten Minahasa Utara",
    # Sulawesi Tenggara
    "Kota Kendari", "Kota Baubau",
    "Kabupaten Bombana", "Kabupaten Buton", "Kabupaten Buton Selatan",
    "Kabupaten Buton Tengah", "Kabupaten Buton Utara",
    "Kabupaten Kolaka", "Kabupaten Kolaka Timur", "Kabupaten Kolaka Utara",
    "Kabupaten Konawe", "Kabupaten Konawe Kepulauan",
    "Kabupaten Konawe Selatan", "Kabupaten Konawe Utara",
    "Kabupaten Muna", "Kabupaten Muna Barat", "Kabupaten Wakatobi",
    # Gorontalo
    "Kota Gorontalo", "Kabupaten Boalemo", "Kabupaten Bone Bolango",
    "Kabupaten Gorontalo Utara", "Kabupaten Pohuwato", "Kabupaten Gorontalo",
]

# Set untuk lookup cepat (lowercase)
VALID_SET = {v.lower(): v for v in VALID_KAB_KOTA}

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_FILE)
original_kabupaten = df['kabupaten'].copy()
log = []

def apply_fix(mask, to, desc):
    """Terapkan fix ke baris yang sesuai mask, catat log."""
    n = int(mask.sum()) if hasattr(mask, 'sum') else int(mask)
    if n:
        df.loc[mask, 'kabupaten'] = to
        log.append(f"[{n:3d}] {desc}  →  '{to}'")

# =============================================================================
# 1. TYPO / EJAAN TIDAK STANDAR
# =============================================================================
apply_fix(df['kabupaten'] == 'Kota Bau-Bau',
          'Kota Baubau',
          "'Kota Bau-Bau'")

apply_fix(df['kabupaten'] == 'Kotamobagu',
          'Kota Kotamobagu',
          "'Kotamobagu'")

apply_fix(df['kabupaten'].str.strip() == 'Kabupaten Pangkajene dan Kepulauan',
          'Kabupaten Pangkajene Dan Kepulauan',
          "'Kabupaten Pangkajene dan Kepulauan' (kapital)")

# =============================================================================
# 2. KABUPATEN DI LUAR SULAWESI / JELAS SALAH
# =============================================================================
apply_fix(df['kabupaten'] == 'Kota Jakarta Selatan',
          'Kabupaten Muna',
          "'Kota Jakarta Selatan' (koordinat Sultra)")

apply_fix(df['kabupaten'] == 'Kabupaten Province of Davao Oriental',
          'Kabupaten Kepulauan Talaud',
          "'Kab. Province of Davao Oriental' (alamat: Miangas/Talaud)")

# =============================================================================
# 3. NAMA KECAMATAN/KELURAHAN DIJADIKAN KABUPATEN
# =============================================================================
apply_fix(df['kabupaten'] == 'Kabupaten  Utara',
          'Kabupaten Gorontalo Utara',
          "'Kabupaten  Utara' (spasi ganda)")

apply_fix(df['kabupaten'] == 'Kota Timur Tanamodindi Mantikulore',
          'Kota Palu',
          "'Kota Timur Tanamodindi Mantikulore' (kecamatan di Palu)")

apply_fix(df['kabupaten'] == 'Kota Pulu',
          'Kabupaten Sigi',
          "'Kota Pulu' (alamat: Kabupaten Sigi)")

apply_fix(df['kabupaten'] == 'Kota Jin',
          'Kabupaten Gorontalo Utara',
          "'Kota Jin' (alamat: Kec. Atinggola, Gorontalo Utara)")

apply_fix(df['kabupaten'] == 'Kota Tentena',
          'Kabupaten Poso',
          "'Kota Tentena' (ibu kota Kec. Pamona Utara, Poso)")

apply_fix(df['kabupaten'] == 'Kota Utara',
          'Kabupaten Poso',
          "'Kota Utara' (Kec. Poso Kota Utara)")

apply_fix(df['kabupaten'] == 'Kota Menara',
          'Kabupaten Minahasa Tenggara',
          "'Kota Menara' (Kec. Silian Raya, Minahasa Tenggara)")

apply_fix(df['kabupaten'].str.lower().str.contains('toli-toli', na=False),
          'Kabupaten Tolitoli',
          "'Kabupaten Toli-Toli' (ejaan resmi: Tolitoli)")

apply_fix(df['kabupaten'] == 'Kabupaten Siau Tagulandang Biaro',
          'Kabupaten Kepulauan Siau Tagulandang Biaro',
          "'Kabupaten Siau Tagulandang Biaro' (kurang prefix Kepulauan)")


# =============================================================================
# 4. OTOMATIS: EKSTRAK KABUPATEN DARI KOLOM ALAMAT
#    Regex cari pola "Kabupaten X" atau "Kota X" di string alamat,
#    lalu validasi terhadap whitelist. Jika valid & berbeda → update.
# =============================================================================

# Bangun pola regex dari whitelist (urutkan terpanjang duluan agar greedy match)
sorted_valid = sorted(VALID_KAB_KOTA, key=len, reverse=True)
# Escape karakter khusus dan join dengan |
pattern_body = '|'.join(re.escape(v) for v in sorted_valid)
PATTERN = re.compile(r'\b(' + pattern_body + r')\b', re.IGNORECASE)

def extract_kabupaten_from_alamat(alamat_str):
    """
    Cari nama kabupaten/kota valid pertama dalam string alamat.
    Return canonical name (case-standar) atau None.
    """
    if not isinstance(alamat_str, str) or alamat_str.strip() in ('', '-', 'nan'):
        return None
    match = PATTERN.search(alamat_str)
    if match:
        return VALID_SET.get(match.group(1).lower())
    return None

auto_fixed = 0
auto_details = {}

for idx, row in df.iterrows():
    current_kab = str(row['kabupaten']).strip()
    alamat      = str(row.get('alamat', ''))
    extracted   = extract_kabupaten_from_alamat(alamat)

    if extracted and extracted.lower() != current_kab.lower():
        # Hanya update jika nilai saat ini BUKAN ada di whitelist
        # atau jika nilai saat ini memang tidak valid
        if current_kab.lower() not in VALID_SET:
            df.at[idx, 'kabupaten'] = extracted
            key = f"'{current_kab}'  →  '{extracted}'"
            auto_details[key] = auto_details.get(key, 0) + 1
            auto_fixed += 1
        else:
            # Nilai saat ini valid tapi TIDAK cocok dengan alamat → override dari alamat
            df.at[idx, 'kabupaten'] = extracted
            key = f"'{current_kab}'  →  '{extracted}' (koreksi alamat)"
            auto_details[key] = auto_details.get(key, 0) + 1
            auto_fixed += 1

if auto_fixed:
    log.append(f"[{auto_fixed:3d}] AUTO-FIX dari kolom alamat (lihat detail di bawah)")

# =============================================================================
# 5. PERBAIKAN SPESIFIK NAMA WISATA (OVERRIDE SETELAH AUTO)
# =============================================================================
apply_fix(
    (df['nama_wisata'].str.contains('Bantimurung Bulusaraung', na=False)) &
    (df['kabupaten'] == 'Kabupaten Bone'),
    'Kabupaten Maros',
    "TN Bantimurung Bulusaraung tercatat di Kab. Bone"
)

apply_fix(
    (df['nama_wisata'] == 'Cinta Souvenir Bantimurung') &
    (~df['kabupaten'].eq('Kabupaten Maros')),
    'Kabupaten Maros',
    "Cinta Souvenir Bantimurung (Kec. Bantimurung = Maros)"
)

apply_fix(
    (df['nama_wisata'] == 'Tongkonan Buntu') &
    (df['kabupaten'] == 'Kabupaten Bone'),
    'Kabupaten Toraja Utara',
    "Tongkonan Buntu (koordinat: Toraja Utara)"
)

apply_fix(
    (df['nama_wisata'] == 'Tugu Adipura') &
    (df['kabupaten'] == 'Kota Kendari'),
    'Kabupaten Konawe',
    "Tugu Adipura (alamat: Kabupaten Konawe)"
)

apply_fix(
    (df['nama_wisata'].str.contains('Desa Wisata Untia', na=False)) &
    (df['kabupaten'] == 'Kabupaten Maros'),
    'Kota Makassar',
    "Desa Wisata Untia (Kec. Biringkanaya = Kota Makassar)"
)

# =============================================================================
# 6. SIMPAN & LAPORAN
# =============================================================================
df.drop(columns=['kab_from_alamat'], errors='ignore', inplace=True)
df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

total_changed = (df['kabupaten'] != original_kabupaten).sum()

print("=" * 70)
print("  LAPORAN PERBAIKAN DATA KABUPATEN WISATA SULAWESI")
print("=" * 70)
print()
print(">> RINGKASAN FIX MANUAL & RULE-BASED:")
for l in log:
    print(f"  OK {l}")

if auto_details:
    print()
    print(">> DETAIL AUTO-FIX DARI ALAMAT:")
    for detail, count in sorted(auto_details.items(), key=lambda x: -x[1]):
        print(f"  [{count:3d}] {detail}")

print()
print(f"  Total baris diperbaiki : {total_changed} dari {len(df)}")
print(f"  Output                 : {OUTPUT_FILE}")
print("=" * 70)