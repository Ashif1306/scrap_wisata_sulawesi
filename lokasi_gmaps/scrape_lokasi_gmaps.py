"""
scrape_lokasi_gmaps.py
======================
Ambil informasi lokasi (kabupaten/kota) dari tab Overview Google Maps
menggunakan Playwright, satu per satu berdasarkan place_id dan nama_wisata.

Strategi:
  1. Buka Google Maps via place_id URL (Strategi A)
  2. Fallback: cari via nama_wisata + Sulawesi (Strategi B)
  3. Di tab Overview, baca alamat yang tampil
  4. Ekstrak koordinat dari URL Maps (@lat,lon)
  5. Validasi geografi: reverse-geocode koordinat via Nominatim
     → Kabupaten dari alamat teks HARUS cocok dgn kabupaten dari koordinat
     → Jika tidak cocok → pakai hasil koordinat (lebih dipercaya)
     → Jika koordinat tidak tersedia / di luar Sulawesi → hanya pakai teks alamat
  6. Jika tidak ada info sama sekali → kosongkan

Status result:
  OK_GEO   : alamat teks & koordinat sama-sama konfirmasi kabupaten yg sama
  OK_TEXT  : kabupaten dari teks, koordinat tidak tersedia/gagal
  GEO_WIN  : koordinat konfirmasi beda kabupaten dari teks → pakai koordinat
  NO_MATCH : ada alamat tapi tidak ada nama kab/kota yang dikenal
  NO_ADDR  : tidak ada teks alamat sama sekali
  WRONG_PLACE : Maps membuka tempat di luar Sulawesi
  FAIL     : gagal navigasi total

Fitur Resume:
  - Simpan progress ke CSV setiap AUTOSAVE_INTERVAL baris
  - Lanjut otomatis dari posisi terakhir jika dijalankan ulang

Penggunaan:
  python scrape_lokasi_gmaps.py
  python scrape_lokasi_gmaps.py --headless
  python scrape_lokasi_gmaps.py --limit 50
  python scrape_lokasi_gmaps.py --force   (proses ulang semua meski sudah ada)
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
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

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
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))  # .../lokasi_gmaps/
ROOT_DIR    = os.path.join(BASE_DIR, "..")               # .../scrapt_wisata/
FINAL_DIR   = os.path.join(ROOT_DIR, "hasil_final")

INPUT_FILE  = os.path.join(FINAL_DIR, "wisata_sulawesi_lengkap.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "lokasi_scraped.csv")  # disimpan di folder ini

DEFAULT_DELAY     = 3.0
AUTOSAVE_INTERVAL = 25
NAV_TIMEOUT       = 20_000
ELEM_TIMEOUT      = 8_000

MAPS_PID_URL = "https://www.google.com/maps/search/?api=1&query={name}&query_place_id={place_id}"
MAPS_SEARCH  = "https://www.google.com/maps/search/{query}"

# Rate limit Nominatim: 1 request per detik (syarat penggunaan OpenStreetMap)
NOMINATIM_DELAY = 1.1  # detik

# 81 kab/kota resmi Sulawesi (untuk matching)
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
    "Kabupaten Minahasa Selatan","Kabupaten Minahasa Tenggara","Kabupaten Minahasa Utara",
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


# ─────────────────────────────────────────────
#  HELPER
# ─────────────────────────────────────────────
def match_kab_dari_teks(text: str) -> tuple[str, str] | tuple[None, None]:
    """
    Cari nama kabupaten/kota valid dari teks alamat Google Maps.
    Return: (kab_name, confidence) atau (None, None)

    confidence:
      'explicit'    → Pass 1: full "Kabupaten X" / "Kota X" ditemukan di teks
                       (sangat dipercaya — kalahkan Nominatim jika konflik)
      'contextual'  → Pass 2: nama pendek setelah konteks Kab./Kec.
                       (dipercaya — kalahkan Nominatim jika konflik)
      'loose'       → Pass 3: word-boundary saja
                       (lemah — kalah jika Nominatim konfirmasi beda)
    """
    if not text:
        return None, None
    text_lower = text.lower()

    # Pass 1: cari "Kabupaten X" atau "Kota X" secara eksplisit di teks
    for kab in VALID_SORTED:
        if kab.lower() in text_lower:
            return kab, 'explicit'

    # Pass 2: nama pendek setelah konteks kab/kec
    ctx_pattern = re.compile(
        r'(?:kab(?:upaten)?[\s.]+|kec(?:amatan)?[\s.,]+\w+[\s,]+)([\w\s]+?)(?:\s*\d{4}|,|$)',
        re.I
    )
    for m in ctx_pattern.finditer(text):
        candidate = m.group(1).strip()
        for kab in VALID_SORTED:
            kab_short = kab.lower().replace("kabupaten ", "").replace("kota ", "")
            if re.fullmatch(re.escape(kab_short), candidate.lower()):
                # Nama ambigu (makassar, bone) yang muncul setelah Kec. tidak bisa dipercaya
                # sebagai kabupaten — turunkan ke 'loose'
                conf = 'loose' if kab_short in {"makassar", "bone"} else 'contextual'
                return kab, conf

    # Pass 3: word-boundary bebas, skip ambigu dulu
    AMBIGUOUS_BASES = {"makassar", "bone"}
    for kab in VALID_SORTED:
        kab_short = kab.lower().replace("kabupaten ", "").replace("kota ", "")
        if kab_short in AMBIGUOUS_BASES:
            continue
        if re.search(r'\b' + re.escape(kab_short) + r'\b', text_lower):
            return kab, 'loose'

    # Pass 3b: ambigu sebagai last resort
    for kab in VALID_SORTED:
        kab_short = kab.lower().replace("kabupaten ", "").replace("kota ", "")
        if kab_short not in AMBIGUOUS_BASES:
            continue
        if re.search(r'\b' + re.escape(kab_short) + r'\b', text_lower):
            return kab, 'loose'

    return None, None


def extract_lat_lon_from_url(url: str) -> tuple[float, float] | tuple[None, None]:
    """Ekstrak koordinat dari URL Google Maps (@lat,lon,zoom)."""
    m = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None, None


def is_in_sulawesi(lat: float, lon: float) -> bool:
    """Cek apakah koordinat berada di rentang Pulau Sulawesi (bounding box kasar)."""
    return -6.5 <= lat <= 2.5 and 119.0 <= lon <= 127.5


# ─────────────────────────────────────────────
#  VALIDASI GEOGRAFI via Nominatim
# ─────────────────────────────────────────────
_geolocator = Nominatim(user_agent="wisata_sulawesi_lokasi_v1", timeout=10)
_reverse_geo = RateLimiter(_geolocator.reverse, min_delay_seconds=NOMINATIM_DELAY, max_retries=2)


def geo_reverse_kab(lat: float, lon: float) -> str | None:
    """
    Reverse-geocode koordinat ke nama kabupaten/kota resmi Sulawesi.
    Menggunakan Nominatim (OpenStreetMap) — TIDAK bergantung pada data Google Maps.
    Return None jika gagal / koordinat di luar Sulawesi.
    """
    if not is_in_sulawesi(lat, lon):
        return None
    try:
        location = _reverse_geo(f"{lat}, {lon}", language="id")
        if not location or not location.raw:
            return None
        addr = location.raw.get("address", {})
        candidates = [
            addr.get("county", ""),
            addr.get("city", ""),
            addr.get("town", ""),
            addr.get("municipality", ""),
            addr.get("state_district", ""),
        ]
        for raw in candidates:
            raw = raw.strip()
            if not raw:
                continue
            # match_kab_dari_teks sekarang return tuple (kab, confidence)
            kab, _conf = match_kab_dari_teks(raw)
            if kab:
                return kab
    except Exception:
        pass
    return None


def dismiss_cookie(page) -> None:
    """Tutup dialog cookie/consent Google jika muncul."""
    for sel in [
        'button:has-text("Tolak semua")',
        'button:has-text("Reject all")',
        'button[aria-label*="Tolak"]',
        'form[action*="reject"] button',
    ]:
        try:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=2000):
                btn.click()
                time.sleep(0.8)
                break
        except Exception:
            pass


# ─────────────────────────────────────────────
#  CORE: scrape lokasi satu wisata
# ─────────────────────────────────────────────
def scrape_lokasi_satu(
    page,
    nama: str,
    place_id: str,
    lat_original: float | None,
    lon_original: float | None,
    delay: float,
) -> dict:
    """
    Buka Google Maps, cari tempat, baca alamat dari tab Overview.
    Return dict: {alamat_gmaps, kabupaten, provinsi, lat, lon, status}
    """
    result = {
        "alamat_gmaps": "",
        "kabupaten_gmaps": "",
        "provinsi_gmaps": "",
        "kab_dari_teks": "",   # simpan hasil teks jika berbeda dari geo
        "lat_gmaps": None,
        "lon_gmaps": None,
        "status": "FAIL",
    }

    # ── Strategi A: langsung via place_id ───────────────────
    loaded = False
    if place_id and place_id.lower() not in ("nan", "none", ""):
        try:
            url = MAPS_PID_URL.format(
                name=nama.replace(" ", "+"),
                place_id=place_id,
            )
            page.goto(url, timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
            time.sleep(2)
            loaded = True
        except Exception:
            loaded = False

    # ── Strategi B: pencarian nama ──────────────────────────
    if not loaded:
        try:
            query = f"{nama} Sulawesi".replace(" ", "+")
            page.goto(MAPS_SEARCH.format(query=query), timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
            time.sleep(2)
            # Klik hasil pertama
            first = page.locator('a[href*="/maps/place/"]').first
            if first.count() > 0:
                first.click(timeout=ELEM_TIMEOUT)
                time.sleep(2)
        except Exception:
            return result  # total gagal navigasi

    dismiss_cookie(page)

    # ── Ambil lat/lon dari URL ───────────────────────────────
    # URL Maps mengandung @lat,lon hanya SETELAH redirect selesai.
    # Polling sampai lat/lon muncul, jangan break dulu hanya karena /maps/place/ ada.
    lat_gmaps, lon_gmaps = None, None
    for _wait in range(14):           # coba tiap 0.5 detik, maks 7 detik
        time.sleep(0.5)
        current_url = page.url
        lat_try, lon_try = extract_lat_lon_from_url(current_url)
        if lat_try is not None:
            lat_gmaps, lon_gmaps = lat_try, lon_try
            break
        # Jika URL belum redirect ke maps/place sama sekali, lanjut tunggu
        # JANGAN break hanya karena '/maps/place/' ada — @lat,lon mungkin belum muncul

    # ── Koordinat final: Maps URL > lat_original (fallback Nominatim) ──
    # Koordinat untuk Nominatim: pakai Maps jika ada, fallback ke original CSV
    lat_for_geo = lat_gmaps
    lon_for_geo = lon_gmaps

    if lat_gmaps and lon_gmaps:
        # Validasi: harus di Sulawesi
        if not is_in_sulawesi(lat_gmaps, lon_gmaps):
            if lat_original and lon_original and is_in_sulawesi(lat_original, lon_original):
                # Maps buka tempat di luar Sulawesi, tapi original benar → flagging
                result["status"] = "WRONG_PLACE"
                return result
            # Koordinat Maps tidak valid sama sekali, jangan simpan
            lat_for_geo = None
            lon_for_geo = None
        else:
            result["lat_gmaps"] = lat_gmaps
            result["lon_gmaps"] = lon_gmaps
    elif lat_original and lon_original and is_in_sulawesi(float(lat_original), float(lon_original)):
        # Maps tidak kasih koordinat → pakai koordinat dari CSV original untuk Nominatim
        # (tidak disimpan ke lat_gmaps/lon_gmaps, hanya untuk validasi geo)
        lat_for_geo = float(lat_original)
        lon_for_geo = float(lon_original)

    # ── Baca alamat dari tab Overview ───────────────────────
    # Coba ambil dari elemen alamat yang khas di panel sidebar Google Maps
    alamat_text = ""

    # Selector 1: elemen address button di sidebar
    selectors_alamat = [
        'button[data-item-id="address"] .fontBodyMedium',
        '[data-item-id="address"] span.fontBodyMedium',
        'button[data-tooltip="Salin alamat"] .fontBodyMedium',
        'div[class*="rogA2c"]',      # class internal Google Maps (bisa berubah)
        'div[aria-label*="Alamat:"]',
        'div[aria-label*="Address:"]',
    ]
    for sel in selectors_alamat:
        try:
            el = page.locator(sel).first
            if el.is_visible(timeout=3000):
                alamat_text = el.inner_text().strip()
                if alamat_text:
                    break
        except Exception:
            continue

    # Selector 2: fallback — ambil dari teks yang mengandung nama kabupaten
    if not alamat_text:
        try:
            # Cari semua elemen yang isinya mirip alamat
            elems = page.locator('.fontBodyMedium').all()
            for el in elems:
                try:
                    t = el.inner_text().strip()
                    if any(k.lower() in t.lower() for k in ["kabupaten", "kota", "sulawesi", "gorontalo"]):
                        alamat_text = t
                        break
                except Exception:
                    continue
        except Exception:
            pass

    # Selector 3: fallback — ambil seluruh teks di bagian alamat dari aria-label
    if not alamat_text:
        try:
            aria = page.locator('[aria-label*="alamat"], [aria-label*="Alamat"]').first
            if aria.is_visible(timeout=2000):
                alamat_text = aria.get_attribute("aria-label") or ""
                alamat_text = alamat_text.replace("Alamat:", "").replace("alamat:", "").strip()
        except Exception:
            pass

    result["alamat_gmaps"] = alamat_text

    # ── Match kabupaten dari teks alamat (dengan confidence level) ──
    kab_dari_teks, teks_confidence = match_kab_dari_teks(alamat_text) if alamat_text else (None, None)

    # ── Validasi geografi via Nominatim ─────────────────────
    # Gunakan lat_for_geo (dari Maps URL atau fallback CSV) untuk reverse-geocode.
    # Ini memastikan Nominatim tetap berjalan meski Maps tidak beri koordinat baru.
    kab_dari_geo = None
    if lat_for_geo and lon_for_geo:
        kab_dari_geo = geo_reverse_kab(lat_for_geo, lon_for_geo)

    # ── Tentukan kabupaten final ─────────────────────────────
    # Resolusi konflik berdasarkan confidence teks:
    #   explicit/contextual → alamat Google Maps sudah menyebut kabupaten secara jelas
    #                         → percayai TEKS meski koordinat beda (Nominatim bisa meleset di perbatasan)
    #   loose               → hanya cocok kata biasa → percayai KOORDINAT jika konflik
    if kab_dari_geo and kab_dari_teks:
        if kab_dari_geo == kab_dari_teks:
            result["kabupaten_gmaps"] = kab_dari_geo
            result["provinsi_gmaps"]  = KAB_TO_PROV.get(kab_dari_geo, "")
            result["status"]          = "OK_GEO"
        elif teks_confidence in ('explicit', 'contextual'):
            # Teks eksplisit/kontekstual → teks lebih dipercaya dari Nominatim
            result["kabupaten_gmaps"] = kab_dari_teks
            result["provinsi_gmaps"]  = KAB_TO_PROV.get(kab_dari_teks, "")
            result["kab_dari_teks"]   = kab_dari_geo   # simpan hasil geo sebagai alternatif
            result["status"]          = "TEXT_WIN"
        else:
            # Teks hanya loose match → koordinat lebih dipercaya
            result["kabupaten_gmaps"] = kab_dari_geo
            result["provinsi_gmaps"]  = KAB_TO_PROV.get(kab_dari_geo, "")
            result["kab_dari_teks"]   = kab_dari_teks
            result["status"]          = "GEO_WIN"
    elif kab_dari_geo:
        result["kabupaten_gmaps"] = kab_dari_geo
        result["provinsi_gmaps"]  = KAB_TO_PROV.get(kab_dari_geo, "")
        result["status"]          = "OK_GEO"
    elif kab_dari_teks:
        result["kabupaten_gmaps"] = kab_dari_teks
        result["provinsi_gmaps"]  = KAB_TO_PROV.get(kab_dari_teks, "")
        result["status"]          = "OK_TEXT"
    elif alamat_text:
        result["status"] = "NO_MATCH"
    else:
        result["status"] = "NO_ADDR"

    return result


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────
def main() -> None:
    ap = argparse.ArgumentParser(description="Scrape lokasi wisata dari Google Maps Overview")
    ap.add_argument("--input",    default=INPUT_FILE)
    ap.add_argument("--output",   default=OUTPUT_FILE)
    ap.add_argument("--limit",    type=int, default=0,   help="Maks baris (0=semua)")
    ap.add_argument("--delay",    type=float, default=DEFAULT_DELAY)
    ap.add_argument("--headless", action="store_true")
    ap.add_argument("--force",    action="store_true",   help="Proses ulang meski sudah ada hasil")
    args = ap.parse_args()

    _TS = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(BASE_DIR, f"log_scrape_lokasi_{_TS}.txt")  # log disimpan di folder lokasi_gmaps
    sys.stdout = LoggerWriter(log_file)
    sys.stderr = sys.stdout

    print("=" * 65)
    print("  SCRAPE LOKASI WISATA DARI GOOGLE MAPS")
    print("=" * 65)

    if not os.path.isfile(args.input):
        print(f"[ERROR] File input tidak ditemukan: {args.input}")
        sys.exit(1)

    df = pd.read_csv(args.input, encoding="utf-8-sig")
    print(f"[INPUT]  {args.input} ({len(df)} baris)")
    print(f"[OUTPUT] {args.output}")

    # ── Fitur Resume: baca progress tersimpan ───────────────
    # Output menyimpan: place_id, kabupaten_gmaps, provinsi_gmaps, alamat_gmaps, lat_gmaps, lon_gmaps, status
    done_pids: dict = {}  # place_id -> row dict
    if os.path.exists(args.output):
        try:
            df_prog = pd.read_csv(args.output)
            for _, r in df_prog.iterrows():
                pid = str(r.get("place_id", "")).strip()
                if pid:
                    done_pids[pid] = r.to_dict()
            print(f"[RESUME] {len(done_pids)} entri sudah diproses sebelumnya")
        except Exception as e:
            print(f"[WARN] Gagal baca progress: {e}")

    # Kolom output baru di df
    for col in ["kabupaten_gmaps", "provinsi_gmaps", "kab_dari_teks", "alamat_gmaps", "lat_gmaps", "lon_gmaps", "status_gmaps"]:
        if col not in df.columns:
            df[col] = ""

    # Paksa kolom numerik ke dtype object agar bisa menyimpan float MAUPUN None
    # (pandas kadang infer sebagai StringDtype jika semua nilai awal adalah string "")
    df["lat_gmaps"] = df["lat_gmaps"].astype(object)
    df["lon_gmaps"] = df["lon_gmaps"].astype(object)

    # Pre-fill dari resume
    for i, row in df.iterrows():
        pid = str(row.get("place_id", "")).strip()
        if pid in done_pids:
            saved = done_pids[pid]
            df.at[i, "kabupaten_gmaps"]  = str(saved.get("kabupaten_gmaps", "") or "")
            df.at[i, "provinsi_gmaps"]   = str(saved.get("provinsi_gmaps", "") or "")
            df.at[i, "alamat_gmaps"]     = str(saved.get("alamat_gmaps", "") or "")
            df.at[i, "kab_dari_teks"]    = str(saved.get("kab_dari_teks", "") or "")
            df.at[i, "status_gmaps"]     = str(saved.get("status_gmaps", "") or "")
            # lat/lon disimpan sebagai float atau None
            lat_v = saved.get("lat_gmaps", None)
            lon_v = saved.get("lon_gmaps", None)
            df.at[i, "lat_gmaps"] = float(lat_v) if lat_v is not None and str(lat_v) not in ("", "nan") else None
            df.at[i, "lon_gmaps"] = float(lon_v) if lon_v is not None and str(lon_v) not in ("", "nan") else None

    def save_output():
        out_cols = [
            "place_id", "nama_wisata", "kabupaten", "provinsi",
            "kabupaten_gmaps", "provinsi_gmaps", "kab_dari_teks",
            "alamat_gmaps", "lat_gmaps", "lon_gmaps", "status_gmaps",
        ]
        out_cols = [c for c in out_cols if c in df.columns]
        df[out_cols].to_csv(args.output, index=False, encoding="utf-8-sig")

    # ── Graceful shutdown ────────────────────────────────────
    def _handle_sigint(sig, frame):
        print("\n[STOP] Ctrl+C! Menyimpan progress darurat...")
        try:
            save_output()
            print(f"       [OK] Tersimpan di {args.output}")
        except Exception as e:
            print(f"       [ERR] {e}")
        os._exit(0)

    signal.signal(signal.SIGINT, _handle_sigint)

    n_ok = n_skip = n_fail = n_no_addr = 0
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

        # Buka Maps dulu untuk set cookie
        try:
            page.goto("https://www.google.com/maps", timeout=NAV_TIMEOUT, wait_until="domcontentloaded")
            time.sleep(2)
            dismiss_cookie(page)
        except Exception as e:
            print(f"[WARN] Gagal buka Google Maps awal: {e}")

        for idx, row in df.iterrows():
            if args.limit and processed >= args.limit:
                break

            nama     = str(row.get("nama_wisata", "")).strip()
            place_id = str(row.get("place_id", "")).strip()
            lat_ori  = row.get("lat", None)
            lon_ori  = row.get("long", None)

            if not nama:
                continue

            # Skip jika sudah berhasil di-scrape (kecuali --force)
            status_lama = str(row.get("status_gmaps", "")).strip()
            kab_lama    = str(row.get("kabupaten_gmaps", "")).strip()
            sudah_ok    = (status_lama in ("OK_GEO", "OK_TEXT", "GEO_WIN", "TEXT_WIN") and kab_lama not in ("", "nan"))

            if sudah_ok and not args.force:
                n_skip += 1
                continue

            processed += 1
            print(f"[{idx+1:>5}] {nama[:55]}", end=" → ", flush=True)

            try:
                lat_ori_f = float(lat_ori) if lat_ori and str(lat_ori) not in ("nan", "") else None
                lon_ori_f = float(lon_ori) if lon_ori and str(lon_ori) not in ("nan", "") else None

                res = scrape_lokasi_satu(page, nama, place_id, lat_ori_f, lon_ori_f, args.delay)
            except Exception as e:
                res = {"status": "ERROR", "kabupaten_gmaps": "", "provinsi_gmaps": "",
                       "alamat_gmaps": "", "lat_gmaps": None, "lon_gmaps": None}
                print(f"ERROR: {e}")

            # Tulis ke df — pastikan semua nilai scalar (bukan tuple/list)
            def _s(v):
                """Paksa nilai menjadi string scalar yang aman untuk pandas."""
                if v is None or (isinstance(v, float) and v != v):
                    return ""
                if isinstance(v, (list, tuple)):
                    return str(v[0]) if v else ""
                return str(v)

            df.at[idx, "kabupaten_gmaps"] = _s(res.get("kabupaten_gmaps", ""))
            df.at[idx, "provinsi_gmaps"]  = _s(res.get("provinsi_gmaps", ""))
            df.at[idx, "kab_dari_teks"]   = _s(res.get("kab_dari_teks", ""))
            df.at[idx, "alamat_gmaps"]    = _s(res.get("alamat_gmaps", ""))
            df.at[idx, "status_gmaps"]    = _s(res.get("status", ""))
            # lat/lon tetap numeric atau None
            df.at[idx, "lat_gmaps"]  = res.get("lat_gmaps") if isinstance(res.get("lat_gmaps"), (int, float)) else None
            df.at[idx, "lon_gmaps"]  = res.get("lon_gmaps") if isinstance(res.get("lon_gmaps"), (int, float)) else None

            st = res["status"]
            if st in ("OK_GEO", "OK_TEXT"):
                n_ok += 1
                print(f"{st}  → {res['kabupaten_gmaps']}")
            elif st == "GEO_WIN":
                n_ok += 1
                print(f"GEO_WIN   → {res['kabupaten_gmaps']} (teks bilang: {res.get('kab_dari_teks', '?')})")
            elif st == "TEXT_WIN":
                n_ok += 1
                print(f"TEXT_WIN  → {res['kabupaten_gmaps']} (geo bilang: {res.get('kab_dari_teks', '?')})")
            elif st == "NO_ADDR":
                n_no_addr += 1
                print("NO_ADDR (tidak ada info alamat)")
            else:
                n_fail += 1
                print(f"{st}")

            # Auto-save
            if processed % AUTOSAVE_INTERVAL == 0:
                save_output()
                print(f"    [SAVE] auto-save ({processed} diproses, {n_ok} OK)")

            time.sleep(max(1.0, args.delay))

        try:
            browser.close()
        except Exception:
            pass

    # Final save
    save_output()

    print("\n" + "=" * 65)
    print("  SELESAI!")
    print(f"  Output      : {args.output}")
    print(f"  OK (geo+teks confirm) + GEO_WIN : {n_ok}")
    print(f"  No Alamat   : {n_no_addr}")
    print(f"  Gagal/Lain  : {n_fail}")
    print(f"  Dilewati    : {n_skip}")
    print(f"  Diproses    : {processed}")
    print("=" * 65)


if __name__ == "__main__":
    main()
