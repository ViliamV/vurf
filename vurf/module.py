import sys

from pathlib import Path
from typing import Any, Iterable, Optional, Union
import contextlib

from vurf.lib import ensure_config, expand_path
from vurf.parser import parse
from vurf.types import Parameters, Sections


class Vurf:
    def __init__(self) -> None:
        self._config = ensure_config(quiet=True)
        with self.packages_location.open() as f:
            self._root = parse(f)

    def reload(self) -> None:
        """Reload data from disk."""
        self._config = ensure_config(quiet=True)
        with self.packages_location.open() as f:
            self._root = parse(f)

    def save(self) -> None:
        """Save contents to disk."""
        with self.packages_location.open("w") as f:
            f.write(self._root.to_string())

    @property
    def packages_location(self) -> Path:
        return expand_path(self._config.packages_location)

    @property
    def default_section(self) -> str:
        return self._config.default_section

    @property
    def config_sections(self) -> Sections:
        return self._config.sections

    @property
    def config_parameters(self) -> Parameters:
        return self._config.parameters

    def add(self, packages: Union[str, Iterable[str]], section: Optional[str] = None) -> None:
        """
        Adds `packages` to `section`.
        Defaults to `default_section`.
        """
        if isinstance(packages, str):
            packages = [packages]
        for package in packages:
            self._root.add_package(section or self.default_section, package)

    def remove(self, packages: Union[str, Iterable[str]], section: Optional[str] = None) -> None:
        """
        Removes `packages` from `section`.
        Defaults to `default_section`.
        """
        if isinstance(packages, str):
            packages = [packages]
        for package in packages:
            self._root.remove_package(section or self.default_section, package)

    def has(self, package: str, section: Optional[str] = None) -> bool:
        """
        Returns True if `package` is in `section`.
        Defaults to all sections.
        """
        return self._root.has_package(section, package)

    def package_section(self, package: str) -> Optional[str]:
        """
        Returns section of a `package` or `None` if there is none.
        """
        return self._root.get_package_section(package)

    def packages(self, section: Optional[str] = None) -> list[str]:
        """
        Returns list of packages in `section`.
        Defaults to all sections.
        """
        return list(self._root.get_packages(section, self.config_parameters))

    def sections(self) -> list[str]:
        """Returns list of sections."""
        return list(self._root.get_sections())

    def has_section(self, section: str) -> bool:
        """
        Returns True if `section` is in sections.
        """
        return self._root.has_section(section)

    def add_section(self, section: str) -> None:
        """
        Adds new `section`.
        """
        self._root.add_section(section)

    def remove_section(self, section: str) -> None:
        """
        Removes `section` from sections.
        """
        self._root.remove_section(section)

    def install(self, section: Optional[str] = None) -> None:
        """
        Run install commands on packages in `section`.
        Defaults to all sections.
        """
        self._root.install(section, self.config_sections, self.config_parameters)

    def uninstall(self, section: Optional[str] = None) -> None:
        """
        Run uninstall commands on packages in `section`.
        Defaults to all sections.
        """
        self._root.install(section, self.config_sections, self.config_parameters)

    @classmethod
    @contextlib.contextmanager
    def context(cls):
        ''' Convenience method to use Vurf as contextmanager. '''
        instance = cls()
        try:
            yield instance
        except Exception as e:
            args = " ".join(map(str, e.args))
            sys.stderr.write(f"Not saving because an exception occurred:\n{args}\n")
        else:
            instance.save()
