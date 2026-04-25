"""
=================================================================
VALIDASI KABUPATEN WISATA SULAWESI MENGGUNAKAN GEMINI AI
=================================================================
- Model    : gemini-2.0-flash (terbaru & paling akurat untuk ini)
- API Keys : 3 key dengan auto-rotate saat rate limit
- Aturan   : HANYA update kabupaten jika salah, JANGAN tambah
             data baru, JANGAN ubah alamat
- Output   : wisata_sulawesi_fixed.csv (overwrite)
=================================================================
"""

import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import pandas as pd
import json
import time
import os
import signal
import google.generativeai as genai

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(SCRIPT_DIR, "wisata_sulawesi_fixed.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "wisata_sulawesi_fixed.csv")
PROGRESS_FILE = os.path.join(SCRIPT_DIR, "_ai_validation_progress.json")

# ── API KEYS (auto-rotate saat limit) ──────────────
API_KEYS = [
    "AIzaSyA1hJBvslDmQfQeJp7pkr8zUevsfN0c6DU", # Key Baru (Fresh)
    "AIzaSyDABMnmqILkzPQ_1o1jfexw-XGp2o2GdJM",
    "AIzaSyD041vz668DIZ0bulbq_NJmb9c6ApEyI3U",
    "AIzaSyD23r7ATLNTth9A1sPumE8i75AgAZl6qkI",
]
current_key_idx = 0

def get_model():
    """Kembalikan model Gemini dengan API key aktif."""
    genai.configure(api_key=API_KEYS[current_key_idx])
    # Pakai 2.0-flash karena terbaru dan paling akurat sesuai deskripsi
    return genai.GenerativeModel("gemini-2.0-flash")

def rotate_key(reason=""):
    """Pindah ke API key berikutnya."""
    global current_key_idx
    current_key_idx = (current_key_idx + 1) % len(API_KEYS)
    print(f"  [KEY ROTATE] Pindah ke key #{current_key_idx + 1} ({reason})")
    time.sleep(5)

# ... (VALID_KAB_KOTA tetap)
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

VALID_KAB_SET  = {k.lower() for k in VALID_KAB_KOTA}
VALID_KAB_LIST = json.dumps(VALID_KAB_KOTA, ensure_ascii=False)

# ── SHUTDOWN GRACEFUL ────────────────────────────────
shutdown_flag = False
def signal_handler(sig, frame):
    global shutdown_flag
    print("\n[!] Ctrl+C — menyimpan progress...")
    shutdown_flag = True
signal.signal(signal.SIGINT, signal_handler)

# ── PROGRESS ─────────────────────────────────────────
def save_progress(done, fixes):
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump({'done': list(done), 'fixes': fixes}, f, ensure_ascii=False, indent=2)

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
                d = json.load(f)
            return set(d.get('done', [])), d.get('fixes', [])
        except Exception:
            pass
    return set(), []

# ── IDENTIFIKASI SUSPECT ─────────────────────────────
def identify_suspects(df):
    """
    Hanya proses baris yang kabupaten-nya TIDAK muncul di kolom alamat.
    Data yang sudah benar (kabupaten ada di alamat) TIDAK diproses.
    """
    suspects = []
    for idx, row in df.iterrows():
        kab = str(row['kabupaten'])
        alamat = str(row.get('alamat', ''))
        # Hapus prefix untuk cek apakah nama ada di alamat
        kab_name = kab.replace('Kabupaten ', '').replace('Kota ', '').strip().lower()
        if kab_name not in alamat.lower():
            suspects.append(idx)
    return suspects

# ── TANYA AI ─────────────────────────────────────────
PROMPT_TEMPLATE = """
Kamu adalah validator data geografis Indonesia yang sangat akurat.

Tugas: Periksa apakah kolom "kabupaten" BENAR untuk tempat wisata berikut.

Data:
- Nama wisata : {nama}
- Alamat      : {alamat}
- Kabupaten sekarang : {kabupaten}
- Provinsi    : {provinsi}

Aturan KETAT:
1. Pilih kabupaten HANYA dari daftar ini: {valid_list}
2. JANGAN membuat nama kabupaten baru di luar daftar.
3. Jika "kabupaten sekarang" SUDAH BENAR berdasarkan alamat, kembalikan nilai yang SAMA.
4. Jika ada ketidaksesuaian (misal: alamat menyebut kecamatan "Turikale" tapi itu sebenarnya masuk Kabupaten Maros), koreksi.
5. JANGAN ubah alamat, JANGAN ubah provinsi.
6. Jika tidak yakin, kembalikan nilai SAMA dengan "kabupaten sekarang".

Balas HANYA dengan JSON berikut (tanpa penjelasan, tanpa markdown):
{{"kabupaten": "nama kabupaten/kota yang benar", "alasan": "singkat"}}
"""

def ask_ai(nama, alamat, kabupaten, provinsi):
    """
    Tanya Gemini apakah kabupaten sudah benar.
    Return: string nama kabupaten yang benar, atau None jika gagal.
    """
    global current_key_idx

    prompt = PROMPT_TEMPLATE.format(
        nama=nama,
        alamat=alamat,
        kabupaten=kabupaten,
        provinsi=provinsi,
        valid_list=VALID_KAB_LIST
    )

    # Coba setiap key maksimal 1x putaran
    for attempt in range(len(API_KEYS) * 2):
        try:
            model = get_model()
            resp = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.0,       # Harus deterministik
                )
            )
            result = json.loads(resp.text)
            new_kab = result.get('kabupaten', '').strip()
            alasan  = result.get('alasan', '')

            # Validasi: harus ada di whitelist
            if new_kab.lower() not in VALID_KAB_SET:
                print(f"    [SKIP] AI mengembalikan kabupaten tidak valid: '{new_kab}'")
                return None, None

            return new_kab, alasan

        except Exception as e:
            err = str(e)
            print(f"    [DEBUG ERROR] {err}") # Tambahkan ini untuk diagnosa
            if '429' in err or 'quota' in err.lower() or 'rate' in err.lower():
                print(f"    [LIMIT] Key #{current_key_idx+1} limit!")
                rotate_key("rate limit")
                time.sleep(10) # Jeda lebih lama
            else:
                print(f"    [ERR] {e}")
                return None, None

    print("    [FAIL] Semua key limit. Skip entry ini.")
    return None, None

# ── MAIN ─────────────────────────────────────────────
def main():
    global shutdown_flag

    print("=" * 60)
    print("VALIDASI KABUPATEN DENGAN GEMINI AI")
    print(f"Model  : gemini-2.0-flash")
    print(f"API Key: {len(API_KEYS)} key (auto-rotate)")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"Total data: {len(df)}")

    # Identifikasi data yang suspect salah
    suspects = identify_suspects(df)
    print(f"Suspect (kabupaten tidak cocok alamat): {len(suspects)}")

    if not suspects:
        print("Tidak ada data suspect. Selesai!")
        return

    # Load progress
    done, fixes = load_progress()
    done_idx = {int(x) for x in done}
    remaining = [i for i in suspects if i not in done_idx]
    print(f"Resume: {len(done_idx)} done, {len(fixes)} fixes | Sisa: {len(remaining)}\n")

    if not remaining:
        print("Semua suspect sudah diproses. Menerapkan fixes...")
        apply_fixes(df, fixes)
        return

    # Proses satu per satu
    for count, idx in enumerate(remaining):
        if shutdown_flag:
            break

        row = df.iloc[idx]
        nama      = str(row['nama_wisata'])
        alamat    = str(row['alamat'])
        old_kab   = str(row['kabupaten'])
        provinsi  = str(row['provinsi'])

        print(f"[{count+1}/{len(remaining)}] {nama}")
        print(f"  Saat ini: {old_kab}")

        new_kab, alasan = ask_ai(nama, alamat, old_kab, provinsi)

        if new_kab and new_kab.lower() != old_kab.lower():
            print(f"  -> FIX: {old_kab} => {new_kab} | {alasan}")
            fixes.append({
                'idx'    : int(idx),
                'nama'   : nama,
                'old_kab': old_kab,
                'new_kab': new_kab,
                'alasan' : alasan,
            })
        elif new_kab:
            print(f"  -> OK (tidak berubah)")
        else:
            print(f"  -> SKIP (AI gagal)")

        done_idx.add(idx)

        # Auto-save tiap 10 entry
        if (count + 1) % 10 == 0 or shutdown_flag:
            save_progress(done_idx, fixes)
            print(f"  [SAVE] {count+1}/{len(remaining)} | fixes: {len(fixes)}")

        time.sleep(5.0)  # Jeda diperlama jadi 5 detik biar aman

    save_progress(done_idx, fixes)

    if not shutdown_flag:
        apply_fixes(df, fixes)
        # Hapus progress setelah selesai
        if os.path.exists(PROGRESS_FILE):
            os.remove(PROGRESS_FILE)
        print("Progress file dihapus.")
    else:
        print(f"\nDihentikan. Jalankan ulang untuk melanjutkan.")

def apply_fixes(df, fixes):
    if not fixes:
        print("\nTidak ada perubahan yang diterapkan.")
        df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        return

    count = 0
    for fix in fixes:
        idx = fix['idx']
        df.at[idx, 'kabupaten'] = fix['new_kab']
        count += 1

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\n{'='*60}")
    print(f"SELESAI! {count} kabupaten dikoreksi.")
    print(f"File disimpan: {OUTPUT_FILE}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
