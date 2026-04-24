"""
scrape_lokasi.py
=================
Script untuk mengisi kolom `kabupaten` dan `provinsi` yang masih kosong
pada dataset wisata_sulawesi_cleaned_final.csv menggunakan pencarian DDGS.

Strategi:
  1. Cari via DDGS snippet → parse kabupaten/provinsi dari snippet
  2. Jika gagal, coba regex fallback dari snippet (nama kota Sulawesi)

Fitur:
  - Resume: skip baris yang kabupaten/provinsi sudah terisi
  - Auto-save setiap AUTOSAVE_INTERVAL baris
  - Graceful shutdown (Ctrl+C)
  - Log ke terminal
"""

import os
import re
import signal
import time
import logging

import pandas as pd
from ddgs import DDGS

# ──────────────────────────────────────────────
# KONFIGURASI
# ──────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(BASE_DIR, "wisata_sulawesi_cleaned_final.csv")
OUTPUT_FILE = INPUT_FILE  # overwrite langsung (simpan ke file yang sama)

DELAY_DETIK       = 2     # jeda antar baris (detik)
AUTOSAVE_INTERVAL = 30    # auto-save tiap N baris
DDGS_MAX_RESULTS  = 5     # jumlah snippet DDGS
DDGS_RETRIES      = 2
DDGS_RETRY_SLEEP  = 1.5
DDGS_REGION       = "id-id"

# ──────────────────────────────────────────────
# PETA PROVINSI & NAMA KOTA SULAWESI (untuk parsing)
# ──────────────────────────────────────────────
PROVINSI_MAP = {
    # Bahasa Indonesia
    "sulawesi selatan":  "Sulawesi Selatan",
    "sulawesi utara":    "Sulawesi Utara",
    "sulawesi tengah":   "Sulawesi Tengah",
    "sulawesi tenggara": "Sulawesi Tenggara",
    "sulawesi barat":    "Sulawesi Barat",
    "gorontalo":         "Gorontalo",
    # Variasi bahasa umum / Inggris
    "south sulawesi":    "Sulawesi Selatan",
    "north sulawesi":    "Sulawesi Utara",
    "central sulawesi":  "Sulawesi Tengah",
    "southeast sulawesi":"Sulawesi Tenggara",
    "west sulawesi":     "Sulawesi Barat",
    "sulsel":            "Sulawesi Selatan",
    "sulut":             "Sulawesi Utara",
    "sulteng":           "Sulawesi Tengah",
    "sultra":            "Sulawesi Tenggara",
    "sulbar":            "Sulawesi Barat",
}

# Mapping nama kota/kab terkenal → (kabupaten, provinsi) sebagai fallback
KOTA_FALLBACK = {
    "makassar":      ("Kota Makassar",       "Sulawesi Selatan"),
    "manado":        ("Kota Manado",          "Sulawesi Utara"),
    "palu":          ("Kota Palu",            "Sulawesi Tengah"),
    "kendari":       ("Kota Kendari",         "Sulawesi Tenggara"),
    "gorontalo":     ("Kota Gorontalo",       "Gorontalo"),
    "parepare":      ("Kota Parepare",        "Sulawesi Selatan"),
    "palopo":        ("Kota Palopo",          "Sulawesi Selatan"),
    "tomohon":       ("Kota Tomohon",         "Sulawesi Utara"),
    "bitung":        ("Kota Bitung",          "Sulawesi Utara"),
    "kotamobagu":    ("Kota Kotamobagu",      "Sulawesi Utara"),
    "bau-bau":       ("Kota Bau-Bau",        "Sulawesi Tenggara"),
    "baubau":        ("Kota Bau-Bau",        "Sulawesi Tenggara"),
    "maros":         ("Kabupaten Maros",      "Sulawesi Selatan"),
    "gowa":          ("Kabupaten Gowa",       "Sulawesi Selatan"),
    "bone":          ("Kabupaten Bone",       "Sulawesi Selatan"),
    "toraja utara":  ("Kabupaten Toraja Utara","Sulawesi Selatan"),
    "tana toraja":   ("Kabupaten Tana Toraja","Sulawesi Selatan"),
    "bantaeng":      ("Kabupaten Bantaeng",   "Sulawesi Selatan"),
    "bulukumba":     ("Kabupaten Bulukumba",  "Sulawesi Selatan"),
    "sinjai":        ("Kabupaten Sinjai",     "Sulawesi Selatan"),
    "takalar":       ("Kabupaten Takalar",    "Sulawesi Selatan"),
    "wajo":          ("Kabupaten Wajo",       "Sulawesi Selatan"),
    "soppeng":       ("Kabupaten Soppeng",    "Sulawesi Selatan"),
    "luwu":          ("Kabupaten Luwu",       "Sulawesi Selatan"),
    "luwu timur":    ("Kabupaten Luwu Timur", "Sulawesi Selatan"),
    "luwu utara":    ("Kabupaten Luwu Utara", "Sulawesi Selatan"),
    "enrekang":      ("Kabupaten Enrekang",   "Sulawesi Selatan"),
    "sidrap":        ("Kabupaten Sidenreng Rappang","Sulawesi Selatan"),
    "sidenreng":     ("Kabupaten Sidenreng Rappang","Sulawesi Selatan"),
    "pinrang":       ("Kabupaten Pinrang",    "Sulawesi Selatan"),
    "pangkep":       ("Kabupaten Pangkajene Dan Kepulauan","Sulawesi Selatan"),
    "pangkajene":    ("Kabupaten Pangkajene Dan Kepulauan","Sulawesi Selatan"),
    "barru":         ("Kabupaten Barru",      "Sulawesi Selatan"),
    "selayar":       ("Kabupaten Kepulauan Selayar","Sulawesi Selatan"),
    "mamuju":        ("Kabupaten Mamuju",     "Sulawesi Barat"),
    "majene":        ("Kabupaten Majene",     "Sulawesi Barat"),
    "polewali":      ("Kabupaten Polewali Mandar","Sulawesi Barat"),
    "mamasa":        ("Kabupaten Mamasa",     "Sulawesi Barat"),
    "poso":          ("Kabupaten Poso",       "Sulawesi Tengah"),
    "donggala":      ("Kabupaten Donggala",   "Sulawesi Tengah"),
    "parigi":        ("Kabupaten Parigi Moutong","Sulawesi Tengah"),
    "toli-toli":     ("Kabupaten Toli-Toli", "Sulawesi Tengah"),
    "tolitoli":      ("Kabupaten Toli-Toli", "Sulawesi Tengah"),
    "buol":          ("Kabupaten Buol",       "Sulawesi Tengah"),
    "morowali":      ("Kabupaten Morowali",   "Sulawesi Tengah"),
    "luwuk":         ("Kabupaten Banggai",    "Sulawesi Tengah"),
    "banggai":       ("Kabupaten Banggai",    "Sulawesi Tengah"),
    "sigi":          ("Kabupaten Sigi",       "Sulawesi Tengah"),
    "konawe":        ("Kabupaten Konawe",     "Sulawesi Tenggara"),
    "kolaka":        ("Kabupaten Kolaka",     "Sulawesi Tenggara"),
    "muna":          ("Kabupaten Muna",       "Sulawesi Tenggara"),
    "buton":         ("Kabupaten Buton",      "Sulawesi Tenggara"),
    "wakatobi":      ("Kabupaten Wakatobi",   "Sulawesi Tenggara"),
    "bombana":       ("Kabupaten Bombana",    "Sulawesi Tenggara"),
    "minahasa":      ("Kabupaten Minahasa",   "Sulawesi Utara"),
    "bolaang":       ("Kabupaten Bolaang Mongondow","Sulawesi Utara"),
    "sangihe":       ("Kabupaten Kepulauan Sangihe","Sulawesi Utara"),
    "talaud":        ("Kabupaten Kepulauan Talaud","Sulawesi Utara"),
    "bone bolango":  ("Kabupaten Bone Bolango","Gorontalo"),
}


# ──────────────────────────────────────────────
# SHUTDOWN GRACEFUL
# ──────────────────────────────────────────────
_shutdown = False

def _handle_signal(sig, frame):
    global _shutdown
    print("\n[!] Ctrl+C diterima — menyimpan data lalu keluar ...")
    _shutdown = True

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ──────────────────────────────────────────────
# SETUP LOGGER
# ──────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scrape_lokasi")


# ──────────────────────────────────────────────
# PARSER KABUPATEN & PROVINSI DARI TEKS SNIPPET
# ──────────────────────────────────────────────
def parse_kabupaten_dari_teks(teks: str) -> str:
    """Coba ekstrak 'Kabupaten/Kota XYZ' dari teks."""
    teks = str(teks)
    m = re.search(r'\b(Kabupaten|Kota)\s+([A-Za-z\s]+?)(?=\s*[,\.;(]|$|\d)',
                  teks, re.IGNORECASE)
    if m:
        tipe = m.group(1).capitalize()
        nama = m.group(2).strip().title()
        # Bersihkan kata umum yang sering nyangkut
        for stop in ["Indonesia", "Sulawesi", "Selatan", "Utara", "Tengah", "Tenggara", "Barat"]:
            nama = re.sub(r'\s*\b' + stop + r'\b', '', nama, flags=re.IGNORECASE).strip()
        if len(nama) > 2:
            return f"{tipe} {nama}"
    return ""


def parse_provinsi_dari_teks(teks: str) -> str:
    """Coba ekstrak nama provinsi dari teks."""
    t = str(teks).lower()
    for key, val in PROVINSI_MAP.items():
        if key in t:
            return val
    return ""


def fallback_dari_nama_kota(nama_wisata: str, alamat: str) -> tuple[str, str]:
    """
    Cek apakah salah satu nama kota terkenal muncul di nama wisata atau alamat.
    Kembalikan (kabupaten, provinsi) jika ketemu.
    """
    gabung = (str(nama_wisata) + " " + str(alamat)).lower()
    # Cek yang multi-kata dulu supaya tidak salah match
    for kota, (kab, prov) in sorted(KOTA_FALLBACK.items(), key=lambda x: -len(x[0])):
        if re.search(r'\b' + re.escape(kota) + r'\b', gabung):
            return kab, prov
    return "", ""


# ──────────────────────────────────────────────
# SCRAPING DDGS
# ──────────────────────────────────────────────
def cari_lokasi_ddgs(nama_wisata: str, alamat: str) -> tuple[str, str]:
    """
    Cari kabupaten & provinsi via DDGS.
    Kembalikan ("", "") jika tidak ditemukan.
    """
    query = f"{nama_wisata} Sulawesi lokasi kabupaten provinsi"
    logger.debug(f"  Query: {query}")

    hasil = []
    for attempt in range(DDGS_RETRIES):
        try:
            with DDGS() as ddgs:
                hasil = list(ddgs.text(query,
                                        max_results=DDGS_MAX_RESULTS,
                                        region=DDGS_REGION))
            break
        except Exception as e:
            logger.debug(f"  DDGS retry {attempt+1}: {e}")
            if attempt + 1 < DDGS_RETRIES:
                time.sleep(DDGS_RETRY_SLEEP * (attempt + 1))

    if not hasil:
        return "", ""

    for item in hasil:
        teks = f"{item.get('title', '')} {item.get('body', '')}"
        kab  = parse_kabupaten_dari_teks(teks)
        prov = parse_provinsi_dari_teks(teks)
        if kab and prov:
            return kab, prov
        if prov and not kab:
            # Coba fallback kota dari snippet
            kab2, _ = fallback_dari_nama_kota(nama_wisata, teks)
            if kab2:
                return kab2, prov

    # Jika dari snippet tidak dapat, coba dari provinsi apa pun yang ketemu
    kab_terbaik, prov_terbaik = "", ""
    for item in hasil:
        teks = f"{item.get('title', '')} {item.get('body', '')}"
        if not prov_terbaik:
            prov_terbaik = parse_provinsi_dari_teks(teks)
        if not kab_terbaik:
            kab_terbaik = parse_kabupaten_dari_teks(teks)

    return kab_terbaik, prov_terbaik


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    global _shutdown

    logger.info(f"Membaca: {INPUT_FILE}")
    df = pd.read_csv(INPUT_FILE)
    total = len(df)

    # Pastikan kolom ada
    if 'kabupaten' not in df.columns:
        df['kabupaten'] = None
    if 'provinsi' not in df.columns:
        df['provinsi'] = None

    # Identifikasi baris yang perlu diisi
    perlu_isi = df['kabupaten'].isna() | df['provinsi'].isna() | \
                (df['kabupaten'].astype(str).str.strip() == '') | \
                (df['provinsi'].astype(str).str.strip() == '')

    idx_target = df[perlu_isi].index.tolist()
    logger.info(f"Total data: {total} | Perlu diisi: {len(idx_target)} baris")

    diproses = 0
    diisi    = 0

    for i, idx in enumerate(idx_target):
        if _shutdown:
            break

        row         = df.loc[idx]
        nama_wisata = str(row.get('nama_wisata', ''))
        alamat      = str(row.get('alamat', ''))

        kab_ada  = str(row.get('kabupaten', '')).strip()
        prov_ada = str(row.get('provinsi', '')).strip()
        kab_ada  = '' if kab_ada  in ('nan', 'None', '') else kab_ada
        prov_ada = '' if prov_ada in ('nan', 'None', '') else prov_ada

        logger.info(f"[{i+1}/{len(idx_target)}] {nama_wisata}")

        # ── Langkah 1: Fallback dari nama kota di alamat/nama (gratis, tanpa internet)
        kab_new, prov_new = "", ""
        if not kab_ada or not prov_ada:
            kab_fb, prov_fb = fallback_dari_nama_kota(nama_wisata, alamat)
            kab_new  = kab_fb  if kab_fb  else kab_ada
            prov_new = prov_fb if prov_fb else prov_ada

        # ── Langkah 2: Jika masih belum lengkap, cari via DDGS
        if not kab_new or not prov_new:
            kab_ddgs, prov_ddgs = cari_lokasi_ddgs(nama_wisata, alamat)
            if not kab_new and kab_ddgs:
                kab_new = kab_ddgs
            if not prov_new and prov_ddgs:
                prov_new = prov_ddgs
            time.sleep(DELAY_DETIK)

        # ── Update dataframe
        if kab_new:
            df.at[idx, 'kabupaten'] = kab_new
        if prov_new:
            df.at[idx, 'provinsi'] = prov_new

        if kab_new or prov_new:
            diisi += 1
            logger.info(f"  ✓ Kab: {kab_new or '-'} | Prov: {prov_new or '-'}")
        else:
            logger.info(f"  ✗ Tidak ditemukan")

        diproses += 1

        # Auto-save
        if diproses % AUTOSAVE_INTERVAL == 0:
            df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
            logger.info(f"  [Auto-save] {diproses} baris diproses -> {OUTPUT_FILE}")

    # Simpan akhir
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')

    # Laporan akhir
    logger.info("=" * 50)
    logger.info(f"Selesai! Diproses: {diproses} | Berhasil diisi: {diisi}")
    logger.info(f"Kabupaten kosong sisa: {df['kabupaten'].isna().sum()}")
    logger.info(f"Provinsi kosong sisa : {df['provinsi'].isna().sum()}")
    logger.info(f"File disimpan ke: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
