#!/usr/bin/env python
from . import AddCommand
from . import RemoveCommand
from . import UpdateCommand
from . import UpgradeAllCommand
from . import ViewAllUpgradesCommand
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
