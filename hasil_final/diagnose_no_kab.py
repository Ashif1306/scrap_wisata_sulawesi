"""
diagnose_no_kab.py — Check how many rows have NO extractable kabupaten from alamat.
These would need reverse geocoding.
"""
import pandas as pd
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

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

ALIAS_MAP = {
    "pangkep": "Kabupaten Pangkajene Dan Kepulauan",
    "pangkajene": "Kabupaten Pangkajene Dan Kepulauan",
    "sidrap": "Kabupaten Sidenreng Rappang",
    "toli-toli": "Kabupaten Tolitoli",
    "toli toli": "Kabupaten Tolitoli",
    "bolmong": "Kabupaten Bolaang Mongondow",
    "sitaro": "Kabupaten Kepulauan Siau Tagulandang Biaro",
    "bau-bau": "Kota Baubau",
    "bau bau": "Kota Baubau",
    "sangihe": "Kabupaten Kepulauan Sangihe",
    "talaud": "Kabupaten Kepulauan Talaud",
    "selayar": "Kabupaten Kepulauan Selayar",
    "wakatobi": "Kabupaten Wakatobi",
    "parepare": "Kota Parepare",
    "pare-pare": "Kota Parepare",
    "pare pare": "Kota Parepare",
}

def find_kab_in_alamat(alamat_str):
    """Try to find a valid kabupaten/kota in the alamat string."""
    if not alamat_str or str(alamat_str).strip() in ['-', 'nan', '']:
        return None
    
    alamat_lower = str(alamat_str).lower()
    
    # 1. Direct match against valid list (longest first)
    for kab in sorted(VALID_KAB_KOTA, key=len, reverse=True):
        if kab.lower() in alamat_lower:
            return kab
    
    # 2. Aliases
    for alias, full_name in ALIAS_MAP.items():
        if alias in alamat_lower:
            return full_name
    
    # 3. Regex for "Kab. X" shorthand
    m = re.search(r'kab\.?\s+([a-z][a-z\s]+?)(?:\s*[,\.\d]|$)', alamat_lower)
    if m:
        kab_raw = m.group(1).strip()
        for kab in VALID_KAB_KOTA:
            kab_clean = kab.lower().replace('kabupaten ', '').replace('kota ', '')
            if kab_clean == kab_raw or kab_raw.startswith(kab_clean):
                return kab
    
    return None


df = pd.read_csv('wisata_sulawesi_lengkap.csv')

no_kab = []
has_kab = 0
for i, row in df.iterrows():
    alamat = str(row.get('alamat', ''))
    result = find_kab_in_alamat(alamat)
    if result:
        has_kab += 1
    else:
        no_kab.append(i)

print(f"Total rows: {len(df)}")
print(f"Kabupaten found in alamat: {has_kab}")
print(f"Kabupaten NOT found in alamat: {len(no_kab)}")
print()
print("Sample rows where kabupaten is NOT in alamat:")
for idx in no_kab[:20]:
    row = df.loc[idx]
    print(f"  [{idx}] {row['nama_wisata'][:50]}")
    print(f"       alamat: {str(row['alamat'])[:100]}")
    print(f"       kab: {row['kabupaten']}, lat: {row['lat']}, lon: {row['long']}")
    print()
