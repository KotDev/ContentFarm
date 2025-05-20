import abc
from abc import ABC
from pathlib import Path


class InstagramContentAbstract(ABC):

    @abc.abstractmethod
    async def download_content(self, profile_id: str, descript: str, file_path: Path, js_file):
        pass
