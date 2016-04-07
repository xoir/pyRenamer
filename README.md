# pyRenamer

pyRenamer is an application for mass renaming files.

You can rename files using patterns, substitutions,
insert or delete text, or even rename files manually.

pyRenamer is released under the terms of the GNU General Public License.

## Requirements
* python3
* python3-gobject-base

## Usage

python3 pyrenamer.py [-h] [-r ROOT_DIR] [-a ACTIVE_DIR]

optional arguments:
  -h, --help            show this help message and exit
  -r ROOT_DIR, --root_dir ROOT_DIR
                        The root directory of the file tree when pyRenamer
                        starts
  -a ACTIVE_DIR, --active_dir ACTIVE_DIR
                        Directory with files to be renamed when pyRenamer
                        starts

## Website
  More info on: http://www.infinicode.org/code/pyrenamer/

##Authors
  Adolfo González Blázquez <code@infinicode.org>
  Thomas Freeman <tfree87@users.noreply.github.com>

## TreeFileBrowser
  pyRenamer uses a widget called treefilebrowser.py, which is a tree-like file browser, just like the one on the Nautilus side bar. You can see its source code on src/treefilebrowser.py. There's an example on how to use it on doc/treefilebrowser_example.py
