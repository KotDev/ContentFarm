import logging
from pathlib import Path

instagram_logging = logging.getLogger("Instagram_INFO")

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

inst_handler_info = logging.FileHandler(Path(__file__).parent / "logs" / "info.log")
inst_handler_info.setLevel(logging.INFO)
inst_handler_info.setFormatter(formatter)

instagram_handler_error = logging.FileHandler(
    Path(__file__).parent / "logs" / "error.log"
)
instagram_handler_error.setLevel(logging.ERROR)
instagram_handler_error.setFormatter(formatter)

instagram_handler_critical = logging.FileHandler(
    Path(__file__).parent / "logs" / "critical.log"
)
instagram_handler_critical.setLevel(logging.CRITICAL)
instagram_handler_critical.setFormatter(formatter)

instagram_logging.addHandler(inst_handler_info)
instagram_logging.addHandler(instagram_handler_error)
instagram_logging.addHandler(instagram_handler_critical)
