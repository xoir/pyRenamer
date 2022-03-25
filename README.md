# <img src="images/pyrenamer.png" alt="icon" width="50"/> pyRenamer

pyRenamer is an application with a graphic interface designed for renaming many files at once. It supports renaming files with patterns, substitutions, inserting text, deleting text, or even manually renaming individual files. 

![screenshot](screenshots/screenshot.png)

## Similar Projects
Note: This project is **not** the same as the following projects:
- pyRenamer: https://github.com/lucasbarzan/py-renamer
- pyrename: https://github.com/sgtpepperpt/pyrename

## Requirements
- python3
- python3-gobject-base

## Usage

While pyRenamer is designed to be a graphical program, it can also be called from the command line. Here are the command line options:

```
python3 pyrenamer.py [-h] [-r ROOT_DIR] [-a ACTIVE_DIR]

optional arguments:
  -h, --help            show this help message and exit
  -r ROOT_DIR, --root_dir ROOT_DIR
                        The root directory of the file tree when pyRenamer
                        starts
  -a ACTIVE_DIR, --active_dir ACTIVE_DIR
                        Directory with files to be renamed when pyRenamer
                        starts
```

## About This Repository
pyRenamer has been around for a while and was once a common application in many Linux distributions. A while back, I made this branch as a chance to play around with Python and to update this program that I found so useful. Since then, it appears that much of the pyRenamer code has gone unmaintained so I am making an effort to revive the code and make pyRenamer a useful application once again. I believe pyRenamer still has some value and can be a useful tool for those who want to rename many files and may not be comfortable with command line tools.

## Future
The following items are where I plan to improve pyRenamer:

- Remove all deprecated Gtk+ widgets
- Add docstrings to methods using Numpydoc format
- Reimplement the ability to rename music files with metadata
- Reimplement the ability to rename image files with metadata
