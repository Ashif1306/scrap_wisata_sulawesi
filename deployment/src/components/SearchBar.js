"use client";

import { useRouter, usePathname, useSearchParams } from 'next/navigation';
import { Search } from 'lucide-react';
import { useState, useRef } from 'react';

export default function SearchBar({ initialQuery }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [query, setQuery] = useState(initialQuery);
  const [isFocused, setIsFocused] = useState(false);
  const debounceRef = useRef(null);

  const handleSearch = (value) => {
    setQuery(value);

    // Hapus timer sebelumnya jika pengguna masih mengetik
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Set timer baru (jeda 400ms sebelum me-reload halaman)
    debounceRef.current = setTimeout(() => {
      const params = new URLSearchParams(searchParams);
      if (value) {
        params.set('q', value);
      } else {
        params.delete('q');
      }
      params.set('page', '1'); // Reset ke halaman 1 saat mencari kata baru
      
      router.replace(`${pathname}?${params.toString()}`);
    }, 400); 
  };

  return (
    <div 
      style={{ 
        background: isFocused ? 'rgba(30, 41, 59, 0.8)' : 'var(--bg-dark)', 
        padding: '0.85rem 1.7rem', 
        borderRadius: '30px', 
        display: 'flex', 
        alignItems: 'center', 
        border: isFocused ? '1px solid var(--accent-teal)' : '1px solid var(--glass-border)', 
        boxShadow: isFocused ? '0 0 20px rgba(20, 184, 166, 0.2)' : 'none',
        width: '100%',
        margin: '0 auto',
        transition: 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)',
        transform: isFocused ? 'scale(1.03)' : 'scale(1)'
      }}
    >
      <Search 
        size={22} 
        color={isFocused ? "var(--accent-teal)" : "var(--text-secondary)"} 
        style={{ marginRight: '12px', transition: 'all 0.3s ease' }} 
      />
      <input 
        type="text" 
        value={query}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        onChange={(e) => handleSearch(e.target.value)}
        placeholder="Cari berdasarkan nama wisata atau letak wilayah..." 
        style={{ 
          background: 'transparent', border: 'none', color: 'white', 
          width: '100%', outline: 'none', fontFamily: 'inherit',
          fontSize: '1rem'
        }}
      />
    </div>
  );
}
