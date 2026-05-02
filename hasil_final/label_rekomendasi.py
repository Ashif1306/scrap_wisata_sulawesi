"""
label_rekomendasi.py
====================
Feature Engineering: Pembuatan Kolom Label Rekomendasi
-------------------------------------------------------
Tujuan : Membuat variabel target 'label_rekomendasi' (Terbaik/Baik/Sedang/Buruk)
         untuk model klasifikasi Random Forest destinasi wisata Sulawesi.

Metode :
  1. Data Cleaning         – handle missing values
  2. Kualitas Tertimbang   – Bayesian Average Rating (penilaian kualitas sesungguhnya)
  3. Normalisasi           – MinMaxScaler per fitur (log1p untuk outlier)
  4. Mapping Kategori Harga– bobot numerik untuk variabel teks
  5. Skor Komposit         – weighted sum 5 dimensi
  6. Pelabelan Threshold Alami – berbasis mean±std (distribusi natural)

Output : wisata_sulawesi_label.csv (tersimpan di folder hasil_final/)
"""

import numpy as np
import pandas as pd
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
# 3. KUALITAS TERTIMBANG (Bayesian Average Rating)
# ─────────────────────────────────────────────
print("\n[3/7] Menghitung kualitas tertimbang (Bayesian Average) ...")

# Menghitung parameter Bayesian
# C = rata-rata rating seluruh destinasi
# m = jumlah review minimum (menggunakan median sebagai batas wajar)
C = df["rating"].mean()
m = df["jumlah_riview"].median()

def bayesian_rating(row):
    v = row["jumlah_riview"]
    R = row["rating"]
    # Jika total vote + min_vote = 0 (data kosong), fallback ke mean global
    return (v / (v + m) * R) + (m / (v + m) * C) if (v + m) > 0 else C

df["_kualitas_bayesian"] = df.apply(bayesian_rating, axis=1)
print(f"   Bayesian Average selesai. Range: [{df['_kualitas_bayesian'].min():.4f}, {df['_kualitas_bayesian'].max():.4f}]")


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

# 4d. Kualitas Tertimbang
norm_bayesian = normalize(df["_kualitas_bayesian"])

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
#   30% rating | 20% review | 20% Bayesian | 15% harga | 15% kat_harga
# ─────────────────────────────────────────────
print("\n[6/7] Menghitung skor komposit ...")

WEIGHTS = {
    "rating"    : 0.30,
    "review"    : 0.20,
    "bayesian"  : 0.20,
    "harga"     : 0.15,
    "kat_harga" : 0.15,
}

df["skor_komposit"] = (
    WEIGHTS["rating"]    * norm_rating    +
    WEIGHTS["review"]    * norm_review    +
    WEIGHTS["bayesian"]  * norm_bayesian  +
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
df.drop(columns=["_kualitas_bayesian"], inplace=True)

# ─────────────────────────────────────────────
# 9. SIMPAN OUTPUT
# ─────────────────────────────────────────────
print(f"\nMenyimpan hasil ke: {OUTPUT_PATH}")
cols_to_save = ['nama_wisata', 'kabupaten', 'provinsi', 'label_rekomendasi']
df[cols_to_save].to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

print(f"Mengupdate data lengkap ke: {INPUT_PATH}")
# Kita hapus skor_komposit agar skema tetap sama dengan database Supabase
if "skor_komposit" in df.columns:
    df.drop(columns=["skor_komposit"], inplace=True)
df.to_csv(INPUT_PATH, index=False, encoding="utf-8-sig")

print(f"   SELESAI! {len(df):,} baris diperbarui di kedua file.")
print(f"\n{'='*55}")
print("   LABEL REKOMENDASI BERHASIL DIUPDATE")
print(f"{'='*55}\n")
