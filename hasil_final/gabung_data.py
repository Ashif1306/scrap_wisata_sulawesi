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
FILE_KAB_PROV = os.path.join(BASE_DIR, "hasil_scrap", "kabupaten_provinsi.csv")

OUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_lengkap.csv")

# Provinsi yang valid di Sulawesi
VALID_PROVINSI = [
    'Sulawesi Selatan', 'Sulawesi Barat', 'Sulawesi Tengah',
    'Sulawesi Utara', 'Sulawesi Tenggara', 'Gorontalo'
]

# ── MAPPING STATIS KABUPATEN -> PROVINSI (sumber kebenaran mutlak) ──────────────
KAB_TO_PROVINSI = {
    # Sulawesi Selatan
    "Kota Makassar":"Sulawesi Selatan","Kota Palopo":"Sulawesi Selatan","Kota Parepare":"Sulawesi Selatan",
    "Kabupaten Bantaeng":"Sulawesi Selatan","Kabupaten Barru":"Sulawesi Selatan","Kabupaten Bone":"Sulawesi Selatan",
    "Kabupaten Bulukumba":"Sulawesi Selatan","Kabupaten Enrekang":"Sulawesi Selatan","Kabupaten Gowa":"Sulawesi Selatan",
    "Kabupaten Jeneponto":"Sulawesi Selatan","Kabupaten Kepulauan Selayar":"Sulawesi Selatan",
    "Kabupaten Luwu":"Sulawesi Selatan","Kabupaten Luwu Timur":"Sulawesi Selatan","Kabupaten Luwu Utara":"Sulawesi Selatan",
    "Kabupaten Maros":"Sulawesi Selatan","Kabupaten Pangkajene Dan Kepulauan":"Sulawesi Selatan",
    "Kabupaten Pinrang":"Sulawesi Selatan","Kabupaten Sidenreng Rappang":"Sulawesi Selatan",
    "Kabupaten Sinjai":"Sulawesi Selatan","Kabupaten Soppeng":"Sulawesi Selatan","Kabupaten Takalar":"Sulawesi Selatan",
    "Kabupaten Tana Toraja":"Sulawesi Selatan","Kabupaten Toraja Utara":"Sulawesi Selatan","Kabupaten Wajo":"Sulawesi Selatan",
    # Sulawesi Barat
    "Kabupaten Mamuju":"Sulawesi Barat","Kabupaten Majene":"Sulawesi Barat","Kabupaten Polewali Mandar":"Sulawesi Barat",
    "Kabupaten Mamasa":"Sulawesi Barat","Kabupaten Pasangkayu":"Sulawesi Barat","Kabupaten Mamuju Tengah":"Sulawesi Barat",
    # Sulawesi Tengah
    "Kota Palu":"Sulawesi Tengah","Kabupaten Banggai":"Sulawesi Tengah","Kabupaten Banggai Kepulauan":"Sulawesi Tengah",
    "Kabupaten Banggai Laut":"Sulawesi Tengah","Kabupaten Buol":"Sulawesi Tengah","Kabupaten Donggala":"Sulawesi Tengah",
    "Kabupaten Morowali":"Sulawesi Tengah","Kabupaten Morowali Utara":"Sulawesi Tengah",
    "Kabupaten Parigi Moutong":"Sulawesi Tengah","Kabupaten Poso":"Sulawesi Tengah","Kabupaten Sigi":"Sulawesi Tengah",
    "Kabupaten Tojo Una-Una":"Sulawesi Tengah","Kabupaten Tolitoli":"Sulawesi Tengah",
    # Sulawesi Utara
    "Kota Manado":"Sulawesi Utara","Kota Bitung":"Sulawesi Utara","Kota Tomohon":"Sulawesi Utara","Kota Kotamobagu":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow":"Sulawesi Utara","Kabupaten Bolaang Mongondow Selatan":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow Timur":"Sulawesi Utara","Kabupaten Bolaang Mongondow Utara":"Sulawesi Utara",
    "Kabupaten Kepulauan Sangihe":"Sulawesi Utara","Kabupaten Kepulauan Siau Tagulandang Biaro":"Sulawesi Utara",
    "Kabupaten Kepulauan Talaud":"Sulawesi Utara","Kabupaten Minahasa":"Sulawesi Utara",
    "Kabupaten Minahasa Selatan":"Sulawesi Utara","Kabupaten Minahasa Tenggara":"Sulawesi Utara","Kabupaten Minahasa Utara":"Sulawesi Utara",
    # Sulawesi Tenggara
    "Kota Kendari":"Sulawesi Tenggara","Kota Baubau":"Sulawesi Tenggara",
    "Kabupaten Bombana":"Sulawesi Tenggara","Kabupaten Buton":"Sulawesi Tenggara","Kabupaten Buton Selatan":"Sulawesi Tenggara",
    "Kabupaten Buton Tengah":"Sulawesi Tenggara","Kabupaten Buton Utara":"Sulawesi Tenggara",
    "Kabupaten Kolaka":"Sulawesi Tenggara","Kabupaten Kolaka Timur":"Sulawesi Tenggara","Kabupaten Kolaka Utara":"Sulawesi Tenggara",
    "Kabupaten Konawe":"Sulawesi Tenggara","Kabupaten Konawe Kepulauan":"Sulawesi Tenggara",
    "Kabupaten Konawe Selatan":"Sulawesi Tenggara","Kabupaten Konawe Utara":"Sulawesi Tenggara",
    "Kabupaten Muna":"Sulawesi Tenggara","Kabupaten Muna Barat":"Sulawesi Tenggara","Kabupaten Wakatobi":"Sulawesi Tenggara",
    # Gorontalo
    "Kota Gorontalo":"Gorontalo","Kabupaten Boalemo":"Gorontalo","Kabupaten Bone Bolango":"Gorontalo",
    "Kabupaten Gorontalo Utara":"Gorontalo","Kabupaten Pohuwato":"Gorontalo","Kabupaten Gorontalo":"Gorontalo",
}

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
        print(f"[Error] File harga tidak ditemukan: {FILE_HARGA}")
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
    
    df_final = df_base[cols_order].copy()
    
    # ── KOREKSI LOKASI DARI FILE KABUPATEN_PROVINSI ─────────────
    # Terapkan koreksi alamat, kabupaten, dan provinsi dari hasil_scrap/kabupaten_provinsi.csv
    print(f"\nMenerapkan koreksi lokasi dari: {os.path.basename(FILE_KAB_PROV)}")
    try:
        df_kab_prov = pd.read_csv(FILE_KAB_PROV)
        # Buat lookup dari place_id -> (alamat, kabupaten, provinsi, lat, long)
        fix_lookup = {}
        for _, row in df_kab_prov.iterrows():
            fix_lookup[row['place_id']] = {
                'alamat': row['alamat'],
                'kabupaten': row['kabupaten'],
                'provinsi': row['provinsi'],
                'lat': row['lat'],
                'long': row['long']
            }
        
        lokasi_fixed = 0
        for idx, row in df_final.iterrows():
            pid = row['place_id']
            if pid in fix_lookup:
                # Update kolom lokasi
                df_final.at[idx, 'alamat'] = fix_lookup[pid]['alamat']
                df_final.at[idx, 'kabupaten'] = fix_lookup[pid]['kabupaten']
                df_final.at[idx, 'provinsi'] = fix_lookup[pid]['provinsi']
                df_final.at[idx, 'lat'] = fix_lookup[pid]['lat']
                df_final.at[idx, 'long'] = fix_lookup[pid]['long']
                lokasi_fixed += 1
                
        print(f"Koreksi lokasi diterapkan: {lokasi_fixed} baris diperbarui.")
    except FileNotFoundError:
        print(f"[Warning] File koreksi tidak ditemukan: {FILE_KAB_PROV}. Melanjutkan tanpa koreksi tambahan.")
    except Exception as e:
        print(f"[Warning] Gagal menerapkan koreksi: {e}")
    
    # ── NORMALISASI PROVINSI (WAJIB — berdasarkan mapping statis resmi) ──────────
    # Ini menjamin provinsi SELALU benar sesuai kabupaten, apapun data sumbernya.
    prov_fixed = 0
    for idx, row in df_final.iterrows():
        kab = str(row['kabupaten']).strip()
        correct_prov = KAB_TO_PROVINSI.get(kab)
        if correct_prov and correct_prov != str(row['provinsi']).strip():
            df_final.at[idx, 'provinsi'] = correct_prov
            prov_fixed += 1
    if prov_fixed > 0:
        print(f"Normalisasi provinsi: {prov_fixed} baris dikoreksi otomatis.")

    # ── FILTER: HAPUS DATA DI LUAR SULAWESI ──────────────────
    len_before = len(df_final)
    df_final = df_final[df_final['provinsi'].isin(VALID_PROVINSI)]
    removed = len_before - len(df_final)
    if removed > 0:
        print(f"Menghapus {removed} data di luar Sulawesi.")
    
    print(f"\nMenyimpan file csv hasil akhir ke: {OUT_FILE}")
    df_final.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Data gabungan berhasil disimpan! Total: {len(df_final)} baris dan {len(df_final.columns)} kolom.")

if __name__ == "__main__":
    main()

