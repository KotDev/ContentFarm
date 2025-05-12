import abc
import asyncio
from abc import ABC
from pathlib import Path
from gologin import GoLogin
from instagram_scripts.content import InstagramContent
from aiohttp import ClientSession

class FarmAbstract(ABC):
   @abc.abstractmethod
   async def get_profiles(self):
       pass


class FarmContents(FarmAbstract):
    def __init__(self, API_KEY: str, MEDIA_PATH: Path):
        self.API_KEY = API_KEY

        self.instagram = InstagramContent(self.API_KEY, MEDIA_PATH)
        self.gl = GoLogin({
                            "token": API_KEY
                        })

    async def get_profiles(self):
        async with ClientSession() as session:
            async with session.get("https://api.gologin.com/browser/v2", headers={
                                                                                "Authorization": f"Bearer {self.API_KEY}",
                                                                                "Content-Type": "application/json"
                                                                                 }) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None





async def main():
    farm = FarmContents(API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2ODFjOWIyYjYxYzk2MjBhYjAxYTQ0MzAiLCJ0eXBlIjoiZGV2Iiwiand0aWQiOiI2ODFjOWI0ZjgxMThjZjY1YTBiZWY0NDAifQ.pPUl_LWrP5R_kpGdAsUC_I-Sb7xTmjHvnGITCAuDcCI",
                        MEDIA_PATH=Path(__file__).parent / "medias")
    profiles = await farm.get_profiles()
    print([f"{i['name']} | {i['id']}" for i in profiles["profiles"]])
    await farm.instagram.download_video(video_name="IMG_4384.MP4", profile_id="681c9b2c61c9620ab01a4488", descript="OZON: 1305778952\nWB: 179742155")


asyncio.run(main())
