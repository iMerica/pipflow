# PipFlow


## Background

Pipflow is built for developers who deploy their Python software using Docker and Cloud Native technologies. When 
building docker images our constraints are:

- The more slim the image, the better.
- The less image layers, the better.
- Don't reinvent the wheel by installing a new package manager in your Dockerfile. These tools tend to use 
  lock files, which are fine in general, but in Docker they are redundant because we already have a way to 
  pin dependencies: Docker image layers.
 

This leave us with one option: Continue to use plain old `pip`, but create some new workflows that improve the 
developer experience.

For example, Pipflow replaces this workflow:


    $ pip3 install <new-package>
    $ pip3 freeze | grep <new-package> >> requirements.txt
    $ docker build ... # (A redudant install)


with this:

    $ pipflow add <package>


## Setup
Install `pipflow` on your *HOST OS only* (macOS, Windows, Linux etc). Do not add Pipflow to your `requirements.txt`.

    pip3 install pipflow

## Usage

Add a new package

    pipflow add <package-name>

Remove a package

    pipflow remove <package-name>
    
Upgrade a package version

    pipflow upgrade <package-name>
    
Upgrade all packages
    
    pipflow upgrade-all
    

Vew all packages eligible for upgrade

    pipflow view-all
    
## License
MIT Copyright (c) 2021 Michael.
