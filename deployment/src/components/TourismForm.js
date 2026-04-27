"use client";

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Save, AlertCircle, Loader2, ArrowLeft } from 'lucide-react';
import Link from 'next/link';

const KATEGORI_LIST = [
  'Wisata Alam',
  'Wisata Religi',
  'Wisata Budaya & Sejarah',
  'Wisata Hiburan',
  'Wisata Kota / Landmark'
];


const KAB_TO_PROVINSI = {
  // Sulawesi Selatan
  "Kota Makassar":"Sulawesi Selatan","Kota Palopo":"Sulawesi Selatan","Kota Parepare":"Sulawesi Selatan",
  "Kabupaten Bantaeng":"Sulawesi Selatan","Kabupaten Barru":"Sulawesi Selatan","Kabupaten Bone":"Sulawesi Selatan",
  "Kabupaten Bulukumba":"Sulawesi Selatan","Kabupaten Enrekang":"Sulawesi Selatan","Kabupaten Gowa":"Sulawesi Selatan",
  "Kabupaten Jeneponto":"Sulawesi Selatan","Kabupaten Kepulauan Selayar":"Sulawesi Selatan",
  "Kabupaten Luwu":"Sulawesi Selatan","Kabupaten Luwu Timur":"Sulawesi Selatan","Kabupaten Luwu Utara":"Sulawesi Selatan",
  "Kabupaten Maros":"Sulawesi Selatan","Kabupaten Pangkajene Dan Kepulauan":"Sulawesi Selatan",
  "Kabupaten Pinrang":"Sulawesi Selatan","Kabupaten Sidenreng Rappang":"Sulawesi Selatan",
  "Kabupaten Sinjai":"Sulawesi Selatan","Kabupaten Soppeng":"Sulawesi Selatan","Kabupaten Takalar":"Sulawesi Selatan",
  "Kabupaten Tana Toraja":"Sulawesi Selatan","Kabupaten Toraja Utara":"Sulawesi Selatan","Kabupaten Wajo":"Sulawesi Selatan",
  // Sulawesi Barat
  "Kabupaten Mamuju":"Sulawesi Barat","Kabupaten Majene":"Sulawesi Barat","Kabupaten Polewali Mandar":"Sulawesi Barat",
  "Kabupaten Mamasa":"Sulawesi Barat","Kabupaten Pasangkayu":"Sulawesi Barat","Kabupaten Mamuju Tengah":"Sulawesi Barat",
  // Sulawesi Tengah
  "Kota Palu":"Sulawesi Tengah","Kabupaten Banggai":"Sulawesi Tengah","Kabupaten Banggai Kepulauan":"Sulawesi Tengah",
  "Kabupaten Banggai Laut":"Sulawesi Tengah","Kabupaten Buol":"Sulawesi Tengah","Kabupaten Donggala":"Sulawesi Tengah",
  "Kabupaten Morowali":"Sulawesi Tengah","Kabupaten Morowali Utara":"Sulawesi Tengah",
  "Kabupaten Parigi Moutong":"Sulawesi Tengah","Kabupaten Poso":"Sulawesi Tengah","Kabupaten Sigi":"Sulawesi Tengah",
  "Kabupaten Tojo Una-Una":"Sulawesi Tengah","Kabupaten Tolitoli":"Sulawesi Tengah",
  // Sulawesi Utara
  "Kota Manado":"Sulawesi Utara","Kota Bitung":"Sulawesi Utara","Kota Tomohon":"Sulawesi Utara","Kota Kotamobagu":"Sulawesi Utara",
  "Kabupaten Bolaang Mongondow":"Sulawesi Utara","Kabupaten Bolaang Mongondow Selatan":"Sulawesi Utara",
  "Kabupaten Bolaang Mongondow Timur":"Sulawesi Utara","Kabupaten Bolaang Mongondow Utara":"Sulawesi Utara",
  "Kabupaten Kepulauan Sangihe":"Sulawesi Utara","Kabupaten Kepulauan Siau Tagulandang Biaro":"Sulawesi Utara",
  "Kabupaten Kepulauan Talaud":"Sulawesi Utara","Kabupaten Minahasa":"Sulawesi Utara",
  "Kabupaten Minahasa Selatan":"Sulawesi Utara","Kabupaten Minahasa Tenggara":"Sulawesi Utara","Kabupaten Minahasa Utara":"Sulawesi Utara",
  // Sulawesi Tenggara
  "Kota Kendari":"Sulawesi Tenggara","Kota Baubau":"Sulawesi Tenggara",
  "Kabupaten Bombana":"Sulawesi Tenggara","Kabupaten Buton":"Sulawesi Tenggara","Kabupaten Buton Selatan":"Sulawesi Tenggara",
  "Kabupaten Buton Tengah":"Sulawesi Tenggara","Kabupaten Buton Utara":"Sulawesi Tenggara",
  "Kabupaten Kolaka":"Sulawesi Tenggara","Kabupaten Kolaka Timur":"Sulawesi Tenggara","Kabupaten Kolaka Utara":"Sulawesi Tenggara",
  "Kabupaten Konawe":"Sulawesi Tenggara","Kabupaten Konawe Kepulauan":"Sulawesi Tenggara",
  "Kabupaten Konawe Selatan":"Sulawesi Tenggara","Kabupaten Konawe Utara":"Sulawesi Tenggara",
  "Kabupaten Muna":"Sulawesi Tenggara","Kabupaten Muna Barat":"Sulawesi Tenggara","Kabupaten Wakatobi":"Sulawesi Tenggara",
  // Gorontalo
  "Kota Gorontalo":"Gorontalo","Kabupaten Boalemo":"Gorontalo","Kabupaten Bone Bolango":"Gorontalo",
  "Kabupaten Gorontalo Utara":"Gorontalo","Kabupaten Pohuwato":"Gorontalo","Kabupaten Gorontalo":"Gorontalo"
};

const PROVINSI_LIST = [
  'Sulawesi Selatan', 'Sulawesi Barat', 'Sulawesi Tengah',
  'Sulawesi Utara', 'Sulawesi Tenggara', 'Gorontalo'
];

export default function TourismForm({ initialData = {}, mode = 'add' }) {
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    nama_wisata: initialData.nama_wisata || '',
    kategori: initialData.kategori || '',
    alamat: initialData.alamat || '',
    kabupaten: initialData.kabupaten || '',
    provinsi: initialData.provinsi || 'Sulawesi Selatan',
    rating: initialData.rating || '',
    jumlah_riview: initialData.jumlah_riview || '',
    harga: initialData.harga || '',
    kategori_harga: initialData.kategori_harga || '',
    lat: initialData.lat || initialData.lat_gmaps || '',
    long: initialData.long || initialData.lon_gmaps || '',
    url_image: initialData.url_image || '',
    deskripsi_wisata: initialData.deskripsi_wisata || '',

  });

  const [token, setToken] = useState('');
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [errorMsg, setErrorMsg] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => {
      const newData = { ...prev, [name]: value };
      
      // Jika provinsi berubah, reset kabupaten karena pilihan kabupaten akan berubah
      if (name === 'provinsi') {
        newData.kabupaten = '';
      }

      // Auto-kalkulasi kategori_harga jika harga diubah
      if (name === 'harga') {
        const h = Number(value);
        if (value === '') {
          newData.kategori_harga = '-';
        } else if (h === 0) {
          newData.kategori_harga = 'Gratis';
        } else if (h >= 1 && h <= 9999) {
          newData.kategori_harga = 'Murah';
        } else if (h >= 10000 && h <= 19999) {
          newData.kategori_harga = 'Sedang';
        } else if (h >= 20000) {
          newData.kategori_harga = 'Mahal';
        }
      }
      
      return newData;
    });
  };



  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setErrorMsg('');

    try {
      const url = mode === 'add' 
        ? '/api/tourism' 
        : `/api/tourism/${initialData.place_id}`;
      
      const method = mode === 'add' ? 'POST' : 'PUT';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error('Token akses tidak valid (Unauthorized)');
        }
        throw new Error('Gagal menyimpan data');
      }

      setStatus('success');
      setTimeout(() => {
        router.push('/');
        router.refresh();
      }, 1500);

    } catch (err) {
      setStatus('error');
      setErrorMsg(err.message);
    }
  };

  return (
    <div className="glass" style={{ maxWidth: '800px', margin: '0 auto', padding: '2rem', borderRadius: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '2rem', gap: '1rem' }}>
        <Link href="/" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '40px', height: '40px', borderRadius: '50%', background: 'rgba(255,255,255,0.1)', color: 'white', textDecoration: 'none' }}>
          <ArrowLeft size={20} />
        </Link>
        <h1 style={{ fontSize: '1.8rem', margin: 0 }}>
          {mode === 'add' ? 'Tambah Data Wisata Baru' : 'Edit Data Wisata'}
        </h1>
      </div>

      {status === 'success' && (
        <div style={{ padding: '1rem', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', borderRadius: '12px', marginBottom: '1.5rem', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          ✅ Berhasil menyimpan data! Mengalihkan ke halaman utama...
        </div>
      )}

      {status === 'error' && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', borderRadius: '12px', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <AlertCircle size={18} /> {errorMsg}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        
        {/* Token Input */}
        <div style={{ padding: '1.5rem', background: 'rgba(59, 130, 246, 0.1)', borderRadius: '16px', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
          <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', color: '#60a5fa' }}>
            Token Akses (Wajib)
          </label>
          <input 
            type="password" 
            value={token}
            onChange={(e) => setToken(e.target.value)}
            required
            placeholder="Masukkan token akses untuk menyimpan..."
            style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(0,0,0,0.3)', color: 'white', outline: 'none' }}
          />
        </div>

        {/* Form Fields Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
          
          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Nama Wisata</label>
            <input 
              name="nama_wisata" value={formData.nama_wisata} onChange={handleChange} required
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Kategori</label>
            <select 
              name="kategori" value={formData.kategori} onChange={handleChange} required
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: '#1e293b', color: 'white', appearance: 'auto' }}
            >
              <option value="" disabled>Pilih Kategori</option>
              {KATEGORI_LIST.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Provinsi</label>
            <select 
              name="provinsi" value={formData.provinsi} onChange={handleChange} required
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: '#1e293b', color: 'white', appearance: 'auto' }}
            >
              <option value="" disabled>Pilih Provinsi</option>
              {PROVINSI_LIST.map(prov => (
                <option key={prov} value={prov}>{prov}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Kabupaten / Kota</label>
            <select 
              name="kabupaten" value={formData.kabupaten} onChange={handleChange} required
              disabled={!formData.provinsi}
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: formData.provinsi ? '#1e293b' : 'rgba(255,255,255,0.05)', color: formData.provinsi ? 'white' : 'gray', appearance: 'auto' }}
            >
              <option value="" disabled>
                {!formData.provinsi ? 'Pilih Provinsi Terlebih Dahulu' : 'Pilih Kabupaten/Kota'}
              </option>
              {Object.entries(KAB_TO_PROVINSI)
                .filter(([_, prov]) => prov === formData.provinsi)
                .map(([kab, _]) => kab)
                .sort()
                .map(kab => (
                  <option key={kab} value={kab}>{kab}</option>
                ))
              }
            </select>
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Alamat Lengkap</label>
            <textarea 
              name="alamat" value={formData.alamat} onChange={handleChange} rows="2"
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white', resize: 'vertical' }}
            />
          </div>



          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Harga (Rp)</label>
            <input 
              type="number" name="harga" value={formData.harga} onChange={handleChange} min="0" placeholder="Kosongkan jika tidak ada"
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Kategori Harga (Otomatis)</label>
            <input 
              type="text" name="kategori_harga" value={formData.kategori_harga} readOnly
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)', background: 'rgba(0,0,0,0.2)', color: 'var(--accent-teal)', fontWeight: 'bold', outline: 'none', cursor: 'not-allowed' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Latitude</label>
            <input 
              name="lat" value={formData.lat} onChange={handleChange} placeholder="-5.12345"
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Longitude</label>
            <input 
              name="long" value={formData.long} onChange={handleChange} placeholder="119.12345"
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Rating (0-5)</label>
            <input 
              type="number" step="0.1" name="rating" value={formData.rating} onChange={handleChange}
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
            />
          </div>

          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Jumlah Ulasan</label>
            <input 
              type="number" name="jumlah_riview" value={formData.jumlah_riview} onChange={handleChange}
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
            />
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>URL Gambar</label>
            <input 
              name="url_image" value={formData.url_image} onChange={handleChange} placeholder="https://..."
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white' }}
            />
          </div>

          <div style={{ gridColumn: '1 / -1' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>Deskripsi Wisata</label>
            <textarea 
              name="deskripsi_wisata" value={formData.deskripsi_wisata} onChange={handleChange} rows="4"
              style={{ width: '100%', padding: '0.8rem', borderRadius: '8px', border: '1px solid var(--glass-border)', background: 'rgba(255,255,255,0.05)', color: 'white', resize: 'vertical' }}
            />
          </div>
        </div>

        <button 
          type="submit" 
          disabled={status === 'loading' || !token}
          style={{ 
            marginTop: '1rem', padding: '1rem', borderRadius: '12px', background: 'var(--accent-teal)', color: '#000',
            fontWeight: '700', fontSize: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem',
            border: 'none', cursor: (status === 'loading' || !token) ? 'not-allowed' : 'pointer',
            opacity: (status === 'loading' || !token) ? 0.7 : 1, transition: '0.2s'
          }}
        >
          {status === 'loading' ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
          {status === 'loading' ? 'Menyimpan...' : 'Simpan Data'}
        </button>

      </form>
    </div>
  );
}
