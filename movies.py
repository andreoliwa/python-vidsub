#!/usr/bin/python3
import click
import magic
from identify import identify
from pathlib import Path
from itertools import chain
from slugify import slugify
import imdb

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


@movies.command()
def missing():
    """Missing movies (empty folders)."""
    ia = imdb.IMDb()

    for movie_path in chain(MOVIES_PATH.glob("*"), HORROR_MOVIES_PATH.glob("*")):
        if not movie_path.is_dir():
            continue

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

        click.secho(f"\n{movie_path}", fg="red", err=True)
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


if __name__ == "__main__":
    movies()
