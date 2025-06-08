import time

import requests

from instagram_scripts.abstracts import InstagramContentAbstract
from gologin import GoLogin
from playwright.async_api import async_playwright
from .logger import instagram_logging
import subprocess
import os
import sys


class InstagramContent(InstagramContentAbstract):
    _instance = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs):
        """
        Метод для сощдания singleton класса
        :param args:
        :param kwargs:
        """
        instagram_logging.info("Создан класс InstagramContent")
        if cls._instance is None:
            cls._instance = super(InstagramContent, cls).__new__(cls)
        return cls._instance

    def __init__(self, API_KEY: str) -> None:
        if not self._initialized:
            self.API_KEY: str = API_KEY
            self.URL: str = "https://www.instagram.com/"
            self._initialized: bool = True

    def __str__(self) -> str:
        return f"Класс InstagramContent | API_KET = {self.API_KEY} | Инициализирован: {self._initialized}"

    def __repr__(self) -> str:
        return f"InstagramContent(API_KEY={self.API_KEY}, _initialized={self._initialized})"

    async def download_content(
        self, profile_id: str, descript: str, file_path: str, js_file
    ) -> None:
        """
        Метод загрузки контента в инстаграмм
        :param profile_id: id профиля gologin
        :param descript: описание к видео или фото
        :param file_path: абсолютный путь к файлу типа str
        :return: None
        """
        def get_node_path():
            base_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
            node_path = os.path.join(base_dir, "_internal", "playwright", "driver", "node.exe")
            if not os.path.exists(node_path):
                raise FileNotFoundError(f"Node.js (Playwright) не найден по пути: {node_path}")
            return node_path
        instagram_logging.info("Запуск функции download_content")
        async with async_playwright() as pl:
            instagram_logging.info("инициализация Gologin класс")
            gl = GoLogin(
                {
                    f"token": self.API_KEY,
                    "profile_id": profile_id,
                    "executablePath": "chromium",
                    "browserType": "chrome",
                    "auto_update_browser": False,
                    "launcherProperties": {  # Важно!
                        "headless": False,  # Принудительно отключаем headless
                        "args": ["--start-maximized"],  # Доп. аргументы (опционально)
                    },
                }
            )
            instagram_logging.info("запуск браузера")
            try:
                debug_address = gl.start()
            except Exception as e:
                instagram_logging.critical(
                    f"При старте браузера произошла ошибка {e} - {str(e)}"
                )
                raise

            instagram_logging.info("CDP коннект..")
            try:
                browser = await pl.chromium.connect_over_cdp(f"http://{debug_address}")
                context = browser.contexts[0]
                page = context.pages[0] if context.pages else await context.new_page()
                instagram_logging.info("Выбрана 1 страница")
            except Exception as e:
                instagram_logging.error(
                    f"При CDP коннект произошла ошибка {e} - {str(e)}"
                )
                raise

            instagram_logging.info("Переход по url")
            try:
                await page.goto(self.URL, timeout=900000)
                instagram_logging.info(
                    f"Переход по адрессу {debug_address + '/' + self.URL}"
                )
                await page.click(
                    "div.x9f619.xjbqb8w.x78zum5.x168nmei.x13lgxp2.x5pf9jr.xo71vjh.xixxii4.x13vifvy.x1plvlek.xryxfnj.x1c4vz4f.x2lah0s.xdt5ytf.xqjyukv.x1qjc9v5.x1oa3qoh.x1nhvcw1.x1dr59a3.xeq5yr9.x1n327nk > div > div > div > div > div.x1iyjqo2.xh8yej3 > div:nth-child(7) > div",
                    timeout=900000,
                )
                await page.wait_for_selector(
                    'xpath=//div[contains(@class, "x9f619")]//button[contains(text(), "Select from computer")]',
                    timeout=800000,
                    state="visible",
                )
                try:
                    print(file_path)
                    print(js_file)
                    node_path = get_node_path()
                    instagram_logging.info(f"Используемый Node.js: {node_path}")
                    instagram_logging.info("Загрузка видео")
                    response = requests.get(f"http://{debug_address}/json/version")
                    ws_url = response.json()["webSocketDebuggerUrl"]
                    process = subprocess.Popen(
                        [
                            node_path,
                            js_file,
                            ws_url,
                            "input[type='file']",
                            file_path,
                        ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                    )
                    try:
                        _, _ = process.communicate(timeout=5)
                        instagram_logging.info("Процесс загрузки завершен")
                    except subprocess.TimeoutExpired:
                        instagram_logging.info("Процесс загрузки убит")
                        process.kill()
                except subprocess.CalledProcessError as e:
                    instagram_logging.error(f"Ошибка загрузки stdout - {e.stdout}")
                    instagram_logging.error(f"Ошибка загрузки stderr - {e.stderr}")
                    raise
                time.sleep(10)
                element = await page.query_selector(
                    "div.x78zum5.x1q0g3np.xdko459 > button"
                )
                if element:
                    await element.click()
                await page.wait_for_selector(
                    'xpath=//div[@role="button"][contains(text(), "Next")]',
                    timeout=900000,
                )
                await page.click(
                    'xpath=//div[@role="button"][contains(text(), "Next")]',
                    timeout=900000,
                )
                await page.wait_for_selector(
                    'xpath=//div[@role="button"][contains(text(), "Next")]',
                    timeout=900000,
                )
                await page.click(
                    'xpath=//div[@role="button"][contains(text(), "Next")]',
                    timeout=900000,
                )
                await page.wait_for_selector(
                    'div[data-lexical-editor="true"]', timeout=900000
                )
                await page.fill(
                    'div[data-lexical-editor="true"]', descript, timeout=900000
                )
                await page.click(
                    'xpath=//div[@role="button"][contains(text(), "Share")]',
                    timeout=900000,
                )
                max_iter = 10
                for attempt in range(1, max_iter + 1):
                    try:
                        await page.wait_for_selector(
                            "img[alt='Animated checkmark']", 
                            timeout=9000 * attempt,
                        )
                        instagram_logging.info("Видео успешно загружено")
                        break
                    except Exception as e:

                        try_again_button = page.locator('button:has-text("Try again"), button >> text="Try again"')
                        if await try_again_button.is_visible(timeout=5000):
                            instagram_logging.info("Обнаружена ошибка - кликаем Try again")
                            await try_again_button.click()
                            await page.wait_for_timeout(3000)
                        else:
                            instagram_logging.warning(f"Попытка {attempt}: Не найдено ни завершения, ни ошибки")
                            
                        instagram_logging.info(f"Попытка {attempt}/{max_iter} - осталось {max_iter - attempt} попыток")
                else:
                    instagram_logging.error("Превышено максимальное количество попыток")
                    raise Exception("Не удалось дождаться завершения загрузки")
                try:
                    gl.stop()
                    instagram_logging.info("Браузер закрыт")
                except Exception as e:
                    instagram_logging.error(f"Ошибка при закрытии браузера: {str(e)}")
            except Exception as e:
                instagram_logging.critical(f"Ошибка скрипта: {str(e)}")
                raise
