import os
import pandas as pd

# ── KONFIGURASI PATH ──────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Karena dipindah ke folder hasil_final, base directory adalah folder di atasnya
BASE_DIR = os.path.join(SCRIPT_DIR, "..")

FILE_BASE = os.path.join(BASE_DIR, "hasil_scrap", "wisata_sulawesi_kategori_ai.csv")
FILE_HARGA = os.path.join(BASE_DIR, "harga", "scrap_harga_wisata.csv")
FILE_DESK = os.path.join(BASE_DIR, "deskripsi", "scrap_deskripsi_wisata.csv")
FILE_IMAGE = os.path.join(BASE_DIR, "image", "scrap_image.csv")

OUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_lengkap.csv")

def main():
    print("=" * 50)
    print("PROSES PENGGABUNGAN DATA SCRAPING")
    print("=" * 50)
    
    # 1. Load Base Data
    print(f"Membaca data dasar: {os.path.basename(FILE_BASE)}")
    try:
        df_base = pd.read_csv(FILE_BASE)
    except FileNotFoundError:
        print(f"[Error] File dasar tidak ditemukan: {FILE_BASE}")
        return
        
    # 2. Load Data Harga
    print(f"Membaca data harga: {os.path.basename(FILE_HARGA)}")
    try:
        df_harga = pd.read_csv(FILE_HARGA)
        df_harga = df_harga.rename(columns={'nama wisata': 'nama_wisata'})
    except FileNotFoundError:
        print(f"[Error] File harga rtidak ditemukan: {FILE_HARGA}")
        return
        
    # 3. Load Data Deskripsi
    print(f"Membaca data deskripsi: {os.path.basename(FILE_DESK)}")
    try:
        df_desk = pd.read_csv(FILE_DESK)
    except FileNotFoundError:
        print(f"[Error] File deskripsi tidak ditemukan: {FILE_DESK}")
        return
        
    # 4. Load Data Image
    print(f"Membaca data image: {os.path.basename(FILE_IMAGE)}")
    try:
        df_image = pd.read_csv(FILE_IMAGE)
        df_image = df_image.rename(columns={'nama wisata': 'nama_wisata', 'lokasi': 'alamat'})
    except FileNotFoundError:
        print(f"[Error] File image tidak ditemukan: {FILE_IMAGE}")
        return
        
    print("\nMelakukan penggabungan data...")
    # Base data length
    len_base = len(df_base)
    print(f"Jumlah baris awal: {len_base}")
    
    # Kita hanya butuh kolom tambahan dari tiap dataframe
    if len(df_harga) == len_base:
        df_base['harga'] = df_harga['harga_rp']
        df_base['kategori_harga'] = df_harga['kategori_harga']
        df_base['url_harga'] = df_harga['url_harga']
    else:
        # Fallback merge
        df_harga_subset = df_harga[['nama_wisata', 'alamat', 'harga_rp', 'kategori_harga', 'url_harga']].drop_duplicates()
        df_base = df_base.merge(df_harga_subset, on=['nama_wisata', 'alamat'], how='left')
        df_base = df_base.rename(columns={'harga_rp': 'harga'})

    if len(df_desk) == len_base:
        df_base['deskripsi_wisata'] = df_desk['deskripsi_wisata']
        df_base['sumber_deskripsi'] = df_desk['sumber_deskripsi']
    else:
        # Fallback merge
        df_desk_subset = df_desk[['nama_wisata', 'alamat', 'deskripsi_wisata', 'sumber_deskripsi']].drop_duplicates()
        df_base = df_base.merge(df_desk_subset, on=['nama_wisata', 'alamat'], how='left')
        
    if len(df_image) == len_base:
        df_base['url_image'] = df_image['url_image']
    else:
        # Fallback merge
        df_image_subset = df_image[['nama_wisata', 'alamat', 'url_image']].drop_duplicates()
        df_base = df_base.merge(df_image_subset, on=['nama_wisata', 'alamat'], how='left')
        
    # Pastikan mengganti nama kolom jumlah_review menjadi jumlah_riview jika user meminta eksplisit
    # Walaupun biasanya review ditulis jumlah_review.
    if 'jumlah_review' in df_base.columns:
        df_base = df_base.rename(columns={'jumlah_review': 'jumlah_riview'})
        
    # Mengatur urutan kolom sesuai permintaan:
    # place_id, nama_wisata, kategori, alamat, kabupaten, provinsi, rating, jumlah_riview, 
    # harga, kategori_harga, url_harga, lat, long, url_image, deskripsi_wisata, sumber_deskripsi
    
    # Periksa kolom yang tersedia
    cols_order = [
        col for col in [
            'place_id', 'nama_wisata', 'kategori', 'alamat', 'kabupaten', 'provinsi', 
            'rating', 'jumlah_riview', 'harga', 'kategori_harga', 'url_harga', 'lat', 'long', 
            'url_image', 'deskripsi_wisata', 'sumber_deskripsi'
        ] if col in df_base.columns
    ]
    
    df_final = df_base[cols_order]
    
    print(f"\nMenyimpan file csv hasil akhir ke: {OUT_FILE}")
    df_final.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Data gabungan berhasil disimpan! Total: {len(df_final)} baris dan {len(df_final.columns)} kolom.")

if __name__ == "__main__":
    main()
