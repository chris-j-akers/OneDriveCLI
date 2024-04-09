# OneDriveCLI

## Introduction

OneDriveCLI provides an simple command-line interface into consumer Microsoft OneDrives. It permits directory navigation, downloading and uploading files, creating directories and deleting items (moves them to the OneDrive recycle bin).

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

## Instructions

### Initialisation

Before first use, run the following:

```
>odc init
```
This will open your default web-browser and present you with the Microsoft OneDrive logon page. 

After logging on, you will be presented with a request to accept the access requirements for the application.