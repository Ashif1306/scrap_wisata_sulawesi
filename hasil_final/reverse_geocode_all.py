"""
reverse_geocode_all.py
======================
Reverse geocoding SELURUH data wisata_sulawesi_lengkap.csv
menggunakan Nominatim + RateLimiter + tqdm.

Strategi:
  1. Baca wisata_sulawesi_lengkap.csv
  2. Untuk SETIAP baris, reverse geocode lat/long → kabupaten sebenarnya
  3. Cocokkan hasil geocode dengan daftar 81 kab/kota resmi
  4. Simpan ke kolom 'kabupaten_geografi'
  5. Jika kabupaten_geografi != kabupaten → tandai & perbaiki
  6. Provinsi diturunkan dari mapping 81 kab/kota
  7. Simpan ke wisata_terkoreksi_geo.csv

Fitur:
  - Resume otomatis: jika file progress ada, lanjutkan dari posisi terakhir
  - Save progress setiap 100 baris (aman jika terhenti)
  - tqdm progress bar
  - RateLimiter 1 detik per request

Estimasi waktu: ~45 menit untuk 2707 baris (1 req/detik)

Cara pakai:
  cd hasil_final
  python reverse_geocode_all.py
"""

import pandas as pd
import os
import sys
import json
import re
from tqdm import tqdm
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, 'wisata_sulawesi_lengkap.csv')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'wisata_terkoreksi_geo.csv')
PROGRESS_FILE = os.path.join(SCRIPT_DIR, '_geocode_progress.json')

# ── 81 KABUPATEN/KOTA RESMI SE-SULAWESI ───────────────────────
VALID_KAB_KOTA = [
    # Sulawesi Selatan (24)
    "Kota Makassar","Kota Palopo","Kota Parepare",
    "Kabupaten Bantaeng","Kabupaten Barru","Kabupaten Bone",
    "Kabupaten Bulukumba","Kabupaten Enrekang","Kabupaten Gowa",
    "Kabupaten Jeneponto","Kabupaten Kepulauan Selayar",
    "Kabupaten Luwu","Kabupaten Luwu Timur","Kabupaten Luwu Utara",
    "Kabupaten Maros","Kabupaten Pangkajene Dan Kepulauan",
    "Kabupaten Pinrang","Kabupaten Sidenreng Rappang",
    "Kabupaten Sinjai","Kabupaten Soppeng","Kabupaten Takalar",
    "Kabupaten Tana Toraja","Kabupaten Toraja Utara","Kabupaten Wajo",
    # Sulawesi Barat (6)
    "Kabupaten Mamuju","Kabupaten Majene","Kabupaten Polewali Mandar",
    "Kabupaten Mamasa","Kabupaten Pasangkayu","Kabupaten Mamuju Tengah",
    # Sulawesi Tengah (13)
    "Kota Palu","Kabupaten Banggai","Kabupaten Banggai Kepulauan",
    "Kabupaten Banggai Laut","Kabupaten Buol","Kabupaten Donggala",
    "Kabupaten Morowali","Kabupaten Morowali Utara",
    "Kabupaten Parigi Moutong","Kabupaten Poso","Kabupaten Sigi",
    "Kabupaten Tojo Una-Una","Kabupaten Tolitoli",
    # Sulawesi Utara (15)
    "Kota Manado","Kota Bitung","Kota Tomohon","Kota Kotamobagu",
    "Kabupaten Bolaang Mongondow","Kabupaten Bolaang Mongondow Selatan",
    "Kabupaten Bolaang Mongondow Timur","Kabupaten Bolaang Mongondow Utara",
    "Kabupaten Kepulauan Sangihe","Kabupaten Kepulauan Siau Tagulandang Biaro",
    "Kabupaten Kepulauan Talaud","Kabupaten Minahasa",
    "Kabupaten Minahasa Selatan","Kabupaten Minahasa Tenggara","Kabupaten Minahasa Utara",
    # Sulawesi Tenggara (17)
    "Kota Kendari","Kota Baubau",
    "Kabupaten Bombana","Kabupaten Buton","Kabupaten Buton Selatan",
    "Kabupaten Buton Tengah","Kabupaten Buton Utara",
    "Kabupaten Kolaka","Kabupaten Kolaka Timur","Kabupaten Kolaka Utara",
    "Kabupaten Konawe","Kabupaten Konawe Kepulauan",
    "Kabupaten Konawe Selatan","Kabupaten Konawe Utara",
    "Kabupaten Muna","Kabupaten Muna Barat","Kabupaten Wakatobi",
    # Gorontalo (6)
    "Kota Gorontalo","Kabupaten Boalemo","Kabupaten Bone Bolango",
    "Kabupaten Gorontalo Utara","Kabupaten Pohuwato","Kabupaten Gorontalo",
]
VALID_SORTED = sorted(VALID_KAB_KOTA, key=len, reverse=True)

KAB_TO_PROV = {
    "Kota Makassar":"Sulawesi Selatan","Kota Palopo":"Sulawesi Selatan","Kota Parepare":"Sulawesi Selatan",
    "Kabupaten Bantaeng":"Sulawesi Selatan","Kabupaten Barru":"Sulawesi Selatan","Kabupaten Bone":"Sulawesi Selatan",
    "Kabupaten Bulukumba":"Sulawesi Selatan","Kabupaten Enrekang":"Sulawesi Selatan","Kabupaten Gowa":"Sulawesi Selatan",
    "Kabupaten Jeneponto":"Sulawesi Selatan","Kabupaten Kepulauan Selayar":"Sulawesi Selatan",
    "Kabupaten Luwu":"Sulawesi Selatan","Kabupaten Luwu Timur":"Sulawesi Selatan","Kabupaten Luwu Utara":"Sulawesi Selatan",
    "Kabupaten Maros":"Sulawesi Selatan","Kabupaten Pangkajene Dan Kepulauan":"Sulawesi Selatan",
    "Kabupaten Pinrang":"Sulawesi Selatan","Kabupaten Sidenreng Rappang":"Sulawesi Selatan",
    "Kabupaten Sinjai":"Sulawesi Selatan","Kabupaten Soppeng":"Sulawesi Selatan","Kabupaten Takalar":"Sulawesi Selatan",
    "Kabupaten Tana Toraja":"Sulawesi Selatan","Kabupaten Toraja Utara":"Sulawesi Selatan","Kabupaten Wajo":"Sulawesi Selatan",
    "Kabupaten Mamuju":"Sulawesi Barat","Kabupaten Majene":"Sulawesi Barat","Kabupaten Polewali Mandar":"Sulawesi Barat",
    "Kabupaten Mamasa":"Sulawesi Barat","Kabupaten Pasangkayu":"Sulawesi Barat","Kabupaten Mamuju Tengah":"Sulawesi Barat",
    "Kota Palu":"Sulawesi Tengah","Kabupaten Banggai":"Sulawesi Tengah","Kabupaten Banggai Kepulauan":"Sulawesi Tengah",
    "Kabupaten Banggai Laut":"Sulawesi Tengah","Kabupaten Buol":"Sulawesi Tengah","Kabupaten Donggala":"Sulawesi Tengah",
    "Kabupaten Morowali":"Sulawesi Tengah","Kabupaten Morowali Utara":"Sulawesi Tengah",
    "Kabupaten Parigi Moutong":"Sulawesi Tengah","Kabupaten Poso":"Sulawesi Tengah","Kabupaten Sigi":"Sulawesi Tengah",
    "Kabupaten Tojo Una-Una":"Sulawesi Tengah","Kabupaten Tolitoli":"Sulawesi Tengah",
    "Kota Manado":"Sulawesi Utara","Kota Bitung":"Sulawesi Utara","Kota Tomohon":"Sulawesi Utara","Kota Kotamobagu":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow":"Sulawesi Utara","Kabupaten Bolaang Mongondow Selatan":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow Timur":"Sulawesi Utara","Kabupaten Bolaang Mongondow Utara":"Sulawesi Utara",
    "Kabupaten Kepulauan Sangihe":"Sulawesi Utara","Kabupaten Kepulauan Siau Tagulandang Biaro":"Sulawesi Utara",
    "Kabupaten Kepulauan Talaud":"Sulawesi Utara","Kabupaten Minahasa":"Sulawesi Utara",
    "Kabupaten Minahasa Selatan":"Sulawesi Utara","Kabupaten Minahasa Tenggara":"Sulawesi Utara","Kabupaten Minahasa Utara":"Sulawesi Utara",
    "Kota Kendari":"Sulawesi Tenggara","Kota Baubau":"Sulawesi Tenggara",
    "Kabupaten Bombana":"Sulawesi Tenggara","Kabupaten Buton":"Sulawesi Tenggara","Kabupaten Buton Selatan":"Sulawesi Tenggara",
    "Kabupaten Buton Tengah":"Sulawesi Tenggara","Kabupaten Buton Utara":"Sulawesi Tenggara",
    "Kabupaten Kolaka":"Sulawesi Tenggara","Kabupaten Kolaka Timur":"Sulawesi Tenggara","Kabupaten Kolaka Utara":"Sulawesi Tenggara",
    "Kabupaten Konawe":"Sulawesi Tenggara","Kabupaten Konawe Kepulauan":"Sulawesi Tenggara",
    "Kabupaten Konawe Selatan":"Sulawesi Tenggara","Kabupaten Konawe Utara":"Sulawesi Tenggara",
    "Kabupaten Muna":"Sulawesi Tenggara","Kabupaten Muna Barat":"Sulawesi Tenggara","Kabupaten Wakatobi":"Sulawesi Tenggara",
    "Kota Gorontalo":"Gorontalo","Kabupaten Boalemo":"Gorontalo","Kabupaten Bone Bolango":"Gorontalo",
    "Kabupaten Gorontalo Utara":"Gorontalo","Kabupaten Pohuwato":"Gorontalo","Kabupaten Gorontalo":"Gorontalo",
}

VALID_PROVINSI = list(set(KAB_TO_PROV.values()))


def match_to_valid_kab(raw_text):
    """
    Cocokkan satu field geocode (county/city/dll) ke 81 kab/kota resmi.
    Menggunakan word-boundary regex agar 'luwuk' tidak cocok ke 'luwu',
    'lowian' tidak cocok ke 'gowa', dll.
    """
    if not raw_text:
        return None
    raw_lower = raw_text.lower().strip()

    for kab in VALID_SORTED:
        kab_lower = kab.lower()
        kab_short = kab_lower.replace('kabupaten ', '').replace('kota ', '')

        # Exact match pada full name (misal: "kabupaten luwu")
        if kab_lower == raw_lower:
            return kab

        # Exact match pada short name (misal: "luwu" == "luwu")
        if kab_short == raw_lower:
            return kab

        # Word-boundary match: short name harus berdiri sendiri sebagai kata
        # Gunakan \b di regex agar "luwu" tidak cocok ke "luwuk"
        pattern = r'\b' + re.escape(kab_short) + r'\b'
        if re.search(pattern, raw_lower):
            return kab

    return None


def extract_kab_from_geocode_result(location):
    """
    Ekstrak kabupaten/kota dari hasil reverse geocode Nominatim.
    Hanya gunakan field structured address (county, city, town, dll).
    TIDAK fallback ke display_name karena terlalu panjang dan rawan false positive.
    """
    if not location or not location.raw:
        return None

    addr = location.raw.get('address', {})

    # Prioritas field Nominatim yang paling relevan untuk level kabupaten/kota
    # county   = kabupaten di Nominatim Indonesia
    # city     = kota madya
    # town     = kota kecil / kecamatan
    candidates = [
        addr.get('county', ''),
        addr.get('city', ''),
        addr.get('town', ''),
        addr.get('municipality', ''),
        addr.get('state_district', ''),
    ]

    for candidate in candidates:
        candidate = candidate.strip()
        if candidate:
            result = match_to_valid_kab(candidate)
            if result:
                return result

    # Tidak pakai display_name — rawan false positive
    return None


def load_progress():
    """Load progress dari file JSON (untuk resume)."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_progress(progress):
    """Simpan progress ke file JSON."""
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False)


def main():
    print("=" * 70)
    print("REVERSE GEOCODE ALL — Perbaiki kabupaten dari koordinat")
    print("=" * 70)

    # 1. Baca data
    df = pd.read_csv(INPUT_FILE)
    total = len(df)
    print(f"Total data: {total}")

    # 2. Setup geocoder dengan RateLimiter
    geolocator = Nominatim(user_agent="wisata_sulawesi_geocode_v2", timeout=10)
    reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1.0, max_retries=3)

    # 3. Load progress (untuk resume)
    progress = load_progress()
    print(f"Progress tersimpan: {len(progress)} baris sudah di-geocode")

    # 4. Reverse geocode semua baris
    print(f"\nMemulai reverse geocoding...")
    print(f"Estimasi waktu: ~{(total - len(progress)) // 60} menit\n")

    for i in tqdm(range(total), desc="Geocoding", unit="row"):
        idx_str = str(i)

        # Skip jika sudah pernah diproses
        if idx_str in progress:
            continue

        row = df.iloc[i]
        lat = row.get('lat')
        lon = row.get('long')

        if pd.isna(lat) or pd.isna(lon):
            progress[idx_str] = {"kab_geo": None, "raw": "no_coords"}
        else:
            try:
                location = reverse(f"{lat}, {lon}", language="id")
                kab_geo = extract_kab_from_geocode_result(location)
                raw_display = location.raw.get('display_name', '')[:100] if location else ''
                progress[idx_str] = {"kab_geo": kab_geo, "raw": raw_display}
            except Exception as e:
                progress[idx_str] = {"kab_geo": None, "raw": f"ERROR: {str(e)[:80]}"}

        # Save progress setiap 100 baris
        if (i + 1) % 100 == 0:
            save_progress(progress)
            tqdm.write(f"  [Checkpoint] {i + 1}/{total} tersimpan")

    # Final save
    save_progress(progress)
    print(f"\nGeocoding selesai! {len(progress)} baris diproses.")

    # 5. Terapkan hasil ke DataFrame
    df['kabupaten_original'] = df['kabupaten'].copy()
    df['kabupaten_geografi'] = None

    fixes = 0
    unmatched = 0

    for i in range(total):
        idx_str = str(i)
        if idx_str in progress:
            kab_geo = progress[idx_str].get('kab_geo')
            df.at[i, 'kabupaten_geografi'] = kab_geo if kab_geo else ''

            if kab_geo:
                kab_current = str(df.at[i, 'kabupaten']).strip()
                if kab_geo.lower() != kab_current.lower():
                    df.at[i, 'kabupaten'] = kab_geo
                    df.at[i, 'provinsi'] = KAB_TO_PROV.get(kab_geo, df.at[i, 'provinsi'])
                    fixes += 1
            else:
                unmatched += 1

    # 6. Pastikan provinsi selalu dari mapping
    for i in range(total):
        kab = str(df.at[i, 'kabupaten']).strip()
        prov = KAB_TO_PROV.get(kab)
        if prov:
            df.at[i, 'provinsi'] = prov

    # 7. Laporan
    print(f"\n{'=' * 70}")
    print(f"LAPORAN KOREKSI GEOCODING")
    print(f"{'=' * 70}")
    print(f"Total data           : {total}")
    print(f"Kabupaten diperbaiki : {fixes}")
    print(f"Gagal geocode        : {unmatched}")
    print(f"Sudah benar          : {total - fixes - unmatched}")

    # Tampilkan contoh perubahan
    changed = df[df['kabupaten'] != df['kabupaten_original']]
    if len(changed) > 0:
        print(f"\n── Contoh Perubahan (max 30) {'─' * 42}")
        for _, row in changed.head(30).iterrows():
            print(f"  {row['nama_wisata'][:45]}")
            print(f"    {row['kabupaten_original']}  →  {row['kabupaten']}")

    # 8. Simpan output (hanya wisata_terkoreksi_geo.csv)
    # Kolom: semua kolom asli + kabupaten_geografi + kabupaten_original
    # File utama (wisata_sulawesi_lengkap.csv) TIDAK diubah — update via gabung_data.py
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"\nHasil disimpan ke: {OUTPUT_FILE}")
    print(f"(File utama tidak diubah — gunakan gabung_data.py untuk update)")

    # Hapus progress file karena sudah selesai
    if os.path.exists(PROGRESS_FILE):
        os.remove(PROGRESS_FILE)
        print("File progress dihapus.")

    print("=" * 70)


if __name__ == '__main__':
    main()
