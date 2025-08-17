"""This module defines the content providers.

By content providers, we mean providers which are related to files to be either adapted (templates)
or sent as is (assets).
"""

import sys
import os
import errno
import glob
from pathlib import Path

from flask import abort, current_app, send_from_directory, g, Response

from .base import Provider


py_version = sys.version_info
if (py_version.major >= 3) and (py_version.minor >= 8):
    from shutil import copytree
else:
    from replikant.utils import copytree


class UnknowSourceError(Exception):
    """Wrapping exception for assets whose source is unknown"""

    def __init__(self, path: str, _from: str):
        """Initialisation

        Parameters
        ----------
        path : str
            the path of the assets
        _from : str
            the source type of the asset
        """
        super().__init__()
        self.message = f'Unknown source "{path}/{_from}"'

    def __str__(self) -> str:
        return self.message


class AssetsProvider(Provider):
    """Provider for assets

    Assets are files which will be send as is to the client.
    """

    NAME: str = "assets"
    FORBIDDEN_PATHES = set(["~", "..", ".", "__pycache__"])

    def __init__(self, url_prefix: str):
        """Initialisation method

        Parameters
        ----------
        url_prefix : str
            the URL prefix needed to ensure a valid path resolution of the assets
        """

        super().__init__()

        # Define and setup app url
        self._url_prefix: str = url_prefix
        current_app.add_url_rule(
            self._url_prefix + "/<path:path>",
            self.__class__.__name__ + ":assets:" + self._url_prefix,
            self.get_content,
        )

        # Indicate to the factory that current object is the asset provider
        self._logger.info("Loaded and bound to " + self._url_prefix)

    def local_url(self, path: str, _from: str | None = None) -> str:
        """Local URL generation

        Parameters
        ----------
        path : str
            The path of the assets
        _from : Optional[str]
            the source of the assets (None means it is provided by the core of Replikant!)

        Returns
        -------
        str
            the local URL

        Raises
        ------
        UnknowSourceError
            if the source of the asset can't be resolved

        """

        if path[0] != "/":
            path = "/" + path

        if _from is None:
            return self._url_prefix + path
        elif _from == "replikant":
            return self._url_prefix + "/replikant" + path
        elif _from[:3] == "mod":
            name_mod = _from[4:]
            return self._url_prefix + "/replikant/activities/" + name_mod + path
        else:
            raise UnknowSourceError(path, _from)

    def get_content(self, path: str) -> Response:
        """Retrieve the content of the assets send it to the client

        If the asset path is invalid an HTTP 403 error will be sent.
        If the asset is not found an HTTP 404 error will be sent.
        At the moment no exception is thrown and no specific messages are sent to the client

        Parameters
        ----------
        path : str
            the path of the asset

        Returns
        -------
        Response
            the flask response object containing the asset's content
        """

        # Extract components from the path
        cur_path: Path = Path(path)
        repositories: list[str] = str(cur_path.parent).split("/")  # NOTE: I don't like this, it is dirty
        file: str = cur_path.name

        # Ensure the filename is valid
        if file in AssetsProvider.FORBIDDEN_PATHES:
            abort(403)

        # Assert the repositories are valids
        for repository in repositories:
            if repository in AssetsProvider.FORBIDDEN_PATHES:
                abort(403)

        try:
            try:
                return send_from_directory(
                    current_app.config["REPLIKANT_RECIPE_DIR"] + "/assets/" + "/".join(repositories),
                    file,
                )
            except Exception:
                if repositories[0] == "replikant":
                    try:
                        return send_from_directory(
                            current_app.config["REPLIKANT_DIR"] + "/assets/" + "/".join(repositories[1:]),
                            file,
                        )
                    except Exception:
                        if repositories[1] == "activities":
                            return send_from_directory(
                                current_app.config["REPLIKANT_DIR"]
                                + "/activities/"
                                + repositories[2]
                                + "/assets/"
                                + "/".join(repositories[3:]),
                                file,
                            )
                        else:
                            abort(404)
                else:
                    abort(404)
        except Exception:
            abort(404)


class TemplateImportError(Exception):
    """Wrapping exception of template importing error"""

    pass


class TemplateProvider(Provider):
    """Provider for templates

    Templates are jinja2 files processed to become HTML file to be then sent to the client.
    """

    NAME: str = "templates"

    def __init__(self, folder: str):
        """Initialisation method

        Parameters
        ----------
        folder : str
            The template folder

        Raises
        ------
        TemplateImportError
            if registration of the provider failed


        """
        super().__init__()

        self._instance_files: list[str] = []
        self._folder: Path = Path(folder)
        current_app.template_folder = folder

        try:
            self._register_replikant()
        except Exception:
            raise TemplateImportError("Import from replikant's templates failed.")

        self._logger.info(" loaded and bound to  " + folder)

    def get(self, path: str) -> str:
        """Resolve and validate the path of the template

        Parameters
        ----------
        path : str
            the original path of the template

        Returns
        -------
        str
            the resolved path of the template

        Raises
        ------
        FileNotFoundError
            if the template doesn't exist
        Exception
            if the path of the template is absolute
        """

        self._logger.debug('Getting template "%s"' % path)

        # Ensure that the path is not considered absolute
        if path[0] == "/":
            raise Exception(f"\"{path}\" is invalid, it should not start with the character '/'")

        # Check if the file exists
        if not ((self._folder / path).is_file()):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), self._folder / path)

        return path

    def _register_replikant(self):
        """Register the replikant templates"""

        self._logger.debug(
            "[Core] Copy templates from %s to %s" % (current_app.config["REPLIKANT_DIR"] + "/templates", self._folder)
        )

        copytree(current_app.config["REPLIKANT_DIR"] + "/templates", self._folder, dirs_exist_ok=True)  # type: ignore

    def register_recipe(self):
        """Register the instance templates"""

        self._logger.debug(
            "[Instance] Copy templates from %s to %s"
            % (current_app.config["REPLIKANT_RECIPE_DIR"] + "/templates", self._folder)
        )

        # Save instance templates path to not replace them when registering activities
        tpl_dir: str = current_app.config["REPLIKANT_RECIPE_DIR"] + "/templates"
        self._instance_files = [f.replace(tpl_dir + "/", "") for f in glob.glob(tpl_dir + "/**/*", recursive=True)]
        copytree(tpl_dir, self._folder, dirs_exist_ok=True)  # type: ignore

    def register_scope(self, name: str):
        """Register the templates of a given scope

        Parameters
        ----------
        name : str
            the name of the scope
        """

        def ignore_instance(_: str, names: list[str]):
            return set(names).intersection(set(self._instance_files))

        self._logger.debug(
            "[Scope] Copy templates from %s to %s"
            % (current_app.config["REPLIKANT_DIR"] + "/activities/" + name + "/templates", self._folder)
        )
        copytree(
            current_app.config["REPLIKANT_DIR"] + "/activities/" + name + "/templates",
            str(self._folder),
            dirs_exist_ok=True,
            ignore=ignore_instance,
        )  # type: ignore

        # Fix default
        default_template = self._folder / "default.tpl"
        if default_template.exists():
            default_template.rename(self._folder / f"{name}.tpl")

    def register_admin_unit(self, name: str):
        """Register the templates of a given admin unit

        Parameters
        ----------
        name : str
            the name of the scope
        """

        def ignore_instance(_: str, names: list[str]):
            return set(names).intersection(set(self._instance_files))

        self._logger.debug(
            "[Scope] Copy templates from %s to %s"
            % (current_app.config["REPLIKANT_DIR"] + "/admin_units/" + name + "/templates", self._folder)
        )
        copytree(
            current_app.config["REPLIKANT_DIR"] + "/admin_units/" + name + "/templates",
            str(self._folder),
            dirs_exist_ok=True,
            ignore=ignore_instance,
        )  # type: ignore

        # Fix default
        default_template = self._folder / "default.tpl"
        if default_template.exists():
            default_template.rename(self._folder / f"{name}.tpl")

    def template_loaded(self, rep: str, path: str) -> bool:
        """Determine the template of a given path is already loaded by flask

        Parameters
        ----------
        rep : str
            ????
        path : str
            the path of the template

        Returns
        -------
        bool
            True if the template is loaded, False if it was not (but now it is!)
        """

        if not (hasattr(g, "loaded_template")):
            g.loaded_template = []

        if rep + ":" + path in g.loaded_template:  # type: ignore
            return True
        else:
            g.loaded_template.append(rep + ":" + path)  # type: ignore
            return False
