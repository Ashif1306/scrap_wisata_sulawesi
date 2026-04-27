import { NextResponse } from 'next/server';
import { updateTourismData, getTourismData, deleteTourismData } from '@/lib/data';

export async function PUT(request, { params }) {
  try {
    const authHeader = request.headers.get('authorization');
    
    if (authHeader !== 'Bearer asifganteng') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const { id } = await params;
    const body = await request.json();
    
    // Attempt update
    const success = await updateTourismData(id, body);
    
    if (success) {
      return NextResponse.json({ message: 'Data updated successfully', id });
    } else {
      return NextResponse.json({ error: 'Data not found or failed to write' }, { status: 404 });
    }
  } catch (error) {
    console.error(`API Error (PUT /api/tourism/${params?.id}):`, error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function GET(request, { params }) {
  try {
    const { id } = await params;
    const allData = await getTourismData();
    const item = allData.find(d => d.place_id === id);
    
    if (item) {
      return NextResponse.json(item);
    } else {
      return NextResponse.json({ error: 'Not found' }, { status: 404 });
    }
  } catch (error) {
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function DELETE(request, { params }) {
  try {
    const authHeader = request.headers.get('authorization');
    
    if (authHeader !== 'Bearer hapus') {
      return NextResponse.json({ error: 'Unauthorized token for deletion' }, { status: 401 });
    }

    const { id } = await params;
    
    // Attempt delete
    const success = await deleteTourismData(id);
    
    if (success) {
      return NextResponse.json({ message: 'Data deleted successfully', id });
    } else {
      return NextResponse.json({ error: 'Data not found or failed to delete' }, { status: 404 });
    }
  } catch (error) {
    console.error(`API Error (DELETE /api/tourism/${params?.id}):`, error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
