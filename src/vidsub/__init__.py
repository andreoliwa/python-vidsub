__version__ = "0.0.0"


import os
from pathlib import Path
from typing import Union

from clib.files import shell

VIDEO_EXTENSIONS = {
    f".{item}"
    for item in {
        "asf",
        "avi",
        "divx",
        "f4v",
        "flc",
        "flv",
        "m4v",
        "mkv",
        "mov",
        "mp4",
        "mpa",
        "mpeg",
        "mpg",
        "ogv",
        "wmv",
    }
}


class FileManager:
    def __init__(self, working_dir: Union[Path, str] = "") -> None:
        os.chdir(Path(working_dir).expanduser())

    def videos(self):
        """List videos in the current dir."""
        return sorted(
            file_name
            for file_name in shell("fd", quiet=True, return_lines=True)
            if Path(file_name).suffix in VIDEO_EXTENSIONS
        )
