import { getTourismData } from './data';

// ── KONSTANTA DARI DATASET TRAINING ──────────────────────────
// Threshold label (mean ± 0.5*std dari skor_komposit dataset)
const LABEL_THRESHOLDS = { terbaik: 0.6375, baik: 0.5845, sedang: 0.5316 };

// Mapping kategori harga → bobot numerik
const HARGA_MAP = { 'Gratis': 1.0, 'Murah': 0.75, 'Sedang': 0.5, 'Mahal': 0.25 };

// Parameter Bayesian Average dari dataset training
const BAYESIAN_C = 4.4707675;
const BAYESIAN_M = 28.0;
const BAYESIAN_MIN = 3.7225;
const BAYESIAN_MAX = 4.8956;

// ── BOBOT SKOR KOMPOSIT (SAMA DENGAN PYTHON) ────────────────
const WEIGHTS = {
  rating:    0.30,
  review:    0.20,
  bayesian:  0.20,
  harga:     0.15,
  kat_harga: 0.15,
};

// ── FUNGSI MATEMATIKA ────────────────────────────────────────

/** Menghitung Bayesian Average */
function computeBayesian(r, v, C, m) {
  if (v + m === 0) return C;
  return (v / (v + m) * r) + (m / (v + m) * C);
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

  // 5. Kualitas Tertimbang (Bayesian Average)
  const bayesianScore = computeBayesian(rating, review, BAYESIAN_C, BAYESIAN_M);
  const normBayesian = minmax(bayesianScore, BAYESIAN_MIN, BAYESIAN_MAX);

  // 6. Skor Komposit (BOBOT IDENTIK DENGAN PYTHON)
  const skor = WEIGHTS.rating    * normRating   +
               WEIGHTS.review    * normReview   +
               WEIGHTS.bayesian  * normBayesian +
               WEIGHTS.harga     * normHarga    +
               WEIGHTS.kat_harga * normKatHarga;

  // 7. Pelabelan berdasarkan threshold
  if (skor >= LABEL_THRESHOLDS.terbaik) return 'Terbaik';
  if (skor >= LABEL_THRESHOLDS.baik)    return 'Baik';
  if (skor >= LABEL_THRESHOLDS.sedang)  return 'Sedang';
  return 'Buruk';
}
