"""
scrape_gmaps_photos.py
======================
Ambil foto pengunjung (user-uploaded) dari Google Maps menggunakan Playwright.
Tidak membutuhkan Google Maps API key.

Strategi pencarian:
  1. Buka Google Maps lewat URL place_id (jika tersedia di CSV)
  2. Fallback: ketik "nama_wisata kota" di kotak pencarian Google Maps
  3. Klik tab "Foto" → scroll → ambil URL gambar dari CDN Google
     (lh5.googleusercontent.com / lh3.googleusercontent.com)

Kolom output yang diperbarui:
  - image            : URL foto terbaik (bisa langsung dibuka browser)
  - image_gmaps_src  : audit sumber ("gmaps-visitor-photo")

Penggunaan:
  python scrape_gmaps_photos.py --limit 10
  python scrape_gmaps_photos.py --headless --delay 3
  python scrape_gmaps_photos.py --force   (isi ulang semua meski sudah ada)

Catatan: Digunakan untuk keperluan akademik/penelitian.
"""

from __future__ import annotations

import argparse
import os
import re
import signal
import sys
import time
from datetime import datetime

import pandas as pd
from playwright.sync_api import sync_playwright

# Paksa stdout UTF-8 agar emoji/unicode tidak error di Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

class LoggerWriter:
    def __init__(self, filename):
        self.terminal = sys.stdout
        self.log = open(filename, "a", encoding="utf-8")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    def flush(self):
        self.terminal.flush()
        self.log.flush()

# ─────────────────────────────────────────────
#  KONFIGURASI
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "..", "hasil_scrap")

INPUT_FILE  = os.path.join(DATA_DIR, "wisata_sulawesi_cleaned_final.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "scrap_image.csv")

DEFAULT_DELAY      = 3.5    # detik antar baris
AUTOSAVE_INTERVAL  = 25     # auto-save setiap N baris
MAX_SCROLL         = 3      # berapa kali scroll galeri foto
NAV_TIMEOUT        = 20_000 # ms – timeout navigasi
ELEM_TIMEOUT       = 8_000  # ms – timeout cari elemen

# URL langsung via place_id
MAPS_CID_URL = "https://www.google.com/maps/search/?api=1&query={name}&query_place_id={place_id}"
MAPS_SEARCH  = "https://www.google.com/maps/search/{query}"

# Pattern URL foto Google CDN
_PHOTO_CDN = re.compile(
    r'https://(?:lh\d\.googleusercontent\.com|streetviewpixels-pa\.googleapis\.com)[^"\'>\s]+'
)

# ─────────────────────────────────────────────
#  HELPER: ekstrak kota dari alamat
# ─────────────────────────────────────────────
def _kota_dari_alamat(alamat: str) -> str:
    """Ambil kota/kabupaten pendek untuk query pencarian."""
    if not alamat or str(alamat).lower() == "nan":
        return ""
    a = str(alamat)
    # Cari "Kabupaten X" atau "Kota X"
    m = re.search(r'\b(Kabupaten|Kota)\s+([A-Za-z\s]+?)(?:\s*\d{4,}|,|$)', a, re.I)
    if m:
        return m.group(2).strip().split(",")[0].strip()
    # Fallback: ambil token sebelum kode pos
    parts = a.split(",")
    for part in reversed(parts):
        p = part.strip()
        if re.search(r'sulawesi|gorontalo', p, re.I):
            return p.split()[0].strip()
    return ""


def _best_resolution_url(url: str) -> str:
    """Upgrade resolusi foto Google CDN ke ukuran lebih besar."""
    # Ganti parameter =w<N>-h<M> atau =s<N> ke resolusi 1200px
    url = re.sub(r'=w\d+-h\d+.*$', '=w1200-h800-k-no', url)
    url = re.sub(r'=s\d+.*$',      '=s1200',            url)
    return url


def _is_google_api_url(url: str) -> bool:
    """Cek apakah URL masih url Google Places API (butuh key)."""
    return "maps.googleapis.com/maps/api/place/photo" in str(url)


def _is_valid_gmaps_photo(url: str) -> bool:
    """Cek apakah URL adalah foto CDN Google Maps yang valid."""
    return bool(url) and (
        "googleusercontent.com" in url or
        "streetviewpixels" in url
    )


# ─────────────────────────────────────────────
#  CORE: ambil foto satu tempat wisata
# ─────────────────────────────────────────────
def ambil_foto_satu_wisata(
    page,
    nama: str,
    alamat: str,
    place_id: str,
    delay: float,
) -> str | None:
    """
    Buka Google Maps, cari tempat, klik foto, kembalikan URL foto terbaik.
    Return None jika gagal.
    """
    kota = _kota_dari_alamat(alamat)
    query_str = f"{nama} {kota}".strip() if kota else nama

    # ── Strategi A: langsung via place_id ───────────────────
    photo_url = None
    loaded_via_pid = False

    if place_id and str(place_id).lower() not in ("nan", "none", ""):
        try:
            target_url = MAPS_CID_URL.format(
                name=nama.replace(" ", "+"),
                place_id=place_id,
            )
            page.goto(target_url, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
            time.sleep(1.5)
            loaded_via_pid = True
        except Exception:
            loaded_via_pid = False

    # ── Strategi B: ketik pencarian manual ──────────────────
    if not loaded_via_pid:
        try:
            encoded = query_str.replace(" ", "+")
            page.goto(
                MAPS_SEARCH.format(query=encoded),
                timeout=NAV_TIMEOUT,
                wait_until="domcontentloaded",
            )
            time.sleep(2)

            # Klik hasil pertama jika ada daftar
            first_result = page.locator(
                'a[href*="/maps/place/"], div[data-result-index="0"] a'
            ).first
            if first_result.count() > 0:
                first_result.click(timeout=ELEM_TIMEOUT)
                time.sleep(2)
        except Exception:
            pass

    # ── Tutup dialog "sebelum melanjutkan" jika ada ─────────
    try:
        reject_btn = page.locator(
            'button:has-text("Tolak semua"), '
            'button:has-text("Reject all"), '
            'button:has-text("Accept all"), '
            'button[aria-label*="Tolak"]'
        ).first
        if reject_btn.is_visible(timeout=2000):
            reject_btn.click()
            time.sleep(0.8)
    except Exception:
        pass

    # ── Klik tab Foto ────────────────────────────────────────
    try:
        foto_tab = page.locator(
            'button[aria-label*="Foto"], '
            'button[data-tab-index]:has-text("Foto"), '
            '[role="tab"]:has-text("Photo"), '
            '[role="tab"]:has-text("Foto")'
        ).first
        if foto_tab.is_visible(timeout=ELEM_TIMEOUT):
            foto_tab.click()
            time.sleep(1.5)
    except Exception:
        # Coba selector alternatif
        try:
            page.get_by_role("tab", name=re.compile("foto|photo", re.I)).first.click()
            time.sleep(1.5)
        except Exception:
            pass



    # ── Scroll galeri foto untuk lazy-load ──────────────────
    try:
        for _ in range(MAX_SCROLL):
            page.keyboard.press("PageDown")
            time.sleep(0.8)
    except Exception:
        pass

    # ── Kumpulkan URL foto dari DOM ──────────────────────────
    collected: list[str] = []

    # Cara 1: ambil dari atribut src/srcset semua <img>
    try:
        imgs = page.query_selector_all("img[src*='googleusercontent'], img[src*='lh3.'], img[src*='lh5.']")
        for img in imgs:
            src = img.get_attribute("src") or ""
            if _PHOTO_CDN.match(src):
                collected.append(_best_resolution_url(src))
    except Exception:
        pass

    # Cara 2: scrape innerHTML untuk URL yang ter-escape
    try:
        html = page.content()
        for raw in _PHOTO_CDN.findall(html):
            u = _best_resolution_url(raw)
            if u not in collected:
                collected.append(u)
    except Exception:
        pass

    # Cara 3: cari elemen dengan style background-image (galeri thumbnail)
    try:
        tiles = page.query_selector_all('[style*="googleusercontent"]')
        for tile in tiles:
            style = tile.get_attribute("style") or ""
            m = re.search(r'url\(["\']?(https://[^"\')\s]+)["\']?\)', style)
            if m:
                u = _best_resolution_url(m.group(1))
                if u not in collected:
                    collected.append(u)
    except Exception:
        pass

    if not collected:
        return None

    # Filter tambahan: singkirkan URL yang merupakan thumbnail video Youtube/Maps
    valid_photos = []
    for u in collected:
        u_lower = str(u).lower()
        if "ytimg" in u_lower or "/vi/" in u_lower or "video" in u_lower:
            continue
        valid_photos.append(u)

    if not valid_photos:
        valid_photos = collected

    # Pilih URL PERTAMA (yang paling relevan menurut DOM/urutan Google), 
    # BUKAN yang string-nya terpanjang.
    return valid_photos[0]


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="Scrape foto wisata dari Google Maps via Playwright")
    ap.add_argument("--input",    default=INPUT_FILE)
    ap.add_argument("--output",   default=OUTPUT_FILE)
    ap.add_argument("--limit",    type=int, default=0,    help="Maks baris diproses (0=semua)")
    ap.add_argument("--delay",    type=float, default=DEFAULT_DELAY)
    ap.add_argument("--headless", action="store_true",    help="Jalankan tanpa jendela browser")
    ap.add_argument("--force",    action="store_true",    help="Isi ulang meski sudah ada foto")
    args = ap.parse_args()

    # Inisialisasi logger agar print tampil di console dan ter-save di file log
    _TS = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(BASE_DIR, f"log_scrape_gmaps_photos_{_TS}.txt")
    sys.stdout = LoggerWriter(log_filename)
    sys.stderr = sys.stdout

    if not os.path.isfile(args.input):
        print(f"[ERROR] File input tidak ditemukan: {args.input}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    print(f"[INPUT]  {args.input} ({len(df)} baris)")
    print(f"[OUTPUT] {args.output}")

    # Bersihkan link API Google Maps dari data sebelum memproses
    for i in range(len(df)):
        img = str(df.at[i, "image"]).strip()
        if "googleapis.com" in img:
            df.at[i, "image"] = ""

    # Fitur Resume: Ambil progress yang sudah tersimpan sebelumnya
    if os.path.exists(args.output):
        try:
            df_prog = pd.read_csv(args.output)
            print(f"[RESUME] Membaca progress dari {args.output}")
            for i in range(min(len(df), len(df_prog))):
                prog_img = str(df_prog.at[i, "url_image"]).strip()
                if prog_img and prog_img.lower() not in ("nan", ""):
                    df.at[i, "image"] = prog_img
        except Exception as e:
            print(f"[WARN] Gagal memuat progress (mungkin ini run perdana): {e}")

    # Pastikan kolom audit tersedia
    if "image_gmaps_src" not in df.columns:
        df["image_gmaps_src"] = ""

    # ── INSTANT & GRACEFUL SHUTDOWN ──────────────────────────
    def _handle_sigint(sig, frame):
        print("\n[STOP] Ctrl+C ditekan! Memaksa berhenti instan dan memutus sinkronisasi browser...")
        try:
            os.makedirs(os.path.dirname(args.output), exist_ok=True)
            df_out = df.copy()
            df_out.rename(columns={'nama_wisata': 'nama wisata', 'alamat': 'lokasi', 'image': 'url_image'}, inplace=True)
            df_out[['nama wisata', 'lokasi', 'kabupaten', 'provinsi', 'url_image']].to_csv(args.output, index=False, encoding="utf-8-sig")
            print(f"       [SUCCESS] Progress terbaru sukses diselamatkan di: {args.output}")
        except Exception as e:
            print(f"       [ERROR] Gagal save darurat: {e}")
        os._exit(0) # Langsung terminal kill secara hardcore tanpa menunggu Playwright bengong

    signal.signal(signal.SIGINT, _handle_sigint)

    n_ok = n_skip = n_fail = 0
    processed = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=args.headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        ctx = browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="id-ID",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = ctx.new_page()

        # Buka Google Maps awal (supaya cookie ter-set)
        try:
            page.goto("https://www.google.com/maps", timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
            time.sleep(2)
            # Tolak dialog cookie jika ada
            for selector in [
                'button:has-text("Tolak semua")',
                'button:has-text("Reject all")',
                'button[aria-label*="Tolak"]',
                'form[action*="reject"] button',
            ]:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        btn.click()
                        time.sleep(1)
                        break
                except Exception:
                    pass
        except Exception as e:
            print(f"[WARN] Gagal buka Google Maps awal: {e}")

        for idx, row in df.iterrows():
            if args.limit and processed >= args.limit:
                break

            nama      = str(row.get("nama_wisata", "")).strip()
            alamat    = str(row.get("alamat", "")).strip()
            place_id  = str(row.get("place_id", "")).strip()
            img_cur   = str(row.get("image", "")).strip()

            # Skip baris tanpa nama
            if not nama:
                continue

            # Skip jika sudah punya foto non-API (kecuali --force)
            already_ok = (
                img_cur
                and img_cur.lower() not in ("nan", "")
                and not _is_google_api_url(img_cur)
                and _is_valid_gmaps_photo(img_cur)
            )
            if already_ok and not args.force:
                n_skip += 1
                continue

            processed += 1
            kota = _kota_dari_alamat(alamat) or "Sulawesi"
            print(f"[{idx+1:>5}] CARI: {nama[:50]} | {kota}", end=" -> ", flush=True)

            try:
                url = ambil_foto_satu_wisata(page, nama, alamat, place_id, args.delay)
            except Exception as e:
                url = None
                print(f"ERROR: {e}")

            if url and _is_valid_gmaps_photo(url):
                df.at[idx, "image"]           = url
                df.at[idx, "image_gmaps_src"] = "gmaps-visitor-photo"
                n_ok += 1
                print(f"OK  {url[:80]}...")
            else:
                n_fail += 1
                print("FAIL tidak ditemukan")

            # Auto-save
            if processed % AUTOSAVE_INTERVAL == 0:
                df_out = df.copy()
                df_out.rename(columns={'nama_wisata': 'nama wisata', 'alamat': 'lokasi', 'image': 'url_image'}, inplace=True)
                df_out[['nama wisata', 'lokasi', 'kabupaten', 'provinsi', 'url_image']].to_csv(args.output, index=False, encoding="utf-8-sig")
                print(f"    [SAVE] auto-save ({processed} baris diproses, {n_ok} OK)")

            time.sleep(max(1.0, args.delay))

        # Simpan final
        try:
            browser.close()
        except Exception:
            pass

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    df_out = df.copy()
    df_out.rename(columns={'nama_wisata': 'nama wisata', 'alamat': 'lokasi', 'image': 'url_image'}, inplace=True)
    df_out[['nama wisata', 'lokasi', 'kabupaten', 'provinsi', 'url_image']].to_csv(args.output, index=False, encoding="utf-8-sig")

    print("\n" + "="*60)
    print("  SELESAI!")
    print(f"  File      : {args.output}")
    print(f"  Berhasil  : {n_ok}")
    print(f"  Gagal     : {n_fail}")
    print(f"  Dilewati  : {n_skip}")
    print(f"  Diproses  : {processed}")
    print("="*60)


if __name__ == "__main__":
    main()
