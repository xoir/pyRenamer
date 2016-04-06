pyRenamer
=========

pyRenamer is an application for mass renaming files.

You can rename files using patterns, substitutions,
insert or delete text, or even rename files manually.

pyRenamer is released under the terms of the GNU General Public License.

## Requirements
  * python3
  * python3-gobject-base

## Usage

pyrenamer.py [-h] [-r ROOT_DIR] [-s ACTIVE_DIR]

optional arguments:
  -h, --help            show this help message and exit
  -r ROOT_DIR, --root_dir ROOT_DIR
                        Start pyRenamer with a new root dir
  -s ACTIVE_DIR, --active_dir ACTIVE_DIR
                        Directory to select when pyRenamer starts
## Website
  More info on: http://www.infinicode.org/code/pyrenamer/

##Author
  Adolfo González Blázquez <code@infinicode.org>

## TreeFileBrowser
  pyRenamer uses a widget called treefilebrowser.py, which is a tree-like file browser,
  just like the one on the Nautilus side bar.
  You can see its source code on src/treefilebrowser.py
  There's an example on how to use it on doc/treefilebrowser_example.py
