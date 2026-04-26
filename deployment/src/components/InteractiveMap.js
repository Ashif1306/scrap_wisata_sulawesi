'use client';

import React, { useState, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-defaulticon-compatibility/dist/leaflet-defaulticon-compatibility.css';
import 'leaflet-defaulticon-compatibility';
import { MapPin, Search } from 'lucide-react';

export default function InteractiveMap({ data }) {
  const [selectedProvinsi, setSelectedProvinsi] = useState('Semua');
  const [selectedKabupaten, setSelectedKabupaten] = useState('Semua');
  const [selectedKategori, setSelectedKategori] = useState('Semua');
  const [searchQuery, setSearchQuery] = useState('');

  // Extract unique values for filters
  const provinces = useMemo(() => {
    const provs = new Set(data.map(d => d.provinsi).filter(Boolean));
    return ['Semua', ...Array.from(provs).sort()];
  }, [data]);

  const regencies = useMemo(() => {
    let filtered = data;
    if (selectedProvinsi !== 'Semua') {
      filtered = data.filter(d => d.provinsi === selectedProvinsi);
    }
    const kabs = new Set(filtered.map(d => d.kabupaten).filter(Boolean));
    return ['Semua', ...Array.from(kabs).sort()];
  }, [data, selectedProvinsi]);

  const categories = useMemo(() => {
    const cats = new Set(data.map(d => d.kategori).filter(Boolean));
    return ['Semua', ...Array.from(cats).sort()];
  }, [data]);

  // Filter data based on selections
  const filteredData = useMemo(() => {
    return data.filter(d => {
      const matchProvinsi = selectedProvinsi === 'Semua' || d.provinsi === selectedProvinsi;
      const matchKabupaten = selectedKabupaten === 'Semua' || d.kabupaten === selectedKabupaten;
      const matchKategori = selectedKategori === 'Semua' || d.kategori === selectedKategori;
      const matchSearch = !searchQuery || 
        (d.nama_wisata && d.nama_wisata.toLowerCase().includes(searchQuery.toLowerCase()));
      
      // Ensure it has valid coordinates
      const hasCoords = d.lat && d.long && !isNaN(d.lat) && !isNaN(d.long);
      
      return matchProvinsi && matchKabupaten && matchKategori && matchSearch && hasCoords;
    });
  }, [data, selectedProvinsi, selectedKabupaten, selectedKategori, searchQuery]);

  // Default center point (Sulawesi)
  const defaultCenter = [-2.0, 121.0];
  const defaultZoom = 6;

  // Render a simple rating display
  const renderRating = (rating) => {
    if (!rating || rating === '-') return 'Belum ada rating';
    return `⭐ ${rating}`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Filters Bar */}
      <div style={{ 
        padding: '1rem', 
        background: 'rgba(30, 41, 59, 0.7)', 
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid var(--glass-border)',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        alignItems: 'center',
        zIndex: 1000,
        position: 'relative'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', flex: '1', minWidth: '200px' }}>
          <Search size={18} color="var(--text-secondary)" />
          <input 
            type="text" 
            placeholder="Cari wisata..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              background: 'rgba(15, 23, 42, 0.5)',
              border: '1px solid var(--glass-border)',
              padding: '0.5rem 1rem',
              borderRadius: '8px',
              color: 'white',
              width: '100%',
              outline: 'none'
            }}
          />
        </div>
        
        <select 
          value={selectedProvinsi} 
          onChange={(e) => {
            setSelectedProvinsi(e.target.value);
            setSelectedKabupaten('Semua'); // reset regency when province changes
          }}
          style={{ padding: '0.5rem 1rem', background: '#0f172a', color: 'white', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
        >
          {provinces.map(p => <option key={p} value={p}>{p === 'Semua' ? 'Semua Provinsi' : p}</option>)}
        </select>

        <select 
          value={selectedKabupaten} 
          onChange={(e) => setSelectedKabupaten(e.target.value)}
          style={{ padding: '0.5rem 1rem', background: '#0f172a', color: 'white', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
        >
          {regencies.map(k => <option key={k} value={k}>{k === 'Semua' ? 'Semua Kabupaten' : k}</option>)}
        </select>

        <select 
          value={selectedKategori} 
          onChange={(e) => setSelectedKategori(e.target.value)}
          style={{ padding: '0.5rem 1rem', background: '#0f172a', color: 'white', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
        >
          {categories.map(c => <option key={c} value={c}>{c === 'Semua' ? 'Semua Kategori' : c}</option>)}
        </select>
        
        <div style={{ fontSize: '0.85rem', color: 'var(--accent-teal)', fontWeight: '600' }}>
          {filteredData.length} Destinasi
        </div>
      </div>

      {/* Map Container */}
      <div style={{ flex: 1, position: 'relative' }}>
        <MapContainer 
          center={defaultCenter} 
          zoom={defaultZoom} 
          style={{ height: '100%', width: '100%', background: '#0f172a' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
          
          {filteredData.map((dest, idx) => (
            <Marker 
              key={dest.place_id || idx} 
              position={[parseFloat(dest.lat), parseFloat(dest.long)]}
            >
              <Popup>
                <div style={{ padding: '0.5rem', minWidth: '200px', color: '#1e293b' }}>
                  <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.1rem', borderBottom: '1px solid #e2e8f0', paddingBottom: '0.5rem' }}>
                    {dest.nama_wisata}
                  </h3>
                  <div style={{ fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                    <span style={{ display: 'inline-block', background: '#e0f2fe', color: '#0369a1', padding: '0.2rem 0.5rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>
                      {dest.kategori}
                    </span>
                  </div>
                  <p style={{ margin: '0 0 0.5rem', fontSize: '0.85rem' }}>
                    📍 {dest.kabupaten}, {dest.provinsi}
                  </p>
                  <p style={{ margin: '0', fontSize: '0.85rem' }}>
                    {renderRating(dest.rating)} ({dest.jumlah_riview || 0} ulasan)
                  </p>
                  {dest.harga > 0 && (
                    <p style={{ margin: '0.5rem 0 0', fontSize: '0.85rem', fontWeight: '600' }}>
                      💰 Rp {dest.harga.toLocaleString('id-ID')}
                    </p>
                  )}
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
