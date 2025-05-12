from instagram_scripts.abstracts import InstagramContentAbstract
from gologin import GoLogin
from pathlib import Path
from playwright.async_api import async_playwright
from .logger import instagram_logging
import subprocess

class InstagramContent(InstagramContentAbstract):
    _instance = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        instagram_logging.info("Создан класс InstagramContent")
        if cls._instance is None:
            cls._instance = super(InstagramContent, cls).__new__(cls)
        return cls._instance

    def __init__(self, API_KEY: str, MEDIA_PATH: Path) -> None:
        if not self._initialized:
            self.API_KEY: str = API_KEY
            self.URL: str = "https://www.instagram.com/"
            self.MEDIA_PATH: Path = MEDIA_PATH / "instagram_media"
            self._initialized: bool = True


    def __str__(self) -> str:
        return f"Класс InstagramContent | API_KET = {self.API_KEY} | Инициализирован: {self._initialized}"

    def __repr__(self) -> str:
        return f"InstagramContent(API_KEY={self.API_KEY}, _initialized={self._initialized})"



    async def download_video(self, video_name: str, profile_id: str, descript: str):
        async with async_playwright() as pl:
            gl = GoLogin({f"token": self.API_KEY,
                          "profile_id": profile_id,
                          "executablePath": "chromium",
                          "browserType": "chrome",
                          "local": True,
                          "auto_update_browser": False,
                          })
            debug_address = gl.start()
            file_path = self.MEDIA_PATH / video_name
            browser = await pl.chromium.connect_over_cdp(f"http://{debug_address}")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            await page.goto(self.URL, timeout=10000)
            await page.click('div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.xixxii4.x13vifvy.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1.x1dr59a3.xeq5yr9.x1n327nk > div > div > div > div > div.x1iyjqo2.xh8yej3 > div:nth-child(7) > div', timeout=6000)
            await page.wait_for_selector("div.x9f619.x13lgxp2.x5pf9jr.x1n2onr6.x1plvlek button._acan._acap._acas", timeout=8000, state="visible")
            await page.click("div.x9f619.x13lgxp2.x5pf9jr.x1n2onr6.x1plvlek button._acan._acap._acas", timeout=8000)
            try:
                upload_script = subprocess.run(["node",
                                "upload.js",
                                debug_address,
                                "div.x9f619.x13lgxp2.x5pf9jr.x1n2onr6.x1plvlek button._acan._acap._acas",
                                str(file_path)
                                ],
                               capture_output=True,
                               text=True,
                               check=True
                               )
            except subprocess.CalledProcessError as e:
                print("STDOUT:", e.stdout)
                print("STDERR:", e.stderr)
            await page.wait_for_selector("div.x9f619.x13lgxp2.x5pf9jr.x1n2onr6.x1plvlek div.x1i10hfl.xjqpnuy.xa49m3k.xqeqjp1", timeout=12000)
            await page.click("div.x9f619.x13lgxp2.x5pf9jr.x1n2onr6.x1plvlek div.x1i10hfl.xjqpnuy.xa49m3k.xqeqjp1", timeout=12000)
            await page.wait_for_selector("div.x9f619.x13lgxp2.x5pf9jr.x1n2onr6.x1plvlek div.x1i10hfl.xjqpnuy.xa49m3k.xqeqjp1", timeout=12000)
            await page.click("div.x9f619.x13lgxp2.x5pf9jr.x1n2onr6.x1plvlek div.x1i10hfl.xjqpnuy.xa49m3k.xqeqjp1", timeout=12000)
            await page.wait_for_selector('div[data-lexical-editor="true"]', timeout=12000)
            await page.fill('div[data-lexical-editor="true"]', descript, timeout=6000)
            await page.click("div.x9f619.x13lgxp2.x5pf9jr.x1n2onr6.x1plvlek div.x1i10hfl.xjqpnuy.xa49m3k.xqeqjp1", timeout=15000)



