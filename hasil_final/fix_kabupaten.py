"""
fix_kabupaten.py — Perbaiki kolom kabupaten yang salah.
Strategi:
  1. Ekstrak kabupaten dari kolom alamat (regex + daftar valid)
  2. Bandingkan dengan kolom kabupaten yang ada
  3. Jika berbeda → ganti
  4. Jika alamat tidak jelas → reverse geocoding (Nominatim)
  5. Simpan kabupaten lama ke kolom kabupaten_original
  6. Laporan + simpan ke kabupaten_provinsi.csv
"""
import pandas as pd
import re
import time
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(SCRIPT_DIR, 'wisata_sulawesi_lengkap.csv')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'kabupaten_provinsi.csv')

# ── DAFTAR KABUPATEN/KOTA VALID ─────────────────────────────
VALID_KAB_KOTA = [
    "Kota Makassar","Kota Palopo","Kota Parepare",
    "Kabupaten Bantaeng","Kabupaten Barru","Kabupaten Bone",
    "Kabupaten Bulukumba","Kabupaten Enrekang","Kabupaten Gowa",
    "Kabupaten Jeneponto","Kabupaten Kepulauan Selayar",
    "Kabupaten Luwu","Kabupaten Luwu Timur","Kabupaten Luwu Utara",
    "Kabupaten Maros","Kabupaten Pangkajene Dan Kepulauan",
    "Kabupaten Pinrang","Kabupaten Sidenreng Rappang",
    "Kabupaten Sinjai","Kabupaten Soppeng","Kabupaten Takalar",
    "Kabupaten Tana Toraja","Kabupaten Toraja Utara","Kabupaten Wajo",
    "Kabupaten Mamuju","Kabupaten Majene","Kabupaten Polewali Mandar",
    "Kabupaten Mamasa","Kabupaten Pasangkayu","Kabupaten Mamuju Tengah",
    "Kota Palu","Kabupaten Banggai","Kabupaten Banggai Kepulauan",
    "Kabupaten Banggai Laut","Kabupaten Buol","Kabupaten Donggala",
    "Kabupaten Morowali","Kabupaten Morowali Utara",
    "Kabupaten Parigi Moutong","Kabupaten Poso","Kabupaten Sigi",
    "Kabupaten Tojo Una-Una","Kabupaten Tolitoli",
    "Kota Manado","Kota Bitung","Kota Tomohon","Kota Kotamobagu",
    "Kabupaten Bolaang Mongondow","Kabupaten Bolaang Mongondow Selatan",
    "Kabupaten Bolaang Mongondow Timur","Kabupaten Bolaang Mongondow Utara",
    "Kabupaten Kepulauan Sangihe","Kabupaten Kepulauan Siau Tagulandang Biaro",
    "Kabupaten Kepulauan Talaud","Kabupaten Minahasa",
    "Kabupaten Minahasa Selatan","Kabupaten Minahasa Tenggara",
    "Kabupaten Minahasa Utara",
    "Kota Kendari","Kota Baubau",
    "Kabupaten Bombana","Kabupaten Buton","Kabupaten Buton Selatan",
    "Kabupaten Buton Tengah","Kabupaten Buton Utara",
    "Kabupaten Kolaka","Kabupaten Kolaka Timur","Kabupaten Kolaka Utara",
    "Kabupaten Konawe","Kabupaten Konawe Kepulauan",
    "Kabupaten Konawe Selatan","Kabupaten Konawe Utara",
    "Kabupaten Muna","Kabupaten Muna Barat","Kabupaten Wakatobi",
    "Kota Gorontalo","Kabupaten Boalemo","Kabupaten Bone Bolango",
    "Kabupaten Gorontalo Utara","Kabupaten Pohuwato","Kabupaten Gorontalo",
]

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

# Alias untuk mencocokkan variasi nama di alamat
ALIAS_MAP = {
    "pangkep": "Kabupaten Pangkajene Dan Kepulauan",
    "pangkajene": "Kabupaten Pangkajene Dan Kepulauan",
    "sidrap": "Kabupaten Sidenreng Rappang",
    "sidenreng": "Kabupaten Sidenreng Rappang",
    "toli-toli": "Kabupaten Tolitoli",
    "toli toli": "Kabupaten Tolitoli",
    "bolmong": "Kabupaten Bolaang Mongondow",
    "sitaro": "Kabupaten Kepulauan Siau Tagulandang Biaro",
    "bau-bau": "Kota Baubau",
    "bau bau": "Kota Baubau",
    "sangihe": "Kabupaten Kepulauan Sangihe",
    "talaud": "Kabupaten Kepulauan Talaud",
    "selayar": "Kabupaten Kepulauan Selayar",
    "wakatobi": "Kabupaten Wakatobi",
    "parepare": "Kota Parepare",
    "pare-pare": "Kota Parepare",
    "pare pare": "Kota Parepare",
    "parigi": "Kabupaten Parigi Moutong",
    "donggala regency": "Kabupaten Donggala",
    "makassar city": "Kota Makassar",
    "manado city": "Kota Manado",
    "kendari city": "Kota Kendari",
    "gorontalo city": "Kota Gorontalo",
    "palu city": "Kota Palu",
    "palopo city": "Kota Palopo",
    "tomohon city": "Kota Tomohon",
    "bitung city": "Kota Bitung",
    "north minahasa": "Kabupaten Minahasa Utara",
    "south minahasa": "Kabupaten Minahasa Selatan",
    "southeast minahasa": "Kabupaten Minahasa Tenggara",
    "north toraja": "Kabupaten Toraja Utara",
    "north luwu": "Kabupaten Luwu Utara",
    "east luwu": "Kabupaten Luwu Timur",
    "north morowali": "Kabupaten Morowali Utara",
    "south konawe": "Kabupaten Konawe Selatan",
    "north konawe": "Kabupaten Konawe Utara",
    "east kolaka": "Kabupaten Kolaka Timur",
    "north kolaka": "Kabupaten Kolaka Utara",
    "south buton": "Kabupaten Buton Selatan",
    "north buton": "Kabupaten Buton Utara",
    "central buton": "Kabupaten Buton Tengah",
    "west muna": "Kabupaten Muna Barat",
    "selayar islands": "Kabupaten Kepulauan Selayar",
    "sangihe islands": "Kabupaten Kepulauan Sangihe",
}

# Sorted by length descending to match longest first
VALID_KAB_SORTED = sorted(VALID_KAB_KOTA, key=len, reverse=True)


def find_kab_in_alamat(alamat_str):
    """Cari kabupaten/kota valid dalam string alamat."""
    if not alamat_str or str(alamat_str).strip() in ['-', 'nan', '']:
        return None
    alamat_lower = str(alamat_str).lower()

    # 1. Cocokkan langsung dengan daftar valid (terpanjang dulu)
    for kab in VALID_KAB_SORTED:
        if kab.lower() in alamat_lower:
            return kab

    # 2. Cocokkan alias
    for alias, full_name in sorted(ALIAS_MAP.items(), key=lambda x: len(x[0]), reverse=True):
        if alias in alamat_lower:
            return full_name

    # 3. Regex "Kab. X"
    m = re.search(r'kab\.?\s+([a-z][a-z\s\-]+?)(?:\s*[,\.\d]|$)', alamat_lower)
    if m:
        kab_raw = m.group(1).strip()
        for kab in VALID_KAB_KOTA:
            kab_clean = kab.lower().replace('kabupaten ', '').replace('kota ', '')
            if kab_clean == kab_raw or kab_raw.startswith(kab_clean):
                return kab

    return None


def normalize(s):
    """Normalize string for comparison."""
    return re.sub(r'\s+', ' ', str(s).strip().lower())


def reverse_geocode_nominatim(lat, lon):
    """Reverse geocode menggunakan Nominatim (gratis, rate-limited)."""
    try:
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="wisata_sulawesi_fix_v1", timeout=10)
        location = geolocator.reverse(f"{lat}, {lon}", language="id")
        if location and location.raw:
            addr = location.raw.get('address', {})
            # Nominatim returns county for kabupaten, city for kota
            county = addr.get('county', '')
            city = addr.get('city', '')
            town = addr.get('town', '')

            # Try county first (usually "Kabupaten X")
            candidate = county or city or town
            if candidate:
                candidate_lower = candidate.lower()
                # Match against valid list
                for kab in VALID_KAB_SORTED:
                    kab_lower = kab.lower()
                    kab_short = kab_lower.replace('kabupaten ', '').replace('kota ', '')
                    if kab_lower in candidate_lower or kab_short in candidate_lower or candidate_lower in kab_lower:
                        return kab
                # Try title-casing and prepending
                if 'kabupaten' in candidate_lower:
                    candidate_clean = re.sub(r'^kabupaten\s+', '', candidate_lower).strip().title()
                    full = f"Kabupaten {candidate_clean}"
                    for kab in VALID_KAB_KOTA:
                        if normalize(kab) == normalize(full):
                            return kab
                elif 'kota' in candidate_lower:
                    candidate_clean = re.sub(r'^kota\s+', '', candidate_lower).strip().title()
                    full = f"Kota {candidate_clean}"
                    for kab in VALID_KAB_KOTA:
                        if normalize(kab) == normalize(full):
                            return kab
    except Exception as e:
        print(f"    [Geocode Error] {e}")
    return None


def main():
    print("=" * 70)
    print("FIX KABUPATEN — Perbaiki kolom kabupaten dari alamat + geocoding")
    print("=" * 70)

    df = pd.read_csv(INPUT_FILE)
    print(f"Total baris: {len(df)}")

    # Simpan nilai original
    df['kabupaten_original'] = df['kabupaten'].copy()

    changes = []       # list of dicts for report
    geocode_needed = [] # indices yang perlu reverse geocode

    # ── PASS 1: Ekstrak dari alamat ──────────────────────────
    print("\n[Pass 1] Ekstrak kabupaten dari kolom alamat...")
    pass1_fixes = 0

    for i, row in df.iterrows():
        alamat = str(row.get('alamat', ''))
        kab_current = str(row['kabupaten']).strip()
        kab_from_alamat = find_kab_in_alamat(alamat)

        if kab_from_alamat:
            if normalize(kab_from_alamat) != normalize(kab_current):
                changes.append({
                    'idx': i,
                    'nama': row['nama_wisata'],
                    'kab_lama': kab_current,
                    'kab_baru': kab_from_alamat,
                    'sumber': 'alamat',
                })
                df.at[i, 'kabupaten'] = kab_from_alamat
                df.at[i, 'provinsi'] = KAB_TO_PROV.get(kab_from_alamat, row['provinsi'])
                pass1_fixes += 1
        else:
            geocode_needed.append(i)

    print(f"  Diperbaiki dari alamat: {pass1_fixes}")
    print(f"  Perlu reverse geocoding: {len(geocode_needed)}")

    # ── PASS 2: Reverse geocoding ────────────────────────────
    if geocode_needed:
        print(f"\n[Pass 2] Reverse geocoding {len(geocode_needed)} lokasi...")
        geocode_fixes = 0
        geocode_fail = 0

        for count, idx in enumerate(geocode_needed, 1):
            row = df.loc[idx]
            lat = row.get('lat', None)
            lon = row.get('long', None)

            if pd.isna(lat) or pd.isna(lon):
                geocode_fail += 1
                continue

            kab_geo = reverse_geocode_nominatim(lat, lon)

            if kab_geo:
                kab_current = str(row['kabupaten']).strip()
                if normalize(kab_geo) != normalize(kab_current):
                    changes.append({
                        'idx': idx,
                        'nama': row['nama_wisata'],
                        'kab_lama': kab_current,
                        'kab_baru': kab_geo,
                        'sumber': 'geocode',
                    })
                    df.at[idx, 'kabupaten'] = kab_geo
                    df.at[idx, 'provinsi'] = KAB_TO_PROV.get(kab_geo, row['provinsi'])
                    geocode_fixes += 1

            if count % 50 == 0 or count == len(geocode_needed):
                print(f"  Progres: {count}/{len(geocode_needed)} (fix: {geocode_fixes})")

            time.sleep(1.1)  # Nominatim rate limit: max 1 req/sec

        print(f"  Diperbaiki dari geocode: {geocode_fixes}")
        print(f"  Gagal geocode: {geocode_fail}")

    # ── LAPORAN ──────────────────────────────────────────────
    print(f"\n{'=' * 70}")
    print(f"LAPORAN PERUBAHAN")
    print(f"{'=' * 70}")
    print(f"Total baris data     : {len(df)}")
    print(f"Total diperbaiki     : {len(changes)}")
    print(f"  - dari alamat      : {sum(1 for c in changes if c['sumber'] == 'alamat')}")
    print(f"  - dari geocoding   : {sum(1 for c in changes if c['sumber'] == 'geocode')}")
    print(f"Tidak berubah        : {len(df) - len(changes)}")

    if changes:
        print(f"\n── 20 Contoh Perubahan {'─' * 48}")
        for c in changes[:20]:
            print(f"  [{c['idx']:4d}] {c['nama'][:45]}")
            print(f"         {c['kab_lama']}  →  {c['kab_baru']}  [{c['sumber']}]")

    # ── SIMPAN ───────────────────────────────────────────────
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"\nHasil disimpan ke: {OUTPUT_FILE}")
    print(f"Encoding: UTF-8")
    print("=" * 70)


if __name__ == '__main__':
    main()
