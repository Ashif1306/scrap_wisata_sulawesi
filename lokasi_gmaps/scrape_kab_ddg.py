"""
scrape_kab_ddg.py
=================
Cari kabupaten wisata yang belum ditemukan menggunakan DuckDuckGo HTML search
+ BeautifulSoup parsing. Tidak butuh Playwright, cukup requests + bs4.

Alur per wisata:
  1. Buat query: "{nama_wisata} Sulawesi kabupaten"
  2. Kirim request ke https://html.duckduckgo.com/html/
  3. Parse hasil pencarian dengan BeautifulSoup
  4. Cari nama kabupaten resmi Sulawesi di snippet & judul hasil
  5. Validasi via Nominatim (jika ada koordinat di CSV original)
  6. Simpan ke wisata_no_kab.csv (update inplace dengan resume)

Fitur:
  - Resume otomatis (skip baris yang sudah ada kab_ddg)
  - Rate limiting (jeda 2-4 detik antar request)
  - --force untuk proses ulang semua
  - --limit N untuk test sample kecil

Penggunaan:
  python scrape_kab_ddg.py
  python scrape_kab_ddg.py --limit 20
  python scrape_kab_ddg.py --force
"""

import os
import re
import sys
import time
import random
import argparse
import signal

import requests
from bs4 import BeautifulSoup
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────
#  KONFIGURASI
# ─────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(BASE_DIR, "wisata_no_kab.csv")

DDG_URL     = "https://html.duckduckgo.com/html/"
HEADERS     = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}
MIN_DELAY   = 2.5   # detik antar request
MAX_DELAY   = 5.0
NOMINATIM_DELAY = 1.1

# ─────────────────────────────────────────────
#  DAFTAR KABUPATEN/KOTA SULAWESI
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

# Urutkan dari terpanjang ke terpendek agar multi-kata dicocokkan dulu
VALID_SORTED = sorted(VALID_KAB_KOTA, key=lambda x: len(x), reverse=True)

# ─────────────────────────────────────────────
#  HELPER: match kabupaten dari teks bebas
# ─────────────────────────────────────────────
def match_kab(text: str) -> str | None:
    """Cari nama kabupaten/kota resmi dari teks bebas."""
    if not text:
        return None
    t = text.lower()
    # Pass 1: full match "Kabupaten X" / "Kota X"
    for kab in VALID_SORTED:
        if kab.lower() in t:
            return kab
    # Pass 2: nama pendek, skip ambigu
    AMBIG = {"makassar", "bone"}
    for kab in VALID_SORTED:
        short = kab.lower().replace("kabupaten ", "").replace("kota ", "")
        if short in AMBIG:
            continue
        if re.search(r'\b' + re.escape(short) + r'\b', t):
            return kab
    # Pass 3: ambigu last resort
    for kab in VALID_SORTED:
        short = kab.lower().replace("kabupaten ", "").replace("kota ", "")
        if short not in AMBIG:
            continue
        if re.search(r'\b' + re.escape(short) + r'\b', t):
            return kab
    return None


# ─────────────────────────────────────────────
#  HELPER: Nominatim reverse geocode
# ─────────────────────────────────────────────
_geolocator = Nominatim(user_agent="wisata_sulawesi_ddg_v1", timeout=10)
_reverse_geo = RateLimiter(_geolocator.reverse, min_delay_seconds=NOMINATIM_DELAY, max_retries=2)


def geo_kab(lat: float, lon: float) -> str | None:
    """Reverse-geocode koordinat → nama kabupaten resmi."""
    try:
        loc = _reverse_geo(f"{lat}, {lon}", language="id")
        if not loc or not loc.raw:
            return None
        addr = loc.raw.get("address", {})
        for field in ["county", "city", "town", "municipality", "state_district"]:
            raw = addr.get(field, "").strip()
            kab = match_kab(raw)
            if kab:
                return kab
    except Exception:
        pass
    return None


def is_in_sulawesi(lat, lon) -> bool:
    try:
        return -6.5 <= float(lat) <= 2.5 and 119.0 <= float(lon) <= 127.5
    except Exception:
        return False


# ─────────────────────────────────────────────
#  CORE: cari kabupaten via DuckDuckGo
# ─────────────────────────────────────────────
def cari_kab_ddg(
    nama: str,
    lat_ori=None,
    lon_ori=None,
    session: requests.Session = None,
) -> dict:
    """
    Cari kabupaten wisata via DuckDuckGo HTML.
    Jika ada koordinat original yang valid, juga cek via Nominatim sebagai validasi.
    Return: {kab_ddg, prov_ddg, snippet_ddg, status_ddg}
    """
    result = {"kab_ddg": "", "prov_ddg": "", "snippet_ddg": "", "status_ddg": "FAIL"}

    # ── Cari via DuckDuckGo ───────────────────────────────────
    query = f"{nama} Sulawesi kabupaten"
    kab_dari_ddg = None
    snippet_terbaik = ""

    try:
        resp = (session or requests).post(
            DDG_URL,
            data={"q": query, "b": "", "kl": "id-id"},
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Ambil judul + snippet dari hasil pencarian
        results = soup.select(".result")
        texts_to_check = []
        for r in results[:6]:          # periksa 6 hasil pertama
            title = r.select_one(".result__title")
            snip  = r.select_one(".result__snippet")
            if title:
                texts_to_check.append(title.get_text(" ", strip=True))
            if snip:
                texts_to_check.append(snip.get_text(" ", strip=True))

        for txt in texts_to_check:
            kab = match_kab(txt)
            if kab:
                kab_dari_ddg   = kab
                snippet_terbaik = txt[:200]
                break

    except Exception as e:
        result["status_ddg"] = f"DDG_ERROR: {e}"

    # ── Validasi via Nominatim (jika ada koordinat original) ──
    kab_dari_geo = None
    if lat_ori and lon_ori and is_in_sulawesi(lat_ori, lon_ori):
        kab_dari_geo = geo_kab(float(lat_ori), float(lon_ori))

    # ── Resolusi ──────────────────────────────────────────────
    result["snippet_ddg"] = snippet_terbaik

    if kab_dari_ddg and kab_dari_geo:
        if kab_dari_ddg == kab_dari_geo:
            result["kab_ddg"]    = kab_dari_ddg
            result["prov_ddg"]   = KAB_TO_PROV.get(kab_dari_ddg, "")
            result["status_ddg"] = "OK_BOTH"        # DDG & Nominatim sepakat
        else:
            # Nominatim lebih terpercaya secara geografis
            result["kab_ddg"]    = kab_dari_geo
            result["prov_ddg"]   = KAB_TO_PROV.get(kab_dari_geo, "")
            result["status_ddg"] = "GEO_WIN"        # geo override DDG
    elif kab_dari_geo:
        result["kab_ddg"]    = kab_dari_geo
        result["prov_ddg"]   = KAB_TO_PROV.get(kab_dari_geo, "")
        result["status_ddg"] = "OK_GEO"
    elif kab_dari_ddg:
        result["kab_ddg"]    = kab_dari_ddg
        result["prov_ddg"]   = KAB_TO_PROV.get(kab_dari_ddg, "")
        result["status_ddg"] = "OK_DDG"
    else:
        result["status_ddg"] = "NOT_FOUND"

    return result


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Cari kabupaten wisata via DuckDuckGo + BeautifulSoup")
    ap.add_argument("--input",   default=INPUT_FILE)
    ap.add_argument("--limit",   type=int, default=0, help="Maks baris (0=semua)")
    ap.add_argument("--delay",   type=float, default=0, help="Override jeda (0=random 2.5-5s)")
    ap.add_argument("--force",   action="store_true", help="Proses ulang meski sudah ada hasil")
    args = ap.parse_args()

    if not os.path.exists(args.input):
        print(f"[ERROR] File tidak ditemukan: {args.input}")
        print("        Jalankan pisah_no_kab.py terlebih dahulu.")
        sys.exit(1)

    df = pd.read_csv(args.input, dtype=str)
    print(f"[INPUT]  {args.input} ({len(df)} baris)")

    # Pastikan kolom ada
    for col in ["kab_ddg", "prov_ddg", "snippet_ddg", "status_ddg"]:
        if col not in df.columns:
            df[col] = ""

    n_ok = n_skip = n_fail = 0
    processed = 0

    def save():
        df.to_csv(args.input, index=False, encoding="utf-8-sig")

    def _sigint(sig, frame):
        print("\n[STOP] Ctrl+C! Menyimpan...")
        save()
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint)

    session = requests.Session()
    session.headers.update(HEADERS)

    print("=" * 60)
    for idx, row in df.iterrows():
        if args.limit and processed >= args.limit:
            break

        nama     = str(row.get("nama_wisata", "")).strip()
        status   = str(row.get("status_ddg",  "")).strip()
        kab_lama = str(row.get("kab_ddg",     "")).strip()

        sudah_ok = status in ("OK_BOTH", "OK_GEO", "OK_DDG", "GEO_WIN") and kab_lama not in ("", "nan")
        if sudah_ok and not args.force:
            n_skip += 1
            continue

        processed += 1
        lat_ori = row.get("lat", row.get("latitude", None))
        lon_ori = row.get("lon", row.get("longitude", None))

        print(f"[{idx+1:>5}] {nama[:55]}", end=" → ", flush=True)

        try:
            res = cari_kab_ddg(nama, lat_ori, lon_ori, session)
        except Exception as e:
            res = {"kab_ddg": "", "prov_ddg": "", "snippet_ddg": "", "status_ddg": f"ERROR: {e}"}
            print(f"ERROR: {e}")

        # Simpan ke df
        df.at[idx, "kab_ddg"]     = str(res["kab_ddg"])
        df.at[idx, "prov_ddg"]    = str(res["prov_ddg"])
        df.at[idx, "snippet_ddg"] = str(res["snippet_ddg"])[:300]
        df.at[idx, "status_ddg"]  = str(res["status_ddg"])

        st = res["status_ddg"]
        if st in ("OK_BOTH", "OK_GEO", "OK_DDG", "GEO_WIN"):
            n_ok += 1
            print(f"{st} → {res['kab_ddg']}")
        elif st == "NOT_FOUND":
            n_fail += 1
            print("NOT_FOUND")
        else:
            n_fail += 1
            print(st)

        # Auto-save tiap 25 baris
        if processed % 25 == 0:
            save()
            print(f"   [SAVE] auto-save ({processed} diproses, {n_ok} ditemukan)")

        # Jeda acak agar tidak diblokir
        delay = args.delay if args.delay > 0 else random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)

    save()
    print("\n" + "=" * 60)
    print("  SELESAI!")
    print(f"  Output     : {args.input}")
    print(f"  Ditemukan  : {n_ok}")
    print(f"  Tidak Dapat: {n_fail}")
    print(f"  Dilewati   : {n_skip}")
    print(f"  Diproses   : {processed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
