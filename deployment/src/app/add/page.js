import React from 'react';
import TourismForm from '@/components/TourismForm';
import Link from 'next/link';
import { Edit } from 'lucide-react';

export default function AddTourismPage() {
  return (
    <main style={{ padding: '4rem 1rem' }}>
      <TourismForm mode="add" />

      {/* Tombol Bulk Edit */}
      <div style={{ maxWidth: '800px', margin: '1.5rem auto 0', textAlign: 'center' }}>
        <Link
          href="/bulk-edit"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.6rem',
            padding: '0.9rem 1.8rem',
            background: 'rgba(251, 191, 36, 0.1)',
            color: '#fbbf24',
            textDecoration: 'none',
            borderRadius: '14px',
            fontWeight: '700',
            fontSize: '0.95rem',
            border: '1px solid rgba(251, 191, 36, 0.25)',
            transition: 'all 0.2s ease',
            boxShadow: '0 4px 14px rgba(251, 191, 36, 0.1)',
          }}
        >
          <Edit size={18} />
          Edit Banyak Data Sekaligus
        </Link>
      </div>
    </main>
  );
}
