"""Tools for movie files and directories on Kodi."""
__version__ = "0.0.0"

import os
import re
from itertools import chain
from pathlib import Path
from typing import List, Optional, Tuple, Union

import click
import imdb
import magic
from clib.files import fzf, shell
from clib.iter import roundrobin
from clib.ui import failure, success
from identify import identify
from slugify import slugify

from vidsub.constants import (
    COMPLETED_DIR,
    IGNORE_EXTENSIONS,
    IMDB_URL,
    MOVIE_EXTENSIONS,
    MOVIES_DIR,
    ODD_MOVIES_DIR,
    UNIQUE_SEPARATOR,
    VIDEO_EXTENSIONS,
)


class FileManager:
    def __init__(self, working_dir: Union[Path, str] = "") -> None:
        os.chdir(Path(working_dir).expanduser())

    def videos(self, *partial_names: str) -> List[str]:
        """List videos in the current dir."""
        if not partial_names:
            partial_names = [""]
        return sorted(
            file_name
            for name in partial_names
            for file_name in shell(f"fd {name}", quiet=True, return_lines=True)
            if Path(file_name).suffix in VIDEO_EXTENSIONS
        )


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
        title = (
            movie["title"]
            .replace("&", "")
            .replace("(", "")
            .replace(")", "")
            .replace("'", "")
            .replace('"', "")
        )
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
            str(path)
            for path in chain(MOVIES_DIR.iterdir(), ODD_MOVIES_DIR.iterdir())
            if not path.is_dir()
        ]
        if root_files:
            failure("There are files in the root dir! Move them to subdirectories.")
            failure("  " + "\n  ".join(root_files))
            return False
        success(f"No single files under {MOVIES_DIR} and {ODD_MOVIES_DIR}")
        return True

    @staticmethod
    def validate_completed() -> bool:
        """Validate if the completed dir is empty."""
        wrong: List[Path] = list(COMPLETED_DIR.iterdir())
        if not wrong:
            success(f"No item under {COMPLETED_DIR}")
            return True

        failure(
            f"Files/directories found under {COMPLETED_DIR}. Move them to the correct directory."
        )
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
            [
                Path(dir_) / item
                for item in shell(f"exa -1s age {dir_}", quiet=True, return_lines=True)
            ]
            for dir_ in dirs
        ]
        yield from roundrobin(*iterables)

    @classmethod
    def iter_movie_dirs(cls, patterns: Tuple[str] = None):
        """Iterate over movie directories."""
        regex = re.compile(".*".join(patterns), re.IGNORECASE) if patterns else None
        for movie_path in cls.iterdir_newest_first(MOVIES_DIR, ODD_MOVIES_DIR):
            if not movie_path.is_dir():
                continue
            if not regex or (regex and regex.findall(movie_path.name)):
                yield movie_path

    @staticmethod
    def count_movies() -> int:
        """Return the count of movies in both dirs."""
        return int(
            shell(
                f"ls -1 {MOVIES_DIR} {ODD_MOVIES_DIR} | wc -l | xargs",
                quiet=True,
                return_lines=True,
            )[0]
        )

    @staticmethod
    def iter_movies_in_dir(
        movie_dir: Path, verbose=False, use_magic=False
    ) -> List[Path]:
        """Iterate over movies in a dir."""
        found_movies: List[Path] = []
        for file in movie_dir.iterdir():
            tags = identify.tags_from_path(str(file))
            if "binary" not in tags:
                continue

            if use_magic:
                mime_type = magic.from_file(str(file), mime=True)
                if (
                    mime_type.startswith("video")
                    and file.suffix.lower() not in IGNORE_EXTENSIONS
                ):
                    if verbose:
                        click.echo(
                            f"  Found movie with magic: {file.name} ({mime_type})"
                        )
                    found_movies.append(file)
                    continue
            elif file.suffix.lower() not in IGNORE_EXTENSIONS:
                found_movies.append(file)
                if verbose:
                    click.echo(f"  Found binary movie: {file.name}")

        missing_extensions = {
            movie.suffix.lower()
            for movie in found_movies
            if movie.suffix.lower() not in MOVIE_EXTENSIONS
        }
        if missing_extensions:
            click.secho(
                f"Add these extensions to MOVIE_EXTENSIONS: {missing_extensions}",
                fg="bright_red",
            )

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
