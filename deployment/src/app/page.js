import React from 'react';
import { getTourismData } from '@/lib/data';
import { Map } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import DataTable from '@/components/DataTable';
import Link from 'next/link';

export const revalidate = 0; 

export default async function Home({ searchParams }) {
  const params = await searchParams;
  const page = parseInt(params.page || '1', 10);
  const query = params.q || '';
  const limit = 20;
  const start = (page - 1) * limit;
  const end = start + limit - 1;

  let data = [];
  let count = 0;
  let error = null;

  try {
    const allData = getTourismData();
    let filteredData = allData;
    
    if (query) {
      const qLower = query.toLowerCase();
      filteredData = allData.filter(item => 
        (item.nama_wisata && item.nama_wisata.toLowerCase().includes(qLower)) ||
        (item.kabupaten && item.kabupaten.toLowerCase().includes(qLower))
      );
    }
    
    // Sort by jumlah_riview descending
    filteredData.sort((a, b) => (b.jumlah_riview || 0) - (a.jumlah_riview || 0));

    count = filteredData.length;
    data = filteredData.slice(start, end + 1);
  } catch (err) {
    error = err;
    console.error(err);
  }

  const totalPages = Math.ceil(count / limit);

  return (
    <main>
      <header className="glass" style={{ margin: '0 auto 2rem', maxWidth: '850px', padding: '2.5rem 2rem', borderTop: 'none', borderRadius: '0 0 32px 32px', textAlign: 'center', position: 'relative', zIndex: 10 }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.8rem', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.2)', padding: '0.4rem 1rem', borderRadius: '30px', marginBottom: '1.2rem', color: '#60a5fa', fontWeight: '600', fontSize: '0.85rem' }}>
          <span style={{ display: 'inline-block', width: '8px', height: '8px', borderRadius: '50%', background: '#60a5fa', boxShadow: '0 0 10px #60a5fa' }}></span>
          Kelompok 8
        </div>
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '1rem' }}>
          <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(20, 184, 166, 0.1)', padding: '0.8rem', borderRadius: '50%', boxShadow: '0 0 30px rgba(20, 184, 166, 0.2)' }}>
            <Map size={40} color="var(--accent-teal)" />
          </div>
        </div>
        <h1 style={{ fontSize: '2.2rem', marginBottom: '0.5rem' }}>Sulawesi Tourism Intelligence</h1>
        <p style={{ fontSize: '0.95rem', margin: '0 auto', maxWidth: '600px' }}>Penerapan Algoritma K-Nearest Neighbors (KNN) untuk Rekomendasi Destinasi Wisata di Pulau Sulawesi.</p>
        
        <div style={{ marginTop: '1.5rem', display: 'flex', justifyContent: 'center' }}>
          <div style={{ width: '100%', maxWidth: '500px' }}>
            <SearchBar initialQuery={query} />
          </div>
        </div>
      </header>

      <section className="container">
        {error ? (
          <div style={{ textAlign: 'center', color: '#ef4444', padding: '3rem', background: 'rgba(239, 68, 68, 0.1)', borderRadius: '16px' }}>
            <h2>Failed to load data</h2>
            <p style={{ marginTop: '1rem' }}>Please make sure the CSV file is available.</p>
            <p style={{ fontSize: '0.85rem', marginTop: '1rem', opacity: 0.8 }}>Details: {error.message || 'Unknown error'}</p>
          </div>
        ) : (
          <>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
              <h2 style={{ fontSize: '1.4rem', color: 'var(--text-secondary)' }}>
                Exploring <span style={{ color: 'var(--accent-teal)' }}>{count}</span> Destinations
              </h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <Link href="/add" style={{ padding: '0.6rem 1.2rem', background: 'var(--accent-blue)', color: 'white', textDecoration: 'none', borderRadius: '8px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem', boxShadow: '0 4px 14px rgba(59, 130, 246, 0.3)' }}>
                  <span style={{ fontSize: '18px', lineHeight: 1 }}>+</span> Tambah Data
                </Link>
                <Link href="/map" style={{ padding: '0.6rem 1.2rem', background: 'var(--accent-teal)', color: '#000', textDecoration: 'none', borderRadius: '8px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '0.5rem', boxShadow: '0 4px 14px rgba(20, 184, 166, 0.3)' }}>
                  <Map size={18} /> Peta Interaktif
                </Link>
                <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                  Page {page} of {totalPages || 1}
                </div>
              </div>
            </div>

            <DataTable data={data} start={start} />

            {count > 0 && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '2rem' }}>
                {page > 1 && (
                  <Link href={`/?${query ? `q=${query}&` : ''}page=${page - 1}`} scroll={true} style={{ padding: '0.75rem 1.5rem', background: 'var(--glass-border)', color: 'white', textDecoration: 'none', borderRadius: '30px', fontWeight: '500', transition: 'all 0.3s ease' }}>
                    &larr; Sebelumnya
                  </Link>
                )}
                
                {page < totalPages && (
                  <Link href={`/?${query ? `q=${query}&` : ''}page=${page + 1}`} scroll={true} style={{ padding: '0.75rem 1.5rem', background: 'var(--accent-blue)', color: 'white', textDecoration: 'none', borderRadius: '30px', fontWeight: '500', transition: 'all 0.3s ease', boxShadow: '0 4px 14px rgba(59, 130, 246, 0.3)' }}>
                    Selanjutnya &rarr;
                  </Link>
                )}
              </div>
            )}
            
            {data.length === 0 && count === 0 && !error && (
              <div className="glass" style={{ textAlign: 'center', padding: '4rem' }}>
                <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📭</div>
                <h3>No Data Available</h3>
                <p style={{ marginTop: '0.5rem', color: 'var(--text-secondary)' }}>Tidak ada data wisata yang ditemukan.</p>
              </div>
            )}
          </>
        )}
      </section>
      
      <footer style={{ textAlign: 'center', padding: '2rem', borderTop: '1px solid var(--glass-border)', marginTop: '4rem', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
        <p>&copy; {new Date().getFullYear()} Dibuat dengan ❤️ oleh <strong>Kelompok 8</strong>.</p>
        <p style={{ marginTop: '0.5rem', opacity: 0.6 }}>Sulawesi Tourism Intelligence - Data Analytics & K-Nearest Neighbors</p>
      </footer>
    </main>
  );
}
