import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import time

kab_prov_mapping = {
    'Sulawesi Selatan': ['Makassar', 'Palopo', 'Parepare', 'Bantaeng', 'Barru', 'Bone', 'Bulukumba', 'Enrekang', 'Gowa', 'Jeneponto', 'Kepulauan Selayar', 'Luwu', 'Luwu Timur', 'Luwu Utara', 'Maros', 'Pangkajene Dan Kepulauan', 'Pinrang', 'Sidenreng Rappang', 'Sinjai', 'Soppeng', 'Takalar', 'Tana Toraja', 'Toraja Utara', 'Wajo'],
    'Sulawesi Barat': ['Mamuju', 'Majene', 'Polewali Mandar', 'Mamasa', 'Pasangkayu', 'Mamuju Tengah'],
    'Sulawesi Tengah': ['Palu', 'Banggai', 'Banggai Kepulauan', 'Banggai Laut', 'Buol', 'Donggala', 'Morowali', 'Morowali Utara', 'Parigi Moutong', 'Poso', 'Sigi', 'Tojo Una-Una', 'Tolitoli'],
    'Sulawesi Utara': ['Manado', 'Bitung', 'Tomohon', 'Kotamobagu', 'Bolaang Mongondow', 'Bolaang Mongondow Selatan', 'Bolaang Mongondow Timur', 'Bolaang Mongondow Utara', 'Kepulauan Sangihe', 'Kepulauan Siau Tagulandang Biaro', 'Kepulauan Talaud', 'Minahasa', 'Minahasa Selatan', 'Minahasa Tenggara', 'Minahasa Utara'],
    'Sulawesi Tenggara': ['Kendari', 'Baubau', 'Bombana', 'Buton', 'Buton Selatan', 'Buton Tengah', 'Buton Utara', 'Kolaka', 'Kolaka Timur', 'Kolaka Utara', 'Konawe', 'Konawe Kepulauan', 'Konawe Selatan', 'Konawe Utara', 'Muna', 'Muna Barat', 'Wakatobi'],
    'Gorontalo': ['Gorontalo', 'Boalemo', 'Bone Bolango', 'Gorontalo Utara', 'Pohuwato']
}

valid_kabs = {}
for prov, kabs in kab_prov_mapping.items():
    for kab in kabs:
        valid_kabs[kab.lower()] = prov

def check_mismatch(kab, prov):
    kab_clean = str(kab).replace('Kabupaten', '').replace('Kota', '').strip().lower()
    prov = str(prov).strip()
    if kab_clean in valid_kabs:
        if valid_kabs[kab_clean] != prov:
            return True
    else:
        for k, p in valid_kabs.items():
            if k in kab_clean:
                if p != prov:
                    return True
                return False
    return False

def fix_with_geopy(file_path):
    print(f"Membaca {file_path}")
    df = pd.read_csv(file_path)
    
    geolocator = Nominatim(user_agent="wisata_sulawesi_fixer")
    geocode = RateLimiter(geolocator.reverse, min_delay_seconds=1)
    
    changes = 0
    for idx, row in df.iterrows():
        if check_mismatch(row['kabupaten'], row['provinsi']):
            try:
                lat = float(row['lat'])
                lon = float(row['long'])
                location = geocode((lat, lon), exactly_one=True, language='id')
                if location and 'address' in location.raw:
                    addr = location.raw['address']
                    # Look for city or town or county in address
                    new_kab = addr.get('city') or addr.get('county') or addr.get('town') or addr.get('municipality')
                    if new_kab:
                        new_kab_str = str(new_kab)
                        if not new_kab_str.lower().startswith('kota') and not new_kab_str.lower().startswith('kabupaten'):
                            if addr.get('city'):
                                new_kab_str = f"Kota {new_kab_str}"
                            else:
                                new_kab_str = f"Kabupaten {new_kab_str}"
                                
                        print(f"Fixing row {idx}: {row['nama_wisata']} | {row['kabupaten']} -> {new_kab_str}")
                        df.at[idx, 'kabupaten'] = new_kab_str
                        changes += 1
            except Exception as e:
                print(f"Error at {idx}: {e}")
                pass
                
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"Selesai! {changes} kabupaten diperbaiki.\n")

if __name__ == "__main__":
    files_to_fix = [
        'd:/semester6/mc_learning/scrapt_wisata/hasil_scrap/wisata_sulawesi_kategori_ai.csv',
        'd:/semester6/mc_learning/scrapt_wisata/hasil_final/wisata_sulawesi_lengkap.csv'
    ]
    for f in files_to_fix:
        fix_with_geopy(f)
