"""
validasi_lokasi.py
==================
Memvalidasi apakah pasangan (kabupaten, provinsi) pada dataset
sudah sesuai dengan data administrasi resmi Indonesia.
"""

import pandas as pd
import re

# ──────────────────────────────────────────────────────────────
# DATA RESMI: Kabupaten/Kota → Provinsi
# Sumber: Permendagri & BPS 2023
# ──────────────────────────────────────────────────────────────
PETA_RESMI = {
    # ── SULAWESI SELATAN ──────────────────────────────────────
    "kota makassar":                    "Sulawesi Selatan",
    "kota parepare":                    "Sulawesi Selatan",
    "kota palopo":                      "Sulawesi Selatan",
    "kabupaten gowa":                   "Sulawesi Selatan",
    "kabupaten maros":                  "Sulawesi Selatan",
    "kabupaten bone":                   "Sulawesi Selatan",
    "kabupaten bulukumba":              "Sulawesi Selatan",
    "kabupaten bantaeng":               "Sulawesi Selatan",
    "kabupaten jeneponto":              "Sulawesi Selatan",
    "kabupaten takalar":                "Sulawesi Selatan",
    "kabupaten sinjai":                 "Sulawesi Selatan",
    "kabupaten wajo":                   "Sulawesi Selatan",
    "kabupaten soppeng":                "Sulawesi Selatan",
    "kabupaten enrekang":               "Sulawesi Selatan",
    "kabupaten pinrang":                "Sulawesi Selatan",
    "kabupaten sidenreng rappang":      "Sulawesi Selatan",
    "kabupaten barru":                  "Sulawesi Selatan",
    "kabupaten pangkajene dan kepulauan": "Sulawesi Selatan",
    "kabupaten luwu":                   "Sulawesi Selatan",
    "kabupaten luwu utara":             "Sulawesi Selatan",
    "kabupaten luwu timur":             "Sulawesi Selatan",
    "kabupaten toraja utara":           "Sulawesi Selatan",
    "kabupaten tana toraja":            "Sulawesi Selatan",
    "kabupaten kepulauan selayar":      "Sulawesi Selatan",
    # ── SULAWESI UTARA ────────────────────────────────────────
    "kota manado":                      "Sulawesi Utara",
    "kota bitung":                      "Sulawesi Utara",
    "kota tomohon":                     "Sulawesi Utara",
    "kota kotamobagu":                  "Sulawesi Utara",
    "kabupaten minahasa":               "Sulawesi Utara",
    "kabupaten minahasa utara":         "Sulawesi Utara",
    "kabupaten minahasa selatan":       "Sulawesi Utara",
    "kabupaten minahasa tenggara":      "Sulawesi Utara",
    "kabupaten bolaang mongondow":      "Sulawesi Utara",
    "kabupaten bolaang mongondow utara":"Sulawesi Utara",
    "kabupaten bolaang mongondow selatan":"Sulawesi Utara",
    "kabupaten bolaang mongondow timur":"Sulawesi Utara",
    "kabupaten kepulauan sangihe":      "Sulawesi Utara",
    "kabupaten kepulauan talaud":       "Sulawesi Utara",
    "kabupaten kepulauan siau tagulandang biaro": "Sulawesi Utara",
    # ── SULAWESI TENGAH ───────────────────────────────────────
    "kota palu":                        "Sulawesi Tengah",
    "kabupaten donggala":               "Sulawesi Tengah",
    "kabupaten sigi":                   "Sulawesi Tengah",
    "kabupaten parigi moutong":         "Sulawesi Tengah",
    "kabupaten poso":                   "Sulawesi Tengah",
    "kabupaten morowali":               "Sulawesi Tengah",
    "kabupaten morowali utara":         "Sulawesi Tengah",
    "kabupaten tojo una-una":           "Sulawesi Tengah",
    "kabupaten banggai":                "Sulawesi Tengah",
    "kabupaten banggai kepulauan":      "Sulawesi Tengah",
    "kabupaten banggai laut":           "Sulawesi Tengah",
    "kabupaten buol":                   "Sulawesi Tengah",
    "kabupaten toli-toli":              "Sulawesi Tengah",
    # ── SULAWESI TENGGARA ─────────────────────────────────────
    "kota kendari":                     "Sulawesi Tenggara",
    "kota bau-bau":                     "Sulawesi Tenggara",
    "kabupaten konawe":                 "Sulawesi Tenggara",
    "kabupaten konawe selatan":         "Sulawesi Tenggara",
    "kabupaten konawe utara":           "Sulawesi Tenggara",
    "kabupaten konawe kepulauan":       "Sulawesi Tenggara",
    "kabupaten kolaka":                 "Sulawesi Tenggara",
    "kabupaten kolaka utara":           "Sulawesi Tenggara",
    "kabupaten kolaka timur":           "Sulawesi Tenggara",
    "kabupaten muna":                   "Sulawesi Tenggara",
    "kabupaten muna barat":             "Sulawesi Tenggara",
    "kabupaten buton":                  "Sulawesi Tenggara",
    "kabupaten buton utara":            "Sulawesi Tenggara",
    "kabupaten buton tengah":           "Sulawesi Tenggara",
    "kabupaten buton selatan":          "Sulawesi Tenggara",
    "kabupaten wakatobi":               "Sulawesi Tenggara",
    "kabupaten bombana":                "Sulawesi Tenggara",
    # ── SULAWESI BARAT ────────────────────────────────────────
    "kabupaten mamuju":                 "Sulawesi Barat",
    "kabupaten mamuju tengah":          "Sulawesi Barat",
    "kabupaten mamuju utara":           "Sulawesi Barat",
    "kabupaten pasangkayu":             "Sulawesi Barat",
    "kabupaten majene":                 "Sulawesi Barat",
    "kabupaten polewali mandar":        "Sulawesi Barat",
    "kabupaten mamasa":                 "Sulawesi Barat",
    # ── GORONTALO ─────────────────────────────────────────────
    "kota gorontalo":                   "Gorontalo",
    "kabupaten gorontalo":              "Gorontalo",
    "kabupaten gorontalo utara":        "Gorontalo",
    "kabupaten bone bolango":           "Gorontalo",
    "kabupaten pohuwato":               "Gorontalo",
    "kabupaten boalemo":                "Gorontalo",
}


def normalisasi(s: str) -> str:
    """Lowercase + hapus spasi ganda."""
    return re.sub(r'\s+', ' ', str(s).strip().lower())


def cek_pasangan(kab_raw: str, prov_raw: str) -> str:
    """
    Kembalikan:
      'OK'          - pasangan sesuai data resmi
      'TIDAK_ADA'   - kabupaten tidak ada di peta resmi (tidak bisa divalidasi)
      'SALAH'       - kabupaten ada tapi provinsinya berbeda
    """
    kab  = normalisasi(kab_raw)
    prov = normalisasi(prov_raw)

    # Fuzzy match: coba kecocokan parsial jika tidak exact
    prov_resmi = None
    if kab in PETA_RESMI:
        prov_resmi = PETA_RESMI[kab].lower()
    else:
        for key in PETA_RESMI:
            if key in kab or kab in key:
                prov_resmi = PETA_RESMI[key].lower()
                break

    if prov_resmi is None:
        return "TIDAK_ADA"
    if prov_resmi == prov:
        return "OK"
    return "SALAH"


# ──────────────────────────────────────────────────────────────
# VALIDASI DATASET
# ──────────────────────────────────────────────────────────────
df = pd.read_csv('wisata_sulawesi_cleaned_final.csv')

df['status_validasi'] = df.apply(
    lambda r: cek_pasangan(r['kabupaten'], r['provinsi']), axis=1
)

print("=" * 60)
print("HASIL VALIDASI KABUPATEN vs PROVINSI")
print("=" * 60)
print(f"Total data  : {len(df)}")
print(f"  OK        : {(df['status_validasi'] == 'OK').sum()}")
print(f"  SALAH     : {(df['status_validasi'] == 'SALAH').sum()}")
print(f"  TIDAK_ADA : {(df['status_validasi'] == 'TIDAK_ADA').sum()}")
print()

salah = df[df['status_validasi'] == 'SALAH']
if len(salah) > 0:
    print(f">>> {len(salah)} DATA TIDAK SESUAI <<<")
    cols = ['nama_wisata', 'kabupaten', 'provinsi']
    print(salah[cols].to_string(index=True))
else:
    print("Tidak ada data yang tidak sesuai.")

print()
tidak_ada = df[df['status_validasi'] == 'TIDAK_ADA']
if len(tidak_ada) > 0:
    print(f">>> {len(tidak_ada)} Kabupaten tidak ditemukan di peta resmi (perlu cek manual):")
    print(tidak_ada[['nama_wisata', 'kabupaten', 'provinsi']].to_string(index=True))
