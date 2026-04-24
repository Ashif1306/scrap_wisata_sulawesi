"""
Script untuk re-scrape alamat dari Google Maps menggunakan Playwright.
Hanya baris yang kabupaten-nya tidak cocok dengan provinsi yang akan di-scrape ulang.
Hasil disimpan ke file baru: wisata_sulawesi_fixed.csv
"""

import pandas as pd
import re
import time
import os
import signal
import sys
from playwright.sync_api import sync_playwright

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# ── KONFIGURASI ──────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_lengkap.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_fixed.csv")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "_rescrape_progress.csv")

# Mapping kabupaten -> provinsi yang benar
KAB_PROV_MAPPING = {
    'Sulawesi Selatan': [
        'Makassar', 'Palopo', 'Parepare', 'Bantaeng', 'Barru', 'Bone',
        'Bulukumba', 'Enrekang', 'Gowa', 'Jeneponto', 'Kepulauan Selayar',
        'Luwu', 'Luwu Timur', 'Luwu Utara', 'Maros',
        'Pangkajene Dan Kepulauan', 'Pinrang', 'Sidenreng Rappang',
        'Sinjai', 'Soppeng', 'Takalar', 'Tana Toraja', 'Toraja Utara', 'Wajo'
    ],
    'Sulawesi Barat': [
        'Mamuju', 'Majene', 'Polewali Mandar', 'Mamasa', 'Pasangkayu', 'Mamuju Tengah'
    ],
    'Sulawesi Tengah': [
        'Palu', 'Banggai', 'Banggai Kepulauan', 'Banggai Laut', 'Buol',
        'Donggala', 'Morowali', 'Morowali Utara', 'Parigi Moutong', 'Poso',
        'Sigi', 'Tojo Una-Una', 'Tolitoli'
    ],
    'Sulawesi Utara': [
        'Manado', 'Bitung', 'Tomohon', 'Kotamobagu', 'Bolaang Mongondow',
        'Bolaang Mongondow Selatan', 'Bolaang Mongondow Timur',
        'Bolaang Mongondow Utara', 'Kepulauan Sangihe',
        'Kepulauan Siau Tagulandang Biaro', 'Kepulauan Talaud',
        'Minahasa', 'Minahasa Selatan', 'Minahasa Tenggara', 'Minahasa Utara'
    ],
    'Sulawesi Tenggara': [
        'Kendari', 'Baubau', 'Bombana', 'Buton', 'Buton Selatan',
        'Buton Tengah', 'Buton Utara', 'Kolaka', 'Kolaka Timur',
        'Kolaka Utara', 'Konawe', 'Konawe Kepulauan', 'Konawe Selatan',
        'Konawe Utara', 'Muna', 'Muna Barat', 'Wakatobi'
    ],
    'Gorontalo': [
        'Gorontalo', 'Boalemo', 'Bone Bolango', 'Gorontalo Utara', 'Pohuwato'
    ]
}

VALID_KABS = {}
for prov, kabs in KAB_PROV_MAPPING.items():
    for kab in kabs:
        VALID_KABS[kab.lower()] = prov

PROVINSI_LIST = [
    'Sulawesi Selatan', 'Sulawesi Barat', 'Sulawesi Tengah',
    'Sulawesi Utara', 'Sulawesi Tenggara', 'Gorontalo'
]

# ── FUNGSI UTILITAS ──────────────────────────────────

shutdown_flag = False

def signal_handler(sig, frame):
    global shutdown_flag
    print("\n[!] Ctrl+C diterima, menyimpan progress dan keluar...")
    shutdown_flag = True

signal.signal(signal.SIGINT, signal_handler)


def is_mismatch(kab, prov):
    """Cek apakah kabupaten dan provinsi tidak cocok."""
    kab_clean = str(kab).replace('Kabupaten', '').replace('Kota', '').strip().lower()
    prov = str(prov).strip()
    if kab_clean in VALID_KABS:
        if VALID_KABS[kab_clean] != prov:
            return True
    else:
        for k, p in VALID_KABS.items():
            if k in kab_clean:
                if p != prov:
                    return True
                return False
    return False


def extract_kab_prov_from_address(address):
    """Ekstrak kabupaten dan provinsi dari alamat Google Maps."""
    kab = None
    prov = None

    # Cari provinsi
    for p in PROVINSI_LIST:
        if p.lower() in address.lower():
            prov = p
            break

    # Cari kabupaten/kota dari alamat
    # Pattern: "Kabupaten X," or "Kab. X," or "Kota X,"
    kab_match = re.search(
        r'(Kabupaten\s+[\w\s\-]+|Kab\.\s+[\w\s\-]+|Kota\s+[\w\s\-]+)(?=[,\n])',
        address
    )
    if kab_match:
        kab = kab_match.group(1).replace('Kab.', 'Kabupaten').strip()
        # Bersihkan trailing words yang bukan bagian nama (e.g. "Kota Makassar Sulawesi")
        for p_name in PROVINSI_LIST:
            kab = kab.replace(p_name, '').strip()

    return kab, prov


def scrape_address_from_gmaps(page, place_id, nama_wisata):
    """Buka Google Maps via place_id dan ambil alamat lengkap."""
    url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"

    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)

        # Coba ambil alamat dari beberapa selector
        address = None

        # Selector 1: button dengan data-item-id="address"
        try:
            addr_el = page.query_selector('button[data-item-id="address"]')
            if addr_el:
                address = addr_el.inner_text()
        except Exception:
            pass

        # Selector 2: div.rogA2c (alamat di panel info)
        if not address:
            try:
                addr_el = page.query_selector('div.rogA2c')
                if addr_el:
                    address = addr_el.inner_text()
            except Exception:
                pass

        # Selector 3: aria-label yang mengandung "Alamat"
        if not address:
            try:
                addr_el = page.query_selector('[data-tooltip="Salin alamat"]')
                if addr_el:
                    address = addr_el.inner_text()
            except Exception:
                pass

        # Selector 4: coba ambil dari div.Io6YTe yang berisi alamat
        if not address:
            try:
                elements = page.query_selector_all('div.Io6YTe')
                for el in elements:
                    text = el.inner_text()
                    if any(p in text for p in PROVINSI_LIST) or 'Indonesia' in text:
                        address = text
                        break
            except Exception:
                pass

        # Selector 5: fallback - ambil text dari section info
        if not address:
            try:
                elements = page.query_selector_all('[data-attrid]')
                for el in elements:
                    text = el.inner_text()
                    if 'Indonesia' in text and len(text) > 20:
                        address = text
                        break
            except Exception:
                pass

        return address

    except Exception as e:
        print(f"    [ERROR] Gagal scrape {nama_wisata}: {e}")
        return None


def main():
    global shutdown_flag

    print("=" * 60)
    print("RE-SCRAPE ALAMAT WISATA DARI GOOGLE MAPS (PLAYWRIGHT)")
    print("=" * 60)

    # Load dataset
    df = pd.read_csv(INPUT_FILE)
    total = len(df)
    print(f"Total data: {total}")

    # Identifikasi baris yang perlu di-fix
    mismatch_indices = []
    for idx, row in df.iterrows():
        if is_mismatch(row['kabupaten'], row['provinsi']):
            mismatch_indices.append(idx)

    print(f"Total data mismatch kabupaten/provinsi: {len(mismatch_indices)}")

    if not mismatch_indices:
        print("Tidak ada data yang perlu diperbaiki!")
        return

    # Load progress jika ada (resume)
    already_done = set()
    if os.path.exists(PROGRESS_FILE):
        try:
            df_prog = pd.read_csv(PROGRESS_FILE)
            already_done = set(df_prog['idx'].tolist())
            print(f"Melanjutkan dari progress sebelumnya ({len(already_done)} sudah selesai)")
        except Exception:
            pass

    # Filter yang belum selesai
    remaining = [i for i in mismatch_indices if i not in already_done]
    print(f"Sisa yang perlu di-scrape: {len(remaining)}")

    if not remaining:
        print("Semua sudah di-scrape! Generating output file...")
        apply_progress_to_df(df)
        return

    # Mulai Playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="id-ID",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Buka Google Maps dulu untuk set cookies
        print("\nMembuka Google Maps...")
        try:
            page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
            # Tutup consent dialog jika ada
            try:
                accept_btn = page.query_selector('button:has-text("Accept")')
                if accept_btn:
                    accept_btn.click()
                    time.sleep(1)
            except Exception:
                pass
        except Exception:
            pass

        progress_data = []
        # Load existing progress data
        if os.path.exists(PROGRESS_FILE):
            try:
                existing = pd.read_csv(PROGRESS_FILE)
                progress_data = existing.to_dict('records')
            except Exception:
                pass

        for count, idx in enumerate(remaining):
            if shutdown_flag:
                break

            row = df.iloc[idx]
            place_id = row['place_id']
            nama = str(row['nama_wisata']).encode('ascii', 'replace').decode('ascii')
            old_kab = row['kabupaten']
            old_prov = row['provinsi']

            print(f"\n[{count+1}/{len(remaining)}] Scraping: {nama}")
            print(f"  Old: kab={old_kab}, prov={old_prov}")

            address = scrape_address_from_gmaps(page, place_id, nama)

            new_alamat = address if address else str(row['alamat'])
            new_kab = str(old_kab)
            new_prov = str(old_prov)

            if address:
                print(f"  Alamat ditemukan: {address[:80]}...")
                extracted_kab, extracted_prov = extract_kab_prov_from_address(address)

                if extracted_kab:
                    new_kab = extracted_kab
                if extracted_prov:
                    new_prov = extracted_prov

                print(f"  New: kab={new_kab}, prov={new_prov}")
            else:
                print(f"  [SKIP] Alamat tidak ditemukan, tetap pakai data lama")

            progress_data.append({
                'idx': idx,
                'place_id': place_id,
                'nama_wisata': row['nama_wisata'],
                'old_alamat': row['alamat'],
                'new_alamat': new_alamat,
                'old_kabupaten': old_kab,
                'new_kabupaten': new_kab,
                'old_provinsi': old_prov,
                'new_provinsi': new_prov
            })

            # Auto-save progress setiap 5 item
            if (count + 1) % 5 == 0 or shutdown_flag:
                pd.DataFrame(progress_data).to_csv(PROGRESS_FILE, index=False, encoding='utf-8-sig')
                print(f"  [AUTO-SAVE] Progress disimpan ({len(progress_data)} records)")

            # Delay antar request
            time.sleep(1)

        # Save final progress
        pd.DataFrame(progress_data).to_csv(PROGRESS_FILE, index=False, encoding='utf-8-sig')
        print(f"\nProgress final disimpan ({len(progress_data)} records)")

        browser.close()

    # Apply progress ke dataframe dan simpan
    if not shutdown_flag:
        apply_progress_to_df(df)


def apply_progress_to_df(df):
    """Terapkan hasil scraping ke dataframe dan simpan ke file baru."""
    if not os.path.exists(PROGRESS_FILE):
        print("Tidak ada progress file!")
        return

    df_prog = pd.read_csv(PROGRESS_FILE)
    changes = 0

    for _, prog_row in df_prog.iterrows():
        idx = int(prog_row['idx'])
        if idx < len(df):
            # Update alamat jika ada yang baru
            if pd.notnull(prog_row['new_alamat']) and str(prog_row['new_alamat']) != '-':
                df.at[idx, 'alamat'] = prog_row['new_alamat']

            # Update kabupaten
            if pd.notnull(prog_row['new_kabupaten']):
                df.at[idx, 'kabupaten'] = prog_row['new_kabupaten']

            # Update provinsi
            if pd.notnull(prog_row['new_provinsi']):
                df.at[idx, 'provinsi'] = prog_row['new_provinsi']

            changes += 1

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n{'='*60}")
    print(f"FILE BARU DISIMPAN: {OUTPUT_FILE}")
    print(f"Total perubahan diterapkan: {changes}")
    print(f"Total baris: {len(df)}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
