import React from 'react';
import { getTourismData } from '@/lib/data';
import MapWrapper from '@/components/MapWrapper';
import Link from 'next/link';
import { ArrowLeft } from 'lucide-react';

export const metadata = {
  title: 'Peta Interaktif - Sulawesi Tourism',
  description: 'Eksplorasi destinasi wisata Sulawesi melalui peta interaktif',
};

export default function MapPage() {
  const data = getTourismData();

  return (
    <main style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header style={{ 
        padding: '1rem 2rem', 
        background: 'var(--bg-primary)', 
        borderBottom: '1px solid var(--glass-border)',
        display: 'flex',
        alignItems: 'center',
        gap: '2rem'
      }}>
        <Link href="/" style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '0.5rem', 
          color: 'var(--text-secondary)',
          textDecoration: 'none',
          fontWeight: '500'
        }}>
          <ArrowLeft size={18} /> Kembali
        </Link>
        <h1 style={{ fontSize: '1.2rem', margin: 0 }}>Peta Wisata Sulawesi</h1>
      </header>
      
      <div style={{ flex: 1, position: 'relative' }}>
        <MapWrapper data={data} />
      </div>
    </main>
  );
}
