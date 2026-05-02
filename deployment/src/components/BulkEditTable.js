"use client";

import React, { useState, useMemo, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Save, Search, CheckSquare, Square, AlertCircle, Loader2, ArrowLeft, ChevronLeft, ChevronRight, RotateCcw, ArrowUpDown } from 'lucide-react';
import Link from 'next/link';

const SORT_OPTIONS = [
  { value: 'nama_asc', label: 'Nama A → Z' },
  { value: 'nama_desc', label: 'Nama Z → A' },
  { value: 'harga_asc', label: 'Harga: Kosong → Mahal' },
  { value: 'harga_desc', label: 'Harga: Mahal → Kosong' },
  { value: 'rating_asc', label: 'Rating: Rendah → Tinggi' },
  { value: 'rating_desc', label: 'Rating: Tinggi → Rendah' },
  { value: 'ulasan_asc', label: 'Ulasan: Sedikit → Banyak' },
  { value: 'ulasan_desc', label: 'Ulasan: Banyak → Sedikit' },
];

const KATEGORI_LIST = [
  'Wisata Alam', 'Wisata Religi', 'Wisata Budaya & Sejarah',
  'Wisata Hiburan', 'Wisata Kota / Landmark'
];
const PER_PAGE = 50;

export default function BulkEditTable({ initialData }) {
  const router = useRouter();
  const [data, setData] = useState(() => initialData.map(i => ({ ...i })));
  const [origData] = useState(() => initialData.map(i => ({ ...i })));
  const [selected, setSelected] = useState(new Set());
  const [query, setQuery] = useState('');
  const [sortBy, setSortBy] = useState('nama_asc');
  const [page, setPage] = useState(1);
  const [token, setToken] = useState('');
  const [status, setStatus] = useState('idle');
  const [msg, setMsg] = useState('');
  const [showModal, setShowModal] = useState(false);

  const filtered = useMemo(() => {
    let result = data;
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter(i =>
        (i.nama_wisata || '').toLowerCase().includes(q) ||
        (i.kabupaten || '').toLowerCase().includes(q)
      );
    }
    // Sort
    const sorted = [...result];
    sorted.sort((a, b) => {
      switch (sortBy) {
        case 'nama_asc': return (a.nama_wisata || '').localeCompare(b.nama_wisata || '');
        case 'nama_desc': return (b.nama_wisata || '').localeCompare(a.nama_wisata || '');
        case 'harga_asc': {
          const ha = a.harga === '' || a.harga === null || a.harga === undefined ? -1 : Number(a.harga);
          const hb = b.harga === '' || b.harga === null || b.harga === undefined ? -1 : Number(b.harga);
          return ha - hb;
        }
        case 'harga_desc': {
          const ha = a.harga === '' || a.harga === null || a.harga === undefined ? -1 : Number(a.harga);
          const hb = b.harga === '' || b.harga === null || b.harga === undefined ? -1 : Number(b.harga);
          return hb - ha;
        }
        case 'rating_asc': return (Number(a.rating) || 0) - (Number(b.rating) || 0);
        case 'rating_desc': return (Number(b.rating) || 0) - (Number(a.rating) || 0);
        case 'ulasan_asc': return (Number(a.jumlah_riview) || 0) - (Number(b.jumlah_riview) || 0);
        case 'ulasan_desc': return (Number(b.jumlah_riview) || 0) - (Number(a.jumlah_riview) || 0);
        default: return 0;
      }
    });
    return sorted;
  }, [data, query, sortBy]);

  const totalPages = Math.ceil(filtered.length / PER_PAGE);
  const pageData = useMemo(() => {
    const s = (page - 1) * PER_PAGE;
    return filtered.slice(s, s + PER_PAGE);
  }, [filtered, page]);

  const isChanged = useCallback((pid) => {
    const cur = data.find(d => d.place_id === pid);
    const orig = origData.find(o => o.place_id === pid);
    if (!cur || !orig) return false;
    return cur.nama_wisata !== orig.nama_wisata ||
      cur.kategori !== orig.kategori ||
      String(cur.rating) !== String(orig.rating) ||
      String(cur.jumlah_riview) !== String(orig.jumlah_riview) ||
      String(cur.harga) !== String(orig.harga);
  }, [data, origData]);

  const getChanged = useCallback(() => {
    const out = [];
    for (const item of data) {
      if (!selected.has(item.place_id) || !isChanged(item.place_id)) continue;
      const h = Number(item.harga);
      let kh = item.kategori_harga || '-';
      if (!item.harga && item.harga !== 0) kh = '-';
      else if (h === 0) kh = 'Gratis';
      else if (h <= 9999) kh = 'Murah';
      else if (h <= 19999) kh = 'Sedang';
      else kh = 'Mahal';
      out.push({
        place_id: item.place_id, nama_wisata: item.nama_wisata,
        kategori: item.kategori, rating: item.rating,
        jumlah_riview: item.jumlah_riview, harga: item.harga,
        kategori_harga: kh, alamat: item.alamat,
        kabupaten: item.kabupaten, provinsi: item.provinsi,
        lat: item.lat, long: item.long,
      });
    }
    return out;
  }, [data, origData, selected, isChanged]);

  const editCell = (pid, field, val) => {
    setData(prev => prev.map(i => i.place_id === pid ? { ...i, [field]: val } : i));
    setSelected(prev => { const n = new Set(prev); n.add(pid); return n; });
  };

  const toggleOne = (pid) => {
    setSelected(prev => {
      const n = new Set(prev);
      n.has(pid) ? n.delete(pid) : n.add(pid);
      return n;
    });
  };

  const toggleAll = () => {
    const ids = pageData.map(d => d.place_id);
    const allSel = ids.every(id => selected.has(id));
    setSelected(prev => {
      const n = new Set(prev);
      ids.forEach(id => allSel ? n.delete(id) : n.add(id));
      return n;
    });
  };

  const doSave = async () => {
    const items = getChanged();
    if (!items.length) { setMsg('Tidak ada perubahan.'); setStatus('error'); setShowModal(false); return; }
    setStatus('loading'); setMsg(`Menyimpan ${items.length} data...`); setShowModal(false);
    try {
      const res = await fetch('/api/tourism/batch', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ items })
      });
      if (!res.ok) throw new Error(res.status === 401 ? 'Token tidak valid!' : 'Gagal menyimpan');
      const r = await res.json();
      setStatus('success');
      setMsg(`✅ ${r.successCount} data berhasil${r.failCount ? `, ${r.failCount} gagal` : ''}`);
      setTimeout(() => { router.push('/'); router.refresh(); }, 2000);
    } catch (e) { setStatus('error'); setMsg(e.message); }
  };

  const changedCount = getChanged().length;
  const allSel = pageData.length > 0 && pageData.every(d => selected.has(d.place_id));
  const iStyle = { width: '100%', padding: '0.5rem 0.6rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(0,0,0,0.25)', color: '#f8fafc', fontSize: '0.85rem', outline: 'none', transition: '0.2s' };

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <Link href="/add" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '42px', height: '42px', borderRadius: '50%', background: 'rgba(255,255,255,0.08)', color: 'white', textDecoration: 'none', border: '1px solid rgba(255,255,255,0.12)' }}>
          <ArrowLeft size={20} />
        </Link>
        <div>
          <h1 style={{ fontSize: '1.8rem', margin: 0 }}>Bulk Edit Data</h1>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', margin: '0.3rem 0 0' }}>Edit banyak data wisata sekaligus</p>
        </div>
      </div>

      {status === 'success' && <div style={{ padding: '1rem', background: 'rgba(16,185,129,0.15)', color: '#34d399', borderRadius: '14px', marginBottom: '1.5rem', border: '1px solid rgba(16,185,129,0.3)', fontWeight: '600' }}>{msg}</div>}
      {status === 'error' && <div style={{ padding: '1rem', background: 'rgba(239,68,68,0.15)', color: '#f87171', borderRadius: '14px', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', border: '1px solid rgba(239,68,68,0.3)' }}><AlertCircle size={18} />{msg}</div>}
      {status === 'loading' && <div style={{ padding: '1rem', background: 'rgba(59,130,246,0.1)', borderRadius: '14px', marginBottom: '1rem', border: '1px solid rgba(59,130,246,0.25)', display: 'flex', alignItems: 'center', gap: '0.6rem', color: '#60a5fa' }}><Loader2 size={18} className="animate-spin" />{msg}</div>}

      <div className="glass" style={{ padding: '1rem 1.2rem', borderRadius: '16px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: '1 1 220px', minWidth: '180px' }}>
          <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)', pointerEvents: 'none' }} />
          <input type="text" placeholder="Cari nama/kabupaten..." value={query} onChange={e => { setQuery(e.target.value); setPage(1); }} style={{ ...iStyle, paddingLeft: '2.2rem' }} />
        </div>
        {/* Sort Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flex: '0 0 auto' }}>
          <ArrowUpDown size={14} color="var(--text-secondary)" />
          <select
            value={sortBy}
            onChange={e => { setSortBy(e.target.value); setPage(1); }}
            style={{ ...iStyle, width: 'auto', minWidth: '180px', appearance: 'auto', cursor: 'pointer', background: 'rgba(0,0,0,0.3)' }}
          >
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
          <span><strong style={{ color: 'var(--accent-teal)' }}>{selected.size}</strong> dipilih</span>
          <span><strong style={{ color: changedCount > 0 ? '#fbbf24' : 'inherit' }}>{changedCount}</strong> diubah</span>
        </div>
        <div style={{ display: 'flex', gap: '0.6rem', marginLeft: 'auto' }}>
          <button onClick={() => { setData(origData.map(i => ({ ...i }))); setSelected(new Set()); }} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', padding: '0.55rem 1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.15)', background: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.85rem', fontWeight: '500' }}>
            <RotateCcw size={14} /> Reset
          </button>
          <button onClick={() => changedCount > 0 ? setShowModal(true) : (setStatus('error'), setMsg('Edit data terlebih dahulu.'))} disabled={status === 'loading'} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.55rem 1.2rem', borderRadius: '10px', border: 'none', background: changedCount > 0 ? 'linear-gradient(135deg, var(--accent-teal), #0d9488)' : 'rgba(255,255,255,0.08)', color: changedCount > 0 ? '#000' : 'var(--text-secondary)', cursor: changedCount > 0 ? 'pointer' : 'not-allowed', fontSize: '0.85rem', fontWeight: '700', boxShadow: changedCount > 0 ? '0 4px 14px rgba(20,184,166,0.3)' : 'none' }}>
            {status === 'loading' ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
            {status === 'loading' ? 'Menyimpan...' : `Simpan (${changedCount})`}
          </button>
        </div>
      </div>

      <div className="glass" style={{ overflowX: 'auto', borderRadius: '16px', padding: '0.5rem' }}>
        <style>{`.bi:focus{border-color:rgba(20,184,166,0.6)!important;box-shadow:0 0 0 2px rgba(20,184,166,0.15)}.br:hover{background:rgba(255,255,255,0.04)}.bc{background:rgba(251,191,36,0.06)!important}.bc:hover{background:rgba(251,191,36,0.1)!important}.ck{cursor:pointer;opacity:0.7;transition:0.15s}.ck:hover{opacity:1}@keyframes spin{from{transform:rotate(0)}to{transform:rotate(360deg)}}.animate-spin{animation:spin 1s linear infinite}`}</style>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem', minWidth: '900px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
              <th style={{ padding: '0.9rem 0.7rem', width: '48px', textAlign: 'center' }}>
                <div onClick={toggleAll} className="ck" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  {allSel ? <CheckSquare size={18} color="var(--accent-teal)" /> : <Square size={18} color="var(--text-secondary)" />}
                </div>
              </th>
              {['NO','NAMA WISATA','KABUPATEN','KATEGORI','RATING','ULASAN','HARGA (Rp)'].map((h,i) => (
                <th key={h} style={{ padding: '0.9rem 0.7rem', textAlign: 'left', color: 'var(--accent-teal)', fontWeight: '600', fontSize: '0.8rem', letterSpacing: '0.03em', minWidth: i===1?'220px':i===4?'90px':i===5?'110px':i===6?'120px':i===3?'160px':'auto' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageData.map((item, idx) => {
              const sel = selected.has(item.place_id);
              const chg = isChanged(item.place_id);
              const n = (page - 1) * PER_PAGE + idx + 1;
              return (
                <tr key={item.place_id} className={`br ${chg ? 'bc' : ''}`} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                  <td style={{ padding: '0.6rem 0.7rem', textAlign: 'center' }}>
                    <div onClick={() => toggleOne(item.place_id)} className="ck" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {sel ? <CheckSquare size={17} color="var(--accent-teal)" /> : <Square size={17} color="var(--text-secondary)" />}
                    </div>
                  </td>
                  <td style={{ padding: '0.6rem 0.7rem', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>{n}</td>
                  <td style={{ padding: '0.6rem 0.5rem' }}><input type="text" value={item.nama_wisata || ''} onChange={e => editCell(item.place_id, 'nama_wisata', e.target.value)} className="bi" style={iStyle} /></td>
                  <td style={{ padding: '0.6rem 0.7rem', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>{item.kabupaten || '-'}</td>
                  <td style={{ padding: '0.6rem 0.5rem' }}>
                    <select value={item.kategori || ''} onChange={e => editCell(item.place_id, 'kategori', e.target.value)} className="bi" style={{ ...iStyle, appearance: 'auto', cursor: 'pointer' }}>
                      <option value="">-</option>
                      {KATEGORI_LIST.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </td>
                  <td style={{ padding: '0.6rem 0.5rem' }}><input type="number" step="0.1" min="0" max="5" value={item.rating ?? ''} onChange={e => editCell(item.place_id, 'rating', e.target.value)} className="bi" style={{ ...iStyle, textAlign: 'center' }} /></td>
                  <td style={{ padding: '0.6rem 0.5rem' }}><input type="number" min="0" value={item.jumlah_riview ?? ''} onChange={e => editCell(item.place_id, 'jumlah_riview', e.target.value)} className="bi" style={{ ...iStyle, textAlign: 'center' }} /></td>
                  <td style={{ padding: '0.6rem 0.5rem' }}><input type="number" min="0" value={item.harga ?? ''} onChange={e => editCell(item.place_id, 'harga', e.target.value)} className="bi" style={{ ...iStyle, textAlign: 'right' }} /></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '1rem', marginTop: '1.5rem' }}>
          <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page===1} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.6rem 1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)', color: page===1?'rgba(255,255,255,0.2)':'white', cursor: page===1?'not-allowed':'pointer', fontSize: '0.85rem' }}><ChevronLeft size={16} /> Prev</button>
          <span style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Halaman <strong style={{ color: 'var(--accent-teal)' }}>{page}</strong> dari {totalPages}</span>
          <button onClick={() => setPage(p => Math.min(totalPages, p+1))} disabled={page===totalPages} style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', padding: '0.6rem 1rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.06)', color: page===totalPages?'rgba(255,255,255,0.2)':'white', cursor: page===totalPages?'not-allowed':'pointer', fontSize: '0.85rem' }}>Next <ChevronRight size={16} /></button>
        </div>
      )}

      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)', backdropFilter: 'blur(8px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 9999, padding: '1rem' }} onClick={() => setShowModal(false)}>
          <div className="animate-fade-in glass" onClick={e => e.stopPropagation()} style={{ width: '100%', maxWidth: '440px', padding: '2rem', borderRadius: '20px', background: 'var(--bg-dark)', border: '1px solid rgba(20,184,166,0.25)' }}>
            <h3 style={{ fontSize: '1.3rem', marginBottom: '0.5rem' }}>Konfirmasi Simpan</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>Menyimpan <strong style={{ color: 'var(--accent-teal)' }}>{changedCount}</strong> perubahan. Masukkan token akses.</p>
            <input type="password" value={token} onChange={e => setToken(e.target.value)} placeholder="Token akses..." autoFocus onKeyDown={e => { if(e.key==='Enter'&&token) doSave(); }} style={{ width: '100%', padding: '0.85rem', borderRadius: '10px', border: '1px solid rgba(20,184,166,0.3)', background: 'rgba(0,0,0,0.3)', color: 'white', outline: 'none', fontSize: '0.95rem', marginBottom: '1.5rem' }} />
            <div style={{ display: 'flex', gap: '0.8rem' }}>
              <button onClick={() => setShowModal(false)} style={{ flex: 1, padding: '0.8rem', borderRadius: '10px', border: '1px solid rgba(255,255,255,0.15)', background: 'transparent', color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: '600' }}>Batal</button>
              <button onClick={doSave} disabled={!token} style={{ flex: 1, padding: '0.8rem', borderRadius: '10px', border: 'none', background: token ? 'linear-gradient(135deg, var(--accent-teal), #0d9488)' : 'rgba(255,255,255,0.08)', color: token ? '#000' : 'var(--text-secondary)', cursor: token ? 'pointer' : 'not-allowed', fontWeight: '700', boxShadow: token ? '0 4px 14px rgba(20,184,166,0.3)' : 'none' }}>Simpan Semua</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
