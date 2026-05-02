import React from 'react';
import BulkEditTable from '@/components/BulkEditTable';
import { getTourismData } from '@/lib/data';

export const revalidate = 0;

export default async function BulkEditPage() {
  const allData = await getTourismData();
  
  // Sort by nama_wisata ascending for easier browsing
  allData.sort((a, b) => (a.nama_wisata || '').localeCompare(b.nama_wisata || ''));

  return (
    <main style={{ padding: '3rem 1rem' }}>
      <BulkEditTable initialData={allData} />
    </main>
  );
}
