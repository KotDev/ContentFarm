const puppeteer = require('puppeteer-core');

const wsUrl = process.argv[2];
const fileSelector = process.argv[3];
const videoPath = process.argv[4];

(async () => {
  try {
    const browser = await puppeteer.connect({
      browserWSEndpoint: wsUrl,
    });

    const [page] = await browser.pages();

    const input = await page.$(fileSelector);
    if (!input) {
      console.error("❌ input[type='file'] not found");
      process.exit(1);
    }

    await input.uploadFile(videoPath);
    console.log("✅ Видео загружено через Puppeteer");

  } catch (error) {
    console.error("❌ Ошибка при работе с Puppeteer:", error.message);
    process.exit(1);
  }
})();