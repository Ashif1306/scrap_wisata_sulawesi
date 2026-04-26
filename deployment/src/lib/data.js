import fs from 'fs';
import path from 'path';
import Papa from 'papaparse';

export function getTourismData() {
  try {
    // Relative to the Next.js project root, we need to go up to hasil_final
    // process.cwd() is usually the 'deployment' folder during dev/build
    const csvFilePath = path.join(process.cwd(), '..', 'hasil_final', 'wisata_sulawesi_lengkap.csv');
    
    if (!fs.existsSync(csvFilePath)) {
      console.error(`CSV file not found at: ${csvFilePath}`);
      return [];
    }
    
    const fileContent = fs.readFileSync(csvFilePath, 'utf8');
    
    const results = Papa.parse(fileContent, {
      header: true,
      skipEmptyLines: true,
      dynamicTyping: true, // converts numbers
    });
    
    if (results.errors && results.errors.length > 0) {
      console.warn("CSV parsing warnings/errors:", results.errors);
    }
    
    return results.data || [];
  } catch (error) {
    console.error("Error reading tourism data:", error);
    return [];
  }
}

export function writeTourismData(dataArray) {
  try {
    const csvFilePath = path.join(process.cwd(), '..', 'hasil_final', 'wisata_sulawesi_lengkap.csv');
    const csvString = Papa.unparse(dataArray);
    fs.writeFileSync(csvFilePath, csvString, 'utf8');
    return true;
  } catch (error) {
    console.error("Error writing tourism data:", error);
    return false;
  }
}

export function addTourismData(newItem) {
  const data = getTourismData();
  // Ensure we have a place_id
  if (!newItem.place_id) {
    newItem.place_id = `MANUAL-${Date.now()}`;
  }
  data.push(newItem);
  return writeTourismData(data);
}

export function updateTourismData(id, updatedItem) {
  const data = getTourismData();
  const index = data.findIndex(item => item.place_id === id);
  
  if (index !== -1) {
    // Keep existing data, overwrite with updated fields
    data[index] = { ...data[index], ...updatedItem, place_id: id };
    return writeTourismData(data);
  }
  return false;
}
