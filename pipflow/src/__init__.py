import abc
from simplejson.errors import JSONDecodeError
from tempfile import mktemp
from cleo import Command
from shutil import copyfileobj
import requests
from typing import Optional, Union
from distutils.version import LooseVersion
from collections import OrderedDict
from cleo.helpers import Argument
from pathlib import Path
import subprocess

__author__ = 'Michael <imichael@pm.me>'


class PipFlowMixin:
    errors = []

    @staticmethod
    def perform_backup():
        original = 'requirements.txt'
        backup = mktemp()
        with open(backup, 'w+',) as _out, open(original) as _in:
            copyfileobj(_in, _out)
        return original, backup

    @staticmethod
    def requirements_as_dict(f: Union[bytes, str]) -> OrderedDict:
        packages = OrderedDict()
        with open(f, 'r') as fp:
            for line in fp:
                cleaned_line = line.rstrip()
                if cleaned_line and not cleaned_line.startswith('#'):
                    try:
                        package, version = cleaned_line.split('==')
                        packages[package] = version
                    except (ValueError, TypeError):
                        continue
        return packages

    @staticmethod
    def version_outdated(a, b):
        try:
            return LooseVersion(a) < LooseVersion(b)
        except AttributeError:
            return False

    @staticmethod
    def get_latest_version(package: str) -> Union[str, bool]:
        try:
            resp = requests.get(f'https://pypi.org/pypi/{package}/json')
            return resp.json()['info']['version']
        except (requests.exceptions.RequestException, JSONDecodeError, KeyError):
            return False

    @staticmethod
    def sort(packages: OrderedDict) -> OrderedDict:
        return OrderedDict(
            sorted(packages.items(), key=lambda item: item[0].lower())
        )

    @staticmethod
    def commit_changes(f: Union[bytes, str], packages: OrderedDict) -> None:
        with open(f, 'w+') as f:
            for package, version in packages.items():
                f.write(f'{package}=={version}\n')

    @staticmethod
    def is_compose():
        extensions = ['yaml', 'yml']
        return any(Path(f'docker-compose.{i}').is_file() for i in extensions)

    @staticmethod
    def has_dockerfile():
        return Path('Dockerfile').is_file()


class BaseCommand(Command, PipFlowMixin):
    packages: []
    original: None
    backup: None
    original_packages = None
    errors = []

    @abc.abstractmethod
    def handle(self):
        pass

    def initiate(self):
        self.original, self.backup = self.perform_backup()
        self.original_packages = self.requirements_as_dict(self.original)
        self.packages = self.original_packages

    def updates_available(self):
        return not self.original_packages == self.packages

    def rebuild_docker(self):
        if self.is_compose():
            self.line(f'Rebuilding compose service')
            command = ["docker-compose", "build"]
        elif self.has_dockerfile():
            self.line('Rebuilding from ./Dockerfile')
            command = ['docker', 'build', '.']
        else:
            command = []
            self.line('No Docker manifests to build from')
        if command:
            subprocess.run(command)

    def report_errors(self):
        if self.errors:
            self.line('<error>\nPackages with Errors</error>')
            self.render_table(
                ['Package', 'Value'],
                self.errors
            )
            return 1
        return 0


class AddCommand(BaseCommand):
    name = 'add'
    help = "Adds a new package to the requirements"
    arguments = [Argument(name='package')]

    def handle(self) -> Optional[int]:
        self.initiate()
        package = self.argument('package')
        if package in self.packages:
            self.line('<error>Package Already exists in Manifest</error>')
            return 1
        version = self.get_latest_version(package)
        self.packages[package] = version
        self.line('<info>Package added. Rebuilding in Docker</info>')
        self.commit_changes(self.original, self.sort(self.packages))
        self.rebuild_docker()
        self.line(f'{package} added')
        return 0


class RemoveCommand(BaseCommand):
    name = 'remove'
    help = "Removes a new package to the requirements"
    arguments = [Argument(name='package')]

    def handle(self) -> Optional[int]:
        self.initiate()
        package = self.argument('package')
        try:
            del self.packages[package]
        except KeyError:
            self.line('<error>Package Not Found</error>')
            return 1
        self.commit_changes(self.original, self.sort(self.packages))
        self.line(f'{package} removed')
        return 0


class UpdateCommand(BaseCommand):
    name = 'upgrade'
    help = "Upgrades a package to it's latest version"
    arguments = [Argument(name='package')]

    def handle(self) -> Optional[int]:
        self.initiate()
        package = self.argument('package')
        original_version = self.packages[package]
        new_version = self.get_latest_version(package)
        if self.packages[package] != new_version:
            self.packages[package] = new_version
            self.commit_changes(self.original, self.sort(self.packages))
            self.line(f'Bumped {package} from {original_version} to {new_version}')
        else:
            self.line('<info>Package already current</info>')
        return 0


class UpgradeAllCommand(BaseCommand):
    name = 'upgrade-all'
    help = "Upgrades all packages to their latest version"

    def handle(self) -> Optional[int]:
        self.initiate()
        for package, current_version in self.packages.items():
            latest_version = self.get_latest_version(package)
            if self.version_outdated(current_version, latest_version):
                self.packages[package] = latest_version
        if not self.updates_available():
            self.line('<info>All Packages Current</info>')
            return 0
        self.commit_changes(self.original, self.sort(self.packages))
        self.line(f'Bumped all packages')
        self.rebuild_docker()
        self.report_errors()
        return 0


class ViewAllUpgradesCommand(BaseCommand):
    name = 'view-all'
    help = 'View available upgrades for all packages'

    def handle(self) -> Optional[int]:
        self.packages = self.requirements_as_dict('requirements.txt')
        rows = []
        for package, current_version in self.packages.items():
            latest_version = self.get_latest_version(package)
            if not latest_version:
                self.errors.append([package, current_version])
            if latest_version and self.version_outdated(current_version, latest_version):
                rows.append([package, current_version, latest_version])
        if rows:
            self.line('<info>Outdated Packages</info>')
            self.render_table(
                ['Package', 'Current', 'Latest'],
                rows,
            )
        else:
            self.line('<info>All Packages Current</info>')
        self.report_errors()
        return 0


