#!/usr/bin/env node
/**
 * Image Compression Script for FarmLens
 * Converts large PNG hero images to optimized WebP format
 * Reduces 7-8MB images to ~500KB (90%+ size reduction)
 */

import sharp from 'sharp';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PUBLIC_DIR = path.join(__dirname, 'public');
const HERO_IMAGES = [
  'bengali-hero.png',
  'englsih-hero.png',
  'gujarati-hero.png',
  'hindi-hero.png',
  'kannada-hero.png',
  'malayalam-hero.png',
  'marathi-hero.png',
  'odia-hero.png',
  'punjabi-hero.png',
  'tamil-hero.png',
  'telugu-hero.png',
  'main.png'
];

async function compressImage(filename) {
  const inputPath = path.join(PUBLIC_DIR, filename);
  const outputFilename = filename.replace('.png', '.webp');
  const outputPath = path.join(PUBLIC_DIR, outputFilename);
  
  // Check if input file exists
  if (!fs.existsSync(inputPath)) {
    console.log(`⚠️  Skipping ${filename} - file not found`);
    return;
  }
  
  console.log(`🔄 Compressing ${filename}...`);
  
  try {
    const inputStats = fs.statSync(inputPath);
    const inputSizeMB = (inputStats.size / (1024 * 1024)).toFixed(2);
    
    // Compress to WebP with high quality
    await sharp(inputPath)
      .webp({ quality: 85, effort: 6 })
      .toFile(outputPath);
    
    const outputStats = fs.statSync(outputPath);
    const outputSizeMB = (outputStats.size / (1024 * 1024)).toFixed(2);
    const reduction = (((inputStats.size - outputStats.size) / inputStats.size) * 100).toFixed(1);
    
    console.log(`✅ ${filename} → ${outputFilename}`);
    console.log(`   Size: ${inputSizeMB}MB → ${outputSizeMB}MB (${reduction}% reduction)\n`);
  } catch (error) {
    console.error(`❌ Error compressing ${filename}:`, error.message);
  }
}

async function main() {
  console.log('🖼️  FarmLens Image Compression Tool\n');
  console.log('📁 Compressing hero images in public/ directory...\n');
  
  for (const image of HERO_IMAGES) {
    await compressImage(image);
  }
  
  console.log('✨ Compression complete!\n');
  console.log('📝 Next steps:');
  console.log('1. Update HeroSection.tsx to use .webp extensions');
  console.log('2. Add fallback support with <picture> element');
  console.log('3. Test in different browsers (WebP support is 96%+)');
  console.log('\nExample usage:');
  console.log('<picture>');
  console.log('  <source srcSet="/hero.webp" type="image/webp" />');
  console.log('  <img src="/hero.png" alt="Hero" />');
  console.log('</picture>');
}

main().catch(console.error);
