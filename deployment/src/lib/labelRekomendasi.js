import { getTourismData } from './data';

// ── KONSTANTA DARI DATASET TRAINING ──────────────────────────
// Threshold label (mean ± 0.5*std dari skor_komposit dataset 2715 baris)
const LABEL_THRESHOLDS = { terbaik: 0.6566, baik: 0.6058, sedang: 0.5551 };

// Mapping kategori harga → bobot numerik
const HARGA_MAP = { 'Gratis': 1.0, 'Murah': 0.75, 'Sedang': 0.5, 'Mahal': 0.25 };

// Range KDE dari dataset training (untuk normalisasi MinMax)
const KDE_MIN = 4.1957;
const KDE_MAX = 39.7043;

// KDE bandwidth (sama dengan Python: 0.05 radian ≈ 3.2 km)
const KDE_BANDWIDTH = 0.05;

// ── BOBOT SKOR KOMPOSIT (SAMA DENGAN PYTHON) ────────────────
const WEIGHTS = {
  rating:    0.30,
  review:    0.20,
  kde:       0.20,
  harga:     0.15,
  kat_harga: 0.15,
};

// ── FUNGSI MATEMATIKA ────────────────────────────────────────

/** Konversi derajat → radian */
function toRadians(deg) {
  return deg * Math.PI / 180;
}

/** Jarak Haversine antara 2 titik (dalam radian) */
function haversine(lat1, lon1, lat2, lon2) {
  const dLat = lat2 - lat1;
  const dLon = lon2 - lon1;
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * Math.asin(Math.sqrt(a));
}

/** Gaussian kernel: K(u) = (1/√2π) * exp(-u²/2) */
function gaussianKernel(u) {
  return (1 / Math.sqrt(2 * Math.PI)) * Math.exp(-0.5 * u * u);
}

/**
 * Hitung KDE density untuk satu titik berdasarkan semua titik lain.
 * Menggunakan metric Haversine + Gaussian kernel, identik dengan sklearn.
 */
function computeKDE(latDeg, lonDeg, allCoords) {
  const latRad = toRadians(latDeg);
  const lonRad = toRadians(lonDeg);

  let densitySum = 0;
  for (const coord of allCoords) {
    const dist = haversine(latRad, lonRad, coord.latRad, coord.lonRad);
    densitySum += gaussianKernel(dist / KDE_BANDWIDTH);
  }

  // Density = rata-rata kernel / bandwidth
  return densitySum / (allCoords.length * KDE_BANDWIDTH);
}

/** MinMax normalisasi ke range [0, 1] */
function minmax(value, min, max) {
  if (max === min) return 0;
  return Math.max(0, Math.min(1, (value - min) / (max - min)));
}

// ── FUNGSI UTAMA: HITUNG LABEL REKOMENDASI ──────────────────

/**
 * Menghitung label rekomendasi untuk sebuah data wisata.
 * Meng-query seluruh koordinat dari Supabase untuk KDE.
 * 
 * @param {Object} data - Data wisata yang akan dilabeli
 * @returns {Promise<string>} - Label: 'Terbaik'|'Baik'|'Sedang'|'Buruk'|'Belum Lengkap'
 */
export async function calculateLabel(data) {
  const rating   = parseFloat(data.rating);
  const review   = parseInt(data.jumlah_riview);
  const harga    = parseFloat(data.harga);
  const katHarga = (data.kategori_harga || '').trim();
  const lat      = parseFloat(data.lat);
  const lon      = parseFloat(data.long);

  // Jika data utama belum lengkap
  if (isNaN(rating) || isNaN(review)) return 'Belum Lengkap';

  // 1. Normalisasi Rating (0-5 → 0-1)
  const normRating = Math.min(Math.max(rating / 5, 0), 1);

  // 2. Normalisasi Review (log1p lalu MinMax, range dataset: 0 ~ 9.8)
  const normReview = Math.min(Math.log1p(review) / 9.8, 1);

  // 3. Normalisasi Harga (log1p + invert: murah = skor tinggi)
  const normHarga = isNaN(harga) ? 1.0 : 1.0 - Math.min(Math.log1p(harga) / 12.2, 1);

  // 4. Bobot Kategori Harga
  const normKatHarga = HARGA_MAP[katHarga] !== undefined ? HARGA_MAP[katHarga] : 0.5;

  // 5. KDE Spatial Density
  let normKDE = 0.5; // fallback jika koordinat tidak tersedia
  if (!isNaN(lat) && !isNaN(lon)) {
    try {
      // Ambil semua data untuk koordinat
      const allData = await getTourismData();
      const allCoords = allData
        .filter(d => d.lat && d.long && !isNaN(parseFloat(d.lat)) && !isNaN(parseFloat(d.long)))
        .map(d => ({
          latRad: toRadians(parseFloat(d.lat)),
          lonRad: toRadians(parseFloat(d.long))
        }));

      if (allCoords.length > 0) {
        const density = computeKDE(lat, lon, allCoords);
        // Normalisasi menggunakan range dari dataset training
        normKDE = minmax(density, KDE_MIN, KDE_MAX);
      }
    } catch (err) {
      console.error('KDE calculation error, using fallback:', err);
      // normKDE tetap 0.5
    }
  }

  // 6. Skor Komposit (BOBOT IDENTIK DENGAN PYTHON)
  const skor = WEIGHTS.rating    * normRating   +
               WEIGHTS.review    * normReview   +
               WEIGHTS.kde       * normKDE      +
               WEIGHTS.harga     * normHarga    +
               WEIGHTS.kat_harga * normKatHarga;

  // 7. Pelabelan berdasarkan threshold
  if (skor >= LABEL_THRESHOLDS.terbaik) return 'Terbaik';
  if (skor >= LABEL_THRESHOLDS.baik)    return 'Baik';
  if (skor >= LABEL_THRESHOLDS.sedang)  return 'Sedang';
  return 'Buruk';
}
