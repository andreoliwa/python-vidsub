#!/usr/bin/python3
import click
import magic
from identify import identify
from pathlib import Path
from itertools import chain

ROOT_PATH = Path("~/data").expanduser()
HORROR_MOVIES_PATH = ROOT_PATH / "horror-movies"
MOVIES_PATH = ROOT_PATH / "movies"

NOT_MOVIE_SUFFIXES = {".sub"}


@click.group()
def movies():
    """Tools for movies."""
    pass


@movies.command()
def missing():
    """Missing movies (empty folders)."""
    for movie_path in chain(MOVIES_PATH.glob("*"), HORROR_MOVIES_PATH.glob("*")):
        if not movie_path.is_dir():
            continue

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

        if not found_movie:
            click.secho(str(movie_path), fg="red", err=True)


if __name__ == "__main__":
    movies()
