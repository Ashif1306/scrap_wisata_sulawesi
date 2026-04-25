"""
diagnose_mismatch.py — Quick diagnostic: how many kabupaten values in the CSV
don't match what appears in the 'alamat' column?
"""
import pandas as pd
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

df = pd.read_csv('wisata_sulawesi_lengkap.csv')

mismatches = []
for i, row in df.iterrows():
    alamat = str(row.get('alamat', ''))
    kab_col = str(row['kabupaten']).strip()

    # Extract "Kabupaten X" or "Kota X" from alamat
    m = re.search(
        r'(Kabupaten|Kota)\s+([A-Za-z][A-Za-z\s\-]+?)(?=\s*[,\.\d]|\s+Sulawesi|\s+Gorontalo|\s+Indonesia|$)',
        alamat, re.IGNORECASE
    )
    if m:
        kab_from_alamat = f'{m.group(1).title()} {m.group(2).strip().title()}'
        if kab_from_alamat.lower().rstrip() != kab_col.lower().rstrip():
            mismatches.append({
                'idx': i,
                'nama': row['nama_wisata'],
                'kab_now': kab_col,
                'kab_alamat': kab_from_alamat,
                'alamat_snippet': alamat[:100]
            })

print(f'Total rows: {len(df)}')
print(f'Mismatches found (alamat vs kabupaten): {len(mismatches)}')
print()
for m in mismatches[:30]:
    print(f"[{m['idx']}] {m['nama'][:50]}")
    print(f"   NOW: {m['kab_now']}  ->  ALAMAT: {m['kab_alamat']}")
    print(f"   {m['alamat_snippet']}")
    print()
