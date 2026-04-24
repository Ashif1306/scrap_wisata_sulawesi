import os
import csv
import json
import time
import re
import logging
import google.generativeai as genai

# ================================================================
# KONFIGURASI API & DATA
# ================================================================
API_KEY = "AIzaSyD041vz668DIZ0bulbq_NJmb9c6ApEyI3U"
genai.configure(api_key=API_KEY)

# Buat instance model (menggunakan model yang terbukti jalan di versi lib saat ini)
model = genai.GenerativeModel("gemini-flash-latest")

CSV_INPUT  = "wisata_sulawesi_cleaned_final.csv"
CSV_OUTPUT = "wisata_sulawesi_kategori_ai.csv"

# Kategori yang diizinkan
KATEGORI_VALID = [
    "Wisata Alam",
    "Wisata Budaya & Sejarah",
    "Wisata Religi",
    "Wisata Kota / Landmark",
    "Wisata Hiburan"
]

# ================================================================
# LOGGING
# ================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)-7s | %(message)s', datefmt='%H:%M:%S')

# ================================================================
# FUNGSI BANTUAN
# ================================================================
def load_processed_ids():
    """Membaca place_id yang sudah diproses dari CSV output."""
    processed = set()
    if os.path.exists(CSV_OUTPUT):
        try:
            with open(CSV_OUTPUT, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row.get('place_id', '').strip()
                    if pid:
                        processed.add(pid)
            logging.info(f"Resume: Ditemukan {len(processed)} tempat wisata yang sudah dikategorikan ulang.")
        except Exception as e:
            logging.warning(f"Tidak dapat membaca output CSV untuk resume: {e}")
    return processed

def write_batch_to_csv(rows, fieldnames):
    """Menyimpan batch data ke CSV Output."""
    file_exists = os.path.isfile(CSV_OUTPUT)
    with open(CSV_OUTPUT, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

def process_batch_with_ai(batch_rows, max_retries=5):
    """Mengirim 1 batch ke Gemini dengan auto-retry jika kena rate limit."""
    
    # 1. Bangun prompt berisi daftar nama tempat + alamat
    prompt = (
        "Anda adalah asisten data cerdas pariwisata. "
        "Tugas Anda: kategorikan tempat pariwisata dari Sulawesi berikut ke dalam SALAH SATU dari kategori berikut.\n\n"
        f"Kategori yang diizinkan (HARUS SAMA PERSIS, tidak boleh membuat kategori baru):\n{json.dumps(KATEGORI_VALID, ensure_ascii=False)}\n\n"
        "Data Tempat Wisata:\n"
    )
    
    for r in batch_rows:
        pid = r['place_id']
        nama = r['nama_wisata']
        alamat = r['alamat']
        prompt += f"- ID: {pid} | Nama: {nama} | Alamat: {alamat}\n"
    
    prompt += (
        "\nInstruksi Output:\n"
        "Berikan output MURNI DALAM FORMAT JSON (tanpa markdown). "
        "Formatnya dictionary dengan key berupa ID dan value berupa Kategori. "
        "WAJIB gunakan salah satu dari 5 kategori di atas, JANGAN buat kategori baru. "
        "Contoh: {\"ChIJ123\": \"Wisata Alam\", \"ChIJ456\": \"Wisata Kota / Landmark\"}"
    )

    # Auto-retry dengan backoff jika kena rate limit (429)
    for attempt in range(1, max_retries + 1):
        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            
            result_dict = json.loads(response.text)
            
            # Validasi/Fallback: pastikan kategori HARUS salah satu dari 5 yang valid
            final_dict = {}
            for r in batch_rows:
                pid = r['place_id']
                ai_kat = result_dict.get(pid, "Wisata Kota / Landmark").strip()
                
                # Normalisasi agar cocok dengan kategori baku
                if "Alam" in ai_kat:
                    ai_kat = "Wisata Alam"
                elif "Sejarah" in ai_kat or "Budaya" in ai_kat:
                    ai_kat = "Wisata Budaya & Sejarah"
                elif "Religi" in ai_kat or "Masjid" in ai_kat or "Gereja" in ai_kat:
                    ai_kat = "Wisata Religi"
                elif "Hiburan" in ai_kat or "Air" in ai_kat or "Kolam" in ai_kat or "Waterpark" in ai_kat:
                    ai_kat = "Wisata Hiburan"
                else:
                    ai_kat = "Wisata Kota / Landmark"
                
                final_dict[pid] = ai_kat
                
            return final_dict

        except Exception as e:
            error_str = str(e)
            # Cek apakah error adalah rate limit (429)
            if "429" in error_str or "quota" in error_str.lower():
                # Coba ambil waktu tunggu dari pesan error
                wait_match = re.search(r'retry in ([\d.]+)s', error_str)
                wait_time = float(wait_match.group(1)) + 5 if wait_match else 60
                
                logging.warning(f"  Rate limit! Percobaan {attempt}/{max_retries}. Menunggu {wait_time:.0f} detik...")
                time.sleep(wait_time)
            else:
                logging.error(f"Gagal memanggil AI (bukan rate limit): {e}")
                return None
    
    logging.error(f"Gagal setelah {max_retries} percobaan. Lewati batch ini.")
    return None

# ================================================================
# MAIN PROGRAM
# ================================================================
def main():
    logging.info("Memulai Proses Re-Kategori dengan AI (Gemini)")
    
    processed_ids = load_processed_ids()
    
    # Baca data sumber
    all_rows = []
    fieldnames = []
    try:
        with open(CSV_INPUT, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            all_rows = list(reader)
    except Exception as e:
        logging.error(f"Gagal baca {CSV_INPUT}: {e}")
        return

    # Filter yang belum diproses
    pending_rows = [r for r in all_rows if r['place_id'] not in processed_ids]
    total_pending = len(pending_rows)
    total_done = len(processed_ids)
    logging.info(f"Total row di CSV: {len(all_rows)} | Sudah diproses: {total_done} | Sisa: {total_pending}")
    
    if total_pending == 0:
        logging.info("Semua baris sudah diproses! Selesai.")
        return

    BATCH_SIZE = 40
    total_batches = (total_pending + BATCH_SIZE - 1) // BATCH_SIZE
    failed_count = 0
    
    for i in range(0, total_pending, BATCH_SIZE):
        batch = pending_rows[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        global_done = total_done + i
        logging.info(f"Batch {batch_num}/{total_batches} ({len(batch)} item) | Progress: {global_done}/{len(all_rows)}")
        
        ai_result = process_batch_with_ai(batch)
        
        if ai_result:
            for r in batch:
                r['kategori'] = ai_result.get(r['place_id'], r['kategori'])
            
            write_batch_to_csv(batch, fieldnames)
            logging.info(f"  -> BATCH SUKSES. Menunggu 8 detik (Rate Limit)...")
            failed_count = 0
        else:
            failed_count += 1
            logging.error(f"  -> BATCH GAGAL (gagal berturut-turut: {failed_count}).")
            if failed_count >= 3:
                logging.error("3x gagal berturut-turut. Berhenti. Jalankan ulang nanti.")
                break
            continue
            
        time.sleep(8)

    final_done = total_done + sum(1 for r in pending_rows[:i + BATCH_SIZE] if r['place_id'] in (ai_result or {}))
    logging.info(f"Selesai. Jalankan ulang untuk melanjutkan sisa data.")

if __name__ == "__main__":
    main()
