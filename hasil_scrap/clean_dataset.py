import pandas as pd
import os
import re

def main():
    # Menggunakan path relatif jika script dijalankan dari dalam folder hasil_scrap
    input_file = "wisata_sulawesi_20260418_120209.csv"
    output_file = "wisata_sulawesi_cleaned_final.csv"

    if not os.path.exists(input_file):
        print(f"Error: File {input_file} tidak ditemukan di folder saat ini.")
        return

    print("=== Membaca Data ===")
    df = pd.read_csv(input_file)
    initial_len = len(df)
    print(f"Total Data Awal: {initial_len} baris\n")

    # ---------------------------------------------------------
    # 1. Hapus yang review-nya di bawah 5
    # ---------------------------------------------------------
    df = df[df['jumlah_review'] >= 5]
    len_after_review = len(df)
    print(f"(-) Dihapus karena Review < 5 : {initial_len - len_after_review} data")

    # ---------------------------------------------------------
    # 2. Hapus data yang tidak memiliki image
    # ---------------------------------------------------------
    len_before_image = len(df)
    df = df[df['image'].notna()]
    df = df[df['image'].str.strip() != ""]
    len_after_image = len(df)
    print(f"(-) Dihapus karena tanpa Image: {len_before_image - len_after_image} data")

    # ---------------------------------------------------------
    # 3. Hapus keyword nama yang BUKAN objek wisata
    # ---------------------------------------------------------
    len_before_kw = len(df)
    
    # Kumpulan keyword yang menjurus ke tempat usaha komunitas/bisnis biasa
    # Menggunakan \b (word boundary) agar tidak salah potong, 
    # e.g., tidak memotong nama "Pantai Kostajaya" karena ada kata lost/kost dll.
    suspect_keywords = [
        'hotel', 'penginapan', 'kos', 'kost', 'sekolah', 'puskesmas', 
        'apotek', 'warung', 'toko', 'klinik', 'rs', 'rumah sakit', 
        'universitas', 'kampus', 'laundry', 'bengkel', 'pt', 'cv',
        'kantor', 'dinas', 'kecamatan', 'kelurahan', 'wisma', 'pabrik',
        'cafe', 'kafe', 'warkop', 'kedai', 'dealer', 'homestay', 'villa', 
        'salon', 'pasar', 'minimarket', 'alfamart', 'indomaret', 'spa'
    ]
    
    pattern = r'(?i)\b(' + '|'.join(suspect_keywords) + r')\b'
    is_suspect = df['nama_wisata'].str.contains(pattern, na=False, regex=True)
    
    # Tampilkan sample apa saja yang ditendang oleh filter keyword (opsional audit)
    ditendang = df[is_suspect]
    df = df[~is_suspect]
    len_after_kw = len(df)
    
    print(f"(-) Dihapus karena Nama Usaha : {len_before_kw - len_after_kw} data")
    if len_before_kw - len_after_kw > 0:
        print("    -> Contoh yang terhapus:", list(ditendang['nama_wisata'].head(5)))

    # ---------------------------------------------------------
    # 4. Deduplikasi nama yang sama di satu Kabupaten/Kota
    # ---------------------------------------------------------
    len_before_dedup = len(df)
    
    # Ekstrak kota sementara dan nama kecil untuk matching
    df['kota_temp'] = df['alamat'].str.extract(r'(?:Kabupaten|Kota)\s+([^,]+)', flags=re.IGNORECASE, expand=False).str.strip().str.lower()
    df['nama_temp'] = df['nama_wisata'].str.lower().str.strip()
    
    # Urutkan dari review terbanyak & rating tertinggi, lalu buang duplikat nama+kota
    df = df.sort_values(by=['jumlah_review', 'rating'], ascending=[False, False])
    df = df.drop_duplicates(subset=['nama_temp', 'kota_temp'], keep='first')
    
    len_after_dedup = len(df)
    print(f"(-) Dihapus karena Duplikat Maps : {len_before_dedup - len_after_dedup} data")
    if len_before_dedup - len_after_dedup > 0:
        print("    -> Menyimpan titik resmi yang memiliki review terbanyak.")
        
    df = df.drop(columns=['kota_temp', 'nama_temp'])

    # ---------------------------------------------------------
    # 5. Extract Kabupaten & Provinsi
    # ---------------------------------------------------------
    # Ekstrak Kabupaten/Kota dan di-title case
    df['kabupaten'] = df['alamat'].str.extract(r'(Kabupaten\s+[^,]+|Kota\s+[^,]+)', flags=re.IGNORECASE, expand=False).str.strip().str.title()
    
    # Ekstrak Provinsi dan di-title case
    provinsi_pattern = r'(Sulawesi\s+Selatan|Sulawesi\s+Utara|Sulawesi\s+Tengah|Sulawesi\s+Tenggara|Sulawesi\s+Barat|Gorontalo)'
    df['provinsi'] = df['alamat'].str.extract(provinsi_pattern, flags=re.IGNORECASE, expand=False).str.strip().str.title()

    # ---------------------------------------------------------
    # Simpan hasil akhir
    # ---------------------------------------------------------
    print("\n=== Ringkasan Akhir ===")
    print(f"Total Data Akhir yang Bersih: {len(df)} baris")
    
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"Tersimpan di file: {output_file}")

if __name__ == "__main__":
    main()
