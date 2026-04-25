"""
Script: extract_kabupaten_provinsi.py
Bangun ulang kolom kabupaten & provinsi dari data mentah.

Strategi:
1. Parse kolom 'alamat' langsung menggunakan regex + daftar nama resmi
2. Untuk alamat yang tidak mengandung info kabupaten/provinsi:
   → Gunakan OpenAI GPT-4o-mini dengan koordinat lat/long
3. Simpan hasil ke hasil_scrap/kabupaten_provinsi.csv
"""

import pandas as pd
import re
import json
import time
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ── KONFIGURASI ──────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(SCRIPT_DIR, 'wisata_sulawesi_cleaned_final.csv')
OUTPUT_FILE = os.path.join(SCRIPT_DIR, 'kabupaten_provinsi.csv')

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ── DAFTAR KABUPATEN/KOTA VALID ───────────────────────────────
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

# ── MAPPING KABUPATEN → PROVINSI ─────────────────────────────
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

# Alias tambahan untuk parsing alamat
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
    "north minahasa": "Kabupaten Minahasa Utara",
    "south minahasa": "Kabupaten Minahasa Selatan",
    "southeast minahasa": "Kabupaten Minahasa Tenggara",
    "north morowali": "Kabupaten Morowali Utara",
    "south konawe": "Kabupaten Konawe Selatan",
    "north konawe": "Kabupaten Konawe Utara",
    "konawe islands": "Kabupaten Konawe Kepulauan",
    "east luwu": "Kabupaten Luwu Timur",
    "north luwu": "Kabupaten Luwu Utara",
    "east bolaang mongondow": "Kabupaten Bolaang Mongondow Timur",
    "north bolaang mongondow": "Kabupaten Bolaang Mongondow Utara",
    "south bolaang mongondow": "Kabupaten Bolaang Mongondow Selatan",
    "selayar islands": "Kabupaten Kepulauan Selayar",
    "sangihe islands": "Kabupaten Kepulauan Sangihe",
    "north toraja": "Kabupaten Toraja Utara",
    "south sulawesi": "Sulawesi Selatan",
    "west sulawesi": "Sulawesi Barat",
    "central sulawesi": "Sulawesi Tengah",
    "north sulawesi": "Sulawesi Utara",
    "south east sulawesi": "Sulawesi Tenggara",
    "southeast sulawesi": "Sulawesi Tenggara",
}

VALID_PROVINSI = [
    "Sulawesi Selatan", "Sulawesi Barat", "Sulawesi Tengah",
    "Sulawesi Utara", "Sulawesi Tenggara", "Gorontalo"
]

def parse_kabupaten_from_alamat(alamat):
    """
    Ekstrak kabupaten/kota dari string alamat.
    Return (kabupaten, provinsi) atau (None, None) jika tidak ditemukan.
    """
    if not alamat or str(alamat).strip() in ['-', 'nan', '']:
        return None, None
    
    alamat_lower = alamat.lower()
    
    # 1. Cari pola "Kabupaten X" atau "Kota X" secara langsung
    for kab in sorted(VALID_KAB_KOTA, key=len, reverse=True):
        if kab.lower() in alamat_lower:
            prov = KAB_TO_PROV.get(kab)
            return kab, prov
    
    # 2. Cari alias (termasuk nama Inggris)
    for alias, full_name in ALIAS_MAP.items():
        if alias in alamat_lower:
            if full_name in VALID_KAB_KOTA:
                prov = KAB_TO_PROV.get(full_name)
                return full_name, prov
    
    # 3. Cari "Kab. X" atau "Kab X" menggunakan regex
    kab_match = re.search(r'kab\.?\s+([a-z\s]+?)(?:,|\.|$)', alamat_lower)
    if kab_match:
        kab_raw = kab_match.group(1).strip()
        for kab in VALID_KAB_KOTA:
            kab_clean = kab.lower().replace('kabupaten ', '').replace('kota ', '')
            if kab_clean in kab_raw or kab_raw in kab_clean:
                prov = KAB_TO_PROV.get(kab)
                return kab, prov
    
    # 4. Cari nama provinsi saja, setidaknya ambil provinsinya
    for prov in VALID_PROVINSI:
        if prov.lower() in alamat_lower:
            return None, prov  # kabupaten tidak ditemukan, provinsi ditemukan
    
    return None, None


def ask_ai_for_kabupaten(nama, alamat, lat, lon):
    """Gunakan OpenAI untuk menentukan kabupaten berdasarkan koordinat."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = f"""Tentukan Kabupaten/Kota yang TEPAT untuk lokasi berikut berdasarkan koordinatnya:
Nama: {nama}
Alamat: {alamat}
Koordinat: lat={lat}, lon={lon}

Pilih HANYA dari daftar ini:
{json.dumps(VALID_KAB_KOTA, ensure_ascii=False)}

Balas HANYA JSON: {{"kabupaten": "nama kabupaten/kota"}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=80,
        )
        result = json.loads(response.choices[0].message.content)
        kab = result.get("kabupaten", "").strip()
        if kab in VALID_KAB_KOTA:
            return kab, KAB_TO_PROV.get(kab)
    except Exception as e:
        print(f"  [AI Error] {e}")
    return None, None


def main():
    print("=" * 60)
    print("EKSTRAKSI KABUPATEN & PROVINSI DARI DATA MENTAH")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"Total data: {len(df)}")
    print(f"Kolom: {list(df.columns)}")

    results = []
    ai_needed = []
    parsed_count = 0

    # Pass 1: Parse dari alamat
    print("\n[Pass 1] Parsing dari kolom alamat...")
    for idx, row in df.iterrows():
        alamat = str(row.get('alamat', ''))
        kab, prov = parse_kabupaten_from_alamat(alamat)
        
        if kab:
            parsed_count += 1
        else:
            ai_needed.append(idx)
        
        results.append({'idx': idx, 'kabupaten': kab, 'provinsi': prov})

    print(f"  Berhasil dari alamat: {parsed_count}")
    print(f"  Perlu AI: {len(ai_needed)}")

    # Pass 2: Gunakan AI untuk yang tidak berhasil diparsing
    if ai_needed and OPENAI_API_KEY:
        print(f"\n[Pass 2] Menggunakan AI untuk {len(ai_needed)} entri...")
        for i, idx in enumerate(ai_needed):
            row = df.loc[idx]
            nama = str(row.get('nama_wisata', ''))
            alamat = str(row.get('alamat', ''))
            lat = row.get('lat', None)
            lon = row.get('long', None)
            
            prov_from_alamat = results[idx]['provinsi']  # Mungkin sudah dapat provinsi dari pass 1
            
            kab, prov = ask_ai_for_kabupaten(nama, alamat, lat, lon)
            
            if kab:
                results[idx]['kabupaten'] = kab
                results[idx]['provinsi'] = prov
                print(f"  [{i+1}/{len(ai_needed)}] AI: {nama} -> {kab}")
            elif prov_from_alamat:
                results[idx]['provinsi'] = prov_from_alamat
                print(f"  [{i+1}/{len(ai_needed)}] SKIP: {nama} -> Provinsi saja: {prov_from_alamat}")
            else:
                print(f"  [{i+1}/{len(ai_needed)}] GAGAL: {nama} | Alamat: {alamat[:50]}")
            
            time.sleep(0.4)
    elif ai_needed:
        print("\n[Pass 2] OPENAI_API_KEY tidak ditemukan, pass 2 dilewati.")
        print("Jalankan: $env:OPENAI_API_KEY='sk-...' lalu jalankan ulang script ini.")

    # Gabungkan ke DataFrame asli
    df['kabupaten'] = [r['kabupaten'] if r['kabupaten'] else '' for r in results]
    df['provinsi'] = [r['provinsi'] if r['provinsi'] else '' for r in results]

    # Statistik akhir
    filled = df[df['kabupaten'] != '']
    empty = df[df['kabupaten'] == '']
    print(f"\n{'='*60}")
    print(f"Kabupaten berhasil diisi: {len(filled)}")
    print(f"Kabupaten masih kosong  : {len(empty)}")
    if len(empty) > 0:
        print("Contoh yang kosong:")
        print(empty[['nama_wisata', 'alamat', 'lat', 'long']].head(10).to_string())

    # Simpan
    df_out = df[['place_id', 'nama_wisata', 'alamat', 'lat', 'long', 'kabupaten', 'provinsi']].copy()
    df_out.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\nDisimpan ke: {OUTPUT_FILE}")
    print("=" * 60)


if __name__ == "__main__":
    main()
