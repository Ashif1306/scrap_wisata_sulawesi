import pandas as pd
import json
import time
import os
import sys
from openai import OpenAI

# Atur encoding untuk stdout
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = 'wisata_sulawesi_fixed.csv'
OUTPUT_FILE = 'wisata_sulawesi_fixed.csv'

# Ambil API Key dari environment variable untuk keamanan
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("Error: API Key tidak ditemukan! Pastikan sudah set environment variable 'OPENAI_API_KEY'.")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)
MODEL_NAME = "gpt-4o-mini"

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

KAB_TO_PROV = {
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

def get_kabupaten_ai(nama, alamat, lat, lon, kab_skrg):
    prompt = f"""
Tentukan Kabupaten/Kota yang BENAR untuk tempat wisata berikut:
Nama: {nama}
Alamat: {alamat}
Koordinat: {lat}, {lon}
Kabupaten Saat Ini: {kab_skrg}

Daftar Kabupaten/Kota yang VALID (Pilih salah satu):
{json.dumps(VALID_KAB_KOTA)}

Instruksi:
1. Gunakan Nama Wisata dan Alamat sebagai petunjuk utama.
2. Jika Alamat menyebutkan kecamatan atau kota tertentu, sesuaikan dengan Kabupaten/Kota yang menaunginya.
3. JANGAN terkecoh oleh kata 'Makassar' jika alamatnya jelas di Maros atau Gowa.
4. Balas HANYA dengan JSON format: {{"kabupaten": "Nama Kabupaten/Kota"}}
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        res = json.loads(response.choices[0].message.content)
        return res.get("kabupaten")
    except:
        return None

def main():
    df = pd.read_csv(INPUT_FILE)
    print(f"Total data: {len(df)}")
    
    # Identifikasi suspect (kabupaten tidak ada di alamat)
    suspects = []
    for idx, row in df.iterrows():
        kab = str(row['kabupaten']).lower()
        kab_clean = kab.replace('kabupaten ', '').replace('kota ', '').strip()
        alamat = str(row['alamat']).lower()
        
        # Pengecualian umum
        if kab_clean in alamat: continue
        if kab_clean == 'pangkajene dan kepulauan' and 'pangkep' in alamat: continue
        if kab_clean == 'sidenreng rappang' and 'sidrap' in alamat: continue
        
        suspects.append(idx)
    
    print(f"Jumlah suspect: {len(suspects)}")
    
    for i, idx in enumerate(suspects):
        row = df.loc[idx]
        print(f"[{i+1}/{len(suspects)}] Memproses: {row['nama_wisata']}...")
        
        new_kab = get_kabupaten_ai(row['nama_wisata'], row['alamat'], row['lat'], row['long'], row['kabupaten'])
        
        if new_kab and new_kab in VALID_KAB_KOTA:
            if new_kab != row['kabupaten']:
                print(f"  FIX: {row['kabupaten']} -> {new_kab}")
                df.at[idx, 'kabupaten'] = new_kab
                # Update provinsi otomatis
                df.at[idx, 'provinsi'] = KAB_TO_PROV.get(new_kab, row['provinsi'])
        
        time.sleep(0.5) # Hindari rate limit berlebih
    
    # Final pass: Seragamkan provinsi untuk semua data
    print("Final pass: Menyelaraskan provinsi...")
    for idx, row in df.iterrows():
        kab = str(row['kabupaten']).strip()
        if kab in KAB_TO_PROV:
            df.at[idx, 'provinsi'] = KAB_TO_PROV[kab]
            
    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print("Selesai! Data disimpan.")

if __name__ == "__main__":
    main()
