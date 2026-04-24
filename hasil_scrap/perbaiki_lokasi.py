"""
perbaiki_lokasi.py
==================
1. Perbaiki 11 baris SALAH (kabupaten vs provinsi tidak cocok)
2. Perbaiki 55 baris TIDAK_ADA (nama kabupaten tidak valid/aneh)
   - Menggunakan regex dari kolom alamat sebagai sumber utama
   - Fallback: inferensi dari nama wisata
"""

import pandas as pd
import re

df = pd.read_csv('wisata_sulawesi_cleaned_final.csv')

# ── Mapping resmi (sama seperti di validasi_lokasi.py) ──────
PETA_RESMI = {
    "kota makassar":"Sulawesi Selatan","kota parepare":"Sulawesi Selatan",
    "kota palopo":"Sulawesi Selatan","kabupaten gowa":"Sulawesi Selatan",
    "kabupaten maros":"Sulawesi Selatan","kabupaten bone":"Sulawesi Selatan",
    "kabupaten bulukumba":"Sulawesi Selatan","kabupaten bantaeng":"Sulawesi Selatan",
    "kabupaten jeneponto":"Sulawesi Selatan","kabupaten takalar":"Sulawesi Selatan",
    "kabupaten sinjai":"Sulawesi Selatan","kabupaten wajo":"Sulawesi Selatan",
    "kabupaten soppeng":"Sulawesi Selatan","kabupaten enrekang":"Sulawesi Selatan",
    "kabupaten pinrang":"Sulawesi Selatan","kabupaten sidenreng rappang":"Sulawesi Selatan",
    "kabupaten barru":"Sulawesi Selatan","kabupaten pangkajene dan kepulauan":"Sulawesi Selatan",
    "kabupaten luwu":"Sulawesi Selatan","kabupaten luwu utara":"Sulawesi Selatan",
    "kabupaten luwu timur":"Sulawesi Selatan","kabupaten toraja utara":"Sulawesi Selatan",
    "kabupaten tana toraja":"Sulawesi Selatan","kabupaten kepulauan selayar":"Sulawesi Selatan",
    "kota manado":"Sulawesi Utara","kota bitung":"Sulawesi Utara",
    "kota tomohon":"Sulawesi Utara","kota kotamobagu":"Sulawesi Utara",
    "kabupaten minahasa":"Sulawesi Utara","kabupaten minahasa utara":"Sulawesi Utara",
    "kabupaten minahasa selatan":"Sulawesi Utara","kabupaten minahasa tenggara":"Sulawesi Utara",
    "kabupaten bolaang mongondow":"Sulawesi Utara","kabupaten bolaang mongondow utara":"Sulawesi Utara",
    "kabupaten bolaang mongondow selatan":"Sulawesi Utara","kabupaten bolaang mongondow timur":"Sulawesi Utara",
    "kabupaten kepulauan sangihe":"Sulawesi Utara","kabupaten kepulauan talaud":"Sulawesi Utara",
    "kabupaten kepulauan siau tagulandang biaro":"Sulawesi Utara",
    "kota palu":"Sulawesi Tengah","kabupaten donggala":"Sulawesi Tengah",
    "kabupaten sigi":"Sulawesi Tengah","kabupaten parigi moutong":"Sulawesi Tengah",
    "kabupaten poso":"Sulawesi Tengah","kabupaten morowali":"Sulawesi Tengah",
    "kabupaten morowali utara":"Sulawesi Tengah","kabupaten tojo una-una":"Sulawesi Tengah",
    "kabupaten banggai":"Sulawesi Tengah","kabupaten banggai kepulauan":"Sulawesi Tengah",
    "kabupaten banggai laut":"Sulawesi Tengah","kabupaten buol":"Sulawesi Tengah",
    "kabupaten toli-toli":"Sulawesi Tengah",
    "kota kendari":"Sulawesi Tenggara","kota bau-bau":"Sulawesi Tenggara",
    "kabupaten konawe":"Sulawesi Tenggara","kabupaten konawe selatan":"Sulawesi Tenggara",
    "kabupaten konawe utara":"Sulawesi Tenggara","kabupaten konawe kepulauan":"Sulawesi Tenggara",
    "kabupaten kolaka":"Sulawesi Tenggara","kabupaten kolaka utara":"Sulawesi Tenggara",
    "kabupaten kolaka timur":"Sulawesi Tenggara","kabupaten muna":"Sulawesi Tenggara",
    "kabupaten muna barat":"Sulawesi Tenggara","kabupaten buton":"Sulawesi Tenggara",
    "kabupaten buton utara":"Sulawesi Tenggara","kabupaten buton tengah":"Sulawesi Tenggara",
    "kabupaten buton selatan":"Sulawesi Tenggara","kabupaten wakatobi":"Sulawesi Tenggara",
    "kabupaten bombana":"Sulawesi Tenggara",
    "kabupaten mamuju":"Sulawesi Barat","kabupaten mamuju tengah":"Sulawesi Barat",
    "kabupaten mamuju utara":"Sulawesi Barat","kabupaten pasangkayu":"Sulawesi Barat",
    "kabupaten majene":"Sulawesi Barat","kabupaten polewali mandar":"Sulawesi Barat",
    "kabupaten mamasa":"Sulawesi Barat",
    "kota gorontalo":"Gorontalo","kabupaten gorontalo":"Gorontalo",
    "kabupaten gorontalo utara":"Gorontalo","kabupaten bone bolango":"Gorontalo",
    "kabupaten pohuwato":"Gorontalo","kabupaten boalemo":"Gorontalo",
}

PROVINSI_MAP = {
    "sulawesi selatan":"Sulawesi Selatan","sulawesi utara":"Sulawesi Utara",
    "sulawesi tengah":"Sulawesi Tengah","sulawesi tenggara":"Sulawesi Tenggara",
    "sulawesi barat":"Sulawesi Barat","gorontalo":"Gorontalo",
    "south sulawesi":"Sulawesi Selatan","north sulawesi":"Sulawesi Utara",
    "central sulawesi":"Sulawesi Tengah","southeast sulawesi":"Sulawesi Tenggara",
    "west sulawesi":"Sulawesi Barat",
}

def cari_prov_dari_alamat(alamat: str) -> str:
    t = str(alamat).lower()
    for k, v in PROVINSI_MAP.items():
        if k in t:
            return v
    return ""

def cari_kab_dari_alamat(alamat: str) -> str:
    m = re.search(r'\b(Kabupaten|Kota)\s+([A-Za-z\s]+?)(?=\s*[\d,.]|$)',
                  str(alamat), re.IGNORECASE)
    if m:
        tipe = m.group(1).capitalize()
        nama = m.group(2).strip().title()
        # bersihkan kata-kata yang sering muncul di akhir
        for stop in ["Indonesia","Sulawesi","Selatan","Utara","Tengah","Tenggara","Barat","Gorontalo"]:
            nama = re.sub(r'\s*\b' + stop + r'\b\s*', ' ', nama, flags=re.IGNORECASE).strip()
        if len(nama) > 2:
            return f"{tipe} {nama}"
    return ""

def provinsi_dari_kab(kab: str) -> str:
    k = str(kab).strip().lower()
    if k in PETA_RESMI:
        return PETA_RESMI[k]
    for key, val in PETA_RESMI.items():
        if key in k or k in key:
            return val
    return ""

# ──────────────────────────────────────────────────────────────
# PERBAIKAN MANUAL untuk 11 data SALAH
# ──────────────────────────────────────────────────────────────
PERBAIKAN_MANUAL = {
    882:  ("Kabupaten Konawe",           "Sulawesi Tenggara"),  # Pantai Salokaili
    949:  ("Kabupaten Luwu Timur",       "Sulawesi Selatan"),   # ANJUNGAN 533
    1001: ("Kota Palu",                  "Sulawesi Tengah"),    # Pantai Batu Oge
    1217: ("Kabupaten Buol",             "Sulawesi Tengah"),    # Pantai Bahari Doulan
    1336: ("Kabupaten Mamuju",           "Sulawesi Barat"),     # Hutan Mangrove
    1848: ("Kabupaten Buol",             "Sulawesi Tengah"),    # Pantai Maninang Buol
    1969: ("Kabupaten Bolaang Mongondow","Sulawesi Utara"),     # Pantai Kuliner Salukaili
    2062: ("Kabupaten Kepulauan Sangihe","Sulawesi Utara"),     # Pantai Seribu Kelapa
    2178: ("Kabupaten Buol",             "Sulawesi Tengah"),    # Batu Tiga Tanjung Leok
    2408: ("Kabupaten Wajo",             "Sulawesi Selatan"),   # A.M.R Shop
    2701: ("Kabupaten Jeneponto",        "Sulawesi Selatan"),   # Wisata Paccumikang
}

perbaikan_count = 0
for idx, (kab_baru, prov_baru) in PERBAIKAN_MANUAL.items():
    df.at[idx, 'kabupaten'] = kab_baru
    df.at[idx, 'provinsi']  = prov_baru
    perbaikan_count += 1

# ──────────────────────────────────────────────────────────────
# PERBAIKAN OTOMATIS untuk 55 TIDAK_ADA
# (kabupaten tidak valid — coba re-extract dari alamat)
# ──────────────────────────────────────────────────────────────

# Periksa ulang semua baris — bukan hanya yang sudah diketahui tidak valid
def is_kab_valid(kab: str) -> bool:
    k = str(kab).strip().lower()
    if k in PETA_RESMI:
        return True
    for key in PETA_RESMI:
        if key in k or k in key:
            return True
    return False

auto_fix = 0
still_invalid = []

for idx, row in df.iterrows():
    if idx in PERBAIKAN_MANUAL:
        continue  # sudah diperbaiki manual

    kab = str(row['kabupaten']).strip()
    prov = str(row['provinsi']).strip()

    if is_kab_valid(kab):
        continue  # sudah valid

    # Coba ekstrak ulang dari alamat
    alamat = str(row.get('alamat', ''))
    kab_baru  = cari_kab_dari_alamat(alamat)
    prov_baru = cari_prov_dari_alamat(alamat) or prov

    if kab_baru and is_kab_valid(kab_baru):
        df.at[idx, 'kabupaten'] = kab_baru
        # Sesuaikan provinsi dengan kabupaten baru
        prov_sesuai = provinsi_dari_kab(kab_baru)
        df.at[idx, 'provinsi'] = prov_sesuai if prov_sesuai else prov_baru
        auto_fix += 1
    elif prov_baru and prov_baru != str(prov).strip():
        df.at[idx, 'provinsi'] = prov_baru
        auto_fix += 1
    else:
        still_invalid.append({
            'idx': idx,
            'nama_wisata': row['nama_wisata'],
            'alamat': row['alamat'],
            'kabupaten': kab,
            'provinsi': prov,
        })

# Simpan hasil
df.to_csv('wisata_sulawesi_cleaned_final.csv', index=False, encoding='utf-8-sig')

print("=" * 60)
print("HASIL PERBAIKAN")
print("=" * 60)
print(f"Diperbaiki manual  : {perbaikan_count}")
print(f"Diperbaiki otomatis: {auto_fix}")
print(f"Masih tidak valid  : {len(still_invalid)}")
print()

if still_invalid:
    print(">>> Daftar yang masih tidak valid (perlu review):")
    for item in still_invalid:
        print(f"  [{item['idx']}] {item['nama_wisata']}")
        print(f"       Kab : {item['kabupaten']}")
        print(f"       Prov: {item['provinsi']}")
        print(f"       Ala : {item['alamat'][:80]}")
        print()
