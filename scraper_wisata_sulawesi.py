"""
==============================================================================
  Scraper Data Wisata Pulau Sulawesi  v4
  Menggunakan Google Maps Places API (Text Search + Nearby Search)

  Arsitektur pengambilan data:
  ┌─ Provinsi (6)
  │   └─ Kabupaten/Kota (83 total)
  │       └─ Keyword (10)  →  query "{keyword} di {kabupaten}"

  Fitur:
  - Loop bertingkat: Provinsi → Kab/Kota → Keyword
  - Nearby Search per pusat kabupaten (koordinat ibu kota kab/kota)
  - Nama file CSV otomatis dengan timestamp agar tidak menimpa data lama
  - Deduplikasi berbasis place_id
  - Klasifikasi 6 kategori wisata
  - Filtering relevansi wisata
  - Delay 2 detik antar request (anti-spam)
  - Logging ke konsol + file

  Output: wisata_sulawesi_YYYYMMDD_HHMMSS.csv

  Kunci API:
  - Wajib set environment variable GOOGLE_MAPS_API_KEY (jangan hardcode di repo).
  - Kolom `photo_reference` disimpan agar URL foto bisa dibentuk ulang dengan kunci baru.
  - Kolom `image` berisi URL lengkap Place Photo hanya saat scrape (butuh kunci aktif);
    jika kunci tidak ada, `image` dikosongkan — gunakan `photo_reference` di backend.
==============================================================================
"""

import requests
import pandas as pd
import time
import logging
import os
import sys
from datetime import datetime

# ═══════════════════════════════════════════════════════
#  KONFIGURASI
# ═══════════════════════════════════════════════════════
API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "").strip()

TEXT_SEARCH_URL   = "https://maps.googleapis.com/maps/api/place/textsearch/json"
NEARBY_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
PHOTO_BASE_URL    = "https://maps.googleapis.com/maps/api/place/photo"
MAX_WIDTH_PHOTO   = 800


def build_place_photo_url(photo_ref: str) -> str:
    """URL Place Photo; kosong jika tidak ada referensi atau GOOGLE_MAPS_API_KEY."""
    if not photo_ref or not API_KEY:
        return ""
    return (
        f"{PHOTO_BASE_URL}?maxwidth={MAX_WIDTH_PHOTO}"
        f"&photoreference={photo_ref}&key={API_KEY}"
    )

DELAY_BETWEEN_REQUESTS = 2   # detik antar setiap request

# Nama file CSV otomatis dengan timestamp agar tidak menimpa file lama
_TS = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"wisata_sulawesi_{_TS}.csv"
LOG_FILE    = f"scraper_log_{_TS}.txt"

# ═══════════════════════════════════════════════════════
#  LOGGING
# ═══════════════════════════════════════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════
#  KEYWORD PENCARIAN
# ═══════════════════════════════════════════════════════
KEYWORDS = [
    "tempat wisata",
    "pantai",
    "air terjun",
    "gunung",
    "danau",
    "bukit",
    "wisata alam",
    "wisata sejarah",
    "desa wisata",
    "wisata bahari",
]


# ═══════════════════════════════════════════════════════
#  DATA PROVINSI → KABUPATEN/KOTA
#  Lengkap 83 kab/kota di Pulau Sulawesi
#  Format: {nama_provinsi: [(nama_kab_kota, lat_ibukota, lng_ibukota, radius_m), ...]}
# ═══════════════════════════════════════════════════════
PROVINSI_KAB = {

    # ── SULAWESI SELATAN (24 kab/kota) ─────────────────────────
    "Sulawesi Selatan": [
        ("Makassar",                  -5.1477,  119.4327, 12000),
        ("Gowa",                      -5.2268,  119.5319, 15000),
        ("Maros",                     -5.0037,  119.5738, 15000),
        ("Takalar",                   -5.4280,  119.3892, 12000),
        ("Pangkajene Kepulauan",      -4.8339,  119.5320, 15000),
        ("Barru",                     -4.4085,  119.6218, 12000),
        ("Parepare",                  -4.0135,  119.6298, 10000),
        ("Pinrang",                   -3.7920,  119.6521, 12000),
        ("Sidenreng Rappang",         -3.9488,  119.9274, 12000),
        ("Wajo",                      -4.1518,  120.0280, 12000),
        ("Bone",                      -4.5355,  120.3285, 15000),
        ("Soppeng",                   -4.3478,  119.8924, 12000),
        ("Bulukumba",                 -5.5518,  120.2057, 15000),
        ("Bantaeng",                  -5.5265,  119.9603, 12000),
        ("Jeneponto",                 -5.5985,  119.7447, 12000),
        ("Sinjai",                    -5.1250,  120.2533, 12000),
        ("Selayar",                   -6.1082,  120.4491, 15000),
        ("Tana Toraja",               -3.0458,  119.8621, 20000),
        ("Toraja Utara",              -2.9668,  119.9058, 18000),
        ("Enrekang",                  -3.5144,  119.7817, 15000),
        ("Luwu",                      -2.9831,  120.5671, 15000),
        ("Luwu Utara",                -2.5653,  120.5768, 15000),
        ("Luwu Timur",                -2.6052,  121.2700, 15000),
        ("Palopo",                    -2.9929,  120.1940, 10000),
    ],

    # ── SULAWESI UTARA (15 kab/kota) ───────────────────────────
    "Sulawesi Utara": [
        ("Manado",                     1.4748,  124.8421, 12000),
        ("Bitung",                     1.4419,  125.1986, 10000),
        ("Tomohon",                    1.3228,  124.8378, 10000),
        ("Kotamobagu",                 0.7282,  124.3049, 10000),
        ("Minahasa",                   1.2979,  124.8311, 15000),
        ("Minahasa Utara",             1.5614,  124.9142, 12000),
        ("Minahasa Selatan",           1.0226,  124.6237, 15000),
        ("Minahasa Tenggara",          0.9124,  124.8395, 12000),
        ("Bolaang Mongondow",          0.5670,  124.0167, 15000),
        ("Bolaang Mongondow Utara",    0.9877,  123.8861, 12000),
        ("Bolaang Mongondow Selatan",  0.3500,  124.0000, 12000),
        ("Bolaang Mongondow Timur",    0.5000,  124.5000, 12000),
        ("Kepulauan Sangihe",          3.5745,  125.4781, 15000),
        ("Kepulauan Sitaro",           2.7745,  125.4148, 12000),
        ("Kepulauan Talaud",           4.3372,  126.7892, 12000),
    ],

    # ── SULAWESI TENGAH (13 kab/kota) ──────────────────────────
    "Sulawesi Tengah": [
        ("Palu",                      -0.8917,  119.8707, 12000),
        ("Donggala",                  -0.7697,  119.7474, 15000),
        ("Sigi",                      -1.1558,  119.8942, 15000),
        ("Parigi Moutong",            -0.7866,  120.1703, 15000),
        ("Poso",                      -1.3953,  120.7550, 15000),
        ("Tojo Una-Una",              -0.7014,  121.6131, 15000),
        ("Morowali",                  -2.4934,  121.9475, 15000),
        ("Morowali Utara",            -1.8567,  121.7028, 15000),
        ("Banggai",                   -0.9405,  122.7910, 15000),
        ("Banggai Laut",              -1.6580,  123.4872, 12000),
        ("Banggai Kepulauan",         -1.5782,  123.5000, 15000),
        ("Buol",                       1.0993,  121.4547, 12000),
        ("Tolitoli",                   1.0418,  120.7952, 12000),
    ],

    # ── SULAWESI TENGGARA (17 kab/kota) ────────────────────────
    "Sulawesi Tenggara": [
        ("Kendari",                   -3.9985,  122.5138, 12000),
        ("Baubau",                    -5.4600,  122.6196, 10000),
        ("Konawe",                    -3.9773,  122.6193, 15000),
        ("Konawe Selatan",            -4.4091,  122.4538, 15000),
        ("Konawe Utara",              -3.4090,  122.4020, 15000),
        ("Konawe Kepulauan",          -3.9565,  123.0956, 12000),
        ("Kolaka",                    -4.0475,  121.5815, 12000),
        ("Kolaka Utara",              -3.4560,  121.3660, 12000),
        ("Kolaka Timur",              -4.2889,  121.7920, 12000),
        ("Bombana",                   -5.2300,  121.8820, 12000),
        ("Muna",                      -4.8298,  122.7239, 15000),
        ("Muna Barat",                -4.9220,  122.4680, 12000),
        ("Buton",                     -5.4520,  122.7440, 15000),
        ("Buton Selatan",             -5.5800,  122.7500, 12000),
        ("Buton Tengah",              -5.0900,  122.7300, 12000),
        ("Buton Utara",               -4.8400,  122.9300, 12000),
        ("Wakatobi",                  -5.5006,  123.5770, 15000),
    ],

    # ── SULAWESI BARAT (6 kab/kota) ────────────────────────────
    "Sulawesi Barat": [
        ("Mamuju",                    -2.6671,  118.8886, 12000),
        ("Mamuju Tengah",             -2.1300,  119.3100, 12000),
        ("Mamuju Utara",              -1.4500,  119.4400, 12000),
        ("Majene",                    -3.5424,  118.9690, 12000),
        ("Polewali Mandar",           -3.4222,  119.3366, 12000),
        ("Mamasa",                    -3.0000,  119.3900, 15000),
    ],

    # ── GORONTALO (6 kab/kota) ─────────────────────────────────
    "Gorontalo": [
        ("Gorontalo Kota",             0.5435,  123.0594, 10000),
        ("Gorontalo Kabupaten",        0.5000,  122.9000, 15000),
        ("Bone Bolango",               0.5570,  123.2100, 12000),
        ("Pohuwato",                   0.7438,  122.1000, 15000),
        ("Boalemo",                    0.4465,  122.4503, 12000),
        ("Gorontalo Utara",            0.8700,  122.8900, 12000),
    ],
}


# ═══════════════════════════════════════════════════════
#  KLASIFIKASI KATEGORI
# ═══════════════════════════════════════════════════════
KATEGORI_RULES = {
    "Wisata Alam": [
        "pantai", "beach", "laut", "sea", "ocean",
        "gunung", "mountain", "hill", "bukit",
        "air terjun", "waterfall", "danau", "lake",
        # "park" SENGAJA TIDAK di sini — taman kota/buatan → Wisata Hiburan
        # Hanya taman alam/nasional yang tetap di sini:
        "taman nasional", "national_park", "nature_reserve", "cagar alam",
        "hutan", "forest", "snorkeling", "diving",
        "sungai", "river", "gua", "cave", "pulau", "island",
        "natural_feature", "bahari",
        "agrowisata", "perkebunan", "batu",
    ],
    "Wisata Budaya & Sejarah": [
        "museum", "sejarah", "history", "historical",
        "benteng", "fort", "candi",
        "heritage", "warisan", "budaya", "culture",
        "traditional", "adat", "istana", "palace",
        "monumen", "monument", "peninggalan", "situs",
        "tongkonan", "rumah adat", "makam raja",
    ],
    "Wisata Religi": [
        "masjid", "mosque", "gereja", "church",
        "pura", "temple", "vihara", "klenteng",
        "ziarah", "pilgrimage", "makam", "tomb",
        "place_of_worship",
    ],
    "Wisata Buatan / Hiburan": [
        # Taman buatan/kota (park yang bukan alam)
        "park",                     # tipe Google Maps untuk taman kota
        "taman kota", "taman publik", "taman bermain", "taman hiburan",
        "taman rekreasi", "taman bunga", "taman wisata alam",
        # Hiburan & wahana
        "theme_park", "amusement_park", "water_park",
        "wahana", "resort", "kebun binatang",
        "zoo", "akuarium", "aquarium", "stadium",
        "entertainment", "hiburan",
    ],
    "Wisata Kota / Landmark": [
        "landmark", "tourist_attraction", "observation",
        "menara", "tower", "jembatan", "bridge",
        "alun-alun", "plaza", "square",
        "tugu", "sculpture", "art_gallery", "gallery",
        "point_of_interest",
    ],
    "Wisata Belanja/Kuliner": [
        "pasar", "market", "mall", "shopping",
        "kuliner", "food", "restaurant", "cafe",
        "oleh-oleh", "souvenir", "bazaar",
    ],
}


def klasifikasi_kategori(name: str, types: list) -> str:
    """Klasifikasi otomatis berdasarkan nama dan tipe Google Maps."""
    combined = f"{name.lower() if name else ''} {' '.join(types).lower() if types else ''}"
    for kategori, kws in KATEGORI_RULES.items():
        if any(kw in combined for kw in kws):
            return kategori
    if "tourist_attraction" in combined or "point_of_interest" in combined:
        return "Wisata Kota / Landmark"
    # Fallback netral — tidak lagi diasumsikan "Wisata Alam"
    return "Wisata Kota / Landmark"


# ═══════════════════════════════════════════════════════
#  FILTER RELEVANSI  (3 lapis)
#
#  Lapis 1 – BLACKLIST TIPE: Langsung tolak jika Google Maps
#            mengklasifikasikan tempat sebagai bukan-wisata.
#
#  Lapis 2 – WHITELIST TIPE: Lolos jika memiliki salah satu
#            tipe yang memang khusus untuk tempat wisata.
#            → 'establishment' & 'point_of_interest' TIDAK dimasukkan
#              karena hampir semua tempat (kost, sekolah, dll.) memilikinya.
#
#  Lapis 3 – WHITELIST NAMA: Lolos jika nama tempat mengandung
#            kata yang spesifik menunjuk ke objek wisata.
#            → Kata-kata umum seperti 'gunung', 'bukit', 'danau'
#              TIDAK dimasukkan karena sering muncul sebagai nama
#              kelurahan/perumahan (mis. "Gunung Sari", "Bukit Baruga").
# ═══════════════════════════════════════════════════════

# ── Lapis 1: Langsung TOLAK jika ada tipe ini ────────────
BLACKLIST_TYPES = {
    # Pendidikan
    "school", "university", "primary_school", "secondary_school",
    # Kesehatan
    "hospital", "doctor", "pharmacy", "dentist", "physiotherapist",
    "veterinary_care", "health",
    # Perumahan & properti
    "real_estate_agency",
    # Keuangan
    "bank", "atm", "finance", "accounting", "insurance_agency",
    # Layanan umum
    "local_government_office", "post_office", "police", "fire_station",
    "courthouse", "embassy",
    # Otomotif
    "car_dealer", "car_rental", "car_repair", "car_wash", "gas_station",
    "parking",
    # Transportasi
    "bus_station", "train_station", "taxi_stand", "airport",
    "transit_station", "subway_station",
    # Lainnya
    "laundry", "storage", "moving_company", "funeral_home",
    "electrician", "plumber", "painter",
}

# Kata negatif di NAMA tempat → langsung tolak
BLACKLIST_NAME_KW = {
    # Pendidikan
    "sekolah", "sma ", "smp ", "sd ", "smk ", "smea",
    "universitas", "univ ", "kampus", "akademi", "politeknik",
    "madrasah", "pesantren", "pondok pesantren", "tk ", "paud",
    "bimbel", "les privat",
    # Penginapan bukan wisata
    "kost", "kos ", "kontrakan", "indekost",
    # Kesehatan
    "klinik", "puskesmas", "apotek", "apotik", "rumah sakit",
    "rs ", "rsia", "rsu ", "praktek dokter", "laboratorium",
    # Kantor & instansi
    "kantor ", "dinas ", "badan ", "kecamatan ", "kelurahan ",
    "balai ", "uptd", "uptb", "samsat", "bpjs", "polres", "polsek",
    "koramil", "kodim",
    # Properti & bisnis
    "perumahan", "kavling", "ruko ", "rukan", "showroom",
    "bengkel", "tambal ban", "spbu", "pertamina",
    # Layanan masyarakat
    "bank ", "atm ", "minimarket", "alfamart", "indomaret",
    "pom bensin", "laundry",
}

# ── Lapis 2: WHITELIST TIPE (spesifik wisata) ─────────────
TOURISM_TYPES = {
    "tourist_attraction",   # tag utama Google untuk wisata
    "natural_feature",      # gunung, danau, air terjun, dll.
    "park",                 # taman nasional, taman kota wisata
    "campground",           # area camping
    "amusement_park",       # taman hiburan
    "aquarium",
    "art_gallery",
    "museum",
    "place_of_worship",     # masjid/gereja/pura bersejarah/wisata religi
    "stadium",
    "zoo",
    "rv_park",
    "lodging",              # resort / penginapan wisata (bukan kost)
}

# ── Lapis 3: WHITELIST NAMA (kata spesifik wisata) ────────
# Hanya kata yang betul-betul menunjuk ke objek wisata,
# bukan nama wilayah/kelurahan yang kebetulan pakai kata tersebut.
TOURISM_KW_FILTER = {
    # Kata langsung = wisata
    "wisata", "objek wisata", "agrowisata", "ekowisata",
    "pariwisata", "desa wisata", "kampung wisata",
    # Jenis alam yang spesifik (bukan sekadar nama wilayah)
    "pantai ", "pantai",    # pantai + spasi agar tidak cocok 'pantaiceria'
    "air terjun", "waterfall",
    "taman nasional", "taman wisata", "taman laut",
    "cagar alam", "suaka",
    "snorkeling", "diving", "selam",
    "bahari",
    # Jenis buatan/budaya
    "benteng", "fort", "istana", "keraton",
    "museum", "monumen", "tugu wisata",
    "situs ", "peninggalan", "warisan", "heritage",
    "tongkonan", "rumah adat",
    # Landmark & rekreasi
    "taman rekreasi", "taman bermain", "wahana",
    "kebun raya", "kebun binatang", "akuarium",
    "menara pandang", "gardu pandang", "bukit pandang",
    "dermaga wisata", "jembatan gantung",
    # Religi wisata
    "makam raja", "makam wali", "ziarah",
}


def _is_blacklisted(name: str, types: list) -> bool:
    """
    Mengembalikan True jika tempat JELAS BUKAN objek wisata.
    Pengecekan dilakukan dari yang paling ketat (tipe) ke nama.
    """
    types_set = set(types)

    # Tolak jika ada tipe blacklist (hanya berlaku jika TIDAK ada
    # tipe whitelist — mis. masjid bersejarah tetap lolos)
    if types_set & BLACKLIST_TYPES and not types_set & TOURISM_TYPES:
        return True

    # Tolak jika nama mengandung kata blacklist
    name_lower = name.lower()
    if any(kw in name_lower for kw in BLACKLIST_NAME_KW):
        # Pengecualian: tetap lolos jika punya tipe wisata eksplisit
        if not types_set & {"tourist_attraction", "natural_feature",
                             "park", "museum", "art_gallery", "zoo"}:
            return True

    return False


def filter_data(raw: list) -> list:
    """
    Filter 3 lapis:
    1. Buang jika tidak punya koordinat.
    2. Buang jika blacklisted (jelas bukan wisata).
    3. Simpan jika punya tipe wisata ATAU nama mengandung kata wisata spesifik.
    """
    out = []
    for item in raw:
        types = item.get("types", [])
        name  = item.get("name", "")
        loc   = item.get("geometry", {}).get("location", {})

        # Lapis 0: wajib punya koordinat
        if not (loc.get("lat") and loc.get("lng")):
            continue

        # Lapis 1: blacklist — buang yang jelas bukan wisata
        if _is_blacklisted(name, types):
            continue

        # Lapis 2 & 3: whitelist tipe ATAU kata kunci nama
        has_tourism_type = bool(set(types) & TOURISM_TYPES)
        has_tourism_name = any(kw in name.lower() for kw in TOURISM_KW_FILTER)

        if has_tourism_type or has_tourism_name:
            out.append(item)

    return out


# ═══════════════════════════════════════════════════════
#  PARSING
# ═══════════════════════════════════════════════════════
def parse_result(item: dict) -> dict:
    """Mengekstrak semua kolom yang dibutuhkan dari satu result Google Places."""
    loc       = item.get("geometry", {}).get("location", {})
    photos    = item.get("photos", [])
    photo_ref = photos[0].get("photo_reference", "") if photos else ""
    return {
        "nama_wisata"      : item.get("name", ""),
        "alamat"           : item.get("formatted_address") or item.get("vicinity", ""),
        "rating"           : item.get("rating", None),
        "jumlah_review"    : item.get("user_ratings_total", None),
        "kategori"         : klasifikasi_kategori(item.get("name", ""), item.get("types", [])),
        "photo_reference"  : photo_ref,
        "image"            : build_place_photo_url(photo_ref),
        "lat"              : loc.get("lat"),
        "long"             : loc.get("lng"),
        "place_id"         : item.get("place_id", ""),
    }


# ═══════════════════════════════════════════════════════
#  HTTP HELPERS
# ═══════════════════════════════════════════════════════
def _safe_get(url: str, params: dict) -> dict:
    """Wrapper request dengan penanganan error sederhana."""
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        log.warning(f"      ✗ Request gagal: {e}")
        return {}


def get_text_search(query: str) -> list:
    """
    Text Search API – satu halaman (maks 20 hasil).
    next_page_token tidak digunakan karena tidak aktif pada key ini.
    """
    data = _safe_get(TEXT_SEARCH_URL, {
        "query"   : query,
        "key"     : API_KEY,
        "language": "id",
    })
    status = data.get("status", "")
    if status not in ("OK", "ZERO_RESULTS", ""):
        log.warning(f"      ✗ API Status: {status}")
    return data.get("results", [])


def get_nearby_search(lat: float, lng: float, radius: int, keyword: str = "") -> list:
    """
    Nearby Search API – satu halaman (maks 20 hasil).
    Mencari tourist_attraction di sekitar koordinat ibukota kabupaten.
    """
    params = {
        "location": f"{lat},{lng}",
        "radius"  : radius,
        "type"    : "tourist_attraction",
        "key"     : API_KEY,
        "language": "id",
    }
    if keyword:
        params["keyword"] = keyword
    data = _safe_get(NEARBY_SEARCH_URL, params)
    return data.get("results", [])


# ═══════════════════════════════════════════════════════
#  DATA CLEANING
# ═══════════════════════════════════════════════════════
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Membersihkan DataFrame:
    - Deduplikasi berdasarkan place_id dan kombinasi nama+alamat
    - Isi nilai kosong
    - Pastikan lat/long tidak kosong
    """
    log.info(f"  [CLEAN] Sebelum : {len(df)} baris")
    df = df.drop_duplicates(subset=["place_id"],           keep="first")
    df = df.drop_duplicates(subset=["nama_wisata", "alamat"], keep="first")
    df = df.dropna(subset=["lat", "long"])
    df["rating"]        = df["rating"].fillna(0.0)
    df["jumlah_review"] = df["jumlah_review"].fillna(0).astype(int)
    df["photo_reference"] = df["photo_reference"].fillna("")
    df["image"]           = df["image"].fillna("")
    df["alamat"]        = df["alamat"].fillna("Tidak diketahui")
    df["kategori"]      = df["kategori"].fillna("Wisata Alam")
    df = df.reset_index(drop=True)
    log.info(f"  [CLEAN] Sesudah : {len(df)} baris")
    return df


# ═══════════════════════════════════════════════════════
#  HELPER: TAMBAH DATA BARU
# ═══════════════════════════════════════════════════════
def _add_new(raw: list, all_raw: list, seen: set) -> int:
    """
    Filter data, deduplikasi, dan tambahkan ke all_raw.
    Mengembalikan jumlah data baru yang ditambahkan.
    """
    added = 0
    for item in filter_data(raw):
        pid = item.get("place_id", "")
        if pid and pid not in seen:
            seen.add(pid)
            all_raw.append(item)
            added += 1
    return added


# ═══════════════════════════════════════════════════════
#  MAIN PIPELINE
# ═══════════════════════════════════════════════════════
def main():
    if not API_KEY:
        log.error(
            "GOOGLE_MAPS_API_KEY tidak di-set. Contoh (PowerShell):\n"
            '  $env:GOOGLE_MAPS_API_KEY = "KUNCI_ANDA"\n'
            "  python scraper_wisata_sulawesi.py"
        )
        sys.exit(1)

    log.info("=" * 65)
    log.info("  SCRAPER WISATA SULAWESI v4 – Provinsi → Kab/Kota → Keyword")
    log.info(f"  Mulai   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"  Output  : {OUTPUT_FILE}")
    log.info("  API key : dari variabel lingkungan GOOGLE_MAPS_API_KEY (aktif)")
    log.info("=" * 65)

    all_raw: list = []
    seen   : set  = set()

    total_prov = len(PROVINSI_KAB)

    # ─────────────────────────────────────────────────────────────
    #  LOOP UTAMA: Provinsi → Kabupaten/Kota → Keyword
    # ─────────────────────────────────────────────────────────────
    for p_idx, (provinsi, kab_list) in enumerate(PROVINSI_KAB.items(), 1):
        total_kab = len(kab_list)
        log.info(f"\n{'═'*65}")
        log.info(f"  PROVINSI [{p_idx}/{total_prov}]: {provinsi} ({total_kab} kab/kota)")
        log.info(f"{'═'*65}")

        for k_idx, (kab_nama, lat, lng, radius) in enumerate(kab_list, 1):
            log.info(f"\n  ── Kab/Kota [{k_idx}/{total_kab}]: {kab_nama}")

            # ── A. Text Search: keyword di kabupaten ──────────────
            for keyword in KEYWORDS:
                query = f"{keyword} di {kab_nama}"
                raw   = get_text_search(query)
                added = _add_new(raw, all_raw, seen)
                if added:
                    log.info(f"     📍 '{query}' → +{added} (total: {len(all_raw)})")
                time.sleep(DELAY_BETWEEN_REQUESTS)

            # ── B. Nearby Search: tourist_attraction (tanpa keyword) ─
            raw   = get_nearby_search(lat, lng, radius)
            added = _add_new(raw, all_raw, seen)
            if added:
                log.info(f"     📍 Nearby [{kab_nama}] → +{added} (total: {len(all_raw)})")
            time.sleep(DELAY_BETWEEN_REQUESTS)

            # ── C. Nearby Search dengan keyword "wisata" ──────────
            raw   = get_nearby_search(lat, lng, radius, keyword="wisata")
            added = _add_new(raw, all_raw, seen)
            if added:
                log.info(f"     📍 Nearby wisata [{kab_nama}] → +{added} (total: {len(all_raw)})")
            time.sleep(DELAY_BETWEEN_REQUESTS)

            # ── D. Nearby Search dengan keyword "pantai" ───────────
            raw   = get_nearby_search(lat, lng, radius, keyword="pantai")
            added = _add_new(raw, all_raw, seen)
            if added:
                log.info(f"     📍 Nearby pantai [{kab_nama}] → +{added} (total: {len(all_raw)})")
            time.sleep(DELAY_BETWEEN_REQUESTS)

        log.info(f"\n  ✓ Selesai {provinsi} | Total sementara: {len(all_raw)} data")

    # ─────────────────────────────────────────────────────────────
    #  PARSING, CLEANING & SIMPAN
    # ─────────────────────────────────────────────────────────────
    log.info(f"\n{'═'*65}")
    log.info(f"  Total data mentah unik terkumpul: {len(all_raw)}")

    if not all_raw:
        log.error("  Tidak ada data yang terkumpul. Script dihentikan.")
        return

    log.info("  Memulai parsing & cleaning ...")
    df = pd.DataFrame([parse_result(item) for item in all_raw])
    df = clean_data(df)

    # Urutan kolom output
    cols_order = [
        "nama_wisata", "alamat", "rating", "jumlah_review",
        "kategori", "photo_reference", "image", "lat", "long", "place_id",
    ]
    df = df[[c for c in cols_order if c in df.columns]]

    df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    # ─────────────────────────────────────────────────────────────
    #  RINGKASAN AKHIR
    # ─────────────────────────────────────────────────────────────
    log.info(f"\n{'═'*65}")
    log.info(f"  ✅ File disimpan : {OUTPUT_FILE}")
    log.info(f"  📊 Total data   : {len(df)} baris")
    log.info(f"  📑 Distribusi Kategori:")
    for kat, count in df["kategori"].value_counts().items():
        bar = "█" * (count // 10)
        log.info(f"     {kat:<35} {count:>5}  {bar}")

    log.info(f"\n  Rating tersedia      : {(df['rating'] > 0).sum()} data")
    log.info(f"  photo_reference isi  : {(df['photo_reference'] != '').sum()} data")
    log.info(f"  URL image (siap pakai): {(df['image'] != '').sum()} data")

    if len(df) >= 1000:
        log.info(f"\n  🎉 Target 1000 data TERCAPAI! ({len(df)} baris)")
    else:
        log.warning(f"\n  ⚠ Target belum tercapai ({len(df)}/1000).")

    log.info(f"\n  Selesai : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 65)


# ═══════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    main()
