"""Tools for movie files and directories on Kodi."""
import re
import sys
from datetime import datetime, timedelta
from itertools import chain
from pathlib import Path
from typing import List, Optional, Tuple, Union

import click
import imdb
import magic
from clib import verbose_option
from clib.files import fzf, relative_to_home, shell
from clib.iter import roundrobin
from clib.ui import AliasedGroup, failure, success
from identify import identify
from slugify import slugify

ROOT_DIR = Path("~/data").expanduser()
COMPLETED_DIR = ROOT_DIR / "completed"
MOVIES_DIR = ROOT_DIR / "movies"
WEIRD_MOVIES_DIR = ROOT_DIR / "weird-movies"
MOVIE_EXTENSIONS = {f".{item}" for item in {"avi", "mp4", "mpg", "mkv", "wmv", "mov"}}
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

IMDB_URL = "https://www.imdb.com/title/tt"
IMDB_SEARCH_URL = "https://www.imdb.com/find?q="
TORRENT_SEARCH_COMMAND = "torrent-search -a -i on1337x "
MISSING_TXT = "missing.txt"
UNIQUE_SEPARATOR = "±"


@click.group(cls=AliasedGroup)
def main():
    """Tools for movie files and directories on Kodi."""
    if not MOVIES_DIR.exists():
        command = "sshfs osmc@styx:/data/ ~/data"
        click.secho(f"SSH dir not mounted. Run this command:\n{command}", fg="bright_red")
        sys.exit(1)


class MovieManager:
    """Helper to manage movies."""

    def __init__(self, verbose: bool):
        self.ia = imdb.IMDb()
        self.verbose = verbose

    def format_imdb_url(self, movie: imdb.Movie.Movie) -> str:
        """Format IMDb URL."""
        return f"{IMDB_URL}{movie.movieID}"

    def format_info(self, movie: imdb.Movie.Movie, full=False) -> str:
        """Format movie info in one line or multiple lines."""
        title = movie["title"]
        year = movie.get("year")
        url = self.format_imdb_url(movie)
        if not full:
            return f"{movie.movieID} {UNIQUE_SEPARATOR} {title} {UNIQUE_SEPARATOR} {year} {UNIQUE_SEPARATOR} {url}"

        if self.verbose:
            click.echo(f"Loading movie {movie.movieID} from IMDb")
        movie = self.ia.get_movie(movie.movieID)
        rating = movie.get("rating", "Not rated")
        return f"{title} ({year})\nRating: {rating}\n{url}"

    @staticmethod
    def validate_root() -> bool:
        """Validate if both root dirs doen't have single files."""
        root_files = [
            str(path) for path in chain(MOVIES_DIR.iterdir(), WEIRD_MOVIES_DIR.iterdir()) if not path.is_dir()
        ]
        if root_files:
            failure("There are files in the root dir! Move them to subdirectories.")
            failure("  " + "\n  ".join(root_files))
            return False
        success(f"No single files under {MOVIES_DIR} and {WEIRD_MOVIES_DIR}")
        return True

    @staticmethod
    def validate_completed() -> bool:
        """Validate if the completed dir is empty."""
        wrong: List[Path] = list(COMPLETED_DIR.iterdir())
        if not wrong:
            success(f"No item under {COMPLETED_DIR}")
            return True

        failure(f"Files/directories found under {COMPLETED_DIR}. Move them to the correct directory.")
        for item in wrong:
            failure(f"  {item}")
        return False

    def search_imdb(self, movie_dir: Path, verbose=False) -> Optional[imdb.Movie.Movie]:
        """Search the movie directory on IMDb."""
        slugged: str = slugify(movie_dir.name, separator=UNIQUE_SEPARATOR)
        parts = slugged.split(UNIQUE_SEPARATOR)
        movies: Optional[imdb.Movie.Movie] = None
        chosen_line: Optional[str] = None
        choices: List[str] = []
        while parts:
            query = " ".join(parts)
            click.echo(f"Searching IMDb with: {query}")
            movies = self.ia.search_movie(query)
            if movies:
                choices = [self.format_info(movie) for movie in movies]
                if not verbose:
                    # Display the movie dir before showing fzf when not in verbose mode
                    click.echo(f"\nSelect IMDb title for the directory: '{movie_dir}'")

                chosen_line = fzf(choices)
                if chosen_line:
                    break

            # Nothing was chosen, maybe because none of the options were good.
            # Remove one part and search again
            parts.pop()

            if not parts:
                parts = [click.prompt("Type a IMDb query")]

        if not chosen_line or not movies:
            return None
        chosen_movie_id = chosen_line.split(UNIQUE_SEPARATOR)[0].strip()
        for movie in movies:
            if movie.movieID == chosen_movie_id:
                return movie
        return None

    @staticmethod
    def iterdir_newest_first(*dirs):
        """Iterate over dirs sorting by newest first."""
        iterables = [
            [Path(dir_) / item for item in shell(f"exa -1s age {dir_}", quiet=True, return_lines=True)] for dir_ in dirs
        ]
        yield from roundrobin(*iterables)

    @classmethod
    def iter_movie_dirs(cls, patterns: Tuple[str] = None):
        """Iterate over movie directories."""
        regex = re.compile(".*".join(patterns), re.IGNORECASE) if patterns else None
        for movie_path in cls.iterdir_newest_first(MOVIES_DIR, WEIRD_MOVIES_DIR):
            if not movie_path.is_dir():
                continue
            if not regex or (regex and regex.findall(movie_path.name)):
                yield movie_path

    @staticmethod
    def count_movies() -> int:
        """Return the count of movies in both dirs."""
        return int(shell(f"ls -1 {MOVIES_DIR} {WEIRD_MOVIES_DIR} | wc -l | xargs", quiet=True, return_lines=True)[0])

    @staticmethod
    def iter_movies_in_dir(movie_dir: Path, verbose=False, use_magic=False) -> List[Path]:
        """Iterate over movies in a dir."""
        found_movies: List[Path] = []
        for file in movie_dir.iterdir():
            tags = identify.tags_from_path(file)
            if "binary" not in tags:
                continue

            if use_magic:
                mime_type = magic.from_file(str(file), mime=True)
                if mime_type.startswith("video") and file.suffix.lower() not in IGNORE_EXTENSIONS:
                    if verbose:
                        click.echo(f"  Found movie with magic: {file.name} ({mime_type})")
                    found_movies.append(file)
                    continue
            elif file.suffix.lower() not in IGNORE_EXTENSIONS:
                found_movies.append(file)
                if verbose:
                    click.echo(f"  Found binary movie: {file.name}")

        missing_extensions = {
            movie.suffix.lower() for movie in found_movies if movie.suffix.lower() not in MOVIE_EXTENSIONS
        }
        if missing_extensions:
            click.secho(f"Add these extensions to MOVIE_EXTENSIONS: {missing_extensions}", fg="bright_red")

        return found_movies

    @staticmethod
    def iter_torrent_dirs(patterns: Tuple[str] = None):
        """Iterate over torrent directories."""
        import transmissionrpc

        regex = re.compile(".*".join(patterns), re.IGNORECASE) if patterns else None

        tc = transmissionrpc.Client("localhost", port=9091)

        for torrent in tc.get_torrents():
            files = torrent.files().values()
            if not files:
                # Recently added torrents might not have files yet
                continue

            paths = {
                (Path("~" + torrent.downloadDir) / file["name"]).expanduser().parent
                for file in torrent.files().values()
            }
            movie_path = Path(sorted(paths)[0])
            if not regex or (regex and regex.findall(movie_path.name)):
                yield movie_path


@main.command()
@click.option("--force", "-f", is_flag=True, default=False, help=f"Force creation of {MISSING_TXT}")
@verbose_option
@click.argument("movie_name", nargs=-1, required=False)
def validate(force: bool, verbose: bool, movie_name: Tuple[str]):
    """Validate movie files and dirs.

    Check root and completed dirs, and missing movies (empty dirs).
    """
    manager = MovieManager(verbose)
    if not (manager.validate_root() and manager.validate_completed()):
        sys.exit(1)

    with click.progressbar(
        MovieManager.iter_movie_dirs(movie_name),
        length=MovieManager.count_movies(),
        label="Validating directories",
        item_show_func=lambda path: str(relative_to_home(path)) if path else "",
    ) as bar:
        for movie_dir in bar:
            if verbose:
                click.echo(f"\nMovie directory: '{movie_dir}'")

            missing_txt = movie_dir / MISSING_TXT  # TODO save file as json or toml

            # TODO remove .xml files and confirm each file
            # TODO add .nomedia to subdirs https://kodi.wiki/view/Update_Music_Library#Exclude_Folder
            # TODO check VIDEO_TS for movies

            found_movies = manager.iter_movies_in_dir(movie_dir, verbose)
            if found_movies:
                # Remove it once a movie is found
                if missing_txt.exists():
                    missing_txt.unlink()

                main_movie: Optional[Path] = None
                for found_movie in found_movies:
                    if found_movie.with_suffix(".nfo").exists():
                        main_movie = found_movie
                        break

                if len(found_movies) == 1:
                    main_movie = found_movies[0]
                elif not main_movie:
                    # If a .nfo file doesn't exist, select the main movie
                    # A dir can have multiple movies; use fzf to select the main one
                    click.echo(f"\nSelect the main movie:")
                    chosen_movie = fzf(found_movies)
                    if not chosen_movie:
                        click.secho("No main movie selected", fg="red")
                        continue
                    main_movie = Path(chosen_movie)
                if verbose:
                    click.echo(f"  Main movie: {main_movie.name}")

                # TODO remove all other .nfo files, keep only this one
                # https://kodi.wiki/view/NFO_files
                nfo_file = main_movie.with_suffix(".nfo")
                if nfo_file.exists():
                    stat = nfo_file.stat()
                    if verbose:
                        click.echo(f"  NFO file..: {nfo_file.name} (size in bytes: {stat.st_size})")
                else:
                    imdb_movie = manager.search_imdb(movie_dir, verbose)
                    if imdb_movie:
                        url = manager.format_imdb_url(imdb_movie)
                        nfo_file.write_text(f"{url}\n")
                        if verbose:
                            click.echo(f"  Writing {url} on {nfo_file.name}")
                continue

            click.secho(f"\n{movie_dir}", fg="bright_red", err=True)
            if not force and missing_txt.exists():
                click.echo(missing_txt.read_text())
                continue

            lines = []
            clean_movie_name = slugify(movie_dir.name, separator="+")
            lines.append(f"{TORRENT_SEARCH_COMMAND}{clean_movie_name}")
            lines.append(f"IMDB Search: {IMDB_SEARCH_URL}{clean_movie_name}")

            imdb_movie = manager.search_imdb(movie_dir, verbose)
            if imdb_movie:
                lines.append(manager.format_info(imdb_movie, full=True))

            content = "\n".join(lines)
            missing_txt.write_text(content)
            click.echo(content)


def ls_movie(path: Union[Path, str]):
    """List movies."""
    click.echo()
    shell(f'exa -lhaRTF "{path}"')


@main.command()
@click.argument("movie_name", nargs=-1, required=True)
def ls(movie_name):
    """List movies by a partial dir name."""
    for movie_path in MovieManager.iter_movie_dirs(movie_name):
        ls_movie(movie_path)


@main.command()
@click.argument("movie_name", nargs=-1, required=True)
def rm(movie_name: Tuple[str]):
    """Remove a movie directory by a partial dir name."""
    movie_list = [str(movie_path) for movie_path in MovieManager.iter_movie_dirs(movie_name)]
    if not movie_list:
        failure("No movie found", 1)

    chosen_dir = fzf(movie_list)
    if not chosen_dir:
        failure("No directory selected", 2)

    ls_movie(chosen_dir)
    click.confirm("\nDo you really want to remove this directory?", abort=True)

    shell(f'rm -rvf "{chosen_dir}"')
    click.secho(f"Directory removed: {chosen_dir}", fg="green")


@main.command()
@click.option(
    "--torrent", "-t", "for_torrents_only", is_flag=True, default=False, help=f"Only for Transmission torrents"
)
@click.option("--days", "-d", default=2, type=int, help=f"Days to consider recent files")
@click.argument("movie_name", nargs=-1, required=False)
def subtitles(for_torrents_only: bool, days: int, movie_name: Tuple[str]):
    """Search subtitles for recent movies."""
    recent_date = datetime.now() - timedelta(days=days)

    found = False
    function = MovieManager.iter_torrent_dirs if for_torrents_only else MovieManager.iter_movie_dirs
    for movie_dir in function(movie_name):
        if not movie_dir.exists():
            failure(f"Recent torrent, movie dir doesn't exist yet: {movie_dir}")
            continue

        recent_movies = {
            item
            for item in movie_dir.iterdir()
            if item.suffix.lower() in MOVIE_EXTENSIONS and datetime.fromtimestamp(item.stat().st_mtime) > recent_date
        }
        if recent_movies:
            found = True
            click.echo()
            shell(f"subtitles.sh '{movie_dir}'")

    if not found:
        failure("No movies found", 1)


if __name__ == "__main__":
    main()
