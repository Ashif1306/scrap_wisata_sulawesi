import React from 'react';
import TourismForm from '@/components/TourismForm';

export default function AddTourismPage() {
  return (
    <main style={{ padding: '4rem 1rem' }}>
      <TourismForm mode="add" />
    </main>
  );
}
