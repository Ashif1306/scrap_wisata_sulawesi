"""
=================================================================
KOREKSI KABUPATEN — PENDEKATAN TARGETED
=================================================================
Hanya proses entry yang kabupaten-nya TIDAK cocok dengan alamat.
Scrape via Playwright lalu validasi ketat.
=================================================================
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd
import re
import time
import os
import signal
import json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_fixed.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_fixed.csv")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "_koreksi_kab_progress.json")

# Daftar RESMI — diurutkan PANJANG TERPANJANG DULU supaya match yang lebih spesifik menang
VALID_KAB_KOTA = sorted([
    # Sulawesi Selatan
    'Kota Makassar', 'Kota Palopo', 'Kota Parepare',
    'Kabupaten Bantaeng', 'Kabupaten Barru', 'Kabupaten Bone',
    'Kabupaten Bulukumba', 'Kabupaten Enrekang', 'Kabupaten Gowa',
    'Kabupaten Jeneponto', 'Kabupaten Kepulauan Selayar',
    'Kabupaten Luwu', 'Kabupaten Luwu Timur', 'Kabupaten Luwu Utara',
    'Kabupaten Maros', 'Kabupaten Pangkajene Dan Kepulauan',
    'Kabupaten Pinrang', 'Kabupaten Sidenreng Rappang',
    'Kabupaten Sinjai', 'Kabupaten Soppeng', 'Kabupaten Takalar',
    'Kabupaten Tana Toraja', 'Kabupaten Toraja Utara', 'Kabupaten Wajo',
    # Sulawesi Barat
    'Kabupaten Mamuju', 'Kabupaten Majene', 'Kabupaten Polewali Mandar',
    'Kabupaten Mamasa', 'Kabupaten Pasangkayu', 'Kabupaten Mamuju Tengah',
    # Sulawesi Tengah
    'Kota Palu', 'Kabupaten Banggai', 'Kabupaten Banggai Kepulauan',
    'Kabupaten Banggai Laut', 'Kabupaten Buol', 'Kabupaten Donggala',
    'Kabupaten Morowali', 'Kabupaten Morowali Utara',
    'Kabupaten Parigi Moutong', 'Kabupaten Poso', 'Kabupaten Sigi',
    'Kabupaten Tojo Una-Una', 'Kabupaten Tolitoli',
    # Sulawesi Utara
    'Kota Manado', 'Kota Bitung', 'Kota Tomohon', 'Kota Kotamobagu',
    'Kabupaten Bolaang Mongondow', 'Kabupaten Bolaang Mongondow Selatan',
    'Kabupaten Bolaang Mongondow Timur', 'Kabupaten Bolaang Mongondow Utara',
    'Kabupaten Kepulauan Sangihe', 'Kabupaten Kepulauan Siau Tagulandang Biaro',
    'Kabupaten Kepulauan Talaud', 'Kabupaten Minahasa',
    'Kabupaten Minahasa Selatan', 'Kabupaten Minahasa Tenggara',
    'Kabupaten Minahasa Utara',
    # Sulawesi Tenggara
    'Kota Kendari', 'Kota Baubau',
    'Kabupaten Bombana', 'Kabupaten Buton', 'Kabupaten Buton Selatan',
    'Kabupaten Buton Tengah', 'Kabupaten Buton Utara',
    'Kabupaten Kolaka', 'Kabupaten Kolaka Timur', 'Kabupaten Kolaka Utara',
    'Kabupaten Konawe', 'Kabupaten Konawe Kepulauan',
    'Kabupaten Konawe Selatan', 'Kabupaten Konawe Utara',
    'Kabupaten Muna', 'Kabupaten Muna Barat', 'Kabupaten Wakatobi',
    # Gorontalo
    'Kota Gorontalo', 'Kabupaten Boalemo', 'Kabupaten Bone Bolango',
    'Kabupaten Gorontalo Utara', 'Kabupaten Pohuwato', 'Kabupaten Gorontalo',
], key=len, reverse=True)  # Terpanjang dulu!

PROVINSI_LIST = [
    'Sulawesi Selatan', 'Sulawesi Barat', 'Sulawesi Tengah',
    'Sulawesi Utara', 'Sulawesi Tenggara', 'Gorontalo'
]

shutdown_flag = False
def signal_handler(sig, frame):
    global shutdown_flag
    print("\n[!] Ctrl+C — menyimpan progress...")
    shutdown_flag = True
signal.signal(signal.SIGINT, signal_handler)


def find_kab_strict(text):
    """
    Cari kabupaten/kota di teks dengan STRICT matching.
    - Cek terpanjang dulu (Minahasa Utara sebelum Minahasa)
    - Hanya match jika diikuti koma, titik, spasi+angka, atau akhir string
    """
    if not text:
        return None
    for kab in VALID_KAB_KOTA:  # Sudah diurutkan terpanjang dulu
        # Buat regex: nama kabupaten diikuti separator
        pattern = re.escape(kab) + r'(?=[,\.\s\d]|$)'
        if re.search(pattern, text, re.IGNORECASE):
            return kab
    return None


def identify_suspects(df):
    """
    Identifikasi baris yang kabupaten-nya SUSPECT salah:
    - Kabupaten di kolom 'kabupaten' TIDAK muncul di kolom 'alamat'
    """
    suspects = []
    for idx, row in df.iterrows():
        kab = str(row['kabupaten']).strip()
        alamat = str(row.get('alamat', '')).strip()

        # Cek apakah nama kabupaten ada di alamat
        kab_clean = kab.replace('Kabupaten ', '').replace('Kota ', '').strip()
        if kab_clean.lower() not in alamat.lower():
            suspects.append(idx)

    return suspects


def save_progress(data):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'done': [], 'fixes': []}


def main():
    global shutdown_flag

    print("=" * 60)
    print("KOREKSI KABUPATEN — TARGETED (Playwright)")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    total = len(df)
    print(f"Total data: {total}")

    # Identifikasi suspect
    suspects = identify_suspects(df)
    print(f"Data suspect (kabupaten tidak cocok alamat): {len(suspects)}")

    if not suspects:
        print("Tidak ada yang perlu diperbaiki!")
        return

    # Load progress
    progress = load_progress()
    done = set(progress.get('done', []))
    fixes = progress.get('fixes', [])
    remaining = [i for i in suspects if i not in done]

    if done:
        print(f"Resume: {len(done)} done, {len(fixes)} fixes")
    print(f"Sisa: {len(remaining)}\n")

    if not remaining:
        print("Semua suspect sudah diproses!")
        apply_fixes(df, fixes)
        return

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="id-ID",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        try:
            page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
        except Exception:
            pass

        for count, idx in enumerate(remaining):
            if shutdown_flag:
                break

            row = df.iloc[idx]
            place_id = row['place_id']
            old_kab = str(row['kabupaten'])

            # Scrape alamat dari Google Maps
            address = None
            try:
                url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                time.sleep(3)

                for selector in [
                    'button[data-item-id="address"]',
                    'div.rogA2c',
                    '[data-tooltip="Salin alamat"]'
                ]:
                    try:
                        el = page.query_selector(selector)
                        if el:
                            address = el.inner_text()
                            if address:
                                break
                    except Exception:
                        pass

                if not address:
                    try:
                        for el in page.query_selector_all('div.Io6YTe'):
                            text = el.inner_text()
                            if any(pr in text for pr in PROVINSI_LIST) or 'Indonesia' in text:
                                address = text
                                break
                    except Exception:
                        pass
            except Exception:
                pass

            # Cari kabupaten di alamat hasil scraping
            if address:
                new_kab = find_kab_strict(address)
                if new_kab and new_kab.strip().lower() != old_kab.strip().lower():
                    fixes.append({
                        'idx': idx,
                        'nama': str(row['nama_wisata']),
                        'old_kab': old_kab,
                        'new_kab': new_kab,
                        'new_alamat': address,
                    })
                    print(f"  [FIX] {row['nama_wisata']}: {old_kab} -> {new_kab}")

            done.add(idx)

            if (count + 1) % 20 == 0 or shutdown_flag:
                progress['done'] = list(done)
                progress['fixes'] = fixes
                save_progress(progress)
                pct = len(done) / len(suspects) * 100
                print(f"  [SAVE] {len(done)}/{len(suspects)} ({pct:.1f}%)")

            time.sleep(0.5)

        browser.close()

    progress['done'] = list(done)
    progress['fixes'] = fixes
    save_progress(progress)

    if not shutdown_flag:
        apply_fixes(df, fixes)
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
    else:
        print(f"\nDihentikan. {len(done)}/{len(suspects)} selesai. Jalankan ulang untuk lanjut.")


def apply_fixes(df, fixes):
    count = 0
    for fix in fixes:
        idx = fix['idx']
        df.at[idx, 'kabupaten'] = fix['new_kab']
        if 'new_alamat' in fix:
            df.at[idx, 'alamat'] = fix['new_alamat']
        count += 1

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n{'='*60}")
    print(f"SELESAI! {count} kabupaten diperbaiki.")
    print(f"File: {OUTPUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
