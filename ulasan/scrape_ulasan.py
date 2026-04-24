import os
import csv
import json
import logging
import urllib.parse
from playwright.sync_api import sync_playwright

# ================================================================
# KONFIGURASI
# ================================================================
LOG_FILE    = "scraper_ulasan.log"
CSV_INPUT   = r"..\hasil_final\wisata_sulawesi_lengkap.csv"
CSV_OUTPUT  = "ulasan_wisata_sulawesi.csv"
RESUME_FILE = "resume_ulasan.json"
MAX_REVIEWS = 10
MIN_REVIEWS = 10   # Hanya scrape wisata dengan ulasan > MIN_REVIEWS

# ================================================================
# LOGGING
# ================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-7s | %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ================================================================
# RESUME: Baca dari CSV output (primary) + JSON (backup)
# ================================================================
def load_processed_ids():
    """
    Baca place_id yang sudah ada di CSV output sebagai sumber utama.
    Jika ada resume JSON, gabungkan juga.
    """
    processed = set()

    # 1. Baca dari CSV output
    if os.path.isfile(CSV_OUTPUT):
        try:
            with open(CSV_OUTPUT, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get('place_id', '').strip()
                    if pid:
                        processed.add(pid)
            logging.info(f"Resume dari CSV: {len(processed)} wisata sudah punya ulasan.")
        except Exception as e:
            logging.warning(f"Tidak bisa baca CSV output untuk resume: {e}")

    # 2. Tambahkan dari JSON resume (opsional, jika Anda ingin mereset skip, silakan hapus file resume_ulasan.json)
    if os.path.isfile(RESUME_FILE):
        try:
            with open(RESUME_FILE, 'r', encoding='utf-8') as f:
                json_ids = set(json.load(f))
                before = len(processed)
                # processed |= json_ids  <-- Komen baris ini jika ingin retry paksa
                logging.info(f"Resume dari JSON (Skip List) dimatikan sementara agar bisa retry.")
        except Exception as e:
            logging.warning(f"Tidak bisa baca file resume JSON: {e}")

    return processed

def save_resume(processed_ids):
    """Simpan processed_ids ke JSON sebagai backup/log skip."""
    with open(RESUME_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(processed_ids), f, ensure_ascii=False)

# ================================================================
# MAIN SCRAPER
# ================================================================
def scrape_reviews():
    # Inisialisasi file output (buat header jika belum ada)
    if not os.path.isfile(CSV_OUTPUT):
        with open(CSV_OUTPUT, 'w', newline='', encoding='utf-8') as f:
            csv.writer(f).writerow(['place_id', 'nama_pengulas', 'rating', 'waktu_ulasan', 'teks_ulasan'])

    processed_ids = load_processed_ids()

    # Baca dataset input
    wisata_list = []
    try:
        with open(CSV_INPUT, 'r', encoding='utf-8-sig') as f:
            wisata_list = list(csv.DictReader(f))
    except Exception as e:
        logging.error(f"Gagal membaca {CSV_INPUT}: {e}")
        return

    total_wisata = len(wisata_list)
    eligible = [w for w in wisata_list if int(w.get('jumlah_riview') or 0) > MIN_REVIEWS]
    remaining = [w for w in eligible if w.get('place_id', '').strip() not in processed_ids]
    logging.info(f"Total: {total_wisata} | Eligible: {len(eligible)} | Sisa belum diproses: {len(remaining)}")

    if not remaining:
        logging.info("Semua wisata eligible sudah diproses!")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="id-ID")
        page = context.new_page()

        try:
            for index, wisata in enumerate(wisata_list):
                place_id    = wisata.get('place_id', '').strip()
                nama_wisata = wisata.get('nama_wisata', '').strip()

                # Skip jika sudah ada di CSV output atau JSON resume
                if not place_id or place_id in processed_ids:
                    continue

                # Filter jumlah review minimum
                try:
                    jumlah_riview = int(wisata.get('jumlah_riview') or 0)
                except (ValueError, TypeError):
                    jumlah_riview = 0

                if jumlah_riview <= MIN_REVIEWS:
                    continue

                logging.info(f"[{index + 1}/{total_wisata}] [{jumlah_riview} ulasan] {nama_wisata}")

                try:
                    # Navigasi ke Google Maps
                    query = urllib.parse.quote_plus(nama_wisata)
                    url = f"https://www.google.com/maps/search/?api=1&query={query}&query_place_id={place_id}"
                    page.goto(url, timeout=30000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3000)

                    # Klik tab "Ulasan"
                    try:
                        # Selector diperlebar: bisa berupa button atau div dengan role="tab"
                        tab = page.locator(
                            '[role="tab"]:has-text("Ulasan"), [role="tab"]:has-text("Reviews"), button:has-text("Lebih banyak ulasan"), button:has-text("More reviews")'
                        ).first
                        tab.wait_for(state="visible", timeout=10000)
                        tab.click()
                        page.wait_for_timeout(3000)
                    except Exception:
                        logging.warning(f"  -> Tab ulasan tidak ditemukan, coba retry di sesi selanjutnya.")
                        # JANGAN tandai selesai jika tidak ketemu, agar bisa dicoba lagi nanti
                        continue

                    # Kumpulkan ulasan
                    ulasan_terkumpul = []
                    seen_names = set()
                    attempts = 0

                    while len(ulasan_terkumpul) < MAX_REVIEWS and attempts < 15:
                        blocks = page.locator('.jftiEf.fontBodyMedium').all()

                        if not blocks:
                            break

                        for block in blocks:
                            if len(ulasan_terkumpul) >= MAX_REVIEWS:
                                break

                            try:
                                # Expand "Lainnya" / "More"
                                more_btn = block.locator(
                                    'button.w8nwRe.kyuRq:has-text("Lainnya"), button.w8nwRe.kyuRq:has-text("More")'
                                )
                                if more_btn.is_visible():
                                    more_btn.click(timeout=2000)
                                    page.wait_for_timeout(500)
                            except Exception:
                                pass

                            try:
                                nama_pengulas = block.locator('.d4r55').inner_text(timeout=1000).strip()

                                if nama_pengulas in seen_names:
                                    continue
                                seen_names.add(nama_pengulas)

                                rating_str = block.locator('.kvMYJc').get_attribute('aria-label', timeout=1000) or ''
                                try:
                                    rating = float(rating_str.split(' ')[0].replace(',', '.'))
                                except Exception:
                                    rating = 0

                                waktu_ulasan = block.locator('.rsqaWe').inner_text(timeout=1000).strip()

                                try:
                                    teks_ulasan = block.locator('.wiI7pd').inner_text(timeout=1000).strip()
                                except Exception:
                                    teks_ulasan = "-"

                                if teks_ulasan and teks_ulasan != "-":
                                    ulasan_terkumpul.append({
                                        "nama": nama_pengulas,
                                        "rating": rating,
                                        "waktu": waktu_ulasan,
                                        "teks": teks_ulasan,
                                    })
                            except Exception:
                                pass

                        # Scroll panel ulasan untuk load lebih banyak
                        try:
                            panel = page.locator('.m6QErb.DxyBCb.kA9KIf.dS8AEf').nth(1)
                            panel.evaluate("node => node.scrollTo(0, node.scrollHeight)")
                            page.wait_for_timeout(2000)
                        except Exception:
                            pass

                        attempts += 1

                    # *** SIMPAN LANGSUNG KE CSV setelah selesai satu wisata ***
                    with open(CSV_OUTPUT, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.writer(f)
                        for ul in ulasan_terkumpul:
                            writer.writerow([place_id, ul['nama'], ul['rating'], ul['waktu'], ul['teks']])

                    logging.info(f"  -> Tersimpan: {len(ulasan_terkumpul)} ulasan.")
                    processed_ids.add(place_id)
                    save_resume(processed_ids)  # Update JSON juga

                except Exception as e:
                    logging.error(f"  -> GAGAL: {e}")
                    # Tidak masuk processed_ids → akan dicoba ulang saat resume

        except KeyboardInterrupt:
            logging.warning("\n[!] Dihentikan manual. Progress sudah tersimpan di CSV.")
            logging.info("Jalankan ulang untuk melanjutkan dari wisata yang belum diproses.")

        finally:
            try:
                browser.close()
            except Exception:
                pass  # Abaikan error saat menutup browser yang sudah crash

    logging.info("=" * 50)
    logging.info("Scraping selesai!")
    logging.info("=" * 50)


if __name__ == "__main__":
    logging.info("=" * 50)
    logging.info("Memulai Scraper Ulasan Wisata")
    logging.info("=" * 50)
    scrape_reviews()
