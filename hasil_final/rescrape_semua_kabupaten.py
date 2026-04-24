"""
=================================================================
SCRIPT: Koreksi Kabupaten Seluruh Data Wisata Sulawesi
=================================================================
Strategi Multi-Level:
  Level 1: Nominatim reverse geocoding (dari koordinat lat/long)
  Level 2: Playwright Google Maps (dari place_id) — fallback

Fitur:
  - Auto-resume jika terputus
  - Auto-save progress setiap 20 entry
  - Graceful shutdown (Ctrl+C)
  - Output: wisata_sulawesi_fixed.csv (overwrite)
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
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# ── KONFIGURASI ──────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_fixed.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_fixed.csv")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "_koreksi_kab_progress.json")

PROVINSI_LIST = [
    'Sulawesi Selatan', 'Sulawesi Barat', 'Sulawesi Tengah',
    'Sulawesi Utara', 'Sulawesi Tenggara', 'Gorontalo'
]

# ── GRACEFUL SHUTDOWN ────────────────────────────────
shutdown_flag = False
def signal_handler(sig, frame):
    global shutdown_flag
    print("\n[!] Ctrl+C diterima. Menyimpan progress dan keluar...")
    shutdown_flag = True
signal.signal(signal.SIGINT, signal_handler)


# ── UTILITAS ─────────────────────────────────────────

def normalize_kab(kab_str):
    """Normalisasi nama kabupaten untuk perbandingan."""
    if not kab_str or pd.isna(kab_str):
        return ""
    return (str(kab_str)
            .replace('Kabupaten ', '')
            .replace('Kota ', '')
            .replace('Regency', '')
            .strip()
            .lower())


def extract_kab_from_address(address):
    """Ekstrak kabupaten/kota dari string alamat."""
    if not address:
        return None

    # Cari pattern: "Kabupaten X," atau "Kab. X," atau "Kota X,"
    match = re.search(
        r'(Kabupaten\s+[\w\s\-\'\.]+|Kab\.\s+[\w\s\-\'\.]+|Kota\s+[\w\s\-\'\.]+)(?=[,\n])',
        address
    )
    if match:
        result = match.group(1).replace('Kab.', 'Kabupaten').strip()
        # Bersihkan trailing provinsi
        for p in PROVINSI_LIST:
            result = result.replace(p, '').strip()
        # Bersihkan trailing kode pos (5 digit)
        result = re.sub(r'\s+\d{5}$', '', result).strip()
        return result
    return None


def save_progress(progress, done_indices):
    """Simpan progress ke file JSON."""
    data = {
        'done_indices': list(done_indices),
        'fixes': progress
    }
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_progress():
    """Load progress dari file JSON."""
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return set(data.get('done_indices', [])), data.get('fixes', [])
        except Exception:
            pass
    return set(), []


# ── LEVEL 1: NOMINATIM ──────────────────────────────

def phase_nominatim(df, already_done, fixes):
    """
    Phase 1: Gunakan Nominatim reverse geocoding untuk semua entry.
    Return: set of indices yang sudah diproses, list of fixes
    """
    global shutdown_flag

    geolocator = Nominatim(user_agent='wisata_sulawesi_kabfix_v3', timeout=10)
    reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1.05)

    total = len(df)
    remaining = [i for i in range(total) if i not in already_done]

    if not remaining:
        print("  Semua data sudah diproses di Phase 1.")
        return already_done, fixes

    print(f"  Sisa: {len(remaining)} entry")
    need_playwright = []

    for count, idx in enumerate(remaining):
        if shutdown_flag:
            break

        row = df.iloc[idx]
        lat = row['lat']
        lng = row['long']
        old_kab = str(row['kabupaten'])

        try:
            location = reverse(f"{lat}, {lng}", exactly_one=True, language='id')
            if location:
                addr = location.raw.get('address', {})
                # Nominatim returns: county, city, town, village, etc.
                new_kab_raw = (
                    addr.get('county') or
                    addr.get('city') or
                    addr.get('town') or
                    addr.get('municipality')
                )

                if new_kab_raw:
                    # Format: tambahkan prefix Kabupaten/Kota jika belum ada
                    if not new_kab_raw.startswith(('Kabupaten', 'Kota')):
                        # Cek apakah ini kota (biasanya Nominatim pakai 'city')
                        if addr.get('city'):
                            new_kab = f"Kota {new_kab_raw}"
                        else:
                            new_kab = f"Kabupaten {new_kab_raw}"
                    else:
                        new_kab = new_kab_raw

                    if normalize_kab(new_kab) != normalize_kab(old_kab):
                        fixes.append({
                            'idx': idx,
                            'nama': row['nama_wisata'],
                            'old_kab': old_kab,
                            'new_kab': new_kab,
                            'method': 'nominatim'
                        })
                        print(f"  [FIX] {row['nama_wisata']}: {old_kab} -> {new_kab}")
                else:
                    need_playwright.append(idx)
            else:
                need_playwright.append(idx)
        except Exception as e:
            need_playwright.append(idx)

        already_done.add(idx)

        # Auto-save
        if (count + 1) % 20 == 0 or shutdown_flag:
            save_progress(fixes, already_done)
            pct = len(already_done) / total * 100
            print(f"  [SAVE] {len(already_done)}/{total} ({pct:.1f}%) | fixes: {len(fixes)}")

    save_progress(fixes, already_done)
    print(f"  Nominatim gagal untuk {len(need_playwright)} entry (akan dicoba via Playwright)")
    return already_done, fixes


# ── LEVEL 2: PLAYWRIGHT ─────────────────────────────

def phase_playwright(df, already_done, fixes):
    """
    Phase 2: Untuk entry yang Nominatim gagal, coba scrape dari Google Maps.
    """
    global shutdown_flag

    # Identifikasi entry yang Nominatim tidak bisa resolve kabupaten-nya
    # (sudah done tapi tidak ada di fixes dan kabupaten-nya belum berubah)
    fixed_indices = {f['idx'] for f in fixes}
    # Entry yang sudah diproses tapi tidak ada fix = nominatim gagal
    need_pw = [i for i in already_done if i not in fixed_indices]

    # Tapi kita juga perlu track mana yang sudah dicoba Playwright
    pw_done_key = 'pw_done'
    pw_done = set()
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            pw_done = set(data.get(pw_done_key, []))
        except Exception:
            pass

    remaining_pw = [i for i in need_pw if i not in pw_done]

    if not remaining_pw:
        print("  Tidak ada entry yang perlu Playwright.")
        return fixes

    print(f"  Entry untuk Playwright: {len(remaining_pw)}")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  [ERROR] Playwright tidak terinstall!")
        return fixes

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="id-ID",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # Init
        try:
            page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
        except Exception:
            pass

        for count, idx in enumerate(remaining_pw):
            if shutdown_flag:
                break

            row = df.iloc[idx]
            place_id = row['place_id']
            old_kab = str(row['kabupaten'])

            url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            address = None

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=15000)
                time.sleep(3)

                # Coba beberapa selector
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

                # Fallback: cari div yang mengandung nama provinsi
                if not address:
                    try:
                        elements = page.query_selector_all('div.Io6YTe')
                        for el in elements:
                            text = el.inner_text()
                            if any(pr in text for pr in PROVINSI_LIST) or 'Indonesia' in text:
                                address = text
                                break
                    except Exception:
                        pass
            except Exception:
                pass

            if address:
                new_kab = extract_kab_from_address(address)
                if new_kab and normalize_kab(new_kab) != normalize_kab(old_kab):
                    fixes.append({
                        'idx': idx,
                        'nama': row['nama_wisata'],
                        'old_kab': old_kab,
                        'new_kab': new_kab,
                        'new_alamat': address,
                        'method': 'playwright'
                    })
                    print(f"  [PW-FIX] {row['nama_wisata']}: {old_kab} -> {new_kab}")

            pw_done.add(idx)

            # Auto-save
            if (count + 1) % 10 == 0 or shutdown_flag:
                with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                data[pw_done_key] = list(pw_done)
                data['fixes'] = fixes
                with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"  [PW-SAVE] {count+1}/{len(remaining_pw)} | fixes: {len(fixes)}")

            time.sleep(0.5)

        browser.close()

    # Final save
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data[pw_done_key] = list(pw_done)
    data['fixes'] = fixes
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return fixes


# ── APPLY FIXES & SAVE ──────────────────────────────

def apply_and_save(df, fixes):
    """Terapkan semua fixes ke dataframe dan simpan."""
    change_count = 0
    for fix in fixes:
        idx = fix['idx']
        df.at[idx, 'kabupaten'] = fix['new_kab']
        if 'new_alamat' in fix:
            df.at[idx, 'alamat'] = fix['new_alamat']
        change_count += 1

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n{'='*60}")
    print(f"SELESAI!")
    print(f"Total kabupaten diperbaiki: {change_count}")
    print(f"File disimpan: {OUTPUT_FILE}")
    print(f"{'='*60}")


# ── MAIN ─────────────────────────────────────────────

def main():
    global shutdown_flag

    print("=" * 60)
    print("KOREKSI KABUPATEN SELURUH DATA WISATA SULAWESI")
    print("Strategi: Nominatim (koordinat) -> Playwright (Google Maps)")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    total = len(df)
    print(f"Total data: {total}\n")

    # Load progress
    already_done, fixes = load_progress()
    if already_done:
        print(f"Resume: {len(already_done)} sudah diproses, {len(fixes)} fixes.")

    # ── PHASE 1: NOMINATIM ───────────────
    print("\n--- PHASE 1: Nominatim Reverse Geocoding ---")
    already_done, fixes = phase_nominatim(df, already_done, fixes)

    if shutdown_flag:
        print(f"\nDihentikan. Progress tersimpan ({len(already_done)}/{total}).")
        print("Jalankan ulang untuk melanjutkan.")
        return

    # ── PHASE 2: PLAYWRIGHT ──────────────
    print("\n--- PHASE 2: Playwright Google Maps ---")
    fixes = phase_playwright(df, already_done, fixes)

    if shutdown_flag:
        print(f"\nDihentikan. Progress tersimpan.")
        print("Jalankan ulang untuk melanjutkan.")
        return

    # ── APPLY & SAVE ─────────────────────
    apply_and_save(df, fixes)

    # Cleanup progress file
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("Progress file dihapus.")


if __name__ == "__main__":
    main()
