from pathlib import Path

# TODO: read from env var
ROOT_DIR = Path("~/data").expanduser()
MOVIES_DIR = ROOT_DIR / "movies"
COMPLETED_DIR = ROOT_DIR / "completed"
ODD_MOVIES_DIR = ROOT_DIR / "odd-movies"

IMDB_URL = "https://www.imdb.com/title/tt"
IMDB_SEARCH_URL = "https://www.imdb.com/find?q="
TORRENT_SEARCH_COMMAND = "torrent-search -a -i on1337x "
MISSING_TXT = "missing.txt"
UNIQUE_SEPARATOR = "±"

MOVIE_EXTENSIONS = {f".{item}" for item in {"avi", "mp4", "mpg", "mkv", "wmv", "mov"}}
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
IGNORE_EXTENSIONS = {
    f".{item}"
    for item in {
        "sub",
        "jpg",
        "jpeg",
        "nfo",
        "png",
        "part",
        "srt",
        "dts",
        "ac3",
        "swf",
        "pdf",
        "rar",
        "ogv",
        "sqlite",
        "gif",
        "zip",
        "gz",
    }
}
for index in range(50):
    IGNORE_EXTENSIONS.add(f".r{index:02}")
