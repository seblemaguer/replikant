# Python
from typing import Callable
import os
import shutil
from pathlib import Path

# Flask related
from werkzeug import Response
from flask import current_app
from flask import redirect as flask_redirect


def copytree(
    src: str, dst: str, dirs_exist_ok: bool = True, ignore: Callable[[str, list[str]], set[str]] | None = None
) -> None:
    """Alternative copytree to the shutils.copytree which is only available in python >= 3.8

    Parameters
    ----------
    src: str
        the source directory
    dst: str
        The target directory
    dirs_exist_ok: bool
        Always True, else ignored!
    ignore:
        This parameter is ignored!
    """
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            copytree(s, d, dirs_exist_ok=dirs_exist_ok, ignore=ignore)
        else:
            from pathlib import Path

            os.makedirs(Path(d).parent, exist_ok=dirs_exist_ok)
            _ = shutil.copyfile(s, d)


def safe_make_dir(directory: str):
    """Make a fresh empty directory

    Parameters
    ----------
    directory: file
        The directory to (re)-create

    Returns
    -------
    str
        The directory path
    """

    if os.path.exists(directory):
        shutil.rmtree(directory)

    os.makedirs(directory)

    return directory


def create_file(file: str):
    """Create an empty file

    Parameters
    ----------
    file: str
        The file to create
    """

    with open(file, "w"):
        pass


def del_file(file: str):
    """Delete a file but don't crash if the file doesn't exist

    Parameters
    ----------
    file: str
        The file to delete
    """

    if os.path.isfile(file):
        os.remove(file)


def make_absolute_path(relative_path: str) -> str:
    """Generate an absolute path based on a relative path and the absolute path of the Replikant instance

    Args:
        relative_path (string): Relative path to a file
    """
    relative_path_object = Path(relative_path)
    if not relative_path_object.exists():
        return str(Path(current_app.config["REPLIKANT_RECIPE_DIR"]).joinpath(relative_path_object))
    else:
        return relative_path


def make_global_url(local_url: str) -> str:
    """Generate global URL from a local URL

    Parameters
    ----------
    local_url: str
        The local (relative) URL

    Returns
    -------
    str
        the global (complete) URL
    """
    return current_app.config["REPLIKANT_RECIPE_URL"] + local_url


def redirect(local_url: str) -> Response:
    """Prepare redirection to the local URL

    Parameters
    ----------
    local_url: str
        The local (relative) URL

    Returns
    -------
    Response
        the flask Response object which if called redirects the client to the target location
    """
    return flask_redirect(make_global_url(local_url))


class AppSingleton(type):
    def __call__(cls, *args, **kwargs):  # type: ignore
        if not (hasattr(current_app, "_appsingleton_instances")):
            current_app._appsingleton_instances = dict()

        if cls not in current_app._appsingleton_instances:  # type: ignore
            current_app._appsingleton_instances[cls] = super(AppSingleton, cls).__call__(  # type: ignore
                *args, **kwargs
            )
        return current_app._appsingleton_instances[cls]  # type: ignore
