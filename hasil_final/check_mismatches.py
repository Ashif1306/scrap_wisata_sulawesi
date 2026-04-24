import pandas as pd

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

def is_mismatch(kab, prov):
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

df = pd.read_csv('d:/semester6/mc_learning/scrapt_wisata/hasil_final/wisata_sulawesi_lengkap.csv')

mismatches = []
for idx, row in df.iterrows():
    if is_mismatch(row['kabupaten'], row['provinsi']):
        mismatches.append(idx)

print(f"Total remaining mismatches: {len(mismatches)}")
for i in mismatches:
    r = df.iloc[i]
    print(f"  Row {i}: {r['nama_wisata']} | kab={r['kabupaten']} | prov={r['provinsi']} | place_id={r['place_id']}")
