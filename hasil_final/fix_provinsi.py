"""
Fix kolom 'provinsi' supaya konsisten dengan kolom 'kabupaten'.
Menggunakan mapping statis kabupaten/kota -> provinsi yang 100% akurat.
"""
import pandas as pd
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE  = 'wisata_sulawesi_lengkap.csv'
OUTPUT_FIXED  = 'wisata_sulawesi_fixed.csv'
OUTPUT_LENGKAP = 'wisata_sulawesi_lengkap.csv'

# ── MAPPING STATIS: Kabupaten/Kota -> Provinsi ─────────────────────────────────
KAB_TO_PROVINSI = {
    # Sulawesi Selatan
    "Kota Makassar"                      : "Sulawesi Selatan",
    "Kota Palopo"                        : "Sulawesi Selatan",
    "Kota Parepare"                      : "Sulawesi Selatan",
    "Kabupaten Bantaeng"                 : "Sulawesi Selatan",
    "Kabupaten Barru"                    : "Sulawesi Selatan",
    "Kabupaten Bone"                     : "Sulawesi Selatan",
    "Kabupaten Bulukumba"                : "Sulawesi Selatan",
    "Kabupaten Enrekang"                 : "Sulawesi Selatan",
    "Kabupaten Gowa"                     : "Sulawesi Selatan",
    "Kabupaten Jeneponto"                : "Sulawesi Selatan",
    "Kabupaten Kepulauan Selayar"        : "Sulawesi Selatan",
    "Kabupaten Luwu"                     : "Sulawesi Selatan",
    "Kabupaten Luwu Timur"              : "Sulawesi Selatan",
    "Kabupaten Luwu Utara"              : "Sulawesi Selatan",
    "Kabupaten Maros"                    : "Sulawesi Selatan",
    "Kabupaten Pangkajene Dan Kepulauan": "Sulawesi Selatan",
    "Kabupaten Pinrang"                  : "Sulawesi Selatan",
    "Kabupaten Sidenreng Rappang"        : "Sulawesi Selatan",
    "Kabupaten Sinjai"                   : "Sulawesi Selatan",
    "Kabupaten Soppeng"                  : "Sulawesi Selatan",
    "Kabupaten Takalar"                  : "Sulawesi Selatan",
    "Kabupaten Tana Toraja"              : "Sulawesi Selatan",
    "Kabupaten Toraja Utara"             : "Sulawesi Selatan",
    "Kabupaten Wajo"                     : "Sulawesi Selatan",

    # Sulawesi Barat
    "Kabupaten Mamuju"                   : "Sulawesi Barat",
    "Kabupaten Majene"                   : "Sulawesi Barat",
    "Kabupaten Polewali Mandar"          : "Sulawesi Barat",
    "Kabupaten Mamasa"                   : "Sulawesi Barat",
    "Kabupaten Pasangkayu"               : "Sulawesi Barat",
    "Kabupaten Mamuju Tengah"            : "Sulawesi Barat",

    # Sulawesi Tengah
    "Kota Palu"                          : "Sulawesi Tengah",
    "Kabupaten Banggai"                  : "Sulawesi Tengah",
    "Kabupaten Banggai Kepulauan"        : "Sulawesi Tengah",
    "Kabupaten Banggai Laut"             : "Sulawesi Tengah",
    "Kabupaten Buol"                     : "Sulawesi Tengah",
    "Kabupaten Donggala"                 : "Sulawesi Tengah",
    "Kabupaten Morowali"                 : "Sulawesi Tengah",
    "Kabupaten Morowali Utara"           : "Sulawesi Tengah",
    "Kabupaten Parigi Moutong"           : "Sulawesi Tengah",
    "Kabupaten Poso"                     : "Sulawesi Tengah",
    "Kabupaten Sigi"                     : "Sulawesi Tengah",
    "Kabupaten Tojo Una-Una"             : "Sulawesi Tengah",
    "Kabupaten Tolitoli"                 : "Sulawesi Tengah",

    # Sulawesi Utara
    "Kota Manado"                        : "Sulawesi Utara",
    "Kota Bitung"                        : "Sulawesi Utara",
    "Kota Tomohon"                       : "Sulawesi Utara",
    "Kota Kotamobagu"                    : "Sulawesi Utara",
    "Kabupaten Bolaang Mongondow"        : "Sulawesi Utara",
    "Kabupaten Bolaang Mongondow Selatan": "Sulawesi Utara",
    "Kabupaten Bolaang Mongondow Timur"  : "Sulawesi Utara",
    "Kabupaten Bolaang Mongondow Utara"  : "Sulawesi Utara",
    "Kabupaten Kepulauan Sangihe"        : "Sulawesi Utara",
    "Kabupaten Kepulauan Siau Tagulandang Biaro": "Sulawesi Utara",
    "Kabupaten Kepulauan Talaud"         : "Sulawesi Utara",
    "Kabupaten Minahasa"                 : "Sulawesi Utara",
    "Kabupaten Minahasa Selatan"         : "Sulawesi Utara",
    "Kabupaten Minahasa Tenggara"        : "Sulawesi Utara",
    "Kabupaten Minahasa Utara"           : "Sulawesi Utara",

    # Sulawesi Tenggara
    "Kota Kendari"                       : "Sulawesi Tenggara",
    "Kota Baubau"                        : "Sulawesi Tenggara",
    "Kabupaten Bombana"                  : "Sulawesi Tenggara",
    "Kabupaten Buton"                    : "Sulawesi Tenggara",
    "Kabupaten Buton Selatan"            : "Sulawesi Tenggara",
    "Kabupaten Buton Tengah"             : "Sulawesi Tenggara",
    "Kabupaten Buton Utara"              : "Sulawesi Tenggara",
    "Kabupaten Kolaka"                   : "Sulawesi Tenggara",
    "Kabupaten Kolaka Timur"             : "Sulawesi Tenggara",
    "Kabupaten Kolaka Utara"             : "Sulawesi Tenggara",
    "Kabupaten Konawe"                   : "Sulawesi Tenggara",
    "Kabupaten Konawe Kepulauan"         : "Sulawesi Tenggara",
    "Kabupaten Konawe Selatan"           : "Sulawesi Tenggara",
    "Kabupaten Konawe Utara"             : "Sulawesi Tenggara",
    "Kabupaten Muna"                     : "Sulawesi Tenggara",
    "Kabupaten Muna Barat"               : "Sulawesi Tenggara",
    "Kabupaten Wakatobi"                 : "Sulawesi Tenggara",

    # Gorontalo
    "Kota Gorontalo"                     : "Gorontalo",
    "Kabupaten Boalemo"                  : "Gorontalo",
    "Kabupaten Bone Bolango"             : "Gorontalo",
    "Kabupaten Gorontalo Utara"          : "Gorontalo",
    "Kabupaten Pohuwato"                 : "Gorontalo",
    "Kabupaten Gorontalo"                : "Gorontalo",
}

def main():
    print("=" * 60)
    print("FIX KOLOM PROVINSI BERDASARKAN MAPPING STATIS KABUPATEN")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"Total data: {len(df)}")

    fixes = 0
    unknown = []

    for idx, row in df.iterrows():
        kab = str(row['kabupaten']).strip()
        old_prov = str(row['provinsi']).strip()

        new_prov = KAB_TO_PROVINSI.get(kab)

        if new_prov is None:
            unknown.append(kab)
            continue

        if new_prov != old_prov:
            print(f"  FIX: '{row['nama_wisata']}' | Kabupaten: {kab}")
            print(f"       Provinsi: '{old_prov}' -> '{new_prov}'")
            df.at[idx, 'provinsi'] = new_prov
            fixes += 1

    print(f"\nTotal provinsi dikoreksi: {fixes}")

    if unknown:
        unique_unknown = list(set(unknown))
        print(f"\nKabupaten tidak ada di mapping ({len(unique_unknown)}):")
        for u in sorted(unique_unknown):
            print(f"  - {u}")

    df.to_csv(OUTPUT_FIXED, index=False, encoding='utf-8-sig')
    df.to_csv(OUTPUT_LENGKAP, index=False, encoding='utf-8-sig')
    print(f"\nFile tersimpan: {OUTPUT_FIXED} & {OUTPUT_LENGKAP}")
    print("=" * 60)

if __name__ == "__main__":
    main()
