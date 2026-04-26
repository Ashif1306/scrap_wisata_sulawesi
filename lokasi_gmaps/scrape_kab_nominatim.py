"""
scrape_kab_nominatim.py
=======================
Cari kabupaten wisata yang belum ditemukan menggunakan Nominatim (OpenStreetMap).
DUA strategi digabung:
  1. Reverse geocoding dari koordinat original (wisata_sulawesi_lengkap.csv)
     → paling akurat jika koordinat tersedia
  2. Forward geocoding dari nama wisata
     → fallback jika tidak ada koordinat

Rate limit: 1 request/detik (sesuai syarat Nominatim/OSM)

Penggunaan:
  python scrape_kab_nominatim.py
  python scrape_kab_nominatim.py --limit 30
  python scrape_kab_nominatim.py --force
"""

import os
import re
import sys
import time
import argparse
import signal

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────
#  KONFIGURASI
# ─────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR     = os.path.join(BASE_DIR, "..")
FINAL_DIR    = os.path.join(ROOT_DIR, "hasil_final")

NO_KAB_FILE  = os.path.join(BASE_DIR, "wisata_no_kab.csv")
ORIGINAL_CSV = os.path.join(FINAL_DIR, "wisata_sulawesi_lengkap.csv")

NOMINATIM_DELAY = 2.5   # detik — dinaikkan ke 2.5s agar tidak bentrok dengan scraper lain

# ─────────────────────────────────────────────
#  DAFTAR KABUPATEN/KOTA SULAWESI (81 entri)
# ─────────────────────────────────────────────
VALID_KAB_KOTA = [
    "Kota Makassar","Kota Palopo","Kota Parepare",
    "Kabupaten Bantaeng","Kabupaten Barru","Kabupaten Bone",
    "Kabupaten Bulukumba","Kabupaten Enrekang","Kabupaten Gowa",
    "Kabupaten Jeneponto","Kabupaten Kepulauan Selayar","Kabupaten Luwu",
    "Kabupaten Luwu Timur","Kabupaten Luwu Utara","Kabupaten Maros",
    "Kabupaten Pangkajene Dan Kepulauan","Kabupaten Pinrang",
    "Kabupaten Sidenreng Rappang","Kabupaten Sinjai","Kabupaten Soppeng",
    "Kabupaten Takalar","Kabupaten Tana Toraja","Kabupaten Toraja Utara",
    "Kabupaten Wajo",
    "Kota Palu",
    "Kabupaten Banggai","Kabupaten Banggai Kepulauan","Kabupaten Banggai Laut",
    "Kabupaten Buol","Kabupaten Donggala","Kabupaten Morowali",
    "Kabupaten Morowali Utara","Kabupaten Parigi Moutong","Kabupaten Poso",
    "Kabupaten Sigi","Kabupaten Tojo Una-Una","Kabupaten Toli-Toli",
    "Kota Kendari","Kota Baubau",
    "Kabupaten Bombana","Kabupaten Buton","Kabupaten Buton Selatan",
    "Kabupaten Buton Tengah","Kabupaten Buton Utara","Kabupaten Kolaka",
    "Kabupaten Kolaka Timur","Kabupaten Kolaka Utara","Kabupaten Konawe",
    "Kabupaten Konawe Kepulauan","Kabupaten Konawe Selatan","Kabupaten Konawe Utara",
    "Kabupaten Muna","Kabupaten Muna Barat","Kabupaten Wakatobi",
    "Kota Manado","Kota Bitung","Kota Tomohon","Kota Kotamobagu",
    "Kabupaten Bolaang Mongondow","Kabupaten Bolaang Mongondow Selatan",
    "Kabupaten Bolaang Mongondow Timur","Kabupaten Bolaang Mongondow Utara",
    "Kabupaten Kepulauan Sangihe","Kabupaten Kepulauan Siau Tagulandang Biaro",
    "Kabupaten Kepulauan Talaud","Kabupaten Minahasa",
    "Kabupaten Minahasa Selatan","Kabupaten Minahasa Tenggara","Kabupaten Minahasa Utara",
    "Kota Gorontalo",
    "Kabupaten Boalemo","Kabupaten Bone Bolango","Kabupaten Gorontalo",
    "Kabupaten Gorontalo Utara","Kabupaten Pohuwato",
    "Kota Mamuju",
    "Kabupaten Majene","Kabupaten Mamasa","Kabupaten Mamuju",
    "Kabupaten Mamuju Tengah","Kabupaten Pasangkayu","Kabupaten Polewali Mandar",
]

KAB_TO_PROV = {
    "Kota Makassar":"Sulawesi Selatan","Kota Palopo":"Sulawesi Selatan","Kota Parepare":"Sulawesi Selatan",
    "Kabupaten Bantaeng":"Sulawesi Selatan","Kabupaten Barru":"Sulawesi Selatan","Kabupaten Bone":"Sulawesi Selatan",
    "Kabupaten Bulukumba":"Sulawesi Selatan","Kabupaten Enrekang":"Sulawesi Selatan","Kabupaten Gowa":"Sulawesi Selatan",
    "Kabupaten Jeneponto":"Sulawesi Selatan","Kabupaten Kepulauan Selayar":"Sulawesi Selatan","Kabupaten Luwu":"Sulawesi Selatan",
    "Kabupaten Luwu Timur":"Sulawesi Selatan","Kabupaten Luwu Utara":"Sulawesi Selatan","Kabupaten Maros":"Sulawesi Selatan",
    "Kabupaten Pangkajene Dan Kepulauan":"Sulawesi Selatan","Kabupaten Pinrang":"Sulawesi Selatan",
    "Kabupaten Sidenreng Rappang":"Sulawesi Selatan","Kabupaten Sinjai":"Sulawesi Selatan","Kabupaten Soppeng":"Sulawesi Selatan",
    "Kabupaten Takalar":"Sulawesi Selatan","Kabupaten Tana Toraja":"Sulawesi Selatan","Kabupaten Toraja Utara":"Sulawesi Selatan",
    "Kabupaten Wajo":"Sulawesi Selatan",
    "Kota Palu":"Sulawesi Tengah",
    "Kabupaten Banggai":"Sulawesi Tengah","Kabupaten Banggai Kepulauan":"Sulawesi Tengah","Kabupaten Banggai Laut":"Sulawesi Tengah",
    "Kabupaten Buol":"Sulawesi Tengah","Kabupaten Donggala":"Sulawesi Tengah","Kabupaten Morowali":"Sulawesi Tengah",
    "Kabupaten Morowali Utara":"Sulawesi Tengah","Kabupaten Parigi Moutong":"Sulawesi Tengah","Kabupaten Poso":"Sulawesi Tengah",
    "Kabupaten Sigi":"Sulawesi Tengah","Kabupaten Tojo Una-Una":"Sulawesi Tengah","Kabupaten Toli-Toli":"Sulawesi Tengah",
    "Kota Kendari":"Sulawesi Tenggara","Kota Baubau":"Sulawesi Tenggara",
    "Kabupaten Bombana":"Sulawesi Tenggara","Kabupaten Buton":"Sulawesi Tenggara","Kabupaten Buton Selatan":"Sulawesi Tenggara",
    "Kabupaten Buton Tengah":"Sulawesi Tenggara","Kabupaten Buton Utara":"Sulawesi Tenggara","Kabupaten Kolaka":"Sulawesi Tenggara",
    "Kabupaten Kolaka Timur":"Sulawesi Tenggara","Kabupaten Kolaka Utara":"Sulawesi Tenggara","Kabupaten Konawe":"Sulawesi Tenggara",
    "Kabupaten Konawe Kepulauan":"Sulawesi Tenggara","Kabupaten Konawe Selatan":"Sulawesi Tenggara","Kabupaten Konawe Utara":"Sulawesi Tenggara",
    "Kabupaten Muna":"Sulawesi Tenggara","Kabupaten Muna Barat":"Sulawesi Tenggara","Kabupaten Wakatobi":"Sulawesi Tenggara",
    "Kota Manado":"Sulawesi Utara","Kota Bitung":"Sulawesi Utara","Kota Tomohon":"Sulawesi Utara","Kota Kotamobagu":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow":"Sulawesi Utara","Kabupaten Bolaang Mongondow Selatan":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow Timur":"Sulawesi Utara","Kabupaten Bolaang Mongondow Utara":"Sulawesi Utara",
    "Kabupaten Kepulauan Sangihe":"Sulawesi Utara","Kabupaten Kepulauan Siau Tagulandang Biaro":"Sulawesi Utara",
    "Kabupaten Kepulauan Talaud":"Sulawesi Utara","Kabupaten Minahasa":"Sulawesi Utara",
    "Kabupaten Minahasa Selatan":"Sulawesi Utara","Kabupaten Minahasa Tenggara":"Sulawesi Utara","Kabupaten Minahasa Utara":"Sulawesi Utara",
    "Kota Gorontalo":"Gorontalo",
    "Kabupaten Boalemo":"Gorontalo","Kabupaten Bone Bolango":"Gorontalo","Kabupaten Gorontalo":"Gorontalo",
    "Kabupaten Gorontalo Utara":"Gorontalo","Kabupaten Pohuwato":"Gorontalo",
    "Kota Mamuju":"Sulawesi Barat",
    "Kabupaten Majene":"Sulawesi Barat","Kabupaten Mamasa":"Sulawesi Barat","Kabupaten Mamuju":"Sulawesi Barat",
    "Kabupaten Mamuju Tengah":"Sulawesi Barat","Kabupaten Pasangkayu":"Sulawesi Barat","Kabupaten Polewali Mandar":"Sulawesi Barat",
}

VALID_SORTED = sorted(VALID_KAB_KOTA, key=lambda x: len(x), reverse=True)

# ─────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────
def is_in_sulawesi(lat, lon) -> bool:
    try:
        return -6.5 <= float(lat) <= 2.5 and 119.0 <= float(lon) <= 127.5
    except Exception:
        return False


def match_kab(text: str) -> str | None:
    """Cari nama kabupaten/kota resmi dari teks bebas."""
    if not text:
        return None
    t = text.lower()
    AMBIG = {"makassar", "bone"}
    # Pass 1: full name
    for kab in VALID_SORTED:
        if kab.lower() in t:
            return kab
    # Pass 2: short name, skip ambiguous
    for kab in VALID_SORTED:
        short = kab.lower().replace("kabupaten ", "").replace("kota ", "")
        if short in AMBIG:
            continue
        if re.search(r'\b' + re.escape(short) + r'\b', t):
            return kab
    # Pass 3: ambiguous last resort
    for kab in VALID_SORTED:
        short = kab.lower().replace("kabupaten ", "").replace("kota ", "")
        if short not in AMBIG:
            continue
        if re.search(r'\b' + re.escape(short) + r'\b', t):
            return kab
    return None


def kab_dari_addr(addr: dict) -> str | None:
    """Ambil kabupaten dari dict address Nominatim."""
    for field in ["county", "city", "town", "municipality", "state_district", "district"]:
        raw = addr.get(field, "").strip()
        if raw:
            kab = match_kab(raw)
            if kab:
                return kab
    return None


# ─────────────────────────────────────────────
#  NOMINATIM SETUP
# ─────────────────────────────────────────────
_geo = Nominatim(user_agent="wisata_sulawesi_nominatim_v2", timeout=12)
_geocode  = RateLimiter(_geo.geocode,  min_delay_seconds=NOMINATIM_DELAY, max_retries=2)
_reverse  = RateLimiter(_geo.reverse,  min_delay_seconds=NOMINATIM_DELAY, max_retries=2)


def reverse_kab(lat: float, lon: float) -> str | None:
    """Reverse-geocode koordinat → kabupaten resmi.
    Pakai zoom=8 agar Nominatim mengembalikan level kabupaten/municipality.
    """
    if not is_in_sulawesi(lat, lon):
        return None
    try:
        # zoom=8 = level county/kabupaten di OSM
        loc = _reverse(f"{lat}, {lon}", language="id", zoom=8)
        if loc and loc.raw:
            # Coba dari address dict
            kab = kab_dari_addr(loc.raw.get("address", {}))
            if kab:
                return kab
            # Fallback: match dari display_name
            return match_kab(loc.address or "")
    except Exception:
        pass
    return None


def forward_kab(nama: str) -> tuple[str | None, float | None, float | None]:
    """
    Forward geocode nama wisata → (kabupaten, lat, lon).
    Strategi berlapis:
      1. Forward geocode → cek display_name langsung (untuk nama yang sudah spesifik)
      2. Forward geocode → ambil koordinat → reverse dengan zoom=8 (lebih akurat)
    """
    queries = [
        f"{nama}, Sulawesi, Indonesia",
        f"{nama} Sulawesi",
        nama,
    ]
    for q in queries:
        try:
            loc = _geocode(q, language="id", country_codes="id", exactly_one=True)
            if not loc:
                continue
            lat, lon = loc.latitude, loc.longitude
            if not is_in_sulawesi(lat, lon):
                continue   # di luar Sulawesi → skip

            # Coba 1: match dari display_name hasil forward (cepat)
            kab = match_kab(loc.address or "")
            if kab:
                return kab, lat, lon

            # Coba 2: reverse dengan zoom=8 dari koordinat yang ditemukan
            try:
                time.sleep(NOMINATIM_DELAY)
                loc2 = _geo.reverse(f"{lat}, {lon}", language="id", zoom=8)
                if loc2 and loc2.raw:
                    kab = kab_dari_addr(loc2.raw.get("address", {}))
                    if kab:
                        return kab, lat, lon
                    kab = match_kab(loc2.address or "")
                    if kab:
                        return kab, lat, lon
            except Exception:
                pass

        except Exception:
            time.sleep(1)
    return None, None, None


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Cari kabupaten via Nominatim geocoding")
    ap.add_argument("--input",    default=NO_KAB_FILE)
    ap.add_argument("--original", default=ORIGINAL_CSV, help="CSV asli dengan kolom lat/lon")
    ap.add_argument("--limit",    type=int, default=0)
    ap.add_argument("--force",    action="store_true")
    args = ap.parse_args()

    # Baca file no_kab
    df = pd.read_csv(args.input, dtype=str)
    print(f"[INPUT]  {args.input} ({len(df)} baris)")

    # Pastikan kolom ada
    for col in ["kab_ddg", "prov_ddg", "snippet_ddg", "status_ddg"]:
        if col not in df.columns:
            df[col] = ""

    # Baca koordinat original dari wisata_sulawesi_lengkap.csv
    lat_lon_map: dict = {}   # place_id → (lat, lon)
    if os.path.exists(args.original):
        try:
            df_ori = pd.read_csv(args.original, dtype=str)
            lat_col = next((c for c in df_ori.columns if c.lower() in ("lat", "latitude")), None)
            lon_col = next((c for c in df_ori.columns if c.lower() in ("lon", "lng", "longitude", "long")), None)
            if lat_col and lon_col:
                for _, r in df_ori.iterrows():
                    pid = str(r.get("place_id", "")).strip()
                    lat_v = r.get(lat_col)
                    lon_v = r.get(lon_col)
                    if pid and str(lat_v) not in ("", "nan") and str(lon_v) not in ("", "nan"):
                        try:
                            lat_lon_map[pid] = (float(lat_v), float(lon_v))
                        except Exception:
                            pass
            print(f"[ORIGINAL] {len(lat_lon_map)} entri dengan koordinat dari {args.original}")
        except Exception as e:
            print(f"[WARN] Gagal baca original CSV: {e}")
    else:
        print(f"[WARN] File original tidak ditemukan: {args.original}")

    n_ok = n_skip = n_fail = 0
    processed = 0

    def save():
        df.to_csv(args.input, index=False, encoding="utf-8-sig")

    def _sigint(sig, frame):
        print("\n[STOP] Ctrl+C! Menyimpan progress...")
        save()
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint)

    print("=" * 65)
    for idx, row in df.iterrows():
        if args.limit and processed >= args.limit:
            break

        nama     = str(row.get("nama_wisata", "")).strip()
        status   = str(row.get("status_ddg",  "")).strip()
        kab_lama = str(row.get("kab_ddg",     "")).strip()
        place_id = str(row.get("place_id",    "")).strip()

        sudah_ok = status in ("OK_REVERSE", "OK_FORWARD", "OK_BOTH", "OK_NAME", "OK_ORIGINAL") and kab_lama not in ("", "nan")
        if sudah_ok and not args.force:
            n_skip += 1
            continue

        processed += 1
        print(f"[{idx+1:>5}] {nama[:55]}", end=" → ", flush=True)

        kab_result   = None
        lat_result   = None
        lon_result   = None
        status_result = "NOT_FOUND"

        # ── Strategi 1: Reverse dari koordinat original ──────
        coords = lat_lon_map.get(place_id)
        if coords:
            lat_ori, lon_ori = coords
            kab_rev = reverse_kab(lat_ori, lon_ori)
            if kab_rev:
                kab_result    = kab_rev
                lat_result    = lat_ori
                lon_result    = lon_ori
                status_result = "OK_REVERSE"

        # ── Strategi 2: Forward geocoding dari nama ──────────
        if not kab_result:
            kab_fwd, lat_fwd, lon_fwd = forward_kab(nama)
            if kab_fwd:
                kab_result    = kab_fwd
                lat_result    = lat_fwd
                lon_result    = lon_fwd
                status_result = "OK_FORWARD"

        # ── Strategi 3: match dari nama wisata langsung ──────
        # Contoh: "TUGU I LOVE SITARO" → Kabupaten Kepulauan Siau Tagulandang Biaro
        if not kab_result:
            kab_name = match_kab(nama)
            if kab_name:
                kab_result    = kab_name
                lat_result    = None
                lon_result    = None
                status_result = "OK_NAME"

        # ── Strategi 4: pakai kolom kabupaten original (fallback) ─
        # HANYA untuk entri yang belum pernah dicoba (status_gmaps = NaN).
        # Entri yang sudah dicoba scraper tapi gagal (NO_MATCH, NO_ADDR, FAIL)
        # TIDAK pakai fallback ini karena original-nya mungkin memang salah.
        if not kab_result:
            status_gmaps_lama = str(row.get("status_gmaps", "")).strip()
            belum_dicoba = status_gmaps_lama in ("", "nan", "NaN")
            if belum_dicoba:
                kab_ori = str(row.get("kabupaten", "")).strip()
                kab_valid = match_kab(kab_ori) if kab_ori and kab_ori not in ("nan", "") else None
                if kab_valid:
                    kab_result    = kab_valid
                    status_result = "OK_ORIGINAL"
                    print("(original)", end=" ", flush=True)
            else:
                # Entri pernah gagal → tandai supaya bisa dicek manual
                status_result = f"STILL_MISSING ({status_gmaps_lama})"

        # Simpan
        df.at[idx, "kab_ddg"]     = str(kab_result or "")
        df.at[idx, "prov_ddg"]    = str(KAB_TO_PROV.get(kab_result, "") if kab_result else "")
        df.at[idx, "snippet_ddg"] = f"lat={lat_result},lon={lon_result}" if lat_result else ""
        df.at[idx, "status_ddg"]  = status_result

        if kab_result:
            n_ok += 1
            print(f"{status_result} → {kab_result}")
        else:
            n_fail += 1
            print("NOT_FOUND")

        # Auto-save tiap 25 baris
        if processed % 25 == 0:
            save()
            print(f"   [SAVE] auto-save ({processed} diproses, {n_ok} ditemukan)")

    save()
    print("\n" + "=" * 65)
    print("  SELESAI!")
    print(f"  Output      : {args.input}")
    print(f"  Ditemukan   : {n_ok}")
    print(f"  Tidak Dapat : {n_fail}")
    print(f"  Dilewati    : {n_skip}")
    print(f"  Diproses    : {processed}")
    print("=" * 65)


if __name__ == "__main__":
    main()
