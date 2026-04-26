import { supabase } from './supabase';

const TABLE_NAME = 'tourism_data';

export async function getTourismData() {
  try {
    let allData = [];
    let fetchMore = true;
    let from = 0;
    const step = 1000;

    while (fetchMore) {
      const { data, error } = await supabase
        .from(TABLE_NAME)
        .select('*')
        .range(from, from + step - 1);
        
      if (error) {
        console.error("Supabase fetch error:", error);
        break;
      }
      
      if (data && data.length > 0) {
        allData = [...allData, ...data];
        from += step;
      }
      
      // If we got fewer records than requested, it means we reached the end
      if (!data || data.length < step) {
        fetchMore = false;
      }
    }
    
    return allData;
  } catch (error) {
    console.error("Error fetching tourism data from Supabase:", error);
    return [];
  }
}

export async function addTourismData(newItem) {
  try {
    // Ensure we have a place_id
    if (!newItem.place_id) {
      newItem.place_id = `MANUAL-${Date.now()}`;
    }
    
    const { error } = await supabase
      .from(TABLE_NAME)
      .insert([newItem]);
      
    if (error) {
      console.error("Supabase insert error:", error);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error("Error adding tourism data to Supabase:", error);
    return false;
  }
}

export async function updateTourismData(id, updatedItem) {
  try {
    const { error } = await supabase
      .from(TABLE_NAME)
      .update(updatedItem)
      .eq('place_id', id);
      
    if (error) {
      console.error("Supabase update error:", error);
      return false;
    }
    
    return true;
  } catch (error) {
    console.error("Error updating tourism data in Supabase:", error);
    return false;
  }
}
