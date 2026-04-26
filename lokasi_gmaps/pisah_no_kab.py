"""
pisah_no_kab.py
===============
Pisahkan baris dari lokasi_scraped.csv yang belum punya kabupaten_gmaps
ke file wisata_no_kab.csv untuk diproses lanjut oleh scrape_kab_ddg.py.

Kriteria "tidak punya kabupaten":
  - kolom kabupaten_gmaps kosong / NaN
  - ATAU status_gmaps adalah: FAIL, NO_ADDR, NO_MATCH, WRONG_PLACE, ERROR, nan, kosong

Penggunaan:
  python pisah_no_kab.py
  python pisah_no_kab.py --input lokasi_scraped.csv --output wisata_no_kab.csv
"""

import os
import argparse
import pandas as pd

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE  = os.path.join(BASE_DIR, "lokasi_scraped.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "wisata_no_kab.csv")

GAGAL_STATUS = {"FAIL", "NO_ADDR", "NO_MATCH", "WRONG_PLACE", "ERROR", "", "nan"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input",  default=INPUT_FILE)
    ap.add_argument("--output", default=OUTPUT_FILE)
    args = ap.parse_args()

    df = pd.read_csv(args.input, dtype=str)
    print(f"[INPUT]  {args.input} ({len(df)} baris)")

    def tidak_punya_kab(row):
        kab    = str(row.get("kabupaten_gmaps", "")).strip()
        status = str(row.get("status_gmaps",    "")).strip()
        kab_kosong    = kab in ("", "nan")
        status_gagal  = status in GAGAL_STATUS
        return kab_kosong or status_gagal

    mask = df.apply(tidak_punya_kab, axis=1)
    df_no_kab = df[mask].copy()
    df_ok     = df[~mask]

    print(f"[OK]     {len(df_ok)} wisata sudah punya kabupaten")
    print(f"[NO_KAB] {len(df_no_kab)} wisata belum punya kabupaten → disimpan ke {args.output}")

    # Tambah kolom untuk hasil scraping DuckDuckGo
    for col in ["kab_ddg", "prov_ddg", "snippet_ddg", "status_ddg"]:
        if col not in df_no_kab.columns:
            df_no_kab[col] = ""

    df_no_kab.to_csv(args.output, index=False, encoding="utf-8-sig")
    print("[DONE]   File tersimpan.")

    # Statistik status
    print("\n── Statistik status gagal ──────────────────")
    print(df_no_kab["status_gmaps"].value_counts(dropna=False).to_string())


if __name__ == "__main__":
    main()
