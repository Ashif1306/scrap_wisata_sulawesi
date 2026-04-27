import urllib.request
import urllib.parse
import json
import csv
import math
import time

URL = "https://bdtaakyfivzekgyldngw.supabase.co/rest/v1/tourism_data"
HEADERS = {
    "apikey": "sb_publishable_LjvKgQKnGqSOC2gJQzxTow_ABT1Fn8c",
    "Authorization": "Bearer sb_publishable_LjvKgQKnGqSOC2gJQzxTow_ABT1Fn8c",
    "Content-Type": "application/json",
    # Upsert: Merge duplicates (update if exists, insert if new)
    "Prefer": "resolution=merge-duplicates"
}

INPUT_FILE = r"d:\semester6\mc_learning\scrapt_wisata\hasil_final\wisata_sulawesi_lengkap.csv"
BATCH_SIZE = 500  # Upload dalam batch 500 baris agar tidak timeout

def is_nan(val):
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    if str(val).strip() == "" or str(val).strip() == "nan":
        return True
    return False

def clean_row(row):
    """Membersihkan dictionary, menghapus key dengan nilai NaN."""
    cleaned = {}
    for k, v in row.items():
        if not is_nan(v):
            # Coba konversi ke float jika relevan
            if k in ['lat', 'long', 'rating', 'harga']:
                try:
                    cleaned[k] = float(v)
                except ValueError:
                    cleaned[k] = str(v)
            elif k == 'jumlah_riview':
                try:
                    cleaned[k] = int(float(v))
                except ValueError:
                    cleaned[k] = str(v)
            else:
                cleaned[k] = str(v)
        else:
            cleaned[k] = None # Set null untuk Supabase
    return cleaned

def push_to_supabase():
    print(f"Membaca data dari: {INPUT_FILE}")
    data_to_push = []
    
    try:
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Pastikan ada place_id sebagai identitas
                if not row.get('place_id') or is_nan(row['place_id']):
                    continue
                data_to_push.append(clean_row(row))
    except FileNotFoundError:
        print(f"[Error] File tidak ditemukan: {INPUT_FILE}")
        return

    total_rows = len(data_to_push)
    print(f"Berhasil membaca {total_rows} baris. Memulai proses push (Upsert) ke Supabase...")
    
    success_count = 0
    fail_count = 0
    
    for i in range(0, total_rows, BATCH_SIZE):
        batch = data_to_push[i:i+BATCH_SIZE]
        
        req = urllib.request.Request(URL, headers=HEADERS, method="POST")
        data_bytes = json.dumps(batch).encode('utf-8')
        
        try:
            with urllib.request.urlopen(req, data=data_bytes) as response:
                if response.status in (200, 201):
                    success_count += len(batch)
                    print(f"  [{i+1} - {min(i+BATCH_SIZE, total_rows)}] Berhasil diunggah...")
                else:
                    fail_count += len(batch)
                    print(f"  [{i+1} - {min(i+BATCH_SIZE, total_rows)}] Gagal dengan status {response.status}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            print(f"  [{i+1} - {min(i+BATCH_SIZE, total_rows)}] HTTPError: {e.code} - {error_body}")
            fail_count += len(batch)
        except Exception as e:
            print(f"  [{i+1} - {min(i+BATCH_SIZE, total_rows)}] Exception: {str(e)}")
            fail_count += len(batch)
            
        # Jeda antar batch untuk mencegah rate limiting
        time.sleep(1)

    print("=" * 50)
    print("PROSES PUSH SELESAI")
    print(f"Total Data : {total_rows}")
    print(f"Berhasil   : {success_count}")
    print(f"Gagal      : {fail_count}")
    print("=" * 50)

if __name__ == "__main__":
    push_to_supabase()
