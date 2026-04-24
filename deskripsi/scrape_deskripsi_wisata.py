"""
scrape_deskripsi_wisata.py
======================================================
Script untuk menambahkan kolom deskripi ke dataset wisata
dengan menggunakan sistem pencarian bertingkat:
  - Level 1 : Wikipedia API Bahasa Indonesia (Diutamakan)
  - Level 2 : DuckDuckGo Search (DDGS) snippet (Fallback)

Output yang dihasilkan berupa CSV dengan urutan kolom:
  - nama_wisata
  - alamat
  - kabupaten
  - provinsi
  - deskripsi_wisata
  - sumber_deskripsi

Fitur Graceful Shutdown dan Resume sudah disematkan, 
tekan Ctrl+C untuk membatalkan dan menyimpan state.
"""

import os
import re
import sys
import time
import signal
import logging
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

try:
    from ddgs import DDGS
except ImportError:
    # Memastikan pengguna tahu kalau pustaka kurang
    print("Error: pustaka 'duckduckgo_search' belum di-install.")
    print("Jalankan: pip install duckduckgo_search")
    sys.exit(1)

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

# ── KONFIGURASI PATH ──────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
# Sesuaikan posisi file input jika struktur foldernya berubah
INPUT_FILE  = os.path.join(BASE_DIR, "..", "hasil_scrap", "wisata_sulawesi_cleaned_final.csv")
# Jika input file diatas tidak ada, coba ambil file terbaru di hasil_scrap atau base dir.
if not os.path.exists(INPUT_FILE):
    INPUT_FILE = os.path.join(BASE_DIR, "..", "wisata_sulawesi_20260418_120209.csv") # Placeholder

OUTPUT_FILE = os.path.join(BASE_DIR, "scrap_deskripsi_wisata.csv")
LOG_DIR     = os.path.join(BASE_DIR, "logs")

# ── KONFIGURASI SCRAPER ────────────────────────────────
AUTOSAVE_INTERVAL = 20
DELAY_BETWEEN = 1.5 
MAX_CHARS   = 600   # Max karakter jika snippet terlalu panjang

# Global state untuk graceful shutdown
graceful_exit = False
session = requests.Session()

def handle_sigint(signum, frame):
    global graceful_exit
    print("\n[INFO] Menangkap sinyal interupsi (Ctrl+C). Menyimpan data sebelum keluar...")
    graceful_exit = True

signal.signal(signal.SIGINT, handle_sigint)

def setup_logger():
    os.makedirs(LOG_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"scrape_deskripsi_{ts}.log")

    logger = logging.getLogger("ScraperDeskripsi")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", datefmt="%H:%M:%S")

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger

log = setup_logger()

# ── PARSER LOKASI ──────────────────────────────────────
def ekstrak_lokasi(alamat: str) -> tuple[str, str]:
    """Ekstrak (kabupaten/kota, provinsi) dari alamat Google Maps."""
    if not alamat or str(alamat).lower() in ("nan", ""):
        return "", ""

    alamat = str(alamat)
    al_lower = alamat.lower()

    prov_map = {
        "sulawesi selatan":  "Sulawesi Selatan",
        "sulawesi tengah":   "Sulawesi Tengah",
        "sulawesi tenggara": "Sulawesi Tenggara",
        "sulawesi utara":    "Sulawesi Utara",
        "sulawesi barat":    "Sulawesi Barat",
        "gorontalo":         "Gorontalo",
    }
    provinsi = ""
    for key, val in prov_map.items():
        if key in al_lower:
            provinsi = val
            break

    m = re.search(r'\b(Kabupaten|Kota)\s+([A-Za-z\s]+?)(?:\s*\d{4,}|,|$)', alamat, re.IGNORECASE)
    kabupaten = ""
    if m:
        tipe = m.group(1).capitalize()
        nama = m.group(2).strip().title()
        kabupaten = f"{tipe} {nama}"
    
    return kabupaten, provinsi

def clean_text(text: str) -> str:
    """Membersihkan teks dari karakter HTML kotor dan menyingkat panjang."""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[\d+\]', '', text) # buang notasi referensi wikipedia [1]
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS].rsplit(' ', 1)[0] + '...'
    return text

# ── LEVEL 1: WIKIPEDIA ─────────────────────────────────
def get_wikipedia_lvl1(nama: str, kabupaten: str) -> tuple[str, str]:
    """
    Search di API Wikipedia Bahasa Indonesia.
    Return (deskripsi, sumber_url) atau ("", "") jika gagal.
    """
    try:
        # Coba query dengan nama + kabupaten dulu untuk menekan homonim
        queries = [f"{nama} {kabupaten}".strip(), nama.strip()]
        
        for q in queries:
            if not q: continue
            
            # 1. Search Title
            search_url = "https://id.wikipedia.org/w/api.php"
            search_params = {
                "action": "query", "list": "search", "srsearch": q,
                "utf8": "", "format": "json", "srlimit": 1
            }
            res = session.get(search_url, params=search_params, timeout=10)
            data = res.json()
            
            search_results = data.get("query", {}).get("search", [])
            if not search_results:
                continue # Coba query berikutnya
                
            title = search_results[0]['title']
            
            # Abaikan jika hasil title berupa kompilasi daftar atau tidak relevan
            title_lower = title.lower()
            if title_lower.startswith('daftar ') or title_lower.startswith('kecamatan '):
                continue
            
            # Simplifikasi: kita asumsikan Wikipedia rankingnya cukup baik
            
            # 2. Ambil Extract
            ext_params = {
                "action": "query", "prop": "extracts", "exintro": "1",
                "explaintext": "1", "titles": title, "format": "json"
            }
            res_ext = session.get(search_url, params=ext_params, timeout=10)
            data_ext = res_ext.json()
            
            pages = data_ext.get("query", {}).get("pages", {})
            for page_id, page_info in pages.items():
                if int(page_id) < 0: continue
                
                extract = page_info.get("extract", "")
                # Jika terkena halaman disambiguasi biasanya sangat pendek dan ada ciri kalimat 'merujuk pada'
                if len(extract) < 50 or "merujuk pada: " in extract.lower() or "dapat merujuk kepada:" in extract.lower():
                    continue
                    
                desc = clean_text(extract)
                source_url = f"https://id.wikipedia.org/wiki/{title.replace(' ', '_')}"
                return desc, source_url
            
    except Exception as e:
        log.debug(f"[L1 Wiki] Error: {e}")
        
    return "", ""

# ── LEVEL 2 & 3: DUCKDUCKGO + BEAUTIFULSOUP + PLAYWRIGHT ────────────────
def get_ddgs_lvl2_3(nama: str, kabupaten: str, pw_page=None) -> tuple[str, str]:
    """
    Search di DDGS. Mencoba L2 (BS4), L3 (Playwright), lalu fallback Snippet.
    """
    query = f'{nama} {kabupaten} wisata'
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4, region="id-id"))
            
        nama_words = [w.lower() for w in nama.replace('-', ' ').split() if len(w) > 3 and w.lower() not in ["taman", "pantai", "bukit", "gunung", "danau", "batu", "air", "terjun"]]
        if not nama_words:
            nama_words = [nama.lower()]

        valid_urls = []
        for res in results:
            href = res.get("href", "")
            href_lower = href.lower()
            domain_skip = ["trip.com", "traveloka.com", "tiket.com", "agoda.com", "booking.com", "tripadvisor.", "facebook.", "youtube.", "tiktok.", "instagram.", "twitter.", "pinterest."]
            if any(dom in href_lower for dom in domain_skip): continue
            if href: valid_urls.append(href)

        def extract_p(html_text):
            soup = BeautifulSoup(html_text, "html.parser")
            for p in soup.find_all("p"):
                t = p.get_text(separator=" ", strip=True)
                if 120 < len(t) < 1000 and any(w in t.lower() for w in nama_words):
                    return clean_text(t)
            return ""

        # L2: BS4
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"}
        for href in valid_urls:
            try:
                resp = session.get(href, timeout=8, headers=headers)
                if resp.status_code == 200:
                    desc = extract_p(resp.text)
                    if desc: return desc, f"{href} [L2]"
            except Exception as e:
                log.debug(f"[L2 BS4] Gagal ekstraksi url {href} -> {e}")

        # L3: Playwright fallback
        if PLAYWRIGHT_OK and pw_page:
            log.debug(f"      L2 Gagal. Mencoba L3 Playwright...")
            for href in valid_urls:
                try:
                    pw_page.goto(href, wait_until="domcontentloaded", timeout=15000)
                    desc = extract_p(pw_page.content())
                    if desc: return desc, f"{href} [L3]"
                except Exception as e:
                    log.debug(f"[L3 PW] Gagal ekstraksi url {href} -> {e}")

        # Fallback Snippet
        for res in results:
            title_lower = res.get("title", "").lower()
            if not re.search(r'\b(\d+\s+(tempat|destinasi|wisata)|daftar\s|rekomendasi\s)\b', title_lower):
                body = res.get("body", "")
                if len(body) > 100 and any(w in body.lower() for w in nama_words):
                    return clean_text(body), res.get("href", "") + " [Snippet]"

    except Exception as e:
        log.debug(f"[DDGS] Error: {e}")
        
    return "", ""

# ── MAIN PIPELINE ──────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("Memulai Scraper Deskripsi Wisata (L1: Wikipedia, L2: DDGS)")
    log.info("=" * 60)

    # 1. Pastikan File Csv (Resume/Mulai)
    if not os.path.exists(INPUT_FILE) and not os.path.exists(OUTPUT_FILE):
        log.error(f"File input tidak ditemukan di path: {INPUT_FILE}")
        log.error("Jalankan script dari folder yang sama, atau ubah variabel INPUT_FILE di script.")
        return

    # Bila ada output lama, kita load output itu untuk dilanjutkan (resume)
    source_csv = OUTPUT_FILE if os.path.exists(OUTPUT_FILE) else INPUT_FILE
    log.info(f"Membaca data dari: {source_csv}")
    
    try:
        df = pd.read_csv(source_csv)
    except Exception as e:
        log.error(f"Gagal membaca CSV: {e}")
        return

    # Pastikan struktur kolom lengkap di target dataset
    for col in ["kabupaten", "provinsi", "deskripsi_wisata", "sumber_deskripsi"]:
        if col not in df.columns:
            df[col] = ""

    # Sort & Cleanup Kolom untuk keseragaman output yang diminta di chat
    target_cols = [
        "nama_wisata", "alamat", "kabupaten", "provinsi", 
        "deskripsi_wisata", "sumber_deskripsi"
    ]
    # Hanya pastikan kolom target yang disimpan
    df = df[target_cols]

def jalankan_siklus(df, total_baris, pw_page=None):
    global graceful_exit
    baris_baru = 0
    baris_sudah = 0

    for idx, row in df.iterrows():
        if graceful_exit:
            break

        nama = str(row.get("nama_wisata", "")).strip()
        alamat = str(row.get("alamat", "")).strip()
        deskripsi_sebelumnya = str(row.get("deskripsi_wisata", "")).strip()
        kab_sebelumnya = str(row.get("kabupaten", "")).strip()

        # Ekstrak Lokasi jika belum ada
        if not kab_sebelumnya or kab_sebelumnya.lower() == "nan":
            kab, prov = ekstrak_lokasi(alamat)
            df.at[idx, "kabupaten"] = kab
            df.at[idx, "provinsi"]  = prov
        else:
            kab = kab_sebelumnya

        # Cek Resume Mode (Skip jika sudah ada data asli; jangan skip jika '-' atau nan)
        if deskripsi_sebelumnya and deskripsi_sebelumnya.lower() != "nan" and deskripsi_sebelumnya != "-":
            baris_sudah += 1
            if baris_sudah % 100 == 0:
                log.info(f"[Resume] Baris [{idx+1}/{total_baris}] terlewati (sudah ada data).")
            continue

        log.info(f"[{idx+1}/{total_baris}] Mencari: {nama}")

        # L1: Wikipedia
        desc, source = get_wikipedia_lvl1(nama, kab)

        # L2/L3: DuckDuckGo Fallback
        if not desc:
            log.debug(f"      L1 Gagal, mencoba L2/L3 DDGS/BS4/Playwright...")
            time.sleep(DELAY_BETWEEN) # delay wajar
            desc, source = get_ddgs_lvl2_3(nama, kab, pw_page)

        # Simpan state ke DataFrame
        if desc:
            log.info(f"      => Sukses dari: {source}")
            df.at[idx, "deskripsi_wisata"] = desc
            df.at[idx, "sumber_deskripsi"] = source
        else:
            log.info(f"      => Gagal mencari deskripsi.")
            df.at[idx, "deskripsi_wisata"] = "-"
            df.at[idx, "sumber_deskripsi"] = "-"

        baris_baru += 1
        time.sleep(DELAY_BETWEEN)

        # Auto-save
        if baris_baru > 0 and baris_baru % AUTOSAVE_INTERVAL == 0:
            log.info(f"*** Auto-saving {baris_baru} baris diproses...")
            df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

# ── MAIN PIPELINE ──────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("Memulai Scraper Deskripsi Wisata (L1: Wikipedia, L2: BS4, L3: Playwright)")
    log.info("=" * 60)

    # 1. Pastikan File Csv (Resume/Mulai)
    if not os.path.exists(INPUT_FILE) and not os.path.exists(OUTPUT_FILE):
        log.error(f"File input tidak ditemukan di path: {INPUT_FILE}")
        log.error("Jalankan script dari folder yang sama, atau ubah variabel INPUT_FILE di script.")
        return

    # Bila ada output lama, kita load output itu untuk dilanjutkan (resume)
    source_csv = OUTPUT_FILE if os.path.exists(OUTPUT_FILE) else INPUT_FILE
    log.info(f"Membaca data dari: {source_csv}")
    
    try:
        df = pd.read_csv(source_csv)
    except Exception as e:
        log.error(f"Gagal membaca CSV: {e}")
        return

    # Pastikan struktur kolom lengkap di target dataset
    for col in ["kabupaten", "provinsi", "deskripsi_wisata", "sumber_deskripsi"]:
        if col not in df.columns:
            df[col] = ""

    # Sort & Cleanup Kolom untuk keseragaman output yang diminta di chat
    target_cols = [
        "nama_wisata", "alamat", "kabupaten", "provinsi", 
        "deskripsi_wisata", "sumber_deskripsi"
    ]
    # Hanya pastikan kolom target yang disimpan
    df = df[target_cols]

    total_baris = len(df)
    log.info(f"Total baris dataset: {total_baris}")

    try:
        if PLAYWRIGHT_OK:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(extra_http_headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"})
                page.set_default_timeout(15000)
                try:
                    jalankan_siklus(df, total_baris, page)
                finally:
                    browser.close()
        else:
            log.info("Playwright tidak tersedia, L3 akan dilewati.")
            jalankan_siklus(df, total_baris, None)
    except Exception as e:
        log.error(f"Error pada execution pipeline: {e}")

    # Final Save
    log.info("\nMenyimpan file final...")
    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
    log.info(f"Berhasil disimpan: {OUTPUT_FILE}")
    log.info("Selesai dikerjakan!")

if __name__ == "__main__":
    main()
