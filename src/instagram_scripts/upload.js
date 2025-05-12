const puppeteer = require('puppeteer-core');

const debug_url = process.argv[2];
const file_selector = process.argv[3];
const video_path = process.argv[4];

(async () => {
  const browser = await puppeteer.connect({ browserWSEndpoint: wsUrl });
  const [page] = await browser.pages();

  const input = await page.$(fileSelector);
  if (!input) {
    console.error("❌ input[type='file'] not found");
    process.exit(1);
  }

  await input.uploadFile(videoPath);
  console.log("✅ Видео загружено через Puppeteer");
})();
