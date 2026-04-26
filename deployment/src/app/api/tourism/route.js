import { NextResponse } from 'next/server';
import { addTourismData } from '@/lib/data';

export async function POST(request) {
  try {
    const authHeader = request.headers.get('authorization');
    
    if (authHeader !== 'Bearer asifganteng') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    
    // Add default values for fields if they are missing
    const newItem = {
      ...body,
      status_scrape: 'MANUAL_ENTRY'
    };
    
    const success = addTourismData(newItem);
    
    if (success) {
      return NextResponse.json({ message: 'Data added successfully', data: newItem });
    } else {
      return NextResponse.json({ error: 'Failed to write data' }, { status: 500 });
    }
  } catch (error) {
    console.error('API Error (POST /api/tourism):', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
