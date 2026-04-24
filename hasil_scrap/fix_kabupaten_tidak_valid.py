"""
fix_kabupaten_tidak_valid.py
============================
Perbaiki 54 baris dengan kabupaten tidak valid/tidak dikenal.
Sumber perbaikan: analisis alamat + nama wisata + pengetahuan geografis.
"""

import pandas as pd
import re

df = pd.read_csv('wisata_sulawesi_cleaned_final.csv')

# ──────────────────────────────────────────────────────────────
# PETA RESMI (untuk validasi pasca-perbaikan)
# ──────────────────────────────────────────────────────────────
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
    "kabupaten pasangkayu":"Sulawesi Barat","kabupaten majene":"Sulawesi Barat",
    "kabupaten polewali mandar":"Sulawesi Barat","kabupaten mamasa":"Sulawesi Barat",
    "kota gorontalo":"Gorontalo","kabupaten gorontalo":"Gorontalo",
    "kabupaten gorontalo utara":"Gorontalo","kabupaten bone bolango":"Gorontalo",
    "kabupaten pohuwato":"Gorontalo","kabupaten boalemo":"Gorontalo",
}

def norm(s): return re.sub(r'\s+', ' ', str(s).strip().lower())
def is_valid(kab): return norm(kab) in PETA_RESMI

# ──────────────────────────────────────────────────────────────
# PERBAIKAN MANUAL BERDASARKAN ANALISIS ALAMAT & GEOGRAFI
# Format: idx -> (kabupaten_baru, provinsi_baru)
# ──────────────────────────────────────────────────────────────
FIXES = {
    # Kota Palu & sekitarnya
    8:    ("Kota Palu",                            "Sulawesi Tengah"),   # Taman Vatulemo (Kec. Palu Tim.)
    134:  ("Kabupaten Sigi",                       "Sulawesi Tengah"),   # Danau Tambing (Kab. Sigi di alamat)
    1344: ("Kabupaten Poso",                       "Sulawesi Tengah"),   # Bukit Cinta (Kec. Poso Kota Sel.)
    277:  ("Kabupaten Poso",                       "Sulawesi Tengah"),   # Pantai Imbo (Kec. Poso Kota Utara)
    935:  ("Kabupaten Poso",                       "Sulawesi Tengah"),   # Atalambu Hill (Kota Tentena=ibukota Poso)
    2008: ("Kabupaten Poso",                       "Sulawesi Tengah"),   # Pantai Penghibur Kota Poso
    1554: ("Kabupaten Toli-Toli",                  "Sulawesi Tengah"),   # PUNCAK OGOMOLI
    2273: ("Kabupaten Toli-Toli",                  "Sulawesi Tengah"),   # Wisata Pemandian Tuweley
    # Gorontalo
    47:   ("Kota Gorontalo",                       "Gorontalo"),         # Benteng Otanaha (Kec. Kota Bar.)
    53:   ("Kota Gorontalo",                       "Gorontalo"),         # Masjid Agung Baiturrahim
    120:  ("Kota Gorontalo",                       "Gorontalo"),         # WISATA TAMENDAO BEACH (Kec. Kota Tim.)
    147:  ("Kota Gorontalo",                       "Gorontalo"),         # Planet Waterboom (Kota Sel.)
    294:  ("Kota Gorontalo",                       "Gorontalo"),         # Taman Lahilote
    359:  ("Kabupaten Gorontalo Utara",            "Gorontalo"),         # Pantai Minanga (Kec. Atinggola)
    588:  ("Kabupaten Gorontalo Utara",            "Gorontalo"),         # Minanga Beach
    717:  ("Kabupaten Gorontalo",                  "Gorontalo"),         # Wisata Pemandian Potanga (Kec. Kota Bar., Kab. Gorontalo)
    963:  ("Kota Gorontalo",                       "Gorontalo"),         # Pantai Leato Selatan (Kota Tim.)
    1539: ("Kota Gorontalo",                       "Gorontalo"),         # GPPS Gunung Moria
    1678: ("Kota Gorontalo",                       "Gorontalo"),         # SANTORINI Talumolo (Kota Tim)
    1709: ("Kabupaten Gorontalo Utara",            "Gorontalo"),         # Gapura Wisata Pantai Minanga
    2400: ("Kabupaten Gorontalo Utara",            "Gorontalo"),         # Otalojin Batu jin (Kec. Atinggola)
    # Sulawesi Tengah - Togean / Banggai
    190:  ("Kabupaten Tojo Una-Una",               "Sulawesi Tengah"),   # Taman Nasional Kepulauan Togean
    404:  ("Kabupaten Banggai",                    "Sulawesi Tengah"),   # Teluk Lalong (Luwuk = ibukota Banggai)
    2617: ("Kota Palu",                            "Sulawesi Tengah"),   # POCI (Lepo-Lepo = Palu)
    # Sulawesi Utara - Sitaro / Sangihe / Minahasa
    946:  ("Kabupaten Kepulauan Siau Tagulandang Biaro", "Sulawesi Utara"),
    1343: ("Kabupaten Kepulauan Siau Tagulandang Biaro", "Sulawesi Utara"),  # Danau Cinta Makalehi
    1451: ("Kabupaten Kepulauan Sangihe",          "Sulawesi Utara"),   # Banua Wuhu
    1552: ("Kabupaten Kepulauan Sangihe",          "Sulawesi Utara"),   # Lembah Kenari Manganitu
    1769: ("Kabupaten Minahasa Tenggara",          "Sulawesi Utara"),   # Wisata Gn. Soputan (Kab. Minahasa Tenggara)
    1868: ("Kabupaten Kepulauan Siau Tagulandang Biaro","Sulawesi Utara"),   # TUGU I LOVE SITARO
    2578: ("Kabupaten Kepulauan Siau Tagulandang Biaro","Sulawesi Utara"),   # Temboko Mini Wisata Siau
    # Sulawesi Selatan
    83:   ("Kabupaten Bulukumba",                  "Sulawesi Selatan"),  # Pantai Nirwana (Sulawesi Tenggara province was wrong too)
    498:  ("Kota Makassar",                        "Sulawesi Selatan"),  # Taman Teras Unhas (Tamalanrea = Makassar)
    1127: ("Kabupaten Toraja Utara",               "Sulawesi Selatan"),  # Kampong Batulelleng (Rantepao=Toraja Utara)
    1423: ("Kabupaten Sidenreng Rappang",          "Sulawesi Selatan"),  # Kincir Angin PLTB (Sidrap)
    1439: ("Kabupaten Buton",                      "Sulawesi Tenggara"), # Pantai Pinang (Baubau ibukota Buton)
    1505: ("Kabupaten Sinjai",                     "Sulawesi Selatan"),  # Senja Beloka (Sandang Pangan = Sinjai)
    1587: ("Kabupaten Bone",                       "Sulawesi Selatan"),  # Sumur Waranie Palakka (Watang Palakka=Bone)
    1875: ("Kabupaten Bulukumba",                  "Sulawesi Selatan"),  # Kolam renang Roni Cell (Tanah Kongkong=Bulukumba)
    1912: ("Kabupaten Kepulauan Selayar",          "Sulawesi Selatan"),  # Village Cantik Selayar
    2152: ("Kabupaten Banggai",                    "Sulawesi Tengah"),   # Monumen Teluk Lalong (Banggai/Luwuk)
    2246: ("Kabupaten Bone",                       "Sulawesi Selatan"),  # Tugu Jam Watampone
    2274: ("Kabupaten Kolaka",                     "Sulawesi Tenggara"), # Goa Kolam Renang (Labengi=Kolaka)
    2382: ("Kabupaten Majene",                     "Sulawesi Barat"),    # Pembuat minyak kelapa mandar (Labuang=Majene)
    2430: ("Kabupaten Kepulauan Selayar",          "Sulawesi Selatan"),  # Hutan Mangrove Gusung (Bontolebang=Selayar)
    2432: ("Kabupaten Pangkajene Dan Kepulauan",  "Sulawesi Selatan"),  # GUA KAMBUNO (Pangkep)
    # Sulawesi Barat - Pasangkayu
    527:  ("Kabupaten Pasangkayu",                 "Sulawesi Barat"),    # Pasangkayu Beach
    1301: ("Kabupaten Pasangkayu",                 "Sulawesi Barat"),    # Pantai Barat Sarudu
    1316: ("Kabupaten Pasangkayu",                 "Sulawesi Barat"),    # Pantai Koa-Koa
    2611: ("Kabupaten Mamuju",                     "Sulawesi Barat"),    # Nusa dolong
    # Sulawesi Tenggara
    881:  ("Kabupaten Muna",                       "Sulawesi Tenggara"), # Pantai Membuku
    1670: ("Kabupaten Konawe",                     "Sulawesi Tenggara"), # Puncak ghonsume (Ghonsume=Konawe)
    2513: ("Kabupaten Muna",                       "Sulawesi Tenggara"), # Bat-Bat Kota Raha (Raha=ibukota Muna)
    2559: ("Kabupaten Kolaka",                     "Sulawesi Tenggara"), # Cahaya Berkah Abadi (Damai)
}

# ──────────────────────────────────────────────────────────────
# KHUSUS: parse ulang dari alamat untuk pola berulang
# ──────────────────────────────────────────────────────────────
def parse_kab_dari_alamat(alamat: str) -> str:
    """Extract 'Kab. XYZ' atau 'Kabupaten XYZ' dari alamat."""
    # Pola "Kab. Pasangkayu" atau "Kabupaten Pasangkayu"
    m = re.search(
        r'\bKab(?:upaten)?\.?\s+([A-Za-z][A-Za-z\s]+?)(?=\s*[,\.\d]|$)',
        str(alamat), re.IGNORECASE
    )
    if m:
        nama = m.group(1).strip().title()
        # Bersihkan trailing kata non-nama
        for stop in ["Sulawesi","Selatan","Utara","Tengah","Tenggara","Barat","Gorontalo","Indonesia"]:
            nama = re.sub(r'\s*\b' + stop + r'\b\s*', ' ', nama, flags=re.IGNORECASE).strip()
        if len(nama) > 2:
            return f"Kabupaten {nama}"
    return ""

# Terapkan fixes
diperbaiki = 0
for idx, (kab_baru, prov_baru) in FIXES.items():
    if idx in df.index:
        df.at[idx, 'kabupaten'] = kab_baru
        df.at[idx, 'provinsi']  = prov_baru
        diperbaiki += 1

# Perbaikan otomatis sisanya: re-parse dari alamat
sisa_fix = 0
for idx, row in df.iterrows():
    if idx in FIXES:
        continue
    if is_valid(row['kabupaten']):
        continue
    alamat = str(row.get('alamat', ''))
    kab_baru = parse_kab_dari_alamat(alamat)
    if kab_baru and is_valid(kab_baru):
        prov_baru = PETA_RESMI.get(norm(kab_baru), row['provinsi'])
        df.at[idx, 'kabupaten'] = kab_baru
        df.at[idx, 'provinsi']  = prov_baru
        sisa_fix += 1

# Simpan
df.to_csv('wisata_sulawesi_cleaned_final.csv', index=False, encoding='utf-8-sig')

# ──────────────────────────────────────────────────────────────
# LAPORAN AKHIR
# ──────────────────────────────────────────────────────────────
total_ok = sum(1 for _, r in df.iterrows() if is_valid(r['kabupaten']))
total_not = len(df) - total_ok

print("=" * 60)
print("HASIL PERBAIKAN KABUPATEN")
print("=" * 60)
print(f"Total data           : {len(df)}")
print(f"Diperbaiki manual    : {diperbaiki}")
print(f"Diperbaiki otomatis  : {sisa_fix}")
print(f"Kabupaten valid (OK) : {total_ok}")
print(f"Masih tidak valid    : {total_not}")

if total_not > 0:
    print()
    print(">>> Sisa yang belum bisa diperbaiki:")
    for idx, row in df.iterrows():
        if not is_valid(row['kabupaten']):
            print(f"  [{idx}] {row['nama_wisata']}")
            print(f"       Kab  : {row['kabupaten']}")
            print(f"       Prov : {row['provinsi']}")
            print(f"       Ala  : {str(row['alamat'])[:70]}")
else:
    print()
    print("Semua kabupaten sudah valid!")
