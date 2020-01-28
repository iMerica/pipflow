from tempfile import mktemp
from cleo import Command
from shutil import copyfileobj
import requests
from typing import Optional, Union
from distutils.version import LooseVersion
from collections import OrderedDict
from cleo.helpers import Argument
from pathlib import Path
from functools import wraps
import subprocess

__author__ = 'Michael <imichael@pm.me>'


class CommandError(BaseException):
    pass


class PipFlowMixin:

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
                package, version = line.split('==')
                packages[package] = version.rstrip()
        return packages

    @staticmethod
    def get_latest_version(package: str) -> str:
        resp = requests.get(f'https://pypi.org/pypi/{package}/json')
        return resp.json()['info']['version']

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


def rebuild(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        resp = func(self, *args, **kwargs)
        self.rebuild_docker()
        return resp
    return wrapper


class BaseCommand(Command, PipFlowMixin):
    def initiate(self):
        self.original, self.backup = self.perform_backup()

        self.packages = self.requirements_as_dict(self.original)

    def rebuild_docker(self):
        if self.is_compose():
            self.line(f'Rebuilding compose service')
            subprocess.run(["docker-compose", "build"])
        elif self.has_dockerfile():
            self.line('Rebuilding from ./Dockerfile')
            subprocess.run(['docker', 'build', '.'])
        else:
            self.line('No Docker manifests to build from')


class AddCommand(BaseCommand):
    name = 'add'
    help = "Adds a new package to the requirements"
    arguments = [Argument(name='package')]

    @rebuild
    def handle(self) -> Optional[int]:
        self.initiate()
        package = self.argument('package')
        if package in self.packages:
            raise CommandError('Package already in manifest')
        version = self.get_latest_version(package)
        self.packages[package] = version
        self.commit_changes(self.original, self.sort(self.packages))
        self.line(f'{package} added')
        return 0


class RemoveCommand(BaseCommand):
    name = 'remove'
    help = "Removes a new package to the requirements"
    arguments = [Argument(name='package')]

    @rebuild
    def handle(self) -> Optional[int]:
        self.initiate()
        package = self.argument('package')
        del self.packages[package]
        self.commit_changes(self.original, self.sort(self.packages))
        self.line(f'{package} removed')
        return 0


class UpdateCommand(BaseCommand):
    name = 'upgrade'
    help = "Upgrades a package to it's latest version"
    arguments = [Argument(name='package')]

    @rebuild
    def handle(self) -> Optional[int]:
        self.initiate()
        package = self.argument('package')
        original_version = self.packages[package]
        new_version = self.get_latest_version(package)
        self.packages[package] = new_version
        self.commit_changes(self.original, self.sort(self.packages))
        self.line(f'Bumped {package} from {original_version} to {new_version}')
        return 0


class UpgradeAllCommand(BaseCommand):
    name = 'upgrade-all'
    help = "Upgrades all packages to their latest version"

    @rebuild
    def handle(self) -> Optional[int]:
        self.initiate()
        for package, current_version in self.packages.items():
            latest_version = self.get_latest_version(package)
            if LooseVersion(current_version) < LooseVersion(latest_version):
                self.packages[package] = latest_version

        self.commit_changes(self.original, self.sort(self.packages))
        self.line(f'Bumped all packages')
        return 0


class ViewAllUpgradesCommand(BaseCommand):
    name = 'view-all'
    help = 'View available upgrades for all packages'

    def handle(self) -> Optional[int]:
        self.packages = self.requirements_as_dict('requirements.txt')
        table = self.table()
        rows = []
        table.set_header_row(['Package', 'Current', 'Latest'])
        for package, current_version in self.packages.items():
            latest_version = self.get_latest_version(package)
            if LooseVersion(current_version) < LooseVersion(latest_version):
                rows.append([package, current_version, latest_version])
        table.set_rows(rows)
        return table.render(self.io)
