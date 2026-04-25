"""
fix_sisa_26.py
==============
Perbaikan manual berdasarkan analisis alamat untuk 26 data yang masih out-of-bbox.
Dilakukan per-kasus karena ini data yang memang ambigu (kepulauan, perbatasan, dll).
"""

import pandas as pd

file_path = 'd:/semester6/mc_learning/scrapt_wisata/hasil_final/wisata_sulawesi_lengkap.csv'
df = pd.read_csv(file_path)

KAB_TO_PROV = {
    'Kota Makassar':'Sulawesi Selatan','Kota Palopo':'Sulawesi Selatan','Kota Parepare':'Sulawesi Selatan',
    'Kabupaten Bantaeng':'Sulawesi Selatan','Kabupaten Barru':'Sulawesi Selatan','Kabupaten Bone':'Sulawesi Selatan',
    'Kabupaten Bulukumba':'Sulawesi Selatan','Kabupaten Enrekang':'Sulawesi Selatan','Kabupaten Gowa':'Sulawesi Selatan',
    'Kabupaten Jeneponto':'Sulawesi Selatan','Kabupaten Kepulauan Selayar':'Sulawesi Selatan',
    'Kabupaten Luwu':'Sulawesi Selatan','Kabupaten Luwu Timur':'Sulawesi Selatan','Kabupaten Luwu Utara':'Sulawesi Selatan',
    'Kabupaten Maros':'Sulawesi Selatan','Kabupaten Pangkajene Dan Kepulauan':'Sulawesi Selatan',
    'Kabupaten Pinrang':'Sulawesi Selatan','Kabupaten Sidenreng Rappang':'Sulawesi Selatan',
    'Kabupaten Sinjai':'Sulawesi Selatan','Kabupaten Soppeng':'Sulawesi Selatan','Kabupaten Takalar':'Sulawesi Selatan',
    'Kabupaten Tana Toraja':'Sulawesi Selatan','Kabupaten Toraja Utara':'Sulawesi Selatan','Kabupaten Wajo':'Sulawesi Selatan',
    'Kabupaten Mamuju':'Sulawesi Barat','Kabupaten Majene':'Sulawesi Barat','Kabupaten Polewali Mandar':'Sulawesi Barat',
    'Kabupaten Mamasa':'Sulawesi Barat','Kabupaten Pasangkayu':'Sulawesi Barat','Kabupaten Mamuju Tengah':'Sulawesi Barat',
    'Kota Palu':'Sulawesi Tengah','Kabupaten Banggai':'Sulawesi Tengah','Kabupaten Banggai Kepulauan':'Sulawesi Tengah',
    'Kabupaten Banggai Laut':'Sulawesi Tengah','Kabupaten Buol':'Sulawesi Tengah','Kabupaten Donggala':'Sulawesi Tengah',
    'Kabupaten Morowali':'Sulawesi Tengah','Kabupaten Morowali Utara':'Sulawesi Tengah',
    'Kabupaten Parigi Moutong':'Sulawesi Tengah','Kabupaten Poso':'Sulawesi Tengah','Kabupaten Sigi':'Sulawesi Tengah',
    'Kabupaten Tojo Una-Una':'Sulawesi Tengah','Kabupaten Tolitoli':'Sulawesi Tengah',
    'Kota Manado':'Sulawesi Utara','Kota Bitung':'Sulawesi Utara','Kota Tomohon':'Sulawesi Utara','Kota Kotamobagu':'Sulawesi Utara',
    'Kabupaten Bolaang Mongondow':'Sulawesi Utara','Kabupaten Bolaang Mongondow Selatan':'Sulawesi Utara',
    'Kabupaten Bolaang Mongondow Timur':'Sulawesi Utara','Kabupaten Bolaang Mongondow Utara':'Sulawesi Utara',
    'Kabupaten Kepulauan Sangihe':'Sulawesi Utara','Kabupaten Kepulauan Siau Tagulandang Biaro':'Sulawesi Utara',
    'Kabupaten Kepulauan Talaud':'Sulawesi Utara','Kabupaten Minahasa':'Sulawesi Utara',
    'Kabupaten Minahasa Selatan':'Sulawesi Utara','Kabupaten Minahasa Tenggara':'Sulawesi Utara','Kabupaten Minahasa Utara':'Sulawesi Utara',
    'Kota Kendari':'Sulawesi Tenggara','Kota Baubau':'Sulawesi Tenggara',
    'Kabupaten Bombana':'Sulawesi Tenggara','Kabupaten Buton':'Sulawesi Tenggara','Kabupaten Buton Selatan':'Sulawesi Tenggara',
    'Kabupaten Buton Tengah':'Sulawesi Tenggara','Kabupaten Buton Utara':'Sulawesi Tenggara',
    'Kabupaten Kolaka':'Sulawesi Tenggara','Kabupaten Kolaka Timur':'Sulawesi Tenggara','Kabupaten Kolaka Utara':'Sulawesi Tenggara',
    'Kabupaten Konawe':'Sulawesi Tenggara','Kabupaten Konawe Kepulauan':'Sulawesi Tenggara',
    'Kabupaten Konawe Selatan':'Sulawesi Tenggara','Kabupaten Konawe Utara':'Sulawesi Tenggara',
    'Kabupaten Muna':'Sulawesi Tenggara','Kabupaten Muna Barat':'Sulawesi Tenggara','Kabupaten Wakatobi':'Sulawesi Tenggara',
    'Kota Gorontalo':'Gorontalo','Kabupaten Boalemo':'Gorontalo','Kabupaten Bone Bolango':'Gorontalo',
    'Kabupaten Gorontalo Utara':'Gorontalo','Kabupaten Pohuwato':'Gorontalo','Kabupaten Gorontalo':'Gorontalo',
}

# Perbaikan per nama wisata berdasarkan analisis teks alamat di atas
# Format: (nama_wisata_exact, kabupaten_baru, alasan)
FIXES_MANUAL = [
    # Kolaka Utara sebenarnya (alamat menyebut Kab. Kolaka Utara): bbox saja yang terlalu ketat
    # Biarkan → mereka memang di Kolaka Utara (lat -3.7 ada di selatan bbox, tapi nama kecamatan = Kab. Kolaka Utara)
    # Pantai Tamborasi → alamat jelas: Kec. Wolo, Kabupaten Kolaka (bukan Kolaka Utara)
    ("Pantai Tamborasi",                            "Kabupaten Kolaka",              "Alamat: Kec.Wolo Kab.Kolaka"),
    # Pantai Sabang Toli-Toli → alamat: Toli-Toli Regency
    ("Pantai Sabang Toli toli",                     "Kabupaten Tolitoli",            "Alamat: Toli-Toli Regency"),
    # PULAU SABANG TENDE → alamat: Kab. Toli-Toli
    ("PULAU SABANG TENDE",                          "Kabupaten Tolitoli",            "Alamat: Kab.Toli-Toli"),
    # Pijar Beach (Lalos, Kab. Toli-Toli)
    ("Pijar Beach Cottages",                        "Kabupaten Tolitoli",            "Alamat: Lalos Kab.Toli-Toli"),
    # Zalza Beach (Lalos, Kab. Toli-Toli)
    ("Zalza Beach",                                 "Kabupaten Tolitoli",            "Alamat: Lalos Kab.Toli-Toli"),
    # Pantai Lalos (Lalos, Kab. Toli-Toli)
    ("Pantai Lalos",                                "Kabupaten Tolitoli",            "Alamat: Lalos Kab.Toli-Toli"),
    ("Lalos",                                       "Kabupaten Tolitoli",            "Alamat: Kab.Toli-Toli"),
    # Mandel Beach & Pantai Mandel → alamat: Kombutokan, Kabupaten Banggai Kepulauan
    ("Mandel Beach",                                "Kabupaten Banggai Kepulauan",   "Alamat: Kab.Banggai Kepulauan"),
    ("Pantai Mandel",                               "Kabupaten Banggai Kepulauan",   "Alamat: Kab.Banggai Kepulauan"),
    # Wisata Bone Pompon → alamat: Kab.Banggai Kepulauan
    ("Wisata Bone Pompon",                          "Kabupaten Banggai Kepulauan",   "Alamat: Kab.Banggai Kepulauan"),
    # AIR TERJUN TETENU → alamat: Kab.Banggai Kepulauan
    ("AIR TERJUN TETENU",                           "Kabupaten Banggai Kepulauan",   "Alamat: Kab.Banggai Kepulauan"),
    # Wisata Pasir Putih Pompon → alamat: Kab.Banggai Kepulauan
    ("Wisata Pasir Putih Pompon",                   "Kabupaten Banggai Kepulauan",   "Alamat: Kab.Banggai Kepulauan"),
    # Weer Molino → alamat: Kec.Balantak Sel., Kabupaten Banggai (bukan Banggai Kepulauan)
    ("Weer Molino",                                 "Kabupaten Banggai",             "Alamat: Kec.Balantak Sel.,Kab.Banggai"),
    # Danau "Cinta" Makalehi → di Kepulauan SITARO
    ("Danau \"Cinta\" Makalehi",                    "Kabupaten Kepulauan Siau Tagulandang Biaro", "Alamat: Siau Tagulandang Biaro"),
    # Pulau Kodingareng Keke → Kota Makassar (pulau barat Makassar, koordinat di laut)
    ("Pulau Kodingareng Keke",                      "Kota Makassar",                 "Alamat: Kota Makassar"),
    # Pantai Kasambang → alamat: Kec.Tapalang, Kab.Mamuju (bukan Majene)
    ("Pantai Kasambang",                            "Kabupaten Mamuju",              "Alamat: Kec.Tapalang Kab.Mamuju"),
    # Tanjung Ngalo Mamuju → alamat: Kota Makassar (tapi ini jelas Mamuju dari namanya)
    # Koordinat -2.86,118.76 → wilayah Mamuju Selatan. Pertahankan Mamuju.
    # WAWONTULAP BEACH → alamat: Kab.Minahasa Selatan
    ("WAWONTULAP BEACH RESORT (WBR)",               "Kabupaten Minahasa Selatan",    "Alamat: Kab.Minahasa Selatan"),
    ("Wisata Pantai Pasir Putih Wawontulap",        "Kabupaten Minahasa Selatan",    "Alamat: Kab.Minahasa Selatan"),
    # Pantai Ujung Batuatas → koordinat -6.2,122.7 → Kepulauan Buton, tetap Buton
    # Pantai Timur Jiko Belanga → alamat: Kab.Bolaang Mongondow Timur
    ("Pantai Timur, Jiko Belanga - Boltim",         "Kabupaten Bolaang Mongondow Timur", "Alamat: Kab.Bolaang Mongondow Timur"),
    # Pulau Kawaluso → alamat: Kab.Kepulauan Sangihe (lat 4.2 masih Sangihe wilayah kepulauan)
    # GOA TAPPARANG → alamat: Kab.Kolaka Utara (bbox saja yang ketat di sisi barat)
    ("Pantai Pelangi",                              "Kabupaten Kolaka Utara",        "Alamat: Kec.Rante Angin, Kab.Kolaka Utara"),
]

fixes = 0
for (nama, kab_baru, alasan) in FIXES_MANUAL:
    mask = df['nama_wisata'] == nama
    if mask.sum() > 0:
        kab_lama = df.loc[mask, 'kabupaten'].values[0]
        if kab_lama != kab_baru:
            df.loc[mask, 'kabupaten'] = kab_baru
            df.loc[mask, 'provinsi'] = KAB_TO_PROV.get(kab_baru, df.loc[mask, 'provinsi'].values[0])
            print(f"[FIX] {nama}: {kab_lama} -> {kab_baru} ({alasan})")
            fixes += 1

print(f"\nTotal fix: {fixes}")
if fixes > 0:
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"Tersimpan ke {file_path}")
