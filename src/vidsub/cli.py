"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mvidsub` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``vidsub.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``vidsub.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple, Union

import click
from clib import verbose_option
from clib.files import fzf, shell
from clib.ui import AliasedGroup, failure
from slugify import slugify

from vidsub import MOVIE_EXTENSIONS, FileManager, MovieManager
from vidsub.constants import IMDB_SEARCH_URL, MISSING_TXT, MOVIES_DIR, TORRENT_SEARCH_COMMAND


@click.group(cls=AliasedGroup)
def main():
    """Tools for movie files and directories on Kodi."""
    if not MOVIES_DIR.exists():
        command = "sshfs osmc@styx:/mnt/red/ ~/data"
        click.secho(
            f"SSH dir not mounted. Run this command:\n{command}", fg="bright_red"
        )
        sys.exit(1)


@main.command()
@click.option(
    "--dir", "-d", "dir_", type=click.Path(exists=True), help="Working directory"
)
@click.argument("partial_names", nargs=-1)
def ls_videos(dir_, partial_names):
    """List videos in the current dir."""
    for video in FileManager(dir_ or "").videos(*partial_names):
        click.echo(video)


@main.command()
@click.option(
    "--force",
    "-f",
    is_flag=True,
    default=False,
    help=f"Force creation of {MISSING_TXT} and .nfo files",
)
@verbose_option
@click.argument("movie_name", nargs=-1, required=False)
def validate(force: bool, verbose: bool, movie_name: Tuple[str]):
    """Validate movie files and dirs.

    Check root and completed dirs, and missing movies (empty dirs).
    """
    if force:
        click.echo(f"Force creation of {MISSING_TXT} and .nfo files")

    manager = MovieManager(verbose)
    if not (manager.validate_root() and manager.validate_completed()):
        sys.exit(1)

    with click.progressbar(
        MovieManager.iter_movie_dirs(movie_name),
        length=MovieManager.count_movies(),
        label="Validating directories",
        item_show_func=lambda path: str(path) if path else "",
    ) as bar:
        for movie_dir in bar:
            if verbose:
                click.echo(f"\nMovie directory: '{movie_dir}'")

            missing_txt = (
                movie_dir / MISSING_TXT
            )  # TODO feat: save file as json or toml

            # TODO feat: remove .xml files and confirm each file
            # TODO feat: add .nomedia to subdirs https://kodi.wiki/view/Update_Music_Library#Exclude_Folder
            # TODO feat: check VIDEO_TS for movies

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
                    click.echo("\nSelect the main movie:")
                    chosen_movie = fzf(found_movies)
                    if not chosen_movie:
                        click.secho("No main movie selected", fg="red")
                        continue
                    main_movie = Path(chosen_movie)
                if verbose:
                    click.echo(f"  Main movie: {main_movie.name}")

                # TODO feat: remove all other .nfo files, keep only this one
                # https://kodi.wiki/view/NFO_files
                nfo_file = main_movie.with_suffix(".nfo")
                if nfo_file.exists() and not force:
                    stat = nfo_file.stat()
                    if verbose:
                        click.echo(
                            f"  NFO file..: {nfo_file.name} (size in bytes: {stat.st_size})"
                        )
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
def ls_movies(movie_name):
    """List movies by a partial dir name."""
    for movie_path in MovieManager.iter_movie_dirs(movie_name):
        ls_movie(movie_path)


@main.command()
@click.argument("movie_name", nargs=-1, required=True)
def rm(movie_name: Tuple[str]):
    """Remove a movie directory by a partial dir name."""
    movie_list = [
        str(movie_path) for movie_path in MovieManager.iter_movie_dirs(movie_name)
    ]
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
    "--torrent",
    "-t",
    "for_torrents_only",
    is_flag=True,
    default=False,
    help="Only for Transmission torrents",
)
@click.option("--days", "-d", default=2, type=int, help="Days to consider recent files")
@click.argument("movie_name", nargs=-1, required=False)
def subtitles(for_torrents_only: bool, days: int, movie_name: Tuple[str]):
    """Search subtitles for recent movies."""
    recent_date = datetime.now() - timedelta(days=days)

    found = False
    function = (
        MovieManager.iter_torrent_dirs
        if for_torrents_only
        else MovieManager.iter_movie_dirs
    )
    for movie_dir in function(movie_name):
        if not movie_dir.exists():
            failure(f"Recent torrent, movie dir doesn't exist yet: {movie_dir}")
            continue

        recent_movies = {
            item
            for item in movie_dir.iterdir()
            if item.suffix.lower() in MOVIE_EXTENSIONS
            and datetime.fromtimestamp(item.stat().st_mtime) > recent_date
        }
        if recent_movies:
            found = True
            click.echo()
            shell(f"~/container-apps-private/bin/subtitles.sh '{movie_dir}'")

    if not found:
        failure("No movies found", 1)
