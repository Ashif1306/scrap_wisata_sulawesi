"""
label_rekomendasi.py
====================
Feature Engineering: Pembuatan Kolom Label Rekomendasi
-------------------------------------------------------
Tujuan : Membuat variabel target 'label_rekomendasi' (Terbaik/Baik/Sedang/Buruk)
         untuk model klasifikasi Random Forest destinasi wisata Sulawesi.

Metode :
  1. Data Cleaning         – handle missing values
  2. Spatial Density       – KernelDensity (Haversine) untuk deteksi hotspot
  3. Normalisasi           – MinMaxScaler per fitur (log1p untuk outlier)
  4. Mapping Kategori Harga– bobot numerik untuk variabel teks
  5. Skor Komposit         – weighted sum 6 dimensi
  6. Pelabelan Threshold Alami – berbasis mean±std (distribusi natural)

Output : wisata_sulawesi_label.csv (tersimpan di folder hasil_final/)
"""

import numpy as np
import pandas as pd
from sklearn.neighbors import KernelDensity
from sklearn.preprocessing import MinMaxScaler

# ─────────────────────────────────────────────
# 0. KONFIGURASI PATH
# ─────────────────────────────────────────────
INPUT_PATH  = "wisata_sulawesi_lengkap.csv"   # relatif terhadap folder hasil_final
OUTPUT_PATH = "wisata_sulawesi_label.csv"

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
print("[1/7] Memuat dataset ...")
df = pd.read_csv(INPUT_PATH)
print(f"   Baris awal: {len(df):,}  |  Kolom: {list(df.columns)}")

# ─────────────────────────────────────────────
# 2. DATA CLEANING
# ─────────────────────────────────────────────
print("\n[2/7] Data cleaning ...")

# Pastikan tipe numerik
for col in ["rating", "jumlah_riview", "harga", "lat", "long"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Harga kosong → 0 (gratis / tidak diketahui)
df["harga"] = df["harga"].fillna(0)

# Lat & long kosong → mean (agar KDE tidak error)
df["lat"]  = df["lat"].fillna(df["lat"].mean())
df["long"] = df["long"].fillna(df["long"].mean())

# Rating & review kosong → median (lebih robust terhadap outlier)
df["rating"]        = df["rating"].fillna(df["rating"].median())
df["jumlah_riview"] = df["jumlah_riview"].fillna(df["jumlah_riview"].median())

# Kategori harga: konsisten dengan nilai harga
#   harga = 0  → pasti Gratis (bukan Sedang)
#   harga > 0 tapi kategori kosong → Sedang (fallback aman)
mask_gratis = (df["harga"] == 0) & (df["kategori_harga"].isna())
mask_sedang = (df["harga"] >  0) & (df["kategori_harga"].isna())
df.loc[mask_gratis, "kategori_harga"] = "Gratis"
df.loc[mask_sedang, "kategori_harga"] = "Sedang"

print("   Missing values setelah cleaning:")
print(df[['lat','long','rating','jumlah_riview','harga','kategori_harga']].isnull().sum().to_string())

# ─────────────────────────────────────────────
# 3. SPATIAL DENSITY – KDE Haversine
# ─────────────────────────────────────────────
print("\n[3/7] Menghitung kepadatan spasial (KDE Haversine) ...")

# KDE Haversine membutuhkan koordinat dalam RADIAN
coords_rad = np.radians(df[["lat", "long"]].values)

kde = KernelDensity(metric="haversine", bandwidth=0.05, kernel="gaussian")
kde.fit(coords_rad)

# log-density → density (exp agar nilainya positif untuk normalisasi)
log_density   = kde.score_samples(coords_rad)
kde_density   = np.exp(log_density)

df["_kde_density"] = kde_density
print(f"   KDE selesai. Range density: [{kde_density.min():.4f}, {kde_density.max():.4f}]")


# ─────────────────────────────────────────────
# 4. NORMALISASI MinMaxScaler (0–1)
# ─────────────────────────────────────────────
print("\n[4/7] Normalisasi fitur ...")

scaler = MinMaxScaler()

def normalize(series: pd.Series) -> np.ndarray:
    """MinMaxScaler untuk satu kolom (reshape 2D → 1D)."""
    return scaler.fit_transform(series.values.reshape(-1, 1)).ravel()

# 4a. Rating
norm_rating = normalize(df["rating"])

# 4b. Jumlah Review – log1p lalu normalisasi
norm_review = normalize(pd.Series(np.log1p(df["jumlah_riview"])))

# 4c. Harga – log1p lalu normalisasi lalu BALIK (murah = skor tinggi)
norm_harga_raw = normalize(pd.Series(np.log1p(df["harga"])))
norm_harga     = 1.0 - norm_harga_raw   # invert: harga murah → mendekati 1

# 4d. Kepadatan Spasial
norm_kde = normalize(df["_kde_density"])

# ─────────────────────────────────────────────
# 5. MAPPING KATEGORI HARGA → BOBOT NUMERIK
# ─────────────────────────────────────────────
print("\n[5/7] Mapping kategori harga ...")

HARGA_MAP = {
    "Gratis": 1.00,
    "Murah" : 0.75,
    "Sedang": 0.50,
    "Mahal" : 0.25,
}

norm_kat_harga = (
    df["kategori_harga"]
    .str.strip()
    .str.capitalize()
    .map(HARGA_MAP)
    .fillna(0.50)           # nilai default untuk kategori tidak dikenal
    .values
)

# ─────────────────────────────────────────────
# 6. SKOR KOMPOSIT (Weighted Sum)
# ─────────────────────────────────────────────
#   30% rating | 20% review | 20% KDE | 15% harga | 15% kat_harga
# ─────────────────────────────────────────────
print("\n[6/7] Menghitung skor komposit ...")

WEIGHTS = {
    "rating"    : 0.30,
    "review"    : 0.20,
    "kde"       : 0.20,
    "harga"     : 0.15,
    "kat_harga" : 0.15,
}

df["skor_komposit"] = (
    WEIGHTS["rating"]    * norm_rating    +
    WEIGHTS["review"]    * norm_review    +
    WEIGHTS["kde"]       * norm_kde       +
    WEIGHTS["harga"]     * norm_harga     +
    WEIGHTS["kat_harga"] * norm_kat_harga
)

print(f"   Skor komposit — Min: {df['skor_komposit'].min():.4f} | "
      f"Max: {df['skor_komposit'].max():.4f} | "
      f"Mean: {df['skor_komposit'].mean():.4f}")

# ─────────────────────────────────────────────
# 7. PELABELAN FINAL – THRESHOLD ABSOLUT (DISTRIBUSI ALAMI)
# ─────────────────────────────────────────────
# Threshold dihitung otomatis dari distribusi skor:
#   Terbaik : score >= mean + 0.5 * std  (destinasi unggulan)
#   Baik    : mean <= score < mean + 0.5 * std
#   Sedang  : mean - 0.5 * std <= score < mean
#   Buruk   : score < mean - 0.5 * std   (perlu perhatian)
# ─────────────────────────────────────────────
print("\n[7/7] Membuat label rekomendasi (threshold absolut / distribusi alami) ...")

mean_s = df["skor_komposit"].mean()
std_s  = df["skor_komposit"].std()

T_TERBAIK = mean_s + 0.5 * std_s
T_BAIK    = mean_s
T_SEDANG  = mean_s - 0.5 * std_s

print(f"   Mean={mean_s:.4f} | Std={std_s:.4f}")
print(f"   Threshold — Terbaik>={T_TERBAIK:.4f} | Baik>={T_BAIK:.4f} | Sedang>={T_SEDANG:.4f} | Buruk<{T_SEDANG:.4f}")

def assign_label(score: float) -> str:
    if score >= T_TERBAIK:
        return "Terbaik"
    elif score >= T_BAIK:
        return "Baik"
    elif score >= T_SEDANG:
        return "Sedang"
    else:
        return "Buruk"

df["label_rekomendasi"] = df["skor_komposit"].apply(assign_label)

# Distribusi label (natural — tidak harus sama rata)
dist = df["label_rekomendasi"].value_counts()
pct  = (dist / len(df) * 100).round(1)
print("\n   Distribusi label (natural):")
for label, count in dist.items():
    print(f"   {label:<10}: {count:>4} baris ({pct[label]}%)")

# ─────────────────────────────────────────────
# 8. CLEANUP KOLOM SEMENTARA
# ─────────────────────────────────────────────
df.drop(columns=["_kde_density"], inplace=True)

# ─────────────────────────────────────────────
# 9. SIMPAN OUTPUT
# ─────────────────────────────────────────────
print(f"\nMenyimpan hasil ke: {OUTPUT_PATH}")
cols_to_save = ['nama_wisata', 'kabupaten', 'provinsi', 'label_rekomendasi']
df[cols_to_save].to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
print(f"   SELESAI! {len(df):,} baris disimpan.")
print(f"\n{'='*55}")
print("   KOLOM BARU: skor_komposit | label_rekomendasi")
print(f"{'='*55}\n")
