import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time
import sys
import json

# Atur encoding untuk stdout
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = 'wisata_sulawesi_lengkap.csv'
OUTPUT_FILE_FIXED = 'wisata_sulawesi_fixed.csv'
OUTPUT_FILE_LENGKAP = 'wisata_sulawesi_lengkap.csv'

VALID_KAB_KOTA = [
    "Kota Makassar", "Kota Palopo", "Kota Parepare",
    "Kabupaten Bantaeng", "Kabupaten Barru", "Kabupaten Bone",
    "Kabupaten Bulukumba", "Kabupaten Enrekang", "Kabupaten Gowa",
    "Kabupaten Jeneponto", "Kabupaten Kepulauan Selayar",
    "Kabupaten Luwu", "Kabupaten Luwu Timur", "Kabupaten Luwu Utara",
    "Kabupaten Maros", "Kabupaten Pangkajene Dan Kepulauan",
    "Kabupaten Pinrang", "Kabupaten Sidenreng Rappang",
    "Kabupaten Sinjai", "Kabupaten Soppeng", "Kabupaten Takalar",
    "Kabupaten Tana Toraja", "Kabupaten Toraja Utara", "Kabupaten Wajo",
    "Kabupaten Mamuju", "Kabupaten Majene", "Kabupaten Polewali Mandar",
    "Kabupaten Mamasa", "Kabupaten Pasangkayu", "Kabupaten Mamuju Tengah",
    "Kota Palu", "Kabupaten Banggai", "Kabupaten Banggai Kepulauan",
    "Kabupaten Banggai Laut", "Kabupaten Buol", "Kabupaten Donggala",
    "Kabupaten Morowali", "Kabupaten Morowali Utara",
    "Kabupaten Parigi Moutong", "Kabupaten Poso", "Kabupaten Sigi",
    "Kabupaten Tojo Una-Una", "Kabupaten Tolitoli",
    "Kota Manado", "Kota Bitung", "Kota Tomohon", "Kota Kotamobagu",
    "Kabupaten Bolaang Mongondow", "Kabupaten Bolaang Mongondow Selatan",
    "Kabupaten Bolaang Mongondow Timur", "Kabupaten Bolaang Mongondow Utara",
    "Kabupaten Kepulauan Sangihe", "Kabupaten Kepulauan Siau Tagulandang Biaro",
    "Kabupaten Kepulauan Talaud", "Kabupaten Minahasa",
    "Kabupaten Minahasa Selatan", "Kabupaten Minahasa Tenggara",
    "Kabupaten Minahasa Utara",
    "Kota Kendari", "Kota Baubau",
    "Kabupaten Bombana", "Kabupaten Buton", "Kabupaten Buton Selatan",
    "Kabupaten Buton Tengah", "Kabupaten Buton Utara",
    "Kabupaten Kolaka", "Kabupaten Kolaka Timur", "Kabupaten Kolaka Utara",
    "Kabupaten Konawe", "Kabupaten Konawe Kepulauan",
    "Kabupaten Konawe Selatan", "Kabupaten Konawe Utara",
    "Kabupaten Muna", "Kabupaten Muna Barat", "Kabupaten Wakatobi",
    "Kota Gorontalo", "Kabupaten Boalemo", "Kabupaten Bone Bolango",
    "Kabupaten Gorontalo Utara", "Kabupaten Pohuwato", "Kabupaten Gorontalo",
]

# Create a mapping from clean name to full name
KAB_MAP = {}
for k in VALID_KAB_KOTA:
    clean_k = k.lower().replace('kabupaten ', '').replace('kota ', '').replace('kepulauan ', '').replace(' dan kepulauan', '').strip()
    KAB_MAP[clean_k] = k

# Special cases mapping from Nominatim typical responses
KAB_MAP['pangkajene dan kepulauan'] = 'Kabupaten Pangkajene Dan Kepulauan'
KAB_MAP['pangkajene'] = 'Kabupaten Pangkajene Dan Kepulauan'
KAB_MAP['pangkep'] = 'Kabupaten Pangkajene Dan Kepulauan'
KAB_MAP['siau tagulandang biaro'] = 'Kabupaten Kepulauan Siau Tagulandang Biaro'
KAB_MAP['sitaro'] = 'Kabupaten Kepulauan Siau Tagulandang Biaro'
KAB_MAP['sidenreng rappang'] = 'Kabupaten Sidenreng Rappang'
KAB_MAP['sidrap'] = 'Kabupaten Sidenreng Rappang'

def get_best_match(name):
    if not name: return None
    name = name.lower().replace('kabupaten ', '').replace('kota ', '').replace('regency', '').replace('city', '').strip()
    if name in KAB_MAP: return KAB_MAP[name]
    for k in KAB_MAP.keys():
        if k in name: return KAB_MAP[k]
    return None

def main():
    print("=" * 60)
    print("VALIDASI KABUPATEN MENGGUNAKAN GEOPY (NOMINATIM)")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"Total data: {len(df)}")

    # Identifikasi suspect
    suspects = []
    for idx, row in df.iterrows():
        kab = str(row['kabupaten'])
        alamat = str(row.get('alamat', '')).lower()
        kab_clean = kab.lower().replace('kabupaten ', '').replace('kota ', '').strip()
        
        # Tambahan: cari suspect yang lat/long nya aneh (misal: Jeneponto tapi lat nya -4 -> berarti pangkep/maros)
        # Tapi yang paling gampang: cek semua data yang "kab_clean" tidak ada di alamat
        if kab_clean not in alamat:
            suspects.append(idx)

    print(f"Total suspect ditemukan: {len(suspects)}")

    geolocator = Nominatim(user_agent="sulawesi_tourism_validator_app_v1")
    reverse = RateLimiter(geolocator.reverse, min_delay_seconds=1.5)

    fixes = 0
    
    for i, idx in enumerate(suspects):
        row = df.loc[idx]
        lat = row['lat']
        lon = row['long']
        old_kab = row['kabupaten']
        nama = row['nama_wisata']
        
        if pd.isna(lat) or pd.isna(lon):
            continue
            
        try:
            # Lakukan reverse geocoding
            coords = f"{lat}, {lon}"
            
            # Retry logic untuk geocoder
            max_retries = 3
            location = None
            for attempt in range(max_retries):
                try:
                    location = geolocator.reverse(coords, exactly_one=True, language='id', timeout=15)
                    break
                except Exception as req_err:
                    if attempt == max_retries - 1:
                        raise req_err
                    print(f"[{i+1}/{len(suspects)}] Timeout/Error. Retry {attempt+1}/{max_retries}...")
                    time.sleep(3)
                    
            if location and 'address' in location.raw:
                addr = location.raw['address']
                # Ambil regency / city / county / town dari response Nominatim
                # Prioritas: regency > city > county > municipality > town
                geo_name = addr.get('regency') or addr.get('city') or addr.get('county') or addr.get('municipality') or addr.get('town')
                
                if geo_name:
                    new_kab = get_best_match(geo_name)
                    
                    if new_kab and new_kab != old_kab:
                        print(f"[{i+1}/{len(suspects)}] FIX: '{nama}' ({old_kab}) -> Koordinat ada di {geo_name} -> {new_kab}")
                        df.at[idx, 'kabupaten'] = new_kab
                        fixes += 1
                    else:
                        print(f"[{i+1}/{len(suspects)}] OK: '{nama}' ({old_kab}) -> Lokasi valid: {geo_name}")
                else:
                    print(f"[{i+1}/{len(suspects)}] SKIP: '{nama}' ({old_kab}) -> Info regency tidak ditemukan")
            else:
                print(f"[{i+1}/{len(suspects)}] FAIL: '{nama}' ({old_kab}) -> Gagal geocoding")
                
        except Exception as e:
            print(f"[{i+1}/{len(suspects)}] ERROR: '{nama}' ({old_kab}) -> {e}")
        
        # Selalu beri jeda untuk menghormati Nominatim API rate limit (max 1 req/sec)
        time.sleep(1.5)

    if fixes > 0:
        print(f"\nSelesai! {fixes} kabupaten berhasil dikoreksi berdasarkan koordinat map asli.")
        df.to_csv(OUTPUT_FILE_FIXED, index=False, encoding='utf-8-sig')
        df.to_csv(OUTPUT_FILE_LENGKAP, index=False, encoding='utf-8-sig')
        print("Data tersimpan ke wisata_sulawesi_fixed.csv dan wisata_sulawesi_lengkap.csv")
    else:
        print("\nSelesai! Tidak ada yang dikoreksi.")

if __name__ == "__main__":
    main()
