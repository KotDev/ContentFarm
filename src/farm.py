import abc
import asyncio
from abc import ABC
from gologin import GoLogin
from playwright.async_api import async_playwright

from instagram_scripts.content import InstagramContent
from aiohttp import ClientSession


class FarmAbstract(ABC):
    @abc.abstractmethod
    async def get_profiles(self, page):
        pass


class FarmContents(FarmAbstract):
    def __init__(self, API_KEY: str):
        self.API_KEY = API_KEY

        self.instagram = InstagramContent(self.API_KEY)
        self.gl = GoLogin({"token": API_KEY})

    async def get_profiles(self, page: int = 1) -> None:
        """
        Метод получения всех профилей gologin
        :param page: страница, первые 30 профилей
        :return: None
        """
        async with ClientSession() as session:
            async with session.get(
                "https://api.gologin.com/browser/v2",
                headers={
                    "Authorization": f"Bearer {self.API_KEY}",
                    "Content-Type": "application/json",
                },
                params={"page": page},
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None

    async def open_browser_profile(self, profile_id: str):
        """
        Метод открытия браузера профиля gologin
        :param profile_id: id профиля gologin
        :return: None
        """
        gl = GoLogin(
            {
                f"token": self.API_KEY,
                "profile_id": profile_id,
                "executablePath": "chromium",
                "browserType": "chrome",
                "auto_update_browser": False,
                "launcherProperties": {
                    "headless": False,
                    "args": ["--start-maximized"],
                },
            }
        )
        debug_address = gl.start()
        async with async_playwright() as pl:
            browser = await pl.chromium.connect_over_cdp(f"http://{debug_address}")
            try:
                while browser.is_connected():
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                pass
            finally:
                await browser.close()
                gl.stop()
