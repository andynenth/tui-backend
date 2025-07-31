#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function quickTest() {
  const browser = await puppeteer.launch({ headless: false, slowMo: 500 });
  const page = await browser.newPage();
  
  console.log('📍 Loading page...');
  await page.goto('http://localhost:5050');
  
  console.log('📍 Taking screenshot...');
  await page.screenshot({ path: 'debug_home.png', fullPage: true });
  
  console.log('📍 Entering name...');
  await page.type('input[placeholder*="name"]', 'TestPlayer');
  await page.screenshot({ path: 'debug_name_entered.png', fullPage: true });
  
  console.log('📍 Clicking enter lobby...');
  const enterButton = await page.waitForSelector('button[type="submit"]');
  await enterButton.click();
  
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'debug_after_lobby.png', fullPage: true });
  
  console.log('✅ Screenshots saved. Check debug_*.png files');
  console.log('Current URL:', page.url());
  
  // Keep open for manual inspection
  console.log('Browser staying open for inspection...');
  await page.waitForTimeout(60000);
  
  await browser.close();
}

quickTest().catch(console.error);