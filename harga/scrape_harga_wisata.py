"""
scrape_harga_wisata.py  (v5 – Context-Aware + pipeline)
======================================================
Script untuk menambahkan kolom `harga_rp` dan `kategori_harga` ke dataset
wisata Pulau Sulawesi menggunakan sistem pencarian bertingkat.

Perbaikan v4:
  - Ekstraksi harga berbasis konteks: hanya ambil angka yang berada
    dekat kata kunci "tiket / masuk / HTM / biaya" (±200 karakter)
  - Tolak angka yang berada dekat kata akomodasi (hotel/kamar/malam/dll)
  - Batas harga wajar per kategori wisata
  - Ambil harga terkecil yang valid (bukan voting) → tiket masuk
    biasanya angka terkecil dalam sebuah artikel wisata
  - Deteksi gratis tetap aktif

Perbaikan v5:
  - Multi-query DDGS + wilayah id-id; retry ringan saat error DDGS
  - Query dengan place_id (jika ada) untuk mengurangi homonim
  - Skoring & penggabungan URL prioritas (go.id, pariwisata, dll.)
  - requests.Session + satu browser Playwright untuk seluruh run
  - Kolom audit: harga_sumber_url, harga_level, harga_query
  - Validasi geolokasi (jarum dari alamat) + filter URL Bali/Lombok vs Sulawesi
  - Simpan CSV sebelum menutup browser; penutupan Playwright di-swallow jika error

Level pencarian:
  L1 : DDGS snippet
  L2 : requests + BeautifulSoup (buka link hasil DDGS)
  L3 : Playwright (fallback halaman dinamis/JS-heavy)

Kategori Harga:
  0              = Gratis
  1.000 – 9.999  = Murah
  10.000 – 19.999= Sedang
  >= 20.000      = Mahal
  NULL           = Tidak Diketahui

Log:
  - Terminal : level INFO
  - File .log: level DEBUG  (logs/scrape_harga_YYYYMMDD_HHMMSS.log)

Fitur:
  - Output baru tiap run: wisata_sulawesi_harga_YYYYMMDD_HHMMSS.csv
  - Auto-save setiap AUTOSAVE_INTERVAL baris
  - Graceful shutdown (Ctrl+C): simpan data sebelum keluar
  - Resume mode: lewati baris yang harga_rp sudah terisi
"""

import logging
import os
import re
import signal
import time
from datetime import datetime
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

# Playwright opsional (fallback Level 3)
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False

# ──────────────────────────────────────────────
# KONFIGURASI PATH
# ──────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "..", "data")
HASIL_DIR  = os.path.join(BASE_DIR, "..", "hasil")
LOG_DIR    = os.path.join(BASE_DIR, "logs")

INPUT_FILE  = os.path.join(BASE_DIR, "..", "hasil_scrap", "wisata_sulawesi_cleaned_final.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "scrap_harga_wisata.csv")

DELAY_DETIK       = 2    # jeda antar baris
DELAY_L2          = 1    # jeda antar link Level 2
MAX_DDGS_RESULTS  = 5    # snippet DDGS yang diambil
MAX_MERGED_L2     = 6    # setelah gabung multi-query: maks URL dibuka L2/L3
AUTOSAVE_INTERVAL = 50   # auto-save setiap N baris
REQUEST_TIMEOUT   = 20   # timeout requests (detik)
KONTEKS_WINDOW    = 220  # radius karakter pencarian konteks
DDGS_REGION       = "id-id"  # hasil relevan Indonesia
DDGS_L1_RETRIES   = 2      # percobaan DDGS per query (termasuk pertama)
DDGS_RETRY_SLEEP  = 1.5    # jeda sebelum retry DDGS (detik)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8",
}

# ──────────────────────────────────────────────
# KATA KUNCI & FILTER
# ──────────────────────────────────────────────

# Kata yang menandai ada info harga tiket
KATA_TIKET = re.compile(
    r'\b(tiket|htm|harga masuk|harga tiket|tiket masuk|biaya masuk|'
    r'retribusi|tarif masuk|tiket dewasa|tiket anak|harga karcis|'
    r'karcis|bayar|entrance fee|admission)\b',
    re.IGNORECASE
)

# Kata yang menandai harga BUKAN tiket wisata (akomodasi/paket/dll)
KATA_AKOMODASI = re.compile(
    r'\b(hotel|villa|kamar|per malam|per malam|semalam|penginapan|'
    r'resort|homestay|hostel|guest house|losmen|paket wisata|paket tour|'
    r'tur|rental|sewa|booking|reservasi|per orang dewasa paket|'
    r'harga paket|biaya sewa|tarif sewa|tarif parkir|parkir)\b',
    re.IGNORECASE
)

# Pola gratis yang SELALU valid tanpa perlu konteks tambahan
# (frasa ini sudah eksplisit menunjuk ke tiket/masuk)
KATA_GRATIS_EKSPLISIT = re.compile(
    r'\b(tanpa[\s\-]tiket|tanpa[\s\-]biaya[\s\-]masuk|'
    r'tidak[\s\-]dipungut[\s\-]biaya|tidak[\s\-]berbayar|'
    r'masuk[\s\-]gratis|tiket[\s\-]gratis|tiket[\s\-]free|'
    r'bebas[\s\-]biaya[\s\-]masuk|no[\s\-]entrance[\s\-]fee|'
    r'free[\s\-]entry|free[\s\-]admission|free[\s\-]of[\s\-]charge)\b',
    re.IGNORECASE
)

# Kata gratis/free umum (perlu dicek konteks sekitarnya)
KATA_GRATIS_UMUM = re.compile(r'\b(gratis|free)\b', re.IGNORECASE)

# Konteks FALSE POSITIVE — jika 'gratis' dekat kata-kata ini, BUKAN gratis tiket
KATA_BUKAN_GRATIS = re.compile(
    r'\b(parkir|wifi|wi\-fi|internet|konsultasi|ongkir|ongkos[\s\-]kirim|'
    r'pengiriman|biaya[\s\-]admin|admin|promo|diskon|cashback|bonus|'
    r'foto|selfie|akses[\s\-]wifi|berlangganan|daftar|registrasi)\b',
    re.IGNORECASE
)

# Konteks NEGASI — kalimat yang menyatakan 'dulu gratis, kini bayar'
KATA_NEGASI_GRATIS = re.compile(
    r'\b(dulu[\s\w]{0,20}gratis|sebelumnya[\s\w]{0,20}gratis|'
    r'sudah[\s\w]{0,10}tidak[\s\w]{0,10}gratis|'
    r'tidak[\s\w]{0,10}lagi[\s\w]{0,10}gratis|'
    r'kini[\s\w]{0,20}bayar|sekarang[\s\w]{0,20}berbayar)\b',
    re.IGNORECASE
)

# Kata penjelas tiket untuk validasi gratis umum
KATA_TIKET_SEKITAR = re.compile(
    r'\b(tiket|masuk|htm|karcis|biaya[\s\-]masuk|entrance|admission|'
    r'retribusi|tarif[\s\-]masuk)\b',
    re.IGNORECASE
)

# Domain tidak relevan untuk Level 2
DOMAIN_SKIP = {
    "booking.com", "agoda.com", "traveloka.com", "tiket.com",
    "tripadvisor.com", "airbnb.com", "hotels.com", "expedia.com",
    "tokopedia.com", "shopee.co.id", "lazada.co.id", "blibli.com",
    "instagram.com", "facebook.com", "twitter.com", "x.com",
    "youtube.com", "tiktok.com", "maps.google.com",
}

# Substring URL → skor prioritas (lebih tinggi dibuka lebih dulu di L2/L3)
URL_PRIORITY_HINTS: tuple[tuple[str, int], ...] = (
    (".go.id", 120),
    ("disbudpar", 110),
    ("disparbud", 105),
    ("dispar", 100),
    ("pariwisata", 95),
    ("kemenparekraf", 90),
    ("kompas.com", 55),
    ("detik.com", 55),
    ("tribun", 45),
    ("wikipedia.org", 40),
)

_SNIPPET_STOPWORDS = frozenset({
    "dan", "the", "di", "desa", "wisata", "taman", "tempat", "objek",
    "kabupaten", "kota", "kecamatan", "pulau", "gunung", "air", "pantai",
})

# Host yang sangat khas Bali/Lombok — jika alamat prov Sulawesi, URL ini dilewati
_HOST_CURIGA_BALI_LOMBOK: tuple[str, ...] = (
    "rentalmobilbali", "liburanbali", "wisatabali", "balitour", "visitbali",
    "balipedia", "denpasar", "gianyar", "ubud", "tabanan", "mengwi",
    "bedulu", "nusapenida", "kintamani", "lovina", "amed", "lombok",
    "mataram", "senggigi", "gilitrawangan",
)

# Nama kota/kab di Sulawesi & Gorontalo: jika muncul di alamat, dipakai sebagai jarum
_KOTA_SULAWESI_ALAMAT: tuple[str, ...] = (
    "makassar", "manado", "palu", "kendari", "gorontalo", "bitung", "palopo",
    "parepare", "tomohon", "luwuk", "poso", "bantaeng", "maros", "bone",
    "sinjai", "watansoppeng", "polewali", "mamuju", "majene", "makale",
    "rantepao", "toli-toli", "tolitoli", "buol", "parigi", "morowali",
    "baubau", "kolaka", "konawe", "buton", "wakatobi", "banggai",
)

# Batas harga wajar per kategori wisata (Rupiah)
# Harga di atas batas ini dianggap BUKAN harga tiket masuk
BATAS_HARGA_KATEGORI: dict[str, int] = {
    "wisata alam"              : 75_000,   # pantai, air terjun, danau, hutan
    "wisata budaya & sejarah"  : 50_000,   # benteng, museum, candi
    "wisata religi"            : 25_000,   # masjid, gereja, vihara — umumnya gratis/murah
    "wisata hiburan"           : 350_000,  # waterpark, taman bermain
    "wisata kota / landmark"   : 100_000,  # monumen, taman kota, desa wisata
    "default"                  : 150_000,  # fallback jika kategori tidak dikenali
}


def batas_harga(kategori_wisata: str) -> int:
    """Kembalikan batas harga wajar berdasarkan kategori wisata."""
    k = str(kategori_wisata).strip().lower()
    for key, val in BATAS_HARGA_KATEGORI.items():
        if key in k:
            return val
    return BATAS_HARGA_KATEGORI["default"]


def _url_priority_score(url: str) -> int:
    u = url.lower()
    best = 0
    for sub, sc in URL_PRIORITY_HINTS:
        if sub in u:
            best = max(best, sc)
    return best


def _prioritize_urls(urls: list[str]) -> list[str]:
    """Hapus duplikat (case-insensitive), urutkan skor domain menurun."""
    seen: set[str] = set()
    unique: list[tuple[str, int]] = []
    for i, u in enumerate(urls):
        if not u or _domain_skip(u):
            continue
        k = u.lower().rstrip("/")
        if k in seen:
            continue
        seen.add(k)
        unique.append((u, i))
    unique.sort(key=lambda x: (-_url_priority_score(x[0]), x[1]))
    return [u for u, _ in unique]


def _snippet_cocok_nama(nama: str, title_body: str) -> bool:
    """
    Cegah homonim: hanya snippet yang kemungkinan membicarakan POI yang sama
    yang dipakai untuk ekstraksi harga/gratis di L1.
    """
    nama_clean = str(nama).strip()
    if not nama_clean or len(nama_clean) < 3:
        return False
    t = title_body.lower()
    n = nama_clean.lower()
    if len(n) >= 10:
        for length in (min(40, len(n)), min(24, len(n)), min(14, len(n))):
            if length >= 10 and n[:length] in t:
                return True
    toks = re.findall(r"[\w]{3,}", n, flags=re.UNICODE)
    sig = [x for x in toks if x not in _SNIPPET_STOPWORDS][:8]
    if not sig:
        return True
    need = max(1, int(len(sig) * 0.34 + 0.999))
    hit = sum(1 for x in sig if x in t)
    return hit >= need


def _build_search_queries(nama: str, konteks: str, place_id: str) -> list[str]:
    """Beberapa variasi query untuk recall + disambiguasi place_id."""
    nama = str(nama).strip()
    konteks = str(konteks).strip()
    pid = str(place_id).strip()
    if not pid or pid.lower() in ("nan", "none"):
        pid = ""

    seen: set[str] = set()
    out: list[str] = []

    def add(q: str) -> None:
        q = re.sub(r"\s+", " ", q).strip()
        if len(q) < 5:
            return
        if q not in seen:
            seen.add(q)
            out.append(q)

    q_core = f"{nama} {konteks}".strip() if konteks else nama
    if pid:
        add(f"{nama} {pid} harga tiket masuk")
    if konteks:
        add(f"{q_core} harga tiket masuk")
        add(f"{q_core} HTM retribusi tiket masuk wisata")
    else:
        add(f"{nama} harga tiket masuk")
        add(f"{nama} HTM tiket masuk wisata")
    return out


def _provinsi_sulawesi_gorontalo(prov: str) -> bool:
    if not prov:
        return False
    p = str(prov).lower()
    return ("sulawesi" in p) or ("gorontalo" in p)


def _jarum_geografis(alamat: str, kab: str, prov: str) -> list[str]:
    """
    Token lokasi dari alamat Google (prov, kab, kota di Sulawesi).
    Dipakai mewajibkan halaman/snippet memuat minimal satu token
    agar tidak tertukar dengan wisata nama mirip di pulau lain.
    """
    out: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s = str(s).strip().lower()
        if len(s) < 3 or s in seen:
            return
        seen.add(s)
        out.append(s)

    if prov:
        add(prov)
    if kab:
        add(kab)
        pendek = re.sub(r"^(kabupaten|kota)\s+", "", str(kab).strip(), flags=re.I).strip()
        if pendek and pendek.lower() != str(kab).strip().lower():
            add(pendek)

    al = str(alamat).lower()
    for kota in _KOTA_SULAWESI_ALAMAT:
        if re.search(rf"\b{re.escape(kota)}\b", al):
            add(kota)

    return out


def _setuju_geolokasi(
    jarum: list[str],
    teks: str,
    url: str,
    logger: logging.Logger,
) -> bool:
    """True jika tidak ada jarum (tidak bisa cek) atau salah satu jarum muncul di URL/teks."""
    if not jarum:
        return True
    blob = f"{url}\n{teks[:14000]}".lower()
    ok = any(j in blob for j in jarum)
    if not ok:
        logger.debug(f"    [Lokasi] Tidak cocok — butuh salah satu dari: {jarum[:5]}...")
    return ok


def _skip_url_zona_bali_lombok(prov: str, url: str) -> bool:
    """
    Lewati URL yang hampir pasti membahas wisata Bali/Lombok,
    bila provinsi alamat di Sulawesi/Gorontalo.
    """
    if not url or not _provinsi_sulawesi_gorontalo(prov):
        return False
    try:
        host = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
    except Exception:
        return False
    u = url.lower()
    if any(m in host for m in _HOST_CURIGA_BALI_LOMBOK):
        return True
    if "taman-ayun" in path or "taman_ayun" in path or "puratamanayun" in u:
        return True
    if "pura-taman-ayun" in u or "pura taman ayun" in u:
        return True
    return False


# ──────────────────────────────────────────────
# SETUP LOGGER
# ──────────────────────────────────────────────
def setup_logger() -> tuple[logging.Logger, str]:
    os.makedirs(LOG_DIR, exist_ok=True)
    _TS = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(LOG_DIR, f"scrape_harga_{_TS}.log")

    logger = logging.getLogger("scrape_harga")
    logger.setLevel(logging.DEBUG)

    fmt_file    = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s",
                                    datefmt="%Y-%m-%d %H:%M:%S")
    fmt_console = logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s",
                                    datefmt="%H:%M:%S")

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt_console)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt_file)

    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger, log_file


# ──────────────────────────────────────────────
# EKSTRAK LOKASI DARI KOLOM ALAMAT
# ──────────────────────────────────────────────
def ekstrak_lokasi(alamat: str) -> tuple[str, str]:
    """
    Ekstrak (kabupaten/kota, provinsi) dari string alamat Google Maps.
    Contoh: "Jl. Poros Malino, Kec. Tinggimoncong, Kabupaten Gowa,
             Sulawesi Selatan 92174, Indonesia"
    """
    if not alamat or str(alamat).lower() in ("nan", ""):
        return "", ""

    alamat = str(alamat)
    alamat_lower = alamat.lower()

    prov_map = {
        "sulawesi selatan":  "Sulawesi Selatan",
        "sulawesi tengah":   "Sulawesi Tengah",
        "sulawesi tenggara": "Sulawesi Tenggara",
        "sulawesi utara":    "Sulawesi Utara",
        "sulawesi barat":    "Sulawesi Barat",
        "gorontalo":         "Gorontalo",
    }
    provinsi = ""
    for key, val in prov_map.items():
        if key in alamat_lower:
            provinsi = val
            break

    m = re.search(
        r'\b(Kabupaten|Kota)\s+([A-Za-z\s]+?)(?:\s*\d{4,}|,|$)',
        alamat, re.IGNORECASE
    )
    kabupaten = ""
    if m:
        tipe  = m.group(1).capitalize()
        nama  = m.group(2).strip().title()
        kabupaten = f"{tipe} {nama}"

    return kabupaten, provinsi


# ──────────────────────────────────────────────
# EKSTRAKSI HARGA BERBASIS KONTEKS
# ──────────────────────────────────────────────
def _cek_gratis_konteks(t_lower: str, logger: logging.Logger) -> bool:
    """
    Cek apakah teks menyatakan bahwa wisata ini GRATIS — dengan validasi konteks.

    Aturan:
    1. Jika ada frasa EKSPLISIT (tanpa tiket / masuk gratis / free entry) → gratis
    2. Jika ada negasi (dulu gratis, sekarang bayar) → BUKAN gratis
    3. Jika ada kata 'gratis/free' UMUM:
       - Cek jendela ±150 karakter di sekitarnya
       - Jika jendela mengandung kata tiket/masuk → gratis
       - Jika jendela mengandung kata false positive (parkir/wifi/dll) → BUKAN gratis
    """
    # Cek frasa eksplisit dulu — langsung percaya
    if KATA_GRATIS_EKSPLISIT.search(t_lower):
        logger.debug("    [Gratis] Frasa eksplisit ditemukan.")
        return True

    # Cek negasi — "dulu gratis, sekarang bayar" dll
    if KATA_NEGASI_GRATIS.search(t_lower):
        logger.debug("    [Gratis] Frasa negasi ditemukan — BUKAN gratis.")
        return False

    # Cek kata 'gratis/free' umum dengan validasi jendela konteks
    for m in KATA_GRATIS_UMUM.finditer(t_lower):
        pos = m.start()
        w_start = max(0, pos - 150)
        w_end   = min(len(t_lower), pos + 150)
        jendela = t_lower[w_start:w_end]

        # Jika dekat kata false positive → skip kemunculan ini
        if KATA_BUKAN_GRATIS.search(jendela):
            logger.debug(f"    [Gratis] '{m.group()}' dekat kata false positive, dilewati.")
            continue

        # Harus ada kata tiket/masuk di sekitarnya
        if KATA_TIKET_SEKITAR.search(jendela):
            logger.debug(f"    [Gratis] '{m.group()}' valid — dekat kata tiket/masuk.")
            return True

        logger.debug(f"    [Gratis] '{m.group()}' tidak dekat kata tiket, dilewati.")

    return False


def ekstrak_harga_konteks(teks: str, maks_harga: int,
                           logger: logging.Logger) -> int | None:
    """
    Ekstrak harga tiket masuk dari teks dengan mempertimbangkan konteks.

    Strategi:
    1. Cek gratis dengan validasi konteks (bukan sekedar ada kata 'gratis')
    2. Cari semua posisi kata kunci TIKET dalam teks
    3. Di setiap jendela ±KONTEKS_WINDOW karakter sekitar kata kunci itu,
       cari angka Rupiah
    4. Tolak angka yang ada di dekat kata AKOMODASI
    5. Filter angka yang melebihi batas harga kategori wisata
    6. Kembalikan nilai TERKECIL yang valid
    """
    if not teks:
        return None

    t_lower = teks.lower()

    # ── Cek gratis dengan validasi konteks (pengecekan cerdas)
    if _cek_gratis_konteks(t_lower, logger):
        return 0

    # ── Kumpulkan semua kandidat dari jendela konteks tiket
    kandidat: list[int] = []

    posisi_tiket = [m.start() for m in KATA_TIKET.finditer(t_lower)]
    logger.debug(f"    Posisi kata tiket: {posisi_tiket[:5]}")

    if posisi_tiket:
        # Ambil harga hanya dari sekitar kata tiket
        for pos in posisi_tiket:
            jendela_mulai = max(0, pos - KONTEKS_WINDOW)
            jendela_akhir = min(len(t_lower), pos + KONTEKS_WINDOW)
            jendela = t_lower[jendela_mulai:jendela_akhir]

            # Jika jendela ini berisi kata akomodasi, lewati
            if KATA_AKOMODASI.search(jendela):
                logger.debug("    Jendela mengandung kata akomodasi, dilewati.")
                continue

            harga_di_jendela = _cari_angka_rupiah_dengan_posisi(jendela)
            for h, _pos in harga_di_jendela:
                if 0 < h <= maks_harga:
                    kandidat.append(h)
                    logger.debug(f"    Kandidat dari jendela tiket: Rp {h:,}")

    else:
        # Fallback: tidak ada kata tiket → ambil semua angka Rp,
        # tapi tetap tolak yang dekat kata akomodasi
        logger.debug("    Tidak ada kata tiket, fallback ke pencarian global.")
        semua = _cari_angka_rupiah_dengan_posisi(t_lower)
        for h, pos_angka in semua:
            jendela_mulai = max(0, pos_angka - 100)
            jendela_akhir = min(len(t_lower), pos_angka + 100)
            sekitar = t_lower[jendela_mulai:jendela_akhir]

            if KATA_AKOMODASI.search(sekitar):
                logger.debug(f"    Rp {h:,} dekat kata akomodasi, dilewati.")
                continue
            if 0 < h <= maks_harga:
                kandidat.append(h)

    if not kandidat:
        return None

    # Kembalikan nilai TERKECIL yang valid
    # Harga tiket masuk biasanya yang paling kecil di antara semua harga
    hasil = min(kandidat)
    logger.debug(f"    Kandidat valid: {sorted(set(kandidat))}, dipilih: Rp {hasil:,}")
    return hasil


def _cari_angka_rupiah_dengan_posisi(t: str) -> list[tuple[int, int]]:
    """
    Cari semua nominal Rupiah dalam teks (sudah lowercase).
    Kembalikan list berisi tuple (nominal, index_posisi_dalam_string).
    """
    hasil: list[tuple[int, int]] = []

    # Pola 1: rp[.] <angka>
    for m in re.finditer(r'rp\.?\s*([\d][0-9.,]{0,12})', t):
        v = _parse_angka(m.group(1))
        if v is not None:
            hasil.append((v, m.start()))

    # Pola 2: <angka> rupiah
    for m in re.finditer(r'([\d][0-9.,]{0,12})\s*rupiah', t):
        v = _parse_angka(m.group(1))
        if v is not None:
            hasil.append((v, m.start()))

    # Pola 3: <angka> rb / ribu
    # Tambahan: Negative lookahead agar "15 ribu pengunjung/orang/hektar" tidak dianggap harga tiket
    pola_ribu = r'([\d]+(?:[.,]\d+)?)\s*(?:rb|ribu)\b(?!\s+(?:pengunjung|orang|wisatawan|turis|kendaraan|mobil|motor|bus|hektar|meter|ha\b|m2|jiwa|jamaah|spesies|ekor))'
    for m in re.finditer(pola_ribu, t):
        try:
            basis = float(m.group(1).replace(',', '.'))
            v = int(round(basis * 1_000))
            if _valid_nominal(v):
                hasil.append((v, m.start()))
        except ValueError:
            pass

    return hasil


def _parse_angka(raw: str) -> int | None:
    """String angka → int. None jika tidak memenuhi syarat nominal."""
    raw = raw.strip().rstrip(',.').replace('.', '').replace(',', '')
    try:
        v = int(raw)
        return v if _valid_nominal(v) else None
    except ValueError:
        return None


def _valid_nominal(v: int) -> bool:
    """
    Nominal valid untuk harga tiket:
    - Kelipatan Rp 500 (beberapa wisata pakai harga Rp 2.500, 7.500, dll)
    - Antara Rp 1.000 dan Rp 5.000.000
    """
    return 1_000 <= v <= 5_000_000 and v % 500 == 0


# ──────────────────────────────────────────────
# LEVEL 1 – DDGS SNIPPET
# ──────────────────────────────────────────────
def level1_ddgs(
    query: str,
    nama: str,
    maks_harga: int,
    logger: logging.Logger,
    jarum: list[str],
    prov: str,
) -> tuple[int | None, list[str], str | None]:
    """
    Cari via DDGS (wilayah Indonesia + retry).
    Kembalikan (harga, url_untuk_L2_terprioritaskan, url_sumber_jika_L1_ok).
    Harga/gratis dari snippet hanya jika snippet cocok dengan nama POI
    dan (jika ada jarum) memuat bukti lokasi dari alamat.
    """
    logger.debug(f"  [L1] Query: \"{query}\"")
    urls_collected: list[str] = []
    kandidat: list[tuple[int, str]] = []
    hasil: list[dict] = []
    last_err: Exception | None = None

    for attempt in range(DDGS_L1_RETRIES):
        try:
            with DDGS() as ddgs:
                hasil = list(
                    ddgs.text(
                        query,
                        max_results=MAX_DDGS_RESULTS,
                        region=DDGS_REGION,
                    )
                )
            last_err = None
            break
        except Exception as e:
            last_err = e
            logger.debug(f"  [L1] DDGS percobaan {attempt + 1}/{DDGS_L1_RETRIES}: {e}")
            if attempt + 1 < DDGS_L1_RETRIES:
                time.sleep(DDGS_RETRY_SLEEP * (attempt + 1))

    if last_err is not None:
        logger.error(f"  [L1] Error DDGS setelah retry: {last_err}")
        return None, [], None

    logger.debug(f"  [L1] Jumlah snippet: {len(hasil)}")

    for i, item in enumerate(hasil):
        url  = item.get("href", "") or item.get("url", "")
        teks = f"{item.get('title', '')} {item.get('body', '')}"

        if url and not _domain_skip(url) and not _skip_url_zona_bali_lombok(prov, url):
            urls_collected.append(url)

        if not _snippet_cocok_nama(nama, teks):
            continue

        if jarum and not _setuju_geolokasi(jarum, teks, url, logger):
            logger.debug(f"  [L1] snippet {i + 1}: buang — tidak cocok lokasi alamat")
            continue

        teks_lower = teks.lower()
        if _cek_gratis_konteks(teks_lower, logger):
            logger.debug(f"  [L1] snippet {i + 1}: gratis (cocok nama + lokasi)")
            src = url if url else "ddgs:gratis"
            return 0, _prioritize_urls(urls_collected), src

        h = ekstrak_harga_konteks(teks, maks_harga, logger)
        if h is not None:
            logger.debug(f"  [L1] snippet {i + 1}: kandidat Rp {h:,}")
            kandidat.append((h, url if url else ""))

    prio_urls = _prioritize_urls(urls_collected)

    if kandidat:
        best_h, best_u = min(kandidat, key=lambda x: x[0])
        sumber = best_u if best_u else "ddgs:snippet"
        logger.debug(f"  [L1] Harga terpilih: {best_h} | sumber: {sumber} | "
                     f"{len(prio_urls)} URL relevan")
        return best_h, prio_urls, sumber

    logger.debug(f"  [L1] Tidak ada harga di snippet | {len(prio_urls)} URL untuk L2")
    return None, prio_urls, None


# ──────────────────────────────────────────────
# LEVEL 2 – REQUESTS + BEAUTIFULSOUP
# ──────────────────────────────────────────────
def level2_requests(
    urls: list[str],
    maks_harga: int,
    logger: logging.Logger,
    session: requests.Session,
    jarum: list[str],
    prov: str,
) -> tuple[int | None, str | None]:
    """
    Buka setiap URL dengan requests + BeautifulSoup.
    Kembalikan (harga, url_sumber).
    """
    for url in urls:
        if _skip_url_zona_bali_lombok(prov, url):
            logger.debug(f"  [L2] Lewati URL (zona Bali/Lombok vs alamat Sulawesi): {url}")
            continue
        logger.debug(f"  [L2] Membuka: {url}")
        try:
            resp = session.get(
                url, timeout=REQUEST_TIMEOUT, allow_redirects=True,
            )
            if resp.status_code != 200:
                logger.debug(f"  [L2] Status {resp.status_code}, lewati.")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer",
                              "header", "aside", "form"]):
                tag.decompose()

            teks = soup.get_text(separator=" ", strip=True)

            if jarum and not _setuju_geolokasi(jarum, teks, url, logger):
                logger.debug(f"  [L2] Tolak isi halaman — tidak ada bukti lokasi alamat: {url}")
                continue

            if _cek_gratis_konteks(teks.lower(), logger):
                logger.debug(f"  [L2] Gratis terdeteksi di {url}")
                return 0, url

            h = ekstrak_harga_konteks(teks, maks_harga, logger)
            if h is not None:
                logger.debug(f"  [L2] Harga Rp {h:,} dari {url}")
                return h, url

            time.sleep(DELAY_L2)

        except requests.exceptions.Timeout:
            logger.debug(f"  [L2] Timeout: {url}")
        except Exception as e:
            logger.debug(f"  [L2] Error ({url}): {e}")

    return None, None


# ──────────────────────────────────────────────
# LEVEL 3 – PLAYWRIGHT (fallback JS-heavy)
# ──────────────────────────────────────────────
def level3_playwright(
    urls: list[str],
    maks_harga: int,
    logger: logging.Logger,
    page,
    jarum: list[str],
    prov: str,
) -> tuple[int | None, str | None]:
    """
    Buka halaman dengan Playwright (satu Page dipakai ulang dari main).
    Kembalikan (harga, url_sumber).
    """
    if not PLAYWRIGHT_OK or page is None or not urls:
        logger.debug("  [L3] Playwright/page tidak tersedia atau tidak ada URL.")
        return None, None

    logger.debug(f"  [L3] Playwright coba {len(urls)} URL ...")
    try:
        for url in urls:
            if _skip_url_zona_bali_lombok(prov, url):
                logger.debug(f"  [L3] Lewati URL (zona Bali/Lombok): {url}")
                continue
            try:
                logger.debug(f"  [L3] Navigasi ke: {url}")
                page.goto(url, wait_until="domcontentloaded")
                teks = page.inner_text("body")

                if jarum and not _setuju_geolokasi(jarum, teks, url, logger):
                    logger.debug(f"  [L3] Tolak — tidak ada bukti lokasi alamat: {url}")
                    continue

                if _cek_gratis_konteks(teks.lower(), logger):
                    logger.debug(f"  [L3] Gratis terdeteksi di {url}")
                    return 0, url

                h = ekstrak_harga_konteks(teks, maks_harga, logger)
                if h is not None:
                    logger.debug(f"  [L3] Harga Rp {h:,} dari {url}")
                    return h, url

            except Exception as e:
                logger.debug(f"  [L3] Error ({url}): {e}")

    except Exception as e:
        logger.error(f"  [L3] Playwright error: {e}")

    return None, None


# ──────────────────────────────────────────────
# PENCARIAN BERTINGKAT UTAMA
# ──────────────────────────────────────────────
def cari_harga(
    nama: str,
    alamat: str,
    kategori_wisata: str,
    logger: logging.Logger,
    place_id: str = "",
    session: requests.Session | None = None,
    pw_page=None,
) -> tuple[int | None, dict[str, str | None]]:
    """
    Sistem pencarian bertingkat L1 → L2 → L3.
    Kembalikan (harga | None, meta) dengan kunci:
    harga_sumber_url, harga_level, harga_query.
    """
    meta: dict[str, str | None] = {
        "harga_sumber_url": None,
        "harga_level": None,
        "harga_query": None,
    }

    if session is None:
        session = requests.Session()
        session.headers.update(HEADERS)

    kabupaten, provinsi = ekstrak_lokasi(alamat)
    konteks = " ".join(filter(None, [kabupaten, provinsi]))
    maks    = batas_harga(kategori_wisata)
    jarum   = _jarum_geografis(alamat, kabupaten, provinsi)

    queries = _build_search_queries(nama, konteks, place_id)
    merged_urls: list[str] = []

    logger.debug(f"  Lokasi: '{kabupaten}' | '{provinsi}'")
    logger.debug(f"  Jarum geolokasi: {jarum}")
    logger.debug(f"  Batas harga ({kategori_wisata}): Rp {maks:,}")

    for q in queries:
        harga, urls_batch, sumber = level1_ddgs(
            q, nama, maks, logger, jarum, provinsi,
        )
        meta["harga_query"] = q
        if harga == 0:
            meta["harga_sumber_url"] = sumber or "ddgs:gratis"
            meta["harga_level"] = "L1"
            logger.debug("  >> Ditemukan di L1 (gratis)")
            return 0, meta
        if harga is not None:
            meta["harga_sumber_url"] = sumber or "ddgs:snippet"
            meta["harga_level"] = "L1"
            logger.debug(f"  >> Ditemukan di L1: Rp {harga:,}")
            return harga, meta
        merged_urls.extend(urls_batch)

    merged = _prioritize_urls(merged_urls)[:MAX_MERGED_L2]
    meta["harga_query"] = queries[0] if queries else None

    if merged:
        harga, src = level2_requests(
            merged, maks, logger, session, jarum, provinsi,
        )
        if harga is not None:
            meta["harga_sumber_url"] = src
            meta["harga_level"] = "L2"
            logger.debug(f"  >> Ditemukan di L2: Rp {harga:,}")
            return harga, meta

        harga, src = level3_playwright(
            merged, maks, logger, pw_page, jarum, provinsi,
        )
        if harga is not None:
            meta["harga_sumber_url"] = src
            meta["harga_level"] = "L3"
            logger.debug(f"  >> Ditemukan di L3: Rp {harga:,}")
            return harga, meta

    logger.debug("  >> Semua level gagal — NULL.")
    return None, meta


# ──────────────────────────────────────────────
# KATEGORI HARGA
# ──────────────────────────────────────────────
def kategori_harga(harga) -> str:
    if pd.isna(harga) or str(harga).strip() == "-":
        return "-"
    try:
        harga = float(harga)
        if pd.isna(harga): return "-"
        harga = int(harga)
    except ValueError:
        return "-"
    if harga == 0:
        return "Gratis"
    elif harga <= 9_999:
        return "Murah"
    elif harga <= 19_999:
        return "Sedang"
    else:
        return "Mahal"


# ──────────────────────────────────────────────
# HELPER
# ──────────────────────────────────────────────
def _domain_skip(url: str) -> bool:
    return any(d in url for d in DOMAIN_SKIP)


def simpan_checkpoint(df: pd.DataFrame, path: str,
                       logger: logging.Logger, label: str = "checkpoint") -> None:
    df_save = df.copy()
    df_save["kategori_harga"] = df_save["harga_rp"].apply(kategori_harga)
    df_save["harga_rp"] = df_save["harga_rp"].astype(object)
    df_save["harga_rp"] = df_save["harga_rp"].fillna("-")
    df_save.rename(columns={'nama_wisata': 'nama wisata', 'harga_sumber_url': 'url_harga'}, inplace=True)
    kolom = ['nama wisata', 'alamat', 'kabupaten', 'provinsi', 'harga_rp', 'kategori_harga', 'url_harga']
    try:
        df_save[kolom].to_csv(path, index=False, encoding="utf-8-sig")
        terisi = len(df_save[df_save["harga_rp"] != "-"])
        logger.info(f"[{label.upper()}] Simpan -> {os.path.basename(path)} "
                    f"| {terisi}/{len(df_save)} baris terisi")
    except Exception as e:
        logger.error(f"[{label.upper()}] Gagal simpan: {e}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
def main():
    logger, log_file = setup_logger()

    logger.info("=" * 65)
    logger.info("  SCRAPE HARGA WISATA SULAWESI  –  v5.1 (geolokasi + aman Ctrl+C)")
    logger.info("=" * 65)
    logger.info(f"Input            : {INPUT_FILE}")
    logger.info(f"Output           : {OUTPUT_FILE}")
    logger.info(f"Log              : {log_file}")
    logger.info(f"Delay            : {DELAY_DETIK}d/baris | L2={DELAY_L2}d/link")
    logger.info(f"Auto-save setiap : {AUTOSAVE_INTERVAL} baris")
    logger.info(f"Konteks window   : ±{KONTEKS_WINDOW} karakter")
    logger.info(f"DDGS region      : {DDGS_REGION}")
    logger.info(f"Playwright       : {'aktif (1 browser/run)' if PLAYWRIGHT_OK else 'tidak terinstall (L3 skip)'}")
    logger.info("=" * 65)

    os.makedirs(HASIL_DIR, exist_ok=True)

    # Mulai dengan memuat data sumber yang lengkap
    logger.info(f"Membaca dataset induk dari: {os.path.basename(INPUT_FILE)} ...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except FileNotFoundError:
        logger.critical(f"File sumber tidak ditemukan: {INPUT_FILE}")
        return
    except Exception as e:
        logger.critical(f"Gagal baca CSV Induk: {e}")
        return

    if "harga_rp" not in df.columns:
        df["harga_rp"] = None
    if "kategori_harga" not in df.columns:
        df["kategori_harga"] = None
    for _col_audit in ("harga_sumber_url", "harga_level", "harga_query"):
        if _col_audit not in df.columns:
            df[_col_audit] = None

    # Resume dari output jika tersedia
    if os.path.exists(OUTPUT_FILE):
        try:
            logger.info(">>> MENGAKTIFKAN MODE RESUME (Berdasarkan scrap_harga_wisata.csv)")
            df_old = pd.read_csv(OUTPUT_FILE)
            for i in range(min(len(df), len(df_old))):
                h = df_old.at[i, "harga_rp"]
                if pd.notna(h):
                    df.at[i, "harga_rp"] = h
                if "url_harga" in df_old.columns:
                    u = df_old.at[i, "url_harga"]
                    if pd.notna(u):
                        df.at[i, "harga_sumber_url"] = u
        except Exception as e:
            logger.warning(f"Gagal baca history: {e}")

    total = len(df)
    logger.info(f"Total baris: {total}")

    # Log distribusi kategori wisata di dataset
    if "kategori" in df.columns:
        logger.info("Distribusi kategori wisata:")
        for kat, jml in df["kategori"].value_counts().items():
            maks = batas_harga(kat)
            logger.info(f"  {kat:<35}: {jml:>5} baris | batas harga Rp {maks:,}")

    http = requests.Session()
    http.headers.update(HEADERS)

    # Graceful shutdown -> INSTANT KILL
    def handle_shutdown(sig, frame):
        logger.warning(">>> SINYAL HENTI DITEKAN! Memaksa berhenti instan & save...")
        simpan_checkpoint(df, OUTPUT_FILE, logger, label="emergency-save")
        os._exit(0)

    signal.signal(signal.SIGINT,  handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    count_ok    = 0
    count_null  = 0
    count_skip  = 0
    count_gratis = 0
    proses_sejak_save = 0
    waktu_mulai = time.time()

    logger.info("-" * 65)
    logger.info("Memulai proses pencarian harga ...")
    logger.info("-" * 65)

    def satu_siklus_scrape(pw_page) -> None:
        nonlocal count_ok, count_null, count_skip, count_gratis, proses_sejak_save
        for idx, row in df.iterrows():

            nama            = str(row.get("nama_wisata", "")).strip()
            alamat          = str(row.get("alamat", "")).strip()
            kategori_wisata = str(row.get("kategori", "")).strip()
            place_id        = str(row.get("place_id", "")).strip()
            if place_id.lower() in ("nan", "none"):
                place_id = ""

            if not nama or nama.lower() == "nan":
                logger.warning(f"[{idx + 1:>5}/{total}] LEWAT — nama kosong")
                count_skip += 1
                continue

            # Resume mode
            val = df.at[idx, "harga_rp"]
            if pd.notna(val) and str(val).strip() != "-" and str(val).lower() not in ("nan", "<na>"):
                h_lama = str(val)
                logger.info(f"[{idx + 1:>5}/{total}] [SKIP]  '{nama}' -> Rp {h_lama}")
                count_skip += 1
                continue

            logger.info(f"[{idx + 1:>5}/{total}] [CARI]  '{nama}' ({kategori_wisata})")
            harga, meta = cari_harga(
                nama, alamat, kategori_wisata, logger,
                place_id=place_id, session=http, pw_page=pw_page,
            )

            if harga is not None:
                df.at[idx, "harga_rp"] = harga
                df.at[idx, "harga_sumber_url"] = meta.get("harga_sumber_url")
                df.at[idx, "harga_level"] = meta.get("harga_level")
                df.at[idx, "harga_query"] = meta.get("harga_query")
                kat = kategori_harga(harga)
                sumber = meta.get("harga_sumber_url") or ""
                lvl = meta.get("harga_level") or ""
                logger.info(f"[{idx + 1:>5}/{total}] [OK]    '{nama}' "
                            f"-> Rp {harga:,} ({kat}) [{lvl}] {sumber[:70]}")
                count_ok += 1
                if harga == 0:
                    count_gratis += 1
            else:
                df.at[idx, "harga_rp"] = "-"
                df.at[idx, "harga_sumber_url"] = "-"
                df.at[idx, "harga_level"] = "-"
                df.at[idx, "harga_query"] = "-"
                logger.info(f"[{idx + 1:>5}/{total}] [NULL]  '{nama}' -> tidak ditemukan (diset '-')")
                count_null += 1

            proses_sejak_save += 1
            if proses_sejak_save >= AUTOSAVE_INTERVAL:
                simpan_checkpoint(df, OUTPUT_FILE, logger, label="auto-save")
                proses_sejak_save = 0

            time.sleep(DELAY_DETIK)

    if PLAYWRIGHT_OK:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(extra_http_headers=HEADERS)
            page.set_default_timeout(20_000)
            try:
                satu_siklus_scrape(page)
            finally:
                try:
                    simpan_checkpoint(
                        df, OUTPUT_FILE, logger, label="simpan-sebelum-tutup-browser",
                    )
                except Exception as e:
                    logger.error("Gagal simpan sebelum tutup browser: %s", e)
                try:
                    browser.close()
                except Exception as e:
                    logger.warning(
                        "Penutupan Playwright diabaikan (mis. setelah Ctrl+C): %s",
                        e,
                    )
    else:
        satu_siklus_scrape(None)

    # Simpan final (ulang aman setelah blok Playwright)
    logger.info("-" * 65)
    simpan_checkpoint(df, OUTPUT_FILE, logger, label="final")

    # Ringkasan
    durasi = time.time() - waktu_mulai
    menit, detik = divmod(int(durasi), 60)
    jam,   menit = divmod(menit, 60)

    df["kategori_harga"] = df["harga_rp"].apply(kategori_harga)
    kat_count = df["kategori_harga"].value_counts()

    logger.info("=" * 65)
    logger.info("  RINGKASAN AKHIR")
    logger.info("=" * 65)
    logger.info(f"  Total baris           : {total}")
    logger.info(f"  Ditemukan (sesi ini)  : {count_ok}"
                f"  (termasuk {count_gratis} gratis)")
    logger.info(f"  Tidak ditemukan       : {count_null}")
    logger.info(f"  Dilewati / resume     : {count_skip}")
    logger.info(f"  Durasi                : {jam:02d}j {menit:02d}m {detik:02d}d")
    logger.info("-" * 65)
    logger.info("  DISTRIBUSI KATEGORI HARGA:")
    for kat, jml in kat_count.items():
        logger.info(f"    {kat:<20} : {jml:>5}  ({jml/total*100:.1f}%)")
    logger.info("=" * 65)
    logger.info(f"Output  : {OUTPUT_FILE}")
    logger.info(f"Log     : {log_file}")
    logger.info("SELESAI.")


if __name__ == "__main__":
    main()
