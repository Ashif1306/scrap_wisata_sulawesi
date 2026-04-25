import pandas as pd
import math
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(SCRIPT_DIR, 'kabupaten_provinsi.csv')

# ── BOUNDING BOX PER KABUPATEN/KOTA (lat_min, lat_max, long_min, long_max) ──────
KAB_BBOX = {
    "Kota Makassar":                       (-5.27, -5.05, 119.34, 119.58),
    "Kabupaten Gowa":                       (-5.80, -4.80, 119.40, 120.50),
    "Kabupaten Maros":                      (-5.20, -4.60, 119.55, 120.15),
    "Kabupaten Pangkajene Dan Kepulauan":   (-4.95, -4.35, 119.35, 119.85),
    "Kabupaten Barru":                      (-4.65, -3.85, 119.60, 120.05),
    "Kabupaten Bone":                       (-5.10, -3.60, 119.75, 120.65),
    "Kabupaten Sinjai":                     (-5.45, -4.75, 119.85, 120.45),
    "Kabupaten Bulukumba":                  (-5.85, -5.10, 119.90, 120.60),
    "Kabupaten Bantaeng":                   (-5.75, -5.25, 119.70, 120.15),
    "Kabupaten Jeneponto":                  (-5.85, -5.35, 119.35, 120.05),
    "Kabupaten Takalar":                    (-5.65, -5.15, 119.30, 119.80),
    "Kabupaten Kepulauan Selayar":          (-7.20, -5.60, 120.20, 121.10),
    "Kabupaten Enrekang":                   (-3.90, -2.95, 119.55, 120.20),
    "Kabupaten Sidenreng Rappang":          (-4.35, -3.55, 119.70, 120.25),
    "Kabupaten Pinrang":                    (-4.45, -3.20, 119.35, 120.10),
    "Kabupaten Luwu":                       (-3.55, -2.40, 120.05, 120.65),
    "Kabupaten Luwu Utara":                 (-2.80, -2.25, 119.90, 120.75),
    "Kabupaten Luwu Timur":                 (-2.90, -2.05, 120.70, 121.90),
    "Kabupaten Tana Toraja":                (-3.50, -2.55, 119.45, 120.30),
    "Kabupaten Toraja Utara":               (-3.30, -2.55, 119.65, 120.35),
    "Kabupaten Soppeng":                    (-4.45, -3.75, 119.70, 120.25),
    "Kabupaten Wajo":                       (-4.35, -3.35, 119.85, 120.65),
    "Kota Parepare":                        (-4.08, -3.93, 119.58, 119.78),
    "Kota Palopo":                          (-3.08, -2.92, 120.16, 120.30),

    "Kabupaten Mamuju":                     (-2.65, -1.65, 118.90, 119.85),
    "Kabupaten Mamuju Tengah":              (-2.25, -1.55, 119.45, 120.05),
    "Kabupaten Pasangkayu":                 (-1.65, -0.75, 119.20, 120.05),
    "Kabupaten Majene":                     (-3.70, -2.95, 118.75, 119.35),
    "Kabupaten Polewali Mandar":            (-3.80, -3.15, 118.85, 119.65),
    "Kabupaten Mamasa":                     (-3.35, -2.55, 119.05, 119.85),

    "Kota Palu":                            (-0.98, -0.78, 119.78, 119.98),
    "Kabupaten Donggala":                   (-1.40,  0.55, 119.40, 120.25),
    "Kabupaten Sigi":                       (-2.00, -0.80, 119.50, 120.30),
    "Kabupaten Parigi Moutong":             (-1.00,  0.85, 119.85, 121.00),
    "Kabupaten Poso":                       (-2.10, -1.10, 120.10, 121.20),
    "Kabupaten Tojo Una-Una":               (-1.60, -0.05, 121.00, 122.40),
    "Kabupaten Banggai":                    (-2.10, -0.60, 121.75, 123.35),
    "Kabupaten Banggai Kepulauan":          (-2.40, -1.30, 122.60, 123.90),
    "Kabupaten Banggai Laut":              (-1.80, -0.70, 122.40, 123.30),
    "Kabupaten Morowali":                   (-3.30, -1.70, 121.30, 123.00),
    "Kabupaten Morowali Utara":             (-2.30, -0.85, 120.90, 122.30),
    "Kabupaten Tolitoli":                   (-1.05,  1.05, 120.25, 121.40),
    "Kabupaten Buol":                       (-0.10,  1.30, 120.80, 122.00),

    "Kota Manado":                          ( 1.40,  1.60, 124.77, 124.97),
    "Kota Bitung":                          ( 1.40,  1.60, 125.10, 125.30),
    "Kota Tomohon":                         ( 1.28,  1.45, 124.78, 124.95),
    "Kota Kotamobagu":                      ( 0.67,  0.77, 124.28, 124.40),
    "Kabupaten Minahasa":                   ( 1.00,  1.45, 124.60, 125.05),
    "Kabupaten Minahasa Utara":             ( 1.50,  1.90, 124.85, 125.25),
    "Kabupaten Minahasa Selatan":           ( 0.75,  1.20, 124.40, 124.90),
    "Kabupaten Minahasa Tenggara":          ( 0.55,  1.10, 124.55, 125.05),
    "Kabupaten Bolaang Mongondow":          ( 0.30,  0.90, 123.95, 124.80),
    "Kabupaten Bolaang Mongondow Utara":    ( 0.95,  1.65, 123.40, 124.45),
    "Kabupaten Bolaang Mongondow Selatan":  (-0.10,  0.55, 123.80, 124.50),
    "Kabupaten Bolaang Mongondow Timur":    ( 0.55,  1.05, 124.45, 125.05),
    "Kabupaten Kepulauan Sangihe":          ( 2.70,  4.10, 125.30, 125.80),
    "Kabupaten Kepulauan Talaud":           ( 3.80,  4.80, 126.60, 127.20),
    "Kabupaten Kepulauan Siau Tagulandang Biaro": (2.40, 2.80, 125.30, 125.60),

    "Kota Kendari":                         (-4.10, -3.90, 122.45, 122.65),
    "Kota Baubau":                          (-5.53, -5.42, 122.55, 122.75),
    "Kabupaten Konawe":                     (-4.40, -3.30, 121.80, 123.20),
    "Kabupaten Konawe Selatan":             (-4.90, -3.80, 121.70, 122.80),
    "Kabupaten Konawe Utara":               (-3.65, -2.50, 121.50, 122.70),
    "Kabupaten Konawe Kepulauan":           (-4.30, -3.75, 122.75, 123.15),
    "Kabupaten Kolaka":                     (-4.40, -3.50, 121.40, 122.10),
    "Kabupaten Kolaka Utara":               (-3.65, -2.60, 120.90, 121.80),
    "Kabupaten Kolaka Timur":               (-4.50, -3.60, 121.70, 122.35),
    "Kabupaten Bombana":                    (-5.35, -4.50, 121.60, 122.40),
    "Kabupaten Buton":                      (-5.70, -4.90, 122.45, 123.10),
    "Kabupaten Buton Utara":                (-5.00, -4.20, 122.70, 123.20),
    "Kabupaten Buton Tengah":               (-5.30, -4.90, 122.35, 122.85),
    "Kabupaten Buton Selatan":              (-5.65, -5.20, 122.40, 122.90),
    "Kabupaten Muna":                       (-5.35, -4.55, 122.00, 122.80),
    "Kabupaten Muna Barat":                 (-5.20, -4.60, 121.70, 122.30),
    "Kabupaten Wakatobi":                   (-6.25, -5.30, 123.40, 124.20),

    "Kota Gorontalo":                       ( 0.53,  0.62, 122.98, 123.10),
    "Kabupaten Gorontalo":                  ( 0.35,  0.75, 122.60, 123.20),
    "Kabupaten Gorontalo Utara":            ( 0.65,  1.00, 122.20, 122.85),
    "Kabupaten Bone Bolango":               ( 0.40,  0.90, 122.90, 123.50),
    "Kabupaten Boalemo":                    ( 0.30,  0.80, 121.90, 122.55),
    "Kabupaten Pohuwato":                   ( 0.30,  0.85, 121.20, 122.10),
}

KAB_TO_PROV = {
    "Kota Makassar":"Sulawesi Selatan","Kota Palopo":"Sulawesi Selatan","Kota Parepare":"Sulawesi Selatan",
    "Kabupaten Bantaeng":"Sulawesi Selatan","Kabupaten Barru":"Sulawesi Selatan","Kabupaten Bone":"Sulawesi Selatan",
    "Kabupaten Bulukumba":"Sulawesi Selatan","Kabupaten Enrekang":"Sulawesi Selatan","Kabupaten Gowa":"Sulawesi Selatan",
    "Kabupaten Jeneponto":"Sulawesi Selatan","Kabupaten Kepulauan Selayar":"Sulawesi Selatan",
    "Kabupaten Luwu":"Sulawesi Selatan","Kabupaten Luwu Timur":"Sulawesi Selatan","Kabupaten Luwu Utara":"Sulawesi Selatan",
    "Kabupaten Maros":"Sulawesi Selatan","Kabupaten Pangkajene Dan Kepulauan":"Sulawesi Selatan",
    "Kabupaten Pinrang":"Sulawesi Selatan","Kabupaten Sidenreng Rappang":"Sulawesi Selatan",
    "Kabupaten Sinjai":"Sulawesi Selatan","Kabupaten Soppeng":"Sulawesi Selatan","Kabupaten Takalar":"Sulawesi Selatan",
    "Kabupaten Tana Toraja":"Sulawesi Selatan","Kabupaten Toraja Utara":"Sulawesi Selatan","Kabupaten Wajo":"Sulawesi Selatan",
    "Kabupaten Mamuju":"Sulawesi Barat","Kabupaten Majene":"Sulawesi Barat","Kabupaten Polewali Mandar":"Sulawesi Barat",
    "Kabupaten Mamasa":"Sulawesi Barat","Kabupaten Pasangkayu":"Sulawesi Barat","Kabupaten Mamuju Tengah":"Sulawesi Barat",
    "Kota Palu":"Sulawesi Tengah","Kabupaten Banggai":"Sulawesi Tengah","Kabupaten Banggai Kepulauan":"Sulawesi Tengah",
    "Kabupaten Banggai Laut":"Sulawesi Tengah","Kabupaten Buol":"Sulawesi Tengah","Kabupaten Donggala":"Sulawesi Tengah",
    "Kabupaten Morowali":"Sulawesi Tengah","Kabupaten Morowali Utara":"Sulawesi Tengah",
    "Kabupaten Parigi Moutong":"Sulawesi Tengah","Kabupaten Poso":"Sulawesi Tengah","Kabupaten Sigi":"Sulawesi Tengah",
    "Kabupaten Tojo Una-Una":"Sulawesi Tengah","Kabupaten Tolitoli":"Sulawesi Tengah",
    "Kota Manado":"Sulawesi Utara","Kota Bitung":"Sulawesi Utara","Kota Tomohon":"Sulawesi Utara","Kota Kotamobagu":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow":"Sulawesi Utara","Kabupaten Bolaang Mongondow Selatan":"Sulawesi Utara",
    "Kabupaten Bolaang Mongondow Timur":"Sulawesi Utara","Kabupaten Bolaang Mongondow Utara":"Sulawesi Utara",
    "Kabupaten Kepulauan Sangihe":"Sulawesi Utara","Kabupaten Kepulauan Siau Tagulandang Biaro":"Sulawesi Utara",
    "Kabupaten Kepulauan Talaud":"Sulawesi Utara","Kabupaten Minahasa":"Sulawesi Utara",
    "Kabupaten Minahasa Selatan":"Sulawesi Utara","Kabupaten Minahasa Tenggara":"Sulawesi Utara","Kabupaten Minahasa Utara":"Sulawesi Utara",
    "Kota Kendari":"Sulawesi Tenggara","Kota Baubau":"Sulawesi Tenggara",
    "Kabupaten Bombana":"Sulawesi Tenggara","Kabupaten Buton":"Sulawesi Tenggara","Kabupaten Buton Selatan":"Sulawesi Tenggara",
    "Kabupaten Buton Tengah":"Sulawesi Tenggara","Kabupaten Buton Utara":"Sulawesi Tenggara",
    "Kabupaten Kolaka":"Sulawesi Tenggara","Kabupaten Kolaka Timur":"Sulawesi Tenggara","Kabupaten Kolaka Utara":"Sulawesi Tenggara",
    "Kabupaten Konawe":"Sulawesi Tenggara","Kabupaten Konawe Kepulauan":"Sulawesi Tenggara",
    "Kabupaten Konawe Selatan":"Sulawesi Tenggara","Kabupaten Konawe Utara":"Sulawesi Tenggara",
    "Kabupaten Muna":"Sulawesi Tenggara","Kabupaten Muna Barat":"Sulawesi Tenggara","Kabupaten Wakatobi":"Sulawesi Tenggara",
    "Kota Gorontalo":"Gorontalo","Kabupaten Boalemo":"Gorontalo","Kabupaten Bone Bolango":"Gorontalo",
    "Kabupaten Gorontalo Utara":"Gorontalo","Kabupaten Pohuwato":"Gorontalo","Kabupaten Gorontalo":"Gorontalo",
}

def find_correct_kab(lat, lon):
    matches = []
    for kab, (lat_min, lat_max, lon_min, lon_max) in KAB_BBOX.items():
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            matches.append(kab)
    return matches

def main():
    df = pd.read_csv(INPUT_FILE)
    print(f"Total data: {len(df)}")

    fixes = 0
    for idx, row in df.iterrows():
        kab = str(row['kabupaten']).strip()
        lat = row['lat']
        lon = row['long']
        
        if pd.isna(lat) or pd.isna(lon): continue
        if kab not in KAB_BBOX: continue
        
        lat_min, lat_max, lon_min, lon_max = KAB_BBOX[kab]
        
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            # Cek apakah koordinat masuk bounding box kabupaten lain
            correct_candidates = find_correct_kab(lat, lon)
            if correct_candidates:
                new_kab = correct_candidates[0]
                new_prov = KAB_TO_PROV.get(new_kab)
                print(f"[FIX] {row['nama_wisata']} ({lat:.4f}, {lon:.4f}): {kab} -> {new_kab} ({new_prov})")
                df.at[idx, 'kabupaten'] = new_kab
                df.at[idx, 'provinsi'] = new_prov
                fixes += 1
            else:
                print(f"[WARN] {row['nama_wisata']} ({lat:.4f}, {lon:.4f}): di luar batas Sulawesi, kab salah {kab}")

    print(f"\nTotal fix: {fixes}")

    if fixes > 0:
        for idx, row in df.iterrows():
            kab = str(row['kabupaten']).strip()
            if kab in KAB_TO_PROV:
                df.at[idx, 'provinsi'] = KAB_TO_PROV[kab]
        
        df.to_csv(INPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"Data disimpan ke {INPUT_FILE}.")

if __name__ == "__main__":
    main()
