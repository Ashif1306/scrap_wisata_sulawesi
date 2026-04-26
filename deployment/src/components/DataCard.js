"use client";
import React from 'react';
import { MapPin, Star } from 'lucide-react';
import styles from './DataCard.module.css';

export default function DataCard({ data }) {
  // Parsing some properties if they exist
  const rating = data.rating ? Number(data.rating).toFixed(1) : 'N/A';
  const reviewCount = data.jumlah_review ? parseInt(data.jumlah_review).toLocaleString() : '0';
  
  return (
    <article className={`${styles.card} glass animate-fade-in`}>
      <div className={styles.imageContainer}>
        {data.kategori && (
          <span className={styles.categoryBadge}>{data.kategori}</span>
        )}
        <img 
          src={data.image || '/placeholder-image.jpg'} 
          alt={data.nama_wisata}
          className={styles.image}
          loading="lazy"
          onError={(e) => {
            e.target.onerror = null; 
            e.target.src="/placeholder-image.jpg";
          }}
        />
      </div>
      
      <div className={styles.content}>
        <h3 className={styles.title}>{data.nama_wisata}</h3>
        
        <div className={styles.location}>
          <MapPin size={16} className={styles.locationIcon} />
          <span title={data.alamat}>
            {data.alamat && data.alamat.length > 60 
              ? `${data.alamat.substring(0, 60)}...` 
              : data.alamat || 'Alamat tidak tersedia'}
          </span>
        </div>
        
        <div className={styles.footer}>
          <div className={styles.rating}>
            <Star size={18} fill="currentColor" />
            <span>{rating}</span>
            <span className={styles.reviews}>({reviewCount})</span>
          </div>
          
          <div className={styles.meta}>
            <span className={styles.region}>{data.kabupaten || ''}</span>
          </div>
        </div>
      </div>
    </article>
  );
}
