import urllib.request
import urllib.parse
import csv
import json
import time

url = "https://bdtaakyfivzekgyldngw.supabase.co/rest/v1/tourism_data"
headers = {
    "apikey": "sb_publishable_LjvKgQKnGqSOC2gJQzxTow_ABT1Fn8c",
    "Authorization": "Bearer sb_publishable_LjvKgQKnGqSOC2gJQzxTow_ABT1Fn8c"
}

all_data = []
offset = 0
limit = 1000

print("Mulai mengambil data dari Supabase...")
while True:
    params = urllib.parse.urlencode({
        "select": "*",
        "offset": offset,
        "limit": limit
    })
    full_url = f"{url}?{params}"
    
    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            if not data:
                break
            all_data.extend(data)
            print(f"Mengambil {len(data)} baris (Total: {len(all_data)})...")
            offset += limit
    except Exception as e:
        print(f"Error fetching data: {e}")
        break
    
if not all_data:
    print("Tidak ada data yang diambil.")
else:
    fieldnames = ['place_id', 'nama_wisata', 'kategori', 'alamat', 'kabupaten', 'provinsi', 'rating', 'jumlah_riview', 'harga', 'kategori_harga', 'url_harga', 'lat', 'long', 'url_image', 'deskripsi_wisata', 'sumber_deskripsi', 'label_rekomendasi']
    
    output_file = r"d:\semester6\mc_learning\scrapt_wisata\hasil_final\wisata_sulawesi_lengkap.csv"
    
    # Cek missing fields
    if len(all_data) > 0:
        first_row_keys = all_data[0].keys()
        missing_fields = [f for f in first_row_keys if f not in fieldnames and f != 'id' and f != 'created_at']
        if missing_fields:
            print(f"Warning: Terdapat kolom di Supabase yang tidak ada di CSV: {missing_fields}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_data:
            filtered_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(filtered_row)
    print(f"Berhasil menyimpan {len(all_data)} baris data ke {output_file}")
