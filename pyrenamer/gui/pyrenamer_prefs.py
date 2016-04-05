# -*- coding: utf-8 -*-

"""
Copyright (C) 2006-2008 Adolfo González Blázquez <code@infinicode.org>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

If you find any bugs or have any suggestions email: code@infinicode.org
"""

import gi 
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject

import os
from os import path as ospath

from gui import pyrenamer_globals as pyrenamerglob

from gettext import gettext as _
import configparser

class PyrenamerPrefs:

    def __init__(self, main):
        self.main = main
        self.config_path = os.path.join(
            os.path.expanduser('~'),'.config/pyrenamer/pyrenamer.cfg')
        self.config = configparser.ConfigParser()
        if os.path.isfile(self.config_path):
            self.config.read(self.config_path)
        else:
            self.config['DEFAULT'] = {
                'RootDir' : os.path.expanduser('~'),
                'ActiveDir' : os.path.expanduser('~'),
                'OptionsShown' : 'False',
                'FileDir' : '0',
                'Recursive' : 'False',
                'KeepExt' : 'False',
                'AutoPreview' : 'False'
            }

    def create_preferences_dialog(self, glade_file, icon):
        """ Create Preferences dialog and connect signals """
        # Create the window
        gui_objects = [
            'prefs_window',
            'prefs_entry_root',
            'prefs_entry_active',
            'prefs_browse_root',
            'prefs_browse_active',
            'prefs_close'
            ]
        self.builder = Gtk.Builder()
        self.builder.add_objects_from_file(glade_file, gui_objects)

        # Signals
        signals = {
                   "on_prefs_browse_root_clicked": self.on_prefs_browse_root_clicked,
                   "on_prefs_browse_active_clicked": self.on_prefs_browse_active_clicked,
                   "on_prefs_close_clicked": self.on_prefs_close_clicked,
                   "on_prefs_window_destroy": self.on_prefs_destroy,
                   }
        self.builder.connect_signals(signals)

        # Fill in text values for the root and active directories
        root_dir = self.config['DEFAULT']['RootDir']
        active_dir = self.config['DEFAULT']['ActiveDir']
        self.builder.get_object('prefs_entry_root').set_text(root_dir)
        self.builder.get_object('prefs_entry_active').set_text(active_dir)

        # Set prefs window icon
        self.builder.get_object('prefs_window').set_icon_from_file(icon)


    def on_prefs_browse_root_clicked(self, widget):
        """ Browse root clicked """
        f = Gtk.FileChooserDialog(_('Select root directory'),
                                  self.builder.get_object('prefs_window'),
                                  Gtk.FileChooserAction.SELECT_FOLDER,
                                  (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                   Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                                   )
        f.set_current_folder(self.builder.get_object('prefs_entry_root').get_text())
        response = f.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.builder.get_object('prefs_entry_root').set_text(f.get_filename())
        elif response == Gtk.ResponseType.REJECT:
            pass
        f.destroy()


    def on_prefs_browse_active_clicked(self, widget):
        """ Browse active clicked """
        f = Gtk.FileChooserDialog(_('Select active directory'),
                                  self.builder.get_object('prefs_window'),
                                  Gtk.FileChooserAction.SELECT_FOLDER,
                                  (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                   Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                                   )
        f.set_current_folder(self.builder.get_object('prefs_entry_active').get_text())
        response = f.run()
        if response == Gtk.ResponseType.ACCEPT:
            self.builder.get_object('prefs_entry_active').set_text(f.get_filename())
        elif response == Gtk.ResponseType.REJECT:
            pass
        f.destroy()


    def on_prefs_close_clicked(self, widget):
        """ Prefs close button clicked """

        root = self.builder.get_object('prefs_entry_root').get_text()
        active = self.builder.get_object('prefs_entry_active').get_text()
        if root != "" and active != "":
            if not self.check_root_dir(root):
                self.display_error_dialog(_("\nThe root directory is not valid!\nPlease select another directory."))
                self.builder.get_object('prefs_entry_root').set_text('/')
            elif not self.check_active_dir(root, active):
                self.main.display_error_dialog(_("\nThe active directory is not valid!\nPlease select another directory."))
                self.builder.get_object('prefs_entry_active').set_text(root)
            else:
                self.main.root_dir = root
                self.main.active_dir = active
                self.builder.get_object('prefs_window').destroy()
                self.preferences_save()
        else:
            self.main.display_error_dialog(_("\nPlease set both directories!"))
            if root == '': self.builder.get_object(
                    'prefs_entry_root').set_text(self.main.root_dir)
            if active == '': self.builder.get_object(
                    'prefs_entry_active').set_text(self.main.active_dir)


    def on_prefs_destroy(self, widget):
        """ Prefs window destroyed """
        root = self.builder.get_object('prefs_entry_root').get_text()
        active = self.builder.get_object('prefs_entry_active').get_text()
        if root != "" and active != "":
            if not self.check_root_dir(root):
                self.main.display_error_dialog(_(
                    "\nThe root directory is not valid!\nPlease select another directory."))
                self.create_preferences_dialog()
                self.builder.get_object('prefs_entry_root').set_text('/')
            elif not self.check_active_dir(root, active):
                self.main.display_error_dialog(_(
                    "\nThe active directory is not valid!\nPlease select another directory."))
                self.create_preferences_dialog()
                self.builder.get_object('prefs_entry_active').set_text(root)
            else:
                self.main.root_dir = root
                self.main.active_dir = active
                self.builder.get_object('prefs_window').destroy()
                self.preferences_save()
        else:
            self.main.display_error_dialog(_("\nPlease set both directories!"))
            self.create_preferences_dialog()
            if root == '': self.builder.get_object(
                    'prefs_entry_root').set_text(self.main.root_dir)
            if active == '': self.builder.get_object(
                    'prefs_entry_active').set_text(self.main.active_dir)


    def on_add_recursive_toggled(self, widget):
        """ Reload current dir, but with Recursive flag enabled """
        self.main.dir_reload_current()

    def on_filedir_combo_changed(self, combo):
        filedir = combo.get_active()
        self.config['DEFAULT']['FileDir'] = str(filedir)
        self.main.filedir = filedir
        self.main.dir_reload_current()

    def on_extensions_check_toggled(self, check):
        self.config['DEFAULT']['KeepExt'] = str(check.get_active())
        self.main.keepext = check.get_active()

    def on_autopreview_check_toggled(self, check):
        self.main.autopreview = check.get_active()

    def check_root_dir(self, root):
        """ Checks if the root dir is correct """
        return ospath.isdir(ospath.abspath(root))

    def check_active_dir(self, root, active):
        """ Checks if active dir is correct """
        root = ospath.abspath(root)
        active = ospath.abspath(active)
        return ospath.isdir(active) and (root in active)

    def preferences_save(self):
        """ Save preferences to a file using the config_path"""
        print("Saving....")
        directory = os.path.dirname(self.config_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
        with open(self.config_path, 'w+') as configfile:
            self.config.write(configfile)

    def load_preferences(self):
        """Take preferences from the configuration file and load them into the
        main gui"""
        self.main.root_dir = self.config['DEFAULT'].get(
            'RootDir',os.path.expanduser('~'))
        self.main.active_dir = self.config['DEFAULT'].get(
            'ActiveDir',os.path.expanduser('~'))
        self.main.options_shown = self.config['DEFAULT'].getboolean(
            'OptionsShown', False)
        self.main.filedir = self.config['DEFAULT'].getint('FileDir', 0)
        self.main.recursive = self.config['DEFAULT'].getboolean(
            'Recursive', False)
        self.main.keepext = self.config['DEFAULT'].getboolean('KeepExt', False)
        self.main.autopreview = self.config['DEFAULT'].getboolean(
            'AutoPreview', False)
