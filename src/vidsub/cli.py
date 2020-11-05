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
import click

from vidsub import FileManager


@click.command()
@click.option("--dir", "-d", "dir_", type=click.Path(exists=True), help="Working directory")
@click.argument("partial_names", nargs=-1)
def main(dir_, partial_names):
    for video in FileManager(dir_ or "").videos():
        click.echo(video)
