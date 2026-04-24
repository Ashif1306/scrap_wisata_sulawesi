import os
import re
import glob
import pandas as pd

LOG_DIR = "logs"
CSV_FILE = "scrap_harga_wisata.csv"

def recover():
    # Pola regex untuk mengekstrak informasi pencarian nama
    # 2026-04-19 22... | INFO     | [    1/2708] [CARI]  'Losari Beach Platform' (Wisata Alam)
    pola_cari = re.compile(r"\[CARI\]\s+'(.+?)'\s+\(")
    
    # Pola regex untuk L1
    # 2026-04-19 22... | DEBUG    |   [L1] Harga terpilih: 3000 | sumber: https://...
    pola_l1 = re.compile(r"\[L1\] Harga terpilih: \d+ \| sumber: (.+?) \|")
    
    # Pola regex untuk L1 gratis
    # 2026-04-19 ... | DEBUG    |   [L1] snippet 1: gratis (cocok nama + lokasi) -> wait, then info sumber:
    # Actually wait:
    # if it's L1 gratis: meta["harga_sumber_url"] = sumber or "ddgs:gratis", but it doesn't print "sumber: ..." except in INFO:
    # 2026-04-20 05... | INFO     | [    7/2708] [OK]    'Taman Pakui Sayang' -> Rp 0 (Gratis) [L1] ddgs:gratis
    pola_ok_info = re.compile(r"\[OK\]\s+'(.+?)'.+?\[(L\d)\]\s+(.+)")

    # Pola regex untuk L2/L3
    # 2026-04-19 ... | DEBUG    |   [L2] Harga Rp 15,000 dari https://...
    pola_l2_harga = re.compile(r"\[L2\] Harga Rp [\d,]+ dari (.+)")
    pola_l2_gratis = re.compile(r"\[L2\] Gratis terdeteksi di (.+)")
    pola_l3_harga = re.compile(r"\[L3\] Harga Rp [\d,]+ dari (.+)")
    pola_l3_gratis = re.compile(r"\[L3\] Gratis terdeteksi di (.+)")

    # Dictionary: nama wisata -> url
    url_map = {}
    
    log_files = sorted(glob.glob(os.path.join(LOG_DIR, "*.log")))
    for lf in log_files:
        current_nama = None
        with open(lf, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # Cek [CARI]
                m_cari = pola_cari.search(line)
                if m_cari:
                    current_nama = m_cari.group(1).strip()
                    continue
                
                if current_nama:
                    u = None
                    if "[L1] Harga terpilih:" in line:
                        m = pola_l1.search(line)
                        if m: u = m.group(1).strip()
                    elif "[L2] Harga Rp" in line:
                        m = pola_l2_harga.search(line)
                        if m: u = m.group(1).strip()
                    elif "[L2] Gratis terdeteksi di" in line:
                        m = pola_l2_gratis.search(line)
                        if m: u = m.group(1).strip()
                    elif "[L3] Harga Rp" in line:
                        m = pola_l3_harga.search(line)
                        if m: u = m.group(1).strip()
                    elif "[L3] Gratis terdeteksi di" in line:
                        m = pola_l3_gratis.search(line)
                        if m: u = m.group(1).strip()
                        
                    if u:
                        url_map[current_nama] = u
                        current_nama = None # URL obtained
                        continue
                
                # Cek dari baris [OK] untuk fallback (jika URL terpotong 70 char tidak apa-apa jika itu ddgs:snippet)
                m_ok = pola_ok_info.search(line)
                if m_ok:
                    nama_ok = m_ok.group(1).strip()
                    url_ok = m_ok.group(3).strip()
                    if url_ok.startswith("ddgs:"):
                        url_map[nama_ok] = url_ok

    print(f"Berasil mengekstrak {len(url_map)} URL dari logs.")
    
    # 2. Update CSV
    df = pd.read_csv(CSV_FILE)
    if 'url_harga' not in df.columns:
        df['url_harga'] = None
        
    count_updated = 0
    for idx, row in df.iterrows():
        nama = str(row['nama wisata']).strip()
        h = row['harga_rp']
        u = row['url_harga']
        
        # Jika punya harga tetapi url nya NaN / kosong
        if pd.notna(h) and str(h).strip() != "-" and (pd.isna(u) or str(u).strip() == "" or str(u).strip() == "-"):
            # Coba ambil dari map
            if nama in url_map:
                df.at[idx, 'url_harga'] = url_map[nama]
                count_updated += 1
                
    print(f"Berhasil mengupdate {count_updated} baris url_harga di CSV.")
    df.to_csv(CSV_FILE, index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    recover()
