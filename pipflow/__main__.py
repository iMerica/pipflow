#!/usr/bin/env python
from src import AddCommand
from src import RemoveCommand
from src import UpdateCommand
from src import UpgradeAllCommand
from src import ViewAllUpgradesCommand
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
