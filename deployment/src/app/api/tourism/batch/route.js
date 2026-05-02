import { NextResponse } from 'next/server';
import { bulkUpdateTourismData } from '@/lib/data';
import { calculateLabel } from '@/lib/labelRekomendasi';

export async function PUT(request) {
  try {
    const authHeader = request.headers.get('authorization');
    
    if (authHeader !== 'Bearer asifganteng') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { items } = body;

    if (!Array.isArray(items) || items.length === 0) {
      return NextResponse.json({ error: 'Items array is required and must not be empty' }, { status: 400 });
    }

    // Hitung ulang label_rekomendasi untuk setiap item
    const processedItems = [];
    for (const item of items) {
      const { place_id, ...fields } = item;
      const label = await calculateLabel(fields);
      processedItems.push({
        place_id,
        ...fields,
        label_rekomendasi: label
      });
    }

    const result = await bulkUpdateTourismData(processedItems);

    return NextResponse.json({
      message: `Batch update completed: ${result.successCount} berhasil, ${result.failCount} gagal`,
      ...result
    });
  } catch (error) {
    console.error('API Error (PUT /api/tourism/batch):', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
