import pandas as pd
import json
import time
import os
import sys
from openai import OpenAI

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INPUT_FILE = 'wisata_sulawesi_lengkap.csv'
OUTPUT_FILE_FIXED = 'wisata_sulawesi_fixed.csv'
OUTPUT_FILE_LENGKAP = 'wisata_sulawesi_lengkap.csv'

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: API Key tidak ditemukan! Set environment variable 'OPENAI_API_KEY'.")
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
VALID_KAB_LIST = json.dumps(VALID_KAB_KOTA, ensure_ascii=False)

PROMPT_TEMPLATE = """
Kamu adalah sistem pemetaan geografis akurat.

Tugas: Perbaiki kolom "kabupaten" untuk tempat wisata berikut berdasarkan Alamat DAN Koordinat Latitude/Longitude-nya.
Seringkali alamat salah ketik atau kabupaten aslinya salah. Gunakan koordinat (Lat, Long) sebagai penentu utama wilayah mana tempat tersebut berada.

Data:
- Nama wisata : {nama}
- Alamat      : {alamat}
- Lat, Long   : {lat}, {lon}
- Kabupaten Sekarang : {kabupaten}

Aturan KETAT:
1. Pilih kabupaten HANYA dari daftar ini: {valid_list}
2. JANGAN membuat nama kabupaten baru di luar daftar.
3. Berikan jawaban dalam JSON: {{"kabupaten": "nama kabupaten/kota yang benar"}}
"""

def main():
    print("=" * 60)
    print("VALIDASI KABUPATEN DENGAN OPENAI (MENGGUNAKAN KOORDINAT)")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"Total data: {len(df)}")

    suspects = []
    for idx, row in df.iterrows():
        kab = str(row['kabupaten'])
        alamat = str(row.get('alamat', '')).lower()
        kab_clean = kab.lower().replace('kabupaten ', '').replace('kota ', '').strip()
        if kab_clean not in alamat:
            suspects.append(idx)

    print(f"Total suspect ditemukan: {len(suspects)}")

    fixes = 0
    for i, idx in enumerate(suspects):
        row = df.loc[idx]
        nama = row['nama_wisata']
        alamat = row['alamat']
        lat = row['lat']
        lon = row['long']
        old_kab = row['kabupaten']
        
        prompt = PROMPT_TEMPLATE.format(
            nama=nama,
            alamat=alamat,
            lat=lat,
            lon=lon,
            kabupaten=old_kab,
            valid_list=VALID_KAB_LIST
        )
        
        for attempt in range(3):
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "Kamu adalah validator data geografis Indonesia. Balas hanya dalam format JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.0,
                    max_tokens=100,
                    response_format={"type": "json_object"},
                )
                
                result = json.loads(response.choices[0].message.content.strip())
                new_kab = result.get('kabupaten', '').strip()
                
                if new_kab and new_kab in VALID_KAB_KOTA and new_kab != old_kab:
                    print(f"[{i+1}/{len(suspects)}] FIX: '{nama}' | {old_kab} -> {new_kab} (Lat: {lat}, Lon: {lon})")
                    df.at[idx, 'kabupaten'] = new_kab
                    fixes += 1
                else:
                    print(f"[{i+1}/{len(suspects)}] OK: '{nama}' | Tetap {old_kab}")
                break
                
            except Exception as e:
                if attempt == 2:
                    print(f"[{i+1}/{len(suspects)}] ERROR: '{nama}' -> {e}")
                time.sleep(2)
        
        time.sleep(0.5)

    if fixes > 0:
        print(f"\nSelesai! {fixes} kabupaten berhasil dikoreksi.")
        df.to_csv(OUTPUT_FILE_FIXED, index=False, encoding='utf-8-sig')
        df.to_csv(OUTPUT_FILE_LENGKAP, index=False, encoding='utf-8-sig')
        print("Data tersimpan ke wisata_sulawesi_fixed.csv dan wisata_sulawesi_lengkap.csv")
    else:
        print("\nSelesai! Tidak ada yang dikoreksi.")

if __name__ == "__main__":
    main()
