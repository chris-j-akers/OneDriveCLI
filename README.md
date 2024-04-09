# OneDriveCLI

## Introduction

OneDriveCLI provides an simple command-line interface into consumer Microsoft OneDrives. It permits directory navigation, downloading and uploading files, creating directories and deleting items (moves them to the OneDrive recycle bin).

The application is written in Python.

## Source

The GitHub Repo link is here: https://github.com/chris-j-akers/OneDriveCLI

## Installation

The application can be built and installed by cloning this repo (note the `--recurse` option), the running `make install`:

```
➜ git clone --recurse git@github.com:chris-j-akers/OneDriveCLI.git
➜ make install
```
Note that the installation process will create a sub-directory called `OneDriveCLI` in your `~/.config` directory. This is where a SQLite database is stored. The database is used to persist state and settings.

## Initialisation

Before first use, you must register the app with your Microsoft OneDrive account with the following command:

```
➜ odc init
```
This will open your default web-browser and present you with the Microsoft OneDrive logon page. You will need to logon and accept the access requirements for the application.

![Example of Access Requirements Request](readme-assets/odc-access-request.png)

After logging on, you will be presented with a request to accept the access requirements for the application.

### Revoking App Access

OneDriveCLI's access can be revoked at any time by logging onto your Microsoft 365 Account and selecting: `My Account` -> `Privacy` -> `App Access`.

You should see OneDriveCLI in the list of apps. Select `Don't Allow` to revoke.

![Revoking Access](readme-assets/odc-revoke-access.png)

Alternatively, click `Details` and select `Stop Sharing`

![Stop Sharing](readme-assets/odc-stop-sharing.png)


## Instructions

Running `odc`` without parameters will present a brief summary of the available commands.

```
➜ odc 
----------------------------------------------------------------------------------------------
OneDriveCLI | (C) 2024 Chris Akers | https://github.com/chris-j-akers | https://blog.cakers.io
----------------------------------------------------------------------------------------------
initialise                      : 'odc init'
change directory                : 'odc cd <dir_name>'
list items in current directory : 'odc ls'
get current directory           : 'odc pwd'
make new directory              : 'odc mkdir <remote_path>'
delete item                     : 'odc rm <remote_path>'
get file from current directory : 'odc get <remote_path> [local_path]'
put file to current directory   : 'odc put <local_path> [remote_path]'

* <> = required parameter, [] = optional parameter
----------------------------------------------------------------------------------------------
```
