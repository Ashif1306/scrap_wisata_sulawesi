import pandas as pd
import re

def norm(s): return re.sub(r'\s+', ' ', str(s).strip().lower())

def parse_kab_dari_alamat(alamat):
    m = re.search(r'\bKab(?:upaten)?\.?\s+([A-Za-z][A-Za-z\s]+?)(?=\s*[,\.\d]|$)', str(alamat), re.IGNORECASE)
    if m:
        nama = m.group(1).strip().title()
        for stop in ['Sulawesi','Selatan','Utara','Tengah','Tenggara','Barat','Gorontalo','Indonesia']:
            nama = re.sub(r'\s*\b' + stop + r'\b\s*', ' ', nama, flags=re.IGNORECASE).strip()
        if len(nama) > 2: return f'Kabupaten {nama}'
    
    # Check Kota
    m_kota = re.search(r'\bKota\s+([A-Za-z][A-Za-z\s]+?)(?=\s*[,\.\d]|$)', str(alamat), re.IGNORECASE)
    if m_kota:
        nama = m_kota.group(1).strip().title()
        for stop in ['Sulawesi','Selatan','Utara','Tengah','Tenggara','Barat','Gorontalo','Indonesia']:
            nama = re.sub(r'\s*\b' + stop + r'\b\s*', ' ', nama, flags=re.IGNORECASE).strip()
        if len(nama) > 2: return f'Kota {nama}'
        
    return ''

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

file_path = 'd:/semester6/mc_learning/scrapt_wisata/hasil_final/wisata_sulawesi_lengkap.csv'
df = pd.read_csv(file_path)
fixes = 0
for i, row in df.iterrows():
    kab_asli = str(row['kabupaten']).strip().title()
    kab_alamat = parse_kab_dari_alamat(row.get('alamat', ''))
    
    canonical_kab = None
    for k in KAB_TO_PROV.keys():
        if norm(kab_alamat) == norm(k):
            canonical_kab = k
            break
            
    if canonical_kab and norm(canonical_kab) != norm(kab_asli):
        print(f"[FIX] {row['nama_wisata']}: {kab_asli} -> {canonical_kab}")
        df.at[i, 'kabupaten'] = canonical_kab
        df.at[i, 'provinsi'] = KAB_TO_PROV[canonical_kab]
        fixes += 1

if fixes > 0:
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    print(f"\nTotal fixes saved: {fixes}")
