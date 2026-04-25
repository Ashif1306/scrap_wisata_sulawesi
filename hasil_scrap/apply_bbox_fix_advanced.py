import pandas as pd
import math
import sys
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(SCRIPT_DIR, 'kabupaten_provinsi.csv')

from apply_bbox_fix import KAB_BBOX, KAB_TO_PROV

def point_to_bbox_distance(lat, lon, lat_min, lat_max, lon_min, lon_max):
    # Jarak terdekat dari titik ke persegi panjang (bbox)
    dx = max(lon_min - lon, 0, lon - lon_max)
    dy = max(lat_min - lat, 0, lat - lat_max)
    return math.sqrt(dx*dx + dy*dy)

def find_nearest_kab(lat, lon):
    min_dist = float('inf')
    best_kab = None
    for kab, (lat_min, lat_max, lon_min, lon_max) in KAB_BBOX.items():
        dist = point_to_bbox_distance(lat, lon, lat_min, lat_max, lon_min, lon_max)
        if dist < min_dist:
            min_dist = dist
            best_kab = kab
    return best_kab, min_dist

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
        
        # Jika di luar BBox kabupatennya saat ini
        if not (lat_min <= lat <= lat_max and lon_min <= lon <= lon_max):
            
            # Cari kabupaten yang BBox-nya mencakup titik ini
            correct_candidates = []
            for k, (lmin, lmax, lnmin, lnmax) in KAB_BBOX.items():
                if lmin <= lat <= lmax and lnmin <= lon <= lnmax:
                    correct_candidates.append(k)
            
            if correct_candidates:
                new_kab = correct_candidates[0]
            else:
                # Jika titik di laut/di luar semua BBox, cari BBox terdekat!
                new_kab, dist = find_nearest_kab(lat, lon)
                
            if new_kab != kab:
                new_prov = KAB_TO_PROV.get(new_kab)
                print(f"[FIX] {row['nama_wisata']} ({lat:.4f}, {lon:.4f}): {kab} -> {new_kab} ({new_prov})")
                df.at[idx, 'kabupaten'] = new_kab
                df.at[idx, 'provinsi'] = new_prov
                fixes += 1

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
