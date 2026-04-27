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
FILE_SCRAPED = os.path.join(BASE_DIR, "lokasi_gmaps", "lokasi_scraped.csv")
FILE_NOKAB = os.path.join(BASE_DIR, "lokasi_gmaps", "wisata_no_kab.csv")

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
    
    # ── KOREKSI KABUPATEN DARI HASIL SCRAPING GMAPS & NOMINATIM ─────────────
    print(f"\nMenerapkan hasil scraping lokasi (Playwright & Nominatim)...")
    
    # Tambah kolom default dihapus sesuai permintaan
            
    # Status validasi
    OK_GMAPS_COORD = {"OK_GEO", "GEO_WIN"}
    OK_GMAPS_TEXT  = {"OK_TEXT", "TEXT_WIN"}
    OK_DDG         = {"OK_REVERSE", "OK_FORWARD", "OK_NAME", "OK_ORIGINAL"}

    def clean(v):
        s = str(v).strip()
        return "" if s in ("nan", "None", "NaT") else s

    scraped_map = {}
    try:
        df_scraped = pd.read_csv(FILE_SCRAPED, dtype=str)
        for _, r in df_scraped.iterrows():
            pid = clean(r.get('place_id', ''))
            st = clean(r.get('status_gmaps', ''))
            kab_ori = clean(r.get('kabupaten', ''))
            kab_gmaps = clean(r.get('kabupaten_gmaps', ''))
            
            if not pid: continue
            
            if st in OK_GMAPS_COORD and kab_gmaps:
                kab_final = kab_gmaps
                st_final = st
            elif kab_ori:
                kab_final = kab_ori
                st_final = f"TEXT_ONLY_{st}" if st in OK_GMAPS_TEXT else (f"ORIG_{st}" if st else "ORIG")
            else:
                continue

            scraped_map[pid] = {
                'kab': kab_final,
                'alamat': clean(r.get('alamat_gmaps', '')),
                'lat': clean(r.get('lat_gmaps', '')),
                'lon': clean(r.get('lon_gmaps', '')),
                'status': st_final
            }
        print(f"  > Dimuat {len(scraped_map)} data valid dari lokasi_scraped.csv")
    except Exception as e:
        print(f"  > [Warning] Gagal baca {FILE_SCRAPED}: {e}")

    ddg_map = {}
    try:
        df_nokab = pd.read_csv(FILE_NOKAB, dtype=str)
        for _, r in df_nokab.iterrows():
            pid = clean(r.get('place_id', ''))
            st = clean(r.get('status_ddg', ''))
            kab = clean(r.get('kab_ddg', ''))
            if pid and st in OK_DDG and kab:
                ddg_map[pid] = {
                    'kab': kab,
                    'alamat': clean(r.get('alamat_gmaps', '')),
                    'lat': clean(r.get('lat_gmaps', '')),
                    'lon': clean(r.get('lon_gmaps', '')),
                    'status': f"NOMINATIM_{st}"
                }
        print(f"  > Dimuat {len(ddg_map)} data valid dari wisata_no_kab.csv")
    except Exception as e:
        pass

    lokasi_fixed = 0
    for idx, row in df_final.iterrows():
        pid = row['place_id']
        src = None
        if pid in scraped_map:
            src = scraped_map[pid]
        elif pid in ddg_map:
            src = ddg_map[pid]
            
        if src:
            old_kab = str(row['kabupaten']).strip()
            if src['kab'] and src['kab'] != old_kab:
                df_final.at[idx, 'kabupaten'] = src['kab']
                lokasi_fixed += 1
            pass

    print(f"  > Selesai merge. {lokasi_fixed} kabupaten diperbarui.")
    
    # ── NORMALISASI PROVINSI (WAJIB — berdasarkan mapping statis 81 kab/kota) ──────────
    # Provinsi SELALU diturunkan dari KAB_TO_PROVINSI, bukan dari sumber data manapun.
    prov_fixed = 0
    prov_unknown = 0
    for idx, row in df_final.iterrows():
        kab = str(row['kabupaten']).strip()
        correct_prov = KAB_TO_PROVINSI.get(kab)
        if correct_prov:
            if correct_prov != str(row['provinsi']).strip():
                df_final.at[idx, 'provinsi'] = correct_prov
                prov_fixed += 1
        else:
            prov_unknown += 1
    print(f"Normalisasi provinsi: {prov_fixed} baris dikoreksi dari mapping 81 kab/kota.")
    if prov_unknown > 0:
        print(f"[Warning] {prov_unknown} baris memiliki kabupaten yang tidak terdaftar di mapping.")

    # ── FILTER: HAPUS DATA DI LUAR SULAWESI ──────────────────
    len_before = len(df_final)
    df_final = df_final[df_final['provinsi'].isin(VALID_PROVINSI)]
    removed = len_before - len(df_final)
    if removed > 0:
        print(f"Menghapus {removed} data di luar Sulawesi.")

    # ── PRESERVASI BARIS DARI CSV/SUPABASE YANG TIDAK ADA DI BASE ────────
    # Baris yang ditambahkan manual via deployment (Supabase) tidak ada di
    # file scraping dasar. Kita pulihkan baris tersebut dari CSV lama.
    if os.path.exists(OUT_FILE):
        print(f"\nMemeriksa data existing untuk preservasi ...")
        try:
            df_existing = pd.read_csv(OUT_FILE, dtype=str)
            # Cari baris yang ada di CSV lama tapi tidak ada di base baru
            existing_ids = set(df_existing['place_id'].dropna())
            new_ids = set(df_final['place_id'].dropna())
            missing_ids = existing_ids - new_ids
            if missing_ids:
                df_missing = df_existing[df_existing['place_id'].isin(missing_ids)].copy()
                # Pastikan kolom sama (ambil kolom yang cocok saja)
                common_cols = [c for c in df_final.columns if c in df_missing.columns]
                df_missing = df_missing[common_cols]
                df_final = pd.concat([df_final, df_missing], ignore_index=True)
                print(f"  > Dipulihkan {len(df_missing)} baris data yang sebelumnya ada (ditambah manual/Supabase).")
            else:
                print(f"  > Tidak ada baris yang hilang, semua data sudah lengkap.")
        except Exception as e:
            print(f"  > [Warning] Gagal membaca CSV existing: {e}")

    # ── MERGE LABEL REKOMENDASI ──────────────────────────────
    FILE_LABEL = os.path.join(SCRIPT_DIR, "wisata_sulawesi_label.csv")
    print(f"\nMenggabungkan label rekomendasi dari: {os.path.basename(FILE_LABEL)}")
    try:
        df_label = pd.read_csv(FILE_LABEL)
        # Ambil hanya kolom yang dibutuhkan untuk join
        df_label = df_label[['nama_wisata', 'label_rekomendasi']].drop_duplicates(subset='nama_wisata')
        len_before_merge = len(df_final)
        df_final = df_final.merge(df_label, on='nama_wisata', how='left')
        matched = df_final['label_rekomendasi'].notna().sum()
        missing = df_final['label_rekomendasi'].isna().sum()
        print(f"  > {matched} destinasi berhasil dilabeli.")
        if missing > 0:
            print(f"  > [Warning] {missing} destinasi tidak memiliki label (akan diisi 'Belum Dinilai').")
            df_final['label_rekomendasi'] = df_final['label_rekomendasi'].fillna('Belum Dinilai')
    except FileNotFoundError:
        print(f"  > [Warning] File label tidak ditemukan: {FILE_LABEL}")
        print(f"  > Jalankan label_rekomendasi.py terlebih dahulu!")
        df_final['label_rekomendasi'] = 'Belum Dinilai'

    print(f"\nMenyimpan file csv hasil akhir ke: {OUT_FILE}")
    df_final.to_csv(OUT_FILE, index=False, encoding="utf-8-sig")
    print(f"Data gabungan berhasil disimpan! Total: {len(df_final)} baris dan {len(df_final.columns)} kolom.")

if __name__ == "__main__":
    main()

