# -*- coding: utf-8 -*-

"""
undo.py - Undo class for the pyRenamer mass file renamer to provide undo
functionality to revert renamed files

Copyright © 2016 Thomas Freeman <tfree87@users.noreply.github.com>
Copyright © 2006-2008 Adolfo González Blázquez <code@infinicode.org>

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 2 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program.  If not, see <http://www.gnu.org/licenses/>.
"""


# Local Imports
from tools import filetools as renamerfilefuncs

class Undo:

    def __init__(self):
        self.undo_memory = []

    def clean(self):
        self.undo_memory = []

    def add(self, original, renamed):
        self.undo_memory.append([original, renamed])

    def undo(self):
        for i in self.undo_memory:
            renamerfilefuncs.rename_file(i[1], i[0])
            print("Undo: %s -> %s" % (i[1] , i[0]))

    def redo(self):
        for i in self.undo_memory:
            renamerfilefuncs.rename_file(i[0], i[1])
            print("Redo: %s -> %s" % (i[0] , i[1]))
