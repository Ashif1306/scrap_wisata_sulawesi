import React from 'react';
import TourismForm from '@/components/TourismForm';
import { getTourismData } from '@/lib/data';
import { redirect } from 'next/navigation';

export default async function EditTourismPage({ params }) {
  const { id } = await params;
  
  // Fetch existing data
  const allData = getTourismData();
  const dataToEdit = allData.find(item => item.place_id === id);

  if (!dataToEdit) {
    redirect('/'); // If not found, redirect to home
  }

  return (
    <main style={{ padding: '4rem 1rem' }}>
      <TourismForm mode="edit" initialData={dataToEdit} />
    </main>
  );
}
