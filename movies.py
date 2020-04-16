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
from typing import Tuple, Union

ROOT_PATH = Path("~/data").expanduser()
HORROR_MOVIES_PATH = ROOT_PATH / "horror-movies"
MOVIES_PATH = ROOT_PATH / "movies"
NOT_MOVIE_SUFFIXES = {".sub"}
IMDB_URL = "https://www.imdb.com/title/tt"
IMDB_SEARCH_URL = "https://www.imdb.com/find?q="
TORRENT_SEARCH_COMMAND = "torrent-search -a -i on1337x "


@click.group()
def movies():
    """Tools for movies."""
    pass


def iter_movie_directories(patterns: Tuple[str] = None):
    regex = re.compile(".*".join(patterns), re.IGNORECASE) if patterns else None
    for movie_path in chain(MOVIES_PATH.iterdir(), HORROR_MOVIES_PATH.iterdir()):
        if not movie_path.is_dir():
            continue
        if not regex or (regex and regex.findall(movie_path.name)):
            yield movie_path


@movies.command()
def missing():
    """Missing movies (empty folders)."""
    ia = imdb.IMDb()

    for movie_path in iter_movie_directories():
        missing_txt = movie_path / "missing.txt"

        found_movie = False
        for child_path in movie_path.glob("*"):
            tags = identify.tags_from_path(child_path)
            if "binary" not in tags:
                continue

            mime_type = magic.from_file(str(child_path), mime=True)
            if mime_type.startswith("video") and child_path.suffix:
                # click.echo(f"Found movie {child_path} ({mime_type})")
                found_movie = True
                break

        if found_movie:
            # Remove the file once a movie is found
            if missing_txt.exists():
                missing_txt.unlink()
            continue

        click.secho(f"\n{movie_path}", fg="bright_red", err=True)
        if missing_txt.exists():
            click.echo(missing_txt.read_text())
            continue

        clean_movie_name = slugify(movie_path.name, separator="+")
        lines = []
        lines.append(f"{TORRENT_SEARCH_COMMAND}{clean_movie_name}")
        lines.append(f"IMDB Search: {IMDB_SEARCH_URL}{clean_movie_name}")

        results = ia.search_movie(clean_movie_name.replace("+", " "))
        if results:
            first_id = results[0].movieID
            movie = ia.get_movie(first_id)
            title = movie["title"]
            year = movie["year"]
            rating = movie.get("rating", "?")
            lines.append(f"{title} ({year})\nRating: {rating}\n{IMDB_URL}{first_id}")

        content = "\n".join(lines)
        missing_txt.write_text(content)
        click.echo(content)


def ls_movie(path: Union[Path, str]):
    click.echo(f"\n{path}:")
    run(f"ls -lh '{path}'", shell=True, universal_newlines=True)


@movies.command()
@click.argument("partial_name", nargs=-1, required=True)
def ls(partial_name):
    """List movies by a partial dir name."""
    for movie_path in iter_movie_directories(partial_name):
        ls_movie(movie_path)


@movies.command()
@click.argument("partial_name", nargs=-1, required=True)
def rm(partial_name):
    """Remove a movie directory by a partial dir name."""
    movie_list = [str(movie_path) for movie_path in iter_movie_directories(partial_name)]
    if not movie_list:
        click.secho("No movie found", err=True, fg="bright_red")
        sys.exit(1)

    choices = "\n".join(movie_list)
    chosen_dir = run(
        f"echo '{choices}' | fzf --height={len(movie_list)} --cycle --tac",
        shell=True,
        stdout=PIPE,
        universal_newlines=True,
    ).stdout.strip()

    if not chosen_dir:
        click.secho("No directory selected", err=True, fg="bright_red")
        sys.exit(2)

    ls_movie(chosen_dir)
    click.confirm("\nDo you really want to remove this directory?", abort=True)

    run(f"rm -rf '{chosen_dir}'", shell=True)
    click.secho(f"Directory removed: {chosen_dir}", fg="green")


@movies.command()
def check():
    """Check files on the root dir and other problems."""
    root_files = [str(path) for path in chain(MOVIES_PATH.iterdir(), HORROR_MOVIES_PATH.iterdir()) if not path.is_dir()]
    if root_files:
        click.secho("There are files in the root dir! Move them to subdirectories.", fg="bright_red", err=True)
        click.echo("\n".join(root_files))
        sys.exit(1)

    click.secho("No problems found", fg="bright_green")


if __name__ == "__main__":
    movies()
