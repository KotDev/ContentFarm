import abc
from abc import ABC
from gologin import GoLogin

class InstagramContentAbstract(ABC):

    @abc.abstractmethod
    async def download_video(self, video_name: str, profile_id: str, descript: str):
        pass