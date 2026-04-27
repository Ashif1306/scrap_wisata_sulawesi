"use client";

import React, { useState } from 'react';
import { MapPin, Star, X, Ticket, FileText, ExternalLink, Edit, Trash2 } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

const getCategoryStyle = (category) => {
  const cat = category ? category.toLowerCase() : '';
  if (cat.includes('alam')) return { bg: 'rgba(16, 185, 129, 0.15)', text: '#34d399' };
  if (cat.includes('kota') || cat.includes('landmark')) return { bg: 'rgba(59, 130, 246, 0.15)', text: '#60a5fa' };
  if (cat.includes('budaya') || cat.includes('sejarah')) return { bg: 'rgba(245, 158, 11, 0.15)', text: '#fbbf24' };
  if (cat.includes('hiburan')) return { bg: 'rgba(236, 72, 153, 0.15)', text: '#f472b6' };
  if (cat.includes('religi')) return { bg: 'rgba(168, 85, 247, 0.15)', text: '#c084fc' };
  return { bg: 'rgba(20, 184, 166, 0.1)', text: 'var(--accent-teal)' };
};

const getPriceStyle = (kategori) => {
  const k = kategori ? kategori.toLowerCase() : '';
  if (k === 'murah') return { bg: 'rgba(16, 185, 129, 0.2)', text: '#34d399', border: 'rgba(16, 185, 129, 0.4)' };
  if (k === 'sedang') return { bg: 'rgba(245, 158, 11, 0.2)', text: '#fbbf24', border: 'rgba(245, 158, 11, 0.4)' };
  if (k === 'mahal') return { bg: 'rgba(239, 68, 68, 0.2)', text: '#f87171', border: 'rgba(239, 68, 68, 0.4)' };
  return { bg: 'rgba(100, 116, 139, 0.2)', text: '#94a3b8', border: 'rgba(100, 116, 139, 0.4)' };
};

const formatHarga = (harga) => {
  if (!harga || harga === '-') return 'Gratis';
  const num = parseFloat(harga);
  if (isNaN(num) || num === 0) return 'Gratis';
  return 'Rp ' + num.toLocaleString('id-ID');
};

export default function DataTable({ data, start }) {
  const router = useRouter();
  const [selectedItem, setSelectedItem] = useState(null);
  const [imgError, setImgError] = useState(false);
  
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteToken, setDeleteToken] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState('');

  React.useEffect(() => {
    if (selectedItem) {
      document.body.style.overflow = 'hidden';
      setImgError(false); // reset image error on new selection
    } else {
      document.body.style.overflow = 'unset';
      setShowDeleteConfirm(false);
      setDeleteToken('');
      setDeleteError('');
    }
    
    // Cleanup on unmount to prevent scroll lock on other pages
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [selectedItem]);

  const handleDelete = async () => {
    if (!deleteToken) return;
    setIsDeleting(true);
    setDeleteError('');
    try {
      const res = await fetch(`/api/tourism/${selectedItem.place_id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${deleteToken}`
        }
      });
      if (!res.ok) {
        if (res.status === 401) {
          throw new Error('Token keamanan salah!');
        }
        throw new Error('Gagal menghapus data.');
      }
      // Success
      setSelectedItem(null);
      router.refresh();
    } catch (err) {
      setDeleteError(err.message);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>
      <div className="glass" style={{ overflowX: 'auto', padding: '1rem', borderRadius: '16px' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.95rem' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--accent-teal)' }}>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600' }}>No</th>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600' }}>Destinasi Wisata</th>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600' }}>Kategori</th>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600' }}>Alamat</th>
              <th style={{ padding: '1rem 1.5rem', fontWeight: '600' }}>Rating (Ulasan)</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {
              const catStyle = getCategoryStyle(item.kategori);
              return (
                <tr
                  key={item.id || item.place_id || index}
                  className="table-row-hover"
                  style={{
                    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
                    transition: 'background 0.2s',
                    cursor: 'pointer'
                  }}
                  onClick={() => setSelectedItem(item)}
                >
                  <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)' }}>{start + index + 1}</td>
                  <td style={{ padding: '1rem 1.5rem' }}>
                    <div style={{ fontWeight: '500', color: 'var(--text-primary)', fontFamily: 'Outfit, sans-serif', fontSize: '1.05rem' }}>{item.nama_wisata}</div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>{item.kabupaten}</div>
                  </td>
                  <td style={{ padding: '1rem 1.5rem' }}>
                    <span style={{
                      display: 'inline-block',
                      whiteSpace: 'nowrap',
                      background: catStyle.bg,
                      color: catStyle.text,
                      padding: '0.35rem 0.75rem',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: '600'
                    }}>
                      {item.kategori || '-'}
                    </span>
                  </td>
                  <td style={{ padding: '1rem 1.5rem', color: 'var(--text-secondary)', maxWidth: '250px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={item.alamat}>
                    {item.alamat || '-'}
                  </td>
                  <td style={{ padding: '1rem 1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: '#fbbf24', fontWeight: '600' }}>
                      ★ {item.rating ? Number(item.rating).toFixed(1) : 'N/A'}
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', fontWeight: 'normal' }}>
                        ({item.jumlah_riview ? parseInt(item.jumlah_riview).toLocaleString('id-ID') : '0'})
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* POP UP Modal Detail Wisata */}
      {selectedItem && (
        <div
          className="modal-container"
          style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.85)', backdropFilter: 'blur(10px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 9999, padding: '1rem'
          }}
          onClick={() => setSelectedItem(null)}
        >
          <style>{`
            .modal-hero { height: 320px; }
            .modal-title-text { font-size: 1.9rem; }
            .modal-chips { grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
            .modal-iframe { height: 280px; }
            @media (max-width: 600px) {
              .modal-popup { border-radius: 16px !important; max-height: 98vh !important; }
              .modal-hero { height: 200px !important; }
              .modal-title-text { font-size: 1.3rem !important; }
              .modal-chips { grid-template-columns: 1fr 1fr !important; gap: 0.5rem !important; }
              .modal-body-scroll { padding: 1rem 1rem 1.5rem !important; }
              .modal-iframe { height: 200px !important; }
            }
          `}</style>
          <div
            className="animate-fade-in modal-box modal-popup"
            style={{
              width: '100%', maxWidth: '820px', backgroundColor: 'var(--bg-dark)',
              borderRadius: '24px', overflow: 'hidden', position: 'relative',
              boxShadow: '0 25px 60px -12px rgba(0, 0, 0, 0.8)', border: '1px solid var(--glass-border)',
              display: 'flex', flexDirection: 'column', maxHeight: '95vh'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* ===== HERO IMAGE ===== */}
            <div className="modal-hero" style={{ width: '100%', position: 'relative', flexShrink: 0, backgroundColor: '#0f172a' }}>
              {selectedItem.url_image && !imgError ? (
                <img
                  src={selectedItem.url_image}
                  alt={selectedItem.nama_wisata}
                  referrerPolicy="no-referrer"
                  crossOrigin="anonymous"
                  onError={() => setImgError(true)}
                  style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
                />
              ) : (
                <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', color: 'var(--text-secondary)', background: 'linear-gradient(135deg, #0f172a, #1e293b)' }}>
                  <MapPin size={48} opacity={0.3} />
                  <span style={{ fontSize: '0.85rem', opacity: 0.5 }}>Foto tidak tersedia</span>
                </div>
              )}

              {/* Gradient overlay bawah */}
              <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: '120px', background: 'linear-gradient(to top, rgba(10,15,28,1) 0%, rgba(10,15,28,0.5) 60%, transparent 100%)' }} />

              {/* Kategori pill (bottom-left) */}
              <div style={{ position: 'absolute', bottom: '16px', left: '20px' }}>
                <span style={{
                  background: getCategoryStyle(selectedItem.kategori).bg,
                  color: getCategoryStyle(selectedItem.kategori).text,
                  border: `1px solid ${getCategoryStyle(selectedItem.kategori).text}44`,
                  padding: '0.35rem 0.9rem', borderRadius: '20px', fontSize: '0.8rem', fontWeight: '700',
                  backdropFilter: 'blur(4px)', boxShadow: '0 2px 8px rgba(0,0,0,0.4)'
                }}>
                  {selectedItem.kategori || 'Tanpa Kategori'}
                </span>
              </div>

              {/* Rating (bottom-right) */}
              <div style={{ position: 'absolute', bottom: '12px', right: '20px', textAlign: 'right' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', color: '#fbbf24', fontWeight: '800', fontSize: '1.4rem', textShadow: '0 2px 6px rgba(0,0,0,0.6)' }}>
                  <Star size={20} fill="#fbbf24" />
                  {selectedItem.rating ? Number(selectedItem.rating).toFixed(1) : 'N/A'}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'rgba(255,255,255,0.6)', marginTop: '2px' }}>
                  {selectedItem.jumlah_riview ? parseInt(selectedItem.jumlah_riview).toLocaleString('id-ID') : '0'} ulasan
                </div>
              </div>

              {/* Tombol Close */}
              <button
                onClick={() => setSelectedItem(null)}
                style={{
                  position: 'absolute', top: '14px', right: '14px',
                  background: 'rgba(0,0,0,0.6)', border: '1px solid rgba(255,255,255,0.2)',
                  color: 'white', borderRadius: '50%', width: '38px', height: '38px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  cursor: 'pointer', zIndex: 10, transition: '0.2s ease',
                  backdropFilter: 'blur(4px)'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(239, 68, 68, 0.85)'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(0,0,0,0.6)'}
              >
                <X size={18} />
              </button>
            </div>

            {/* ===== SCROLLABLE BODY ===== */}
            <div className="modal-body-scroll" style={{ flex: 1, minHeight: 0, overflowY: 'auto', padding: '1.5rem 2rem 2rem' }}>

              {/* Nama & Lokasi */}
              <h2 className="modal-title-text" style={{ fontFamily: 'Outfit, sans-serif', color: 'var(--text-primary)', marginBottom: '0.4rem', lineHeight: '1.15' }}>
                {selectedItem.nama_wisata}
              </h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
                <MapPin size={14} color="var(--accent-teal)" />
                {selectedItem.kabupaten}{selectedItem.provinsi ? `, ${selectedItem.provinsi}` : ''}
              </div>

              {/* ===== INFO CHIPS ===== */}
              <div className="modal-chips" style={{ display: 'grid', gap: '0.75rem', marginBottom: '1.8rem' }}>
                {/* Harga */}
                <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '14px', padding: '1rem 1.2rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.08em', marginBottom: '0.4rem' }}>
                    <Ticket size={13} /> HARGA TIKET
                  </div>
                  <div style={{ color: 'var(--accent-teal)', fontWeight: '700', fontSize: '1.1rem', marginBottom: '0.4rem' }}>
                    {formatHarga(selectedItem.harga)}
                  </div>
                  {selectedItem.kategori_harga && selectedItem.kategori_harga !== '-' && (
                    <span style={{
                      background: getPriceStyle(selectedItem.kategori_harga).bg,
                      color: getPriceStyle(selectedItem.kategori_harga).text,
                      border: `1px solid ${getPriceStyle(selectedItem.kategori_harga).border}`,
                      fontSize: '0.7rem', fontWeight: '700', padding: '0.2rem 0.6rem', borderRadius: '8px'
                    }}>
                      {selectedItem.kategori_harga}
                    </span>
                  )}
                </div>

                {/* Rating */}
                <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '14px', padding: '1rem 1.2rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.08em', marginBottom: '0.4rem' }}>
                    <Star size={13} /> RATING
                  </div>
                  <div style={{ color: '#fbbf24', fontWeight: '700', fontSize: '1.1rem', marginBottom: '0.4rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                    <Star size={16} fill="#fbbf24" />
                    {selectedItem.rating ? Number(selectedItem.rating).toFixed(1) : 'N/A'}
                  </div>
                  <div style={{ color: 'var(--text-secondary)', fontSize: '0.75rem' }}>
                    {selectedItem.jumlah_riview ? parseInt(selectedItem.jumlah_riview).toLocaleString('id-ID') : '0'} ulasan
                  </div>
                </div>

                {/* Koordinat */}
                {(selectedItem.lat && selectedItem.long) && (
                  <div style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '14px', padding: '1rem 1.2rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-secondary)', fontSize: '0.7rem', fontWeight: '700', letterSpacing: '0.08em', marginBottom: '0.4rem' }}>
                      <MapPin size={13} /> KOORDINAT
                    </div>
                    <div style={{ color: '#60a5fa', fontWeight: '600', fontSize: '0.85rem', lineHeight: 1.5 }}>
                      {parseFloat(selectedItem.lat).toFixed(5)}<br />
                      {parseFloat(selectedItem.long).toFixed(5)}
                    </div>
                  </div>
                )}
              </div>

              {/* ===== ALAMAT ===== */}
              <div style={{ marginBottom: '1.8rem' }}>
                <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', marginBottom: '0.75rem', fontSize: '1rem', fontFamily: 'Outfit, sans-serif' }}>
                  <MapPin size={16} color="var(--accent-teal)" /> Alamat Lengkap
                </h4>
                <p style={{
                  color: 'var(--text-secondary)', lineHeight: '1.7', fontSize: '0.92rem',
                  background: 'rgba(0,0,0,0.2)', padding: '1rem 1.2rem', borderRadius: '12px'
                }}>
                  {selectedItem.alamat || 'Informasi alamat tidak tersedia.'}
                </p>
              </div>

              {/* ===== DESKRIPSI ===== */}
              {selectedItem.deskripsi_wisata && selectedItem.deskripsi_wisata !== '-' && (
                <div style={{ marginBottom: '1.8rem' }}>
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', marginBottom: '0.75rem', fontSize: '1rem', fontFamily: 'Outfit, sans-serif' }}>
                    <FileText size={16} color="var(--accent-teal)" /> Deskripsi
                  </h4>
                  <p style={{
                    color: 'var(--text-secondary)', lineHeight: '1.8', fontSize: '0.92rem',
                    background: 'rgba(0,0,0,0.2)', padding: '1rem 1.2rem', borderRadius: '12px',
                    borderLeft: '3px solid var(--accent-teal)'
                  }}>
                    {selectedItem.deskripsi_wisata}
                  </p>
                  {selectedItem.sumber_deskripsi && selectedItem.sumber_deskripsi !== '-' && (
                    <a
                      href={selectedItem.sumber_deskripsi}
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: '0.3rem', marginTop: '0.5rem', fontSize: '0.75rem', color: 'var(--accent-teal)', opacity: 0.7, textDecoration: 'none' }}
                    >
                      <ExternalLink size={11} /> Sumber
                    </a>
                  )}
                </div>
              )}

              {/* ===== PETA LOKASI ===== */}
              {(selectedItem.lat && selectedItem.long) && (
                <div style={{ marginBottom: '1.8rem' }}>
                  <h4 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--text-primary)', marginBottom: '0.75rem', fontSize: '1rem', fontFamily: 'Outfit, sans-serif' }}>
                    <MapPin size={16} color="var(--accent-teal)" /> Peta Lokasi
                  </h4>
                  <div className="modal-iframe" style={{ borderRadius: '14px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)' }}>
                    <iframe
                      width="100%"
                      height="100%"
                      frameBorder="0"
                      style={{ border: 0, display: 'block' }}
                      src={`https://maps.google.com/maps?q=${selectedItem.lat},${selectedItem.long}&z=15&output=embed`}
                      allowFullScreen
                      title={`Peta ${selectedItem.nama_wisata}`}
                    />
                  </div>
                </div>
              )}              {/* ===== TOMBOL AKSI ===== */}
              {!showDeleteConfirm ? (
                <div style={{ display: 'flex', gap: '1rem', width: '100%', flexWrap: 'wrap' }}>
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem',
                      flex: 1, padding: '0.9rem',
                      background: 'rgba(239, 68, 68, 0.1)',
                      color: '#f87171', borderRadius: '14px', textDecoration: 'none',
                      fontWeight: '700', fontSize: '0.95rem',
                      border: '1px solid rgba(239, 68, 68, 0.3)',
                      transition: 'all 0.2s ease', cursor: 'pointer'
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'; }}
                  >
                    <Trash2 size={18} /> Hapus
                  </button>

                  <Link
                    href={`/edit/${selectedItem.place_id}`}
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem',
                      flex: 1, padding: '0.9rem',
                      background: 'rgba(255, 255, 255, 0.1)',
                      color: 'white', borderRadius: '14px', textDecoration: 'none',
                      fontWeight: '700', fontSize: '0.95rem',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.2)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255, 255, 255, 0.1)'; }}
                  >
                    <Edit size={18} /> Edit Data
                  </Link>

                  <a
                    href={
                      selectedItem.lat && selectedItem.long
                        ? `https://www.google.com/maps/search/?api=1&query=${selectedItem.lat},${selectedItem.long}${selectedItem.place_id ? `&query_place_id=${selectedItem.place_id}` : ''}`
                        : `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selectedItem.nama_wisata)}`
                    }
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.6rem',
                      flex: 2, padding: '0.9rem',
                      background: 'linear-gradient(135deg, var(--accent-blue), var(--accent-teal))',
                      color: 'white', borderRadius: '14px', textDecoration: 'none',
                      fontWeight: '700', fontSize: '0.95rem',
                      boxShadow: '0 4px 20px rgba(20, 184, 166, 0.3)',
                      transition: 'all 0.2s ease'
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.transform = 'translateY(-2px)'; e.currentTarget.style.boxShadow = '0 8px 25px rgba(20, 184, 166, 0.45)'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.boxShadow = '0 4px 20px rgba(20, 184, 166, 0.3)'; }}
                  >
                    <MapPin size={18} /> Buka di Google Maps
                  </a>
                </div>
              ) : (
                <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '14px', padding: '1.2rem', width: '100%' }}>
                  <h4 style={{ color: '#f87171', marginBottom: '0.8rem', fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Trash2 size={16} /> Konfirmasi Penghapusan
                  </h4>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                    Masukkan token keamanan untuk menghapus destinasi wisata ini secara permanen.
                  </p>
                  
                  {deleteError && (
                    <div style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '1rem', background: 'rgba(239,68,68,0.15)', padding: '0.5rem 0.8rem', borderRadius: '8px' }}>
                      {deleteError}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '0.8rem', alignItems: 'center', flexWrap: 'wrap' }}>
                    <input
                      type="password"
                      placeholder="Token keamanan..."
                      value={deleteToken}
                      onChange={(e) => setDeleteToken(e.target.value)}
                      style={{ flex: 1, minWidth: '150px', padding: '0.8rem', borderRadius: '8px', border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(0,0,0,0.3)', color: 'white', outline: 'none' }}
                    />
                    <button
                      onClick={handleDelete}
                      disabled={isDeleting || !deleteToken}
                      style={{
                        padding: '0.8rem 1.5rem', background: '#ef4444', color: 'white', borderRadius: '8px', fontWeight: '700',
                        border: 'none', cursor: (isDeleting || !deleteToken) ? 'not-allowed' : 'pointer',
                        opacity: (isDeleting || !deleteToken) ? 0.7 : 1, transition: '0.2s'
                      }}
                    >
                      {isDeleting ? 'Menghapus...' : 'Ya, Hapus'}
                    </button>
                    <button
                      onClick={() => { setShowDeleteConfirm(false); setDeleteToken(''); setDeleteError(''); }}
                      disabled={isDeleting}
                      style={{
                        padding: '0.8rem 1.5rem', background: 'transparent', color: 'var(--text-secondary)', borderRadius: '8px', fontWeight: '600',
                        border: '1px solid var(--glass-border)', cursor: 'pointer', transition: '0.2s'
                      }}
                    >
                      Batal
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
