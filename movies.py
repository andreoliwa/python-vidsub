#!/usr/bin/python3
import click
import magic
from identify import identify
from pathlib import Path
from itertools import chain
from slugify import slugify
import imdb
import re
import sys
from subprocess import run, PIPE
from typing import Tuple, Union, List, Optional, Any
from pprint import pprint
from datetime import datetime, timedelta
from babelfish import Language
from subliminal import download_best_subtitles, region, save_subtitles, scan_videos

ROOT_PATH = Path("~/data").expanduser()
HORROR_MOVIES_PATH = ROOT_PATH / "horror-movies"
MOVIES_PATH = ROOT_PATH / "movies"
MOVIE_EXTENSIONS = {".avi", ".mp4"}
IGNORE_SUFFIXES = {".sub"}
IMDB_URL = "https://www.imdb.com/title/tt"
IMDB_SEARCH_URL = "https://www.imdb.com/find?q="
TORRENT_SEARCH_COMMAND = "torrent-search -a -i on1337x "
MISSING_TXT = "missing.txt"
UNIQUE_SEPARATOR = "±"


@click.group()
def main():
    """Tools for movies."""
    pass


def iter_movie_directories(patterns: Tuple[str] = None):
    regex = re.compile(".*".join(patterns), re.IGNORECASE) if patterns else None
    for movie_path in chain(MOVIES_PATH.iterdir(), HORROR_MOVIES_PATH.iterdir()):
        if not movie_path.is_dir():
            continue
        if not regex or (regex and regex.findall(movie_path.name)):
            yield movie_path


class MovieManager:
    def __init__(self, verbose: bool):
        self.ia = imdb.IMDb()
        self.verbose = verbose

    def format_imdb_url(self, movie: imdb.Movie.Movie) -> str:
        return f"{IMDB_URL}{movie.movieID}"

    def format_info(self, movie: imdb.Movie.Movie, full=False) -> str:
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

    def search_imdb(self, movie_dir: Path) -> Optional[imdb.Movie.Movie]:
        slugged: str = slugify(movie_dir.name, separator=UNIQUE_SEPARATOR)
        parts = slugged.split(UNIQUE_SEPARATOR)
        movies: Optional[imdb.Movie.Movie] = None
        chosen_line: str = None
        choices: List[str] = []
        while parts:
            movies = self.ia.search_movie(" ".join(parts))
            if not movies:
                parts.pop()
                continue

            choices = [self.format_info(movie) for movie in movies]
            chosen_line = fzf(choices)
            if chosen_line:
                break

            # Nothing was chosen, maybe because none of the options were good.
            # Remove one part and search again
            parts.pop()

        for choice in choices:
            chosen_movie_id = chosen_line.split(UNIQUE_SEPARATOR)[0].strip()
            for movie in movies:
                if movie.movieID == chosen_movie_id:
                    return movie
        return None


@main.command()
@click.option("--force", "-f", is_flag=True, default=False, help=f"Force creation of {MISSING_TXT}")
@click.option("--verbose", "-v", is_flag=True, default=False, help=f"Verbose display")
@click.argument("partial_name", nargs=-1, required=False)
def check(force: bool, verbose: bool, partial_name: Tuple[str]):
    """Check files on the root dir and missing movies (empty dirs)."""
    root_files = [str(path) for path in chain(MOVIES_PATH.iterdir(), HORROR_MOVIES_PATH.iterdir()) if not path.is_dir()]
    if root_files:
        click.secho("There are files in the root dir! Move them to subdirectories.", fg="bright_red", err=True)
        click.echo("\n".join(root_files))
        sys.exit(1)
    click.secho("No files in the root dirs", fg="bright_green")

    movie_manager = MovieManager(verbose)

    for movie_dir in iter_movie_directories(partial_name):
        if verbose:
            click.echo(f"\nMovie directory: {movie_dir}")
        missing_txt = movie_dir / MISSING_TXT

        found_movie = None
        for child_path in movie_dir.iterdir():
            tags = identify.tags_from_path(child_path)
            if "binary" not in tags:
                continue

            mime_type = magic.from_file(str(child_path), mime=True)
            # TODO use identify by default (it should be faster); add --magic option to use optionally
            if mime_type.startswith("video") and child_path.suffix not in IGNORE_SUFFIXES:
                if verbose:
                    click.echo(f"Found movie {child_path.name} ({mime_type})")
                found_movie = child_path
                # TODO a dir can have multiple movies; use fzf to select the main one
                break

        if found_movie:
            # Remove the file once a movie is found
            if missing_txt.exists():
                missing_txt.unlink()

            nfo_file = found_movie.with_suffix(".nfo")
            # TODO remove .xml files
            # TODO remove all other .nfo files, keep only this one
            if nfo_file.exists():
                stat = nfo_file.stat()
                click.echo(f"NFO file found: {nfo_file.name} (size in bytes: {stat.st_size})")
            else:
                imdb_movie = movie_manager.search_imdb(movie_dir)
                if imdb_movie:
                    url = movie_manager.format_imdb_url(imdb_movie)
                    nfo_file.write_text(f"{url}\n")
                    if verbose:
                        click.echo(f"Writing {url} on {nfo_file}")
            continue

        click.secho(f"\n{movie_dir}", fg="bright_red", err=True)
        if not force and missing_txt.exists():
            click.echo(missing_txt.read_text())
            continue

        lines = []
        clean_movie_name = slugify(movie_dir.name, separator="+")
        lines.append(f"{TORRENT_SEARCH_COMMAND}{clean_movie_name}")
        lines.append(f"IMDB Search: {IMDB_SEARCH_URL}{clean_movie_name}")

        imdb_movie = movie_manager.search_imdb(movie_dir)
        if imdb_movie:
            lines.append(movie_manager.format_info(imdb_movie, full=True))

        content = "\n".join(lines)
        missing_txt.write_text(content)
        click.echo(content)


def ls_movie(path: Union[Path, str]):
    click.echo(f"\n{path}:")
    run(f"ls -lh '{path}'", shell=True, universal_newlines=True)


@main.command()
@click.argument("partial_name", nargs=-1, required=True)
def ls(partial_name):
    """List movies by a partial dir name."""
    for movie_path in iter_movie_directories(partial_name):
        ls_movie(movie_path)


def fzf(items: List[Any]) -> str:
    choices = "\n".join([str(item) for item in items]).replace("'", "")
    #  --tac
    return run(
        f"echo '{choices}' | fzf --height={len(items) + 2} --cycle", shell=True, stdout=PIPE, universal_newlines=True,
    ).stdout.strip()


def fail(message: str, exit_code: int = 1) -> None:
    click.secho(message, err=True, fg="bright_red")
    sys.exit(exit_code)


@main.command()
@click.argument("partial_name", nargs=-1, required=True)
def rm(partial_name: Tuple[str]):
    """Remove a movie directory by a partial dir name."""
    movie_list = [str(movie_path) for movie_path in iter_movie_directories(partial_name)]
    if not movie_list:
        fail("No movie found", 1)

    chosen_dir = fzf(movie_list)
    if not chosen_dir:
        fail("No directory selected")

    ls_movie(chosen_dir)
    click.confirm("\nDo you really want to remove this directory?", abort=True)

    run(f"rm -rf '{chosen_dir}'", shell=True)
    click.secho(f"Directory removed: {chosen_dir}", fg="green")


@main.command()
@click.argument("partial_name", nargs=-1, required=False)
def sub(partial_name: Tuple[str]):
    """Search subtitles for recent movies."""
    recent_date = datetime.now() - timedelta(days=10)

    content = ["#!/usr/bin/env bash -x"]
    for movie_dir in iter_movie_directories(partial_name):
        recent_movies = {
            item
            for item in movie_dir.iterdir()
            if "binary" in identify.tags_from_path(item)
            and item.suffix in MOVIE_EXTENSIONS
            and datetime.fromtimestamp(item.stat().st_mtime) > recent_date
        }
        if recent_movies:
            content.append(f"subtitles.sh '{movie_dir}'")
            click.echo(movie_dir)

    script = Path("/tmp/download-all-subtitles.sh")
    script.write_text("\n".join(content))
    click.echo(f"Run this command to download subtitles:\nbash -x {script}")


if __name__ == "__main__":
    main()
