#!/usr/bin/env python
from pipflow.src import AddCommand
from pipflow.src import RemoveCommand
from pipflow.src import UpdateCommand
from pipflow.src import UpgradeAllCommand
from pipflow.src import ViewAllUpgradesCommand

from cleo import Application

application = Application(complete=True)
application.add(AddCommand())
application.add(RemoveCommand())
application.add(UpdateCommand())
application.add(UpgradeAllCommand())
application.add(ViewAllUpgradesCommand())


def main():
    application.run()


if __name__ == '__main__':
    main()
