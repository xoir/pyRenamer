# -*- coding: utf-8 -*-

"""
Copyright (C) 2006-2008, 2016 Adolfo González Blázquez <code@infinicode.org>

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

import argparse
import gi 
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import GObject
from gi.repository import GdkPixbuf
import threading
import os
from os import path as ospath
from os.path import dirname
import locale
import gettext

# Local Imports
from treefilebrowser import treefilebrowser
from tools import filetools as renamerfilefuncs
from gui import pyrenamer_globals as pyrenamerglob
from gui import pyrenamer_prefs
from gui import pyrenamer_pattern_editor
from gui import menu as pyrenamer_menu_cb
from gui import pyrenamer_undo


from gettext import gettext as _
gettext.bindtextdomain(pyrenamerglob.name, pyrenamerglob.locale_dir)
gettext.textdomain(pyrenamerglob.name)


class pyRenamer:

    def __init__(self, root_dir=None, active_dir=None):

        self.name = "pyRenamer"
        self.version = 0.6
        self.menu_cb = pyrenamer_menu_cb.PyrenamerMenuCB(self)
        self.project_dir = dirname(dirname(os.path.abspath(__file__)))
        self.glade_file = ospath.join(self.project_dir, 'glade/pyrenamer.ui')
        self.icon = ospath.join(self.project_dir, 'images/pyrenamer.png')

        # Main variables
        self.count = 0
        self.populate_id = []
        self.listing = []
        self.listing_thread = None
        self.ignore_errors = False

        # Patterns saving variables
        self.patterns = {}
        self.patterns_default = {
            "main_ori": "",
            "main_dest": ""
        }
        
        # Directories variables
        self.home = os.path.expanduser('~')
        self.root_dir = '/'
        self.active_dir = self.home

        # Options
        self.options_shown = False
        self.filedir = 0        # 0: Files; 1: Dirs; 2: Both
        self.keepext = False
        self.autopreview = False

        # Read preferences
        self.prefs = pyrenamer_prefs.PyrenamerPrefs(self)
        self.prefs.load_preferences()

        # Read GUI data from XML
        gui_objects = [
            'uimanager1',
            'model1',
            'model2',
            'model3',
            'adjustment1',
            'adjustment2',
            'adjustment3',
            'main_window',
            'main_hpaned',
            'statusbar',
            'notebook',
            'clear_button',
            'preview_button',
            'rename_button',
            'original_pattern',
            'original_pattern_combo',
            'renamed_pattern',
            'renamed_pattern_combo',
            'subs_spaces',
            'subs_capitalization',
            'subs_spaces_combo',
            'subs_capitalization_combo',
            'subs_replace',
            'subs_replace_orig',
            'subs_replace_new',
            'subs_replace_label',
            'subs_accents',
            'subs_duplicated',
            'insert_radio',
            'insert_entry',
            'insert_pos',
            'insert_end',
            'delete_radio',
            'delete_from',
            'delete_to',
            'manual',
            'menu_clear_preview',
            'menu_rename',
            'menu_show_options',
            'menu_undo',
            'menu_redo',
            ]
            
        self.builder = Gtk.Builder()
        self.builder.add_objects_from_file(self.glade_file, gui_objects)
        self.initialize_defaults()
        if root_dir != None:
            self.root_dir = root_dir
        if active_dir != None:
            self.active_dir = active_dir
        
        # Create selected files treeview
        self.selected_files, selected_files_scrolled = self.create_selected_files_treeview()

        self.statusbar_context = self.builder.get_object('statusbar').get_context_id("file_renamer")
        
        # Get defined signals
        signals = { "on_main_window_destroy": self.on_main_quit,
                    "on_main_window_window_state_event": self.on_main_window_window_state_event,
                    "on_main_window_configure_event": self.on_main_window_configure_event,
                    "on_main_hpaned_notify": self.on_main_hpaned_notify,
                    "on_manual_changed": self.on_manual_changed,
                    "on_file_pattern_changed": self.on_file_pattern_changed,
                    "on_original_pattern_changed": self.on_original_pattern_changed,
                    "on_renamed_pattern_changed": self.on_renamed_pattern_changed,
                    "on_pattern_ori_save_clicked": self.on_pattern_ori_save_clicked,
                    "on_pattern_ori_edit_clicked": self.on_pattern_ori_edit_clicked,
                    "on_pattern_dest_save_clicked": self.on_pattern_dest_save_clicked,
                    "on_pattern_dest_edit_clicked": self.on_pattern_dest_edit_clicked,
                    "on_original_pattern_combo_changed": self.on_original_pattern_combo_changed,
                    "on_renamed_pattern_combo_changed": self.on_renamed_pattern_combo_changed,
                    "on_preview_button_clicked": self.on_preview_button_clicked,
                    "on_clean_button_clicked": self.on_clean_button_clicked,
                    "on_rename_button_clicked": self.on_rename_button_clicked,
                    "on_exit_button_clicked": self.on_main_quit,
                    "on_options_button_clicked": self.on_options_button_clicked,
                    "on_add_recursive_toggled": self.prefs.on_add_recursive_toggled,
                    "on_filedir_combo_changed": self.prefs.on_filedir_combo_changed,
                    "on_extensions_check_toggled": self.prefs.on_extensions_check_toggled,
                    "on_autopreview_check_toggled": self.prefs.on_autopreview_check_toggled,
                    "on_menu_preview_activate": self.on_preview_button_clicked,
                    "on_menu_rename_activate": self.on_rename_button_clicked,
                    "on_menu_load_names_from_file_activate": self.on_menu_load_names_from_file_activate,
                    "on_menu_clear_preview_activate": self.on_clean_button_clicked,
                    "on_menu_undo_activate": self.menu_cb.on_menu_undo_activate,
                    "on_menu_redo_activate": self.menu_cb.on_menu_redo_activate,
                    "on_cut_activate": self.on_cut_activate,
                    "on_copy_activate": self.on_copy_activate,
                    "on_paste_activate": self.on_paste_activate,
                    "on_clear_activate": self.on_clear_activate,
                    "on_select_all_activate": self.on_select_all_activate,
                    "on_select_nothing_activate": self.on_select_nothing_activate,
                    "on_preferences_activate": self.on_preferences_activate,
                    "on_menu_refresh_activate": self.menu_cb.on_menu_refresh_activate,
                    "on_menu_patterns_activate": self.menu_cb.on_menu_patterns_activate,
                    "on_menu_show_options_activate": self.menu_cb.on_menu_show_options_activate,
                    "on_menu_substitutions_activate": self.menu_cb.on_menu_substitutions_activate,
                    "on_menu_insert_activate": self.menu_cb.on_menu_insert_activate,
                    "on_menu_manual_activate": self.menu_cb.on_menu_manual_activate,
                    "on_subs_spaces_toggled": self.on_subs_spaces_toggled,
                    "on_subs_capitalization_toggled": self.on_subs_capitalization_toggled,
                    "on_subs_spaces_combo_changed": self.on_subs_spaces_combo_changed,
                    "on_subs_capitalization_combo_changed": self.on_subs_capitalization_combo_changed,
                    "on_subs_replace_toggled": self.on_subs_replace_toggled,
                    "on_subs_replace_orig_changed": self.on_subs_replace_orig_changed,
                    "on_subs_replace_new_changed": self.on_subs_replace_new_changed,
                    "on_subs_accents_toggled": self.on_subs_accents_toggled,
                    "on_subs_duplicated_toggled": self.on_subs_duplicated_toggled,
                    "on_insert_radio_toggled": self.on_insert_radio_toggled,
                    "on_insert_entry_changed": self.on_insert_entry_changed,
                    "on_insert_pos_changed": self.on_insert_pos_changed,
                    "on_insert_end_toggled": self.on_insert_end_toggled,
                    "on_delete_radio_toggled": self.on_delete_radio_toggled,
                    "on_delete_from_changed": self.on_delete_from_changed,
                    "on_delete_to_changed": self.on_delete_to_changed,
                    "on_menu_quit_activate": self.on_main_quit,
                    "on_menu_about_activate": self.about_info,
                    "on_notebook_switch_page": self.on_notebook_switch_page,
                    "on_manual_key_press_event": self.on_manual_key_press_event,
                    "on_quit_button_clicked": self.on_main_quit }
        self.builder.connect_signals(signals)

        # Create ProgressBar and add it to the StatusBar. Add also a Stop icon
        self.progressbar = Gtk.ProgressBar()
        self.progressbar.set_pulse_step(0.01)
        self.progressbar.set_size_request(-1,14)
        self.progressbar_vbox = Gtk.VBox()
        self.progressbar_vbox.pack_start(self.progressbar, True, 0, 0)
        self.progressbar_vbox.set_homogeneous(True)
        self.stop_button = Gtk.Button()
        self.stop_button.set_relief(Gtk.ReliefStyle.NONE)

        stop_image = Gtk.Image()
        stop_image.set_from_file(os.path.join(self.project_dir, 'images/stop.png'))
        
        self.stop_button.connect("clicked", self.on_stop_button_clicked)
        self.stop_button.set_image(stop_image)

        self.builder.get_object('statusbar').pack_start(self.stop_button,True,0,0)
        self.builder.get_object('statusbar').pack_start(self.progressbar_vbox,True,0,0)
        self.builder.get_object('statusbar').set_size_request(-1,20)
        self.builder.get_object('statusbar').show_all()
        self.stop_button.hide()

        # Init main window
        self.builder.get_object('main_window').set_title('pyRenamer')
        self.builder.get_object('main_window').set_has_resize_grip(True)
        self.builder.get_object('main_window').set_icon_from_file()
        
        # Init TreeFileBrowser
        self.file_browser = treefilebrowser.TreeFileBrowser(self.root_dir)
        self.file_browser_view = self.file_browser.get_view()
        file_browser_scrolled = self.file_browser.get_scrolled()
        signal = self.file_browser.connect("cursor-changed", self.dir_selected)

        # Add dirs and files tomain window
        self.builder.get_object('main_hpaned').pack1(file_browser_scrolled, resize=True, shrink=False)
        self.builder.get_object('main_hpaned').pack2(selected_files_scrolled, resize=True, shrink=False)

        # Create model and add dirs
        self.create_model()

        #  Set cursor on selected dir
        try:
            # Check if the dir is hidden
            if "/." in (self.active_dir or self.root_dir):
                self.file_browser.set_show_hidden(True)
                
            # Check if paths are correct
            if not self.file_browser.check_active_dir(self.active_dir):
                self.active_dir = self.home
                if not self.file_browser.check_active_dir(self.active_dir):
                    self.active_dir = self.root_dir
        except:
            self.active_dir = self.home
        self.file_browser.set_active_dir(self.active_dir)

        # # Init comboboxes
        self.builder.get_object('subs_spaces_combo').set_active(0)
        self.builder.get_object('subs_capitalization_combo').set_active(0)

        # # Init some menu items
        self.builder.get_object('menu_rename').set_sensitive(False)
        self.builder.get_object('menu_clear_preview').set_sensitive(False)

        # # Init delete radio buttons
        self.builder.get_object('delete_from').set_sensitive(False)
        self.builder.get_object('delete_to').set_sensitive(False)

        # # Init pattern comboboxes
        self.populate_pattern_combos()

        # # Init the undo/redo manager
        self.undo_manager = pyrenamer_undo.PyrenamerUndo()
        self.builder.get_object('menu_undo').set_sensitive(False)
        self.builder.get_object('menu_redo').set_sensitive(False)

    def create_selected_files_treeview(self):
        """ Create the TreeView and the ScrolledWindow for the selected files """
        view = Gtk.TreeView()
        view.set_headers_visible(True)
        view.set_enable_search(True)
        view.set_reorderable(False)
        view.set_rules_hint(True)
        view.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        view.connect("cursor-changed", self.on_selected_files_cursor_changed)

        # Create scrollbars around the view
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        scrolled.add(view)
        scrolled.show()

        return view, scrolled

    def create_model(self):
        """ Create the model to hold the needed data
        Model = [file, /path/to/file, newfilename, /path/to/newfilename] """
        self.file_selected_model = Gtk.TreeStore(str, str, str, str, GdkPixbuf.Pixbuf)
        self.selected_files.set_model(self.file_selected_model)

        renderer0 = Gtk.CellRendererPixbuf()
        column0 = Gtk.TreeViewColumn('', renderer0, pixbuf=4)
        self.selected_files.append_column(column0)

        renderer1 = Gtk.CellRendererText()
        column1 = Gtk.TreeViewColumn("Original file name", renderer1, text=0)
        self.selected_files.append_column(column1)

        renderer2 = Gtk.CellRendererText()
        column2 = Gtk.TreeViewColumn("Renamed file name", renderer2, text=2)
        self.column_preview = column2
        self.selected_files.append_column(column2)

        self.selected_files.show()


    def rename_rows(self, model, path, iter, user_data):
        """ This function is called by foreach to rename files on every row """
        ori = model.get_value(iter, 1)
        new = model.get_value(iter, 3)

        if new != None and new != '':
            result, error = renamerfilefuncs.rename_file(ori, new)
            if not result:
                if not self.ignore_errors:
                    self.display_error_dialog(_("Could not rename file %s to %s\n%s") % (ori, new, error))
            else:
                self.undo_manager.add(ori, new)


    def preview_rename_rows(self, model, path, iter, paths):
        """ Called when Preview button is clicked.
        Get new names and paths and add it to the model """

        if (paths != None) and (path not in paths) and (paths != []):
            # Preview only selected rows (if we're not on manual rename)
            return

        # Get current values
        name = model.get_value(iter, 0)
        path = model.get_value(iter, 1)
        newname = name
        newpath = path

        # Keep extension (not valid on manual rename!)
        if self.keepext and self.builder.get_object('notebook').get_current_page() != 3:
            ename, epath, ext = renamerfilefuncs.cut_extension(newname, newpath)
            if ext != '':
                newname = ename
                newpath = epath

        if self.builder.get_object('notebook').get_current_page() == 0:
            # Replace using patterns
            pattern_ini = self.builder.get_object('original_pattern').get_text()
            pattern_end = self.builder.get_object('renamed_pattern').get_text()
            newname, newpath = renamerfilefuncs.rename_using_patterns(newname, newpath, pattern_ini, pattern_end, self.count)

        elif self.builder.get_object('notebook').get_current_page() == 1:
            # Replace spaces
            if self.builder.get_object('subs_spaces').get_active() and newname != None:
                newname, newpath = renamerfilefuncs.replace_spaces(newname, newpath, self.builder.get_object('subs_spaces_combo').get_active())

            # Replace orig with new
            if self.builder.get_object('subs_replace').get_active() and newname != None:
                orig = self.builder.get_object('subs_replace_orig').get_text()
                new = self.builder.get_object('subs_replace_new').get_text()
                newname, newpath = renamerfilefuncs.replace_with(newname, newpath, orig, new)

            # Replace capitalization
            if self.builder.get_object('subs_capitalization').get_active() and newname != None:
                newname, newpath = renamerfilefuncs.replace_capitalization(newname, newpath, self.builder.get_object('subs_capitalization_combo').get_active())

            # Replace accents
            if self.builder.get_object('subs_accents').get_active() and newname != None:
                newname, newpath = renamerfilefuncs.replace_accents(newname, newpath)

            # Fix duplicated symbols
            if self.builder.get_object('subs_duplicated').get_active() and newname != None:
                newname, newpath = renamerfilefuncs.replace_duplicated(newname, newpath)

        elif self.builder.get_object('notebook').get_current_page() == 2:
            # Insert / delete
            if self.insert_radio.get_active():
                text = self.builder.get_object('insert_entry').get_text()
                if text != "":
                    if self.builder.get_object('insert_end').get_active():
                        pos = None
                    else:
                        pos = int(self.builder.get_object('insert_pos').get_value())-1
                    newname, newpath = renamerfilefuncs.insert_at(newname, newpath, text, pos)
            elif self.delete_radio.get_active():
                ini = int(self.builder.get_object('delete_from').get_value())-1
                to = int(self.builder.get_object('delete_to').get_value())-1
                newname, newpath = renamerfilefuncs.delete_from(newname, newpath, ini, to)

        elif self.builder.get_object('notebook').get_current_page() == 3:
            # Manual rename
            self.selected_files.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
            nmodel, niter = self.selected_files.get_selection().get_selected()
            if niter != None:
                if nmodel.get_value(niter,0) == name:
                    newname = self.builder.get_object('manual').get_text()
                    newpath = renamerfilefuncs.get_new_path(newname, path)
                else:
                    newname = model.get_value(iter, 2)
                    newpath = model.get_value(iter, 3)
            self.selected_files.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

            
        # Add the kept extension
        if self.keepext and self.builder.get_object('notebook').get_current_page() != 3 and (newname and newpath) != '':
            if ext != '': newname, newpath = renamerfilefuncs.add_extension(newname, newpath, ext)

        # Set new values on model
        if newname != '' and newname != None:
            model.set_value(iter, 2, newname)
            model.set_value(iter, 3, newpath)
        else:
            model.set_value(iter, 2, None)
            model.set_value(iter, 3, None)
        self.count += 1


    def preview_selected_row(self):
        """ Preview just selected row """

        # Get values of current row
        model, iter = self.selected_files.get_selection().get_selected()
        name = model.get_value(iter, 0)
        path = model.get_value(iter, 1)
        if iter != None:
            newname = self.builder.get_object('manual').get_text()
            if newname != name:
                newpath = renamerfilefuncs.get_new_path(newname, path)
            else:
                newname = None
                newpath = None

         # Set new values on model
        if newname != '' and newname != None:
            model.set_value(iter, 2, newname)
            model.set_value(iter, 3, newpath)
        else:
            model.set_value(iter, 2, None)
            model.set_value(iter, 3, None)
        self.count += 1


    def preview_clear(self, model, path, iter, paths):
        """ Clean a row """

        if (paths != None) and (path not in paths) and (paths != []):
            return

        model.set_value(iter, 2, None)
        model.set_value(iter, 3, None)


    def enable_rename_and_clean(self, model, path, iter):
        """ Check if the rename button and menu should be enabled """
        val = model.get_value(iter, 2) != None
        if path[0] > 0:
            prev = self.builder.get_object('rename_button').get_property("sensitive")
        else:
            prev = False

        self.builder.get_object('rename_button').set_sensitive(val or prev)
        self.builder.get_object('menu_rename').set_sensitive(val or prev)
        self.builder.get_object('clear_button').set_sensitive(val or prev)
        self.builder.get_object('menu_clear_preview').set_sensitive(val or prev)

        return False


#---------------------------------------------------------------------------------------
# Callbacks


    def on_selected_files_cursor_changed(self, treeview):
        """ Clicked a file """

        if self.builder.get_object('notebook').get_current_page() == 3:
            # Manual rename
            try:
                self.selected_files.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
                model, iter = treeview.get_selection().get_selected()
                name = model.get_value(iter,0)
                newname = model.get_value(iter,2)
                if newname != None:
                    self.builder.get_object('manual').set_text(newname)
                else:
                    self.builder.get_object('manual').set_text(name)
            except: pass


    def on_stop_button_clicked(self, widget):
        """ The stop button on Statusbar.
        Stop adding items to the selected files list and show information on statusbar """
        self.populate_stop()


    def on_main_window_window_state_event(self, window, event):
        """ Thrown when window is maximized or demaximized """
        if event.changed_mask & Gdk.WindowState.MAXIMIZED:
            if event.new_window_state & Gdk.WindowState.MAXIMIZED:
                self.window_maximized = True
                self.builder.get_object('main_window').set_has_resize_grip(False)
            else:
                self.window_maximized = False
                self.builder.get_object('main_window').set_has_resize_grip(True)


    def on_main_window_configure_event(self, window, event):
        """ Saving window size to avoid losing data when it gets destroyed """
        self.window_width, self.window_height = self.builder.get_object("main_window").get_size()
        self.window_posx, self.window_posy = self.builder.get_object("main_window").get_position()


    def on_rename_button_clicked(self, widget):
        """ For everyrow rename the files as requested """

        self.undo_manager.clean()
        self.builder.get_object('menu_undo').set_sensitive(True)
        self.builder.get_object('menu_redo').set_sensitive(False)
        self.file_selected_model.foreach(self.rename_rows, None)
        self.dir_reload_current()
        self.builder.get_object('clear_button').set_sensitive(False)
        self.builder.get_object('menu_clear_preview').set_sensitive(False)
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        self.ignore_errors = False


    def on_preview_button_clicked(self, widget):
        """ Set the item count to zero and get new names and paths for files on model """
        self.count = 0

        # Get selected rows and execute rename function
        model, paths = self.selected_files.get_selection().get_selected_rows()
        self.file_selected_model.foreach(self.preview_rename_rows, paths)

        self.selected_files.columns_autosize()
        self.builder.get_object('clear_button').set_sensitive(True)
        self.builder.get_object('menu_clear_preview').set_sensitive(True)
        self.builder.get_object('rename_button').set_sensitive(True)
        self.builder.get_object('menu_rename').set_sensitive(True)
        self.file_selected_model.foreach(self.enable_rename_and_clean)


    def on_clean_button_clicked(self, widget):
        """ Clean the previewed filenames """
        self.count = 0

        # Clean selected rows
        model, paths = self.selected_files.get_selection().get_selected_rows()
        self.file_selected_model.foreach(self.preview_clear, paths)

        self.file_selected_model.foreach(self.enable_rename_and_clean)

        self.selected_files.columns_autosize()

        if self.builder.get_object('notebook').get_current_page() == 3:
            # Manual rename
            try:
                self.selected_files.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
                model, iter = self.selected_files.get_selection().get_selected()
                name = model.get_value(iter,0)
                newname = model.get_value(iter,2)
                if newname != None:
                    self.builder.get_object('manual').set_text(newname)
                else:
                    self.builder.get_object('manual').set_text(name)
            except:
                pass


    def on_main_hpaned_notify(self, pane, gparamspec):
        if gparamspec.name == 'position':
            self.pane_position = pane.get_property('position')

    def on_options_button_clicked(self, widget):
        self.options_panel_state(not self.options_shown)

    def options_panel_state(self, state):

        if state:
            self.builder.get_object('options_vbox').show()
            self.builder.get_object('options_label').show()
            icon = self.builder.get_object('options_button').get_child()
            icon.set_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
        else:
            self.builder.get_object('options_vbox').hide()
            self.builder.get_object('options_label').hide()
            icon = self.builder.get_object('options_button').get_child()
            icon.set_from_stock(Gtk.STOCK_PREFERENCES, Gtk.IconSize.MENU)

        self.options_shown = state
        self.builder.get_object('menu_show_options').set_active(state)


    def on_file_pattern_changed(self, widget):
        """ Reload the current dir 'cause we need it """
        self.dir_reload_current()


    def on_original_pattern_changed(self, widget):
        """ Reload current dir and disable Rename button """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_renamed_pattern_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_spaces_toggled(self, widget):
        """ Enable/Disable spaces combo """
        self.builder.get_object('subs_spaces_combo').set_sensitive(widget.get_active())
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_capitalization_toggled(self, widget):
        """ Enable/Disable caps combo """
        self.builder.get_object('subs_capitalization_combo').set_sensitive(widget.get_active())
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_replace_toggled(self, widget):
        """ Enable/Disable replace with text entries """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        self.builder.get_object('subs_replace_new').set_sensitive(widget.get_active())
        self.builder.get_object('subs_replace_orig').set_sensitive(widget.get_active())
        self.builder.get_object('subs_replace_label').set_sensitive(widget.get_active())
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_spaces_combo_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_capitalization_combo_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_replace_orig_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_replace_new_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_subs_accents_toggled(self, widget):
        """ Enable/Disable accents """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)

    def on_subs_duplicated_toggled(self, widget):
        """ Fixes duplicated symbols """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_insert_radio_toggled(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        self.builder.get_object('insert_entry').set_sensitive(True)
        self.builder.get_object('insert_pos').set_sensitive(True)
        self.builder.get_object('insert_end').set_sensitive(True)
        self.builder.get_object('delete_from').set_sensitive(False)
        self.builder.get_object('delete_to').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_insert_entry_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_insert_pos_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_insert_end_toggled(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        self.builder.get_object('insert_pos').set_sensitive(not self.builder.get_object('insert_end').get_active())
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_delete_radio_toggled(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        self.builder.get_object('delete_from').set_sensitive(True)
        self.builder.get_object('delete_to').set_sensitive(True)
        self.builder.get_object('insert_entry').set_sensitive(False)
        self.builder.get_object('insert_pos').set_sensitive(False)
        self.builder.get_object('insert_end').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_delete_from_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.builder.get_object('delete_from').get_value() > self.builder.get_object('delete_to').get_value():
            self.builder.get_object('delete_from').set_value(self.builder.get_object('delete_to').get_value())
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def on_delete_to_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.builder.get_object('delete_to').get_value() < self.builder.get_object('delete_from').get_value():
            self.builder.get_object('delete_to').set_value(self.builder.get_object('delete_from').get_value())
        if self.autopreview:
            self.on_preview_button_clicked(None)

    def on_manual_changed(self, widget):
        """ Disable Rename button (user has to click on Preview again) """
        self.builder.get_object('rename_button').set_sensitive(False)
        self.builder.get_object('menu_rename').set_sensitive(False)
        if self.autopreview:
            self.on_preview_button_clicked(None)


    def populate_pattern_combos(self):
        """ Populate pattern combo boxes """

        # Clear 'em all first
        self.patterns = {}
        self.builder.get_object('original_pattern_combo').get_model().clear()
        self.builder.get_object('renamed_pattern_combo').get_model().clear()

        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        main_ori = pe.get_patterns('main_ori')
        main_dest = pe.get_patterns('main_dest')

        
        def set_combo_element(combo, newtext):
            pos = 0
            try:
                model = combo.get_model()
                iter = model.get_iter_first()
                elem = model.get_value(iter, 0)

                while elem != newtext:
                    iter = model.iter_next(iter)
                    elem = model.get_value(iter, 0)
                    pos += 1
            except:
                pos = -1

            text = combo.get_active_text()
            if pos >= 0:
                combo.set_active(pos)
            elif text == '':
                combo.set_active(0)
            else:
                # Figure out what text to place here
                combo.get_child().set_text('TEXT')


        # Main original
        for p in main_ori:
            self.builder.get_object('original_pattern_combo').append_text(p)
        set_combo_element(self.builder.get_object('original_pattern_combo'), self.patterns_default["main_ori"])
        self.patterns["main_ori"] = main_ori

        # Main renamed
        for p in main_dest:
            self.builder.get_object('renamed_pattern_combo').append_text(p)
        set_combo_element(self.builder.get_object('renamed_pattern_combo'), self.patterns_default["main_dest"])
        self.patterns["main_dest"] = main_dest


    def on_pattern_ori_save_clicked(self, widget):

        # Get the pattern value
        text = self.builder.get_object('original_pattern').get_text()

        # Add it to the local file
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.add_pattern('main_ori', text)

        # Add it to the variable
        patterns = self.patterns["main_ori"]
        patterns.append(text)
        self.patterns["main_ori"] = patterns

        # And show it on combobox
        self.builder.get_object('original_pattern_combo').append_text(text)


    def on_pattern_ori_edit_clicked(self, widget):
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.create_window('main_ori')


    def on_pattern_dest_save_clicked(self, widget):

        # Get the pattern value
        text = self.builder.get_object('renamed_pattern').get_text()

        # Add it to the local file
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.add_pattern('main_dest', text)

        # Add it to the variable
        patterns = self.patterns["main_dest"]
        patterns.append(text)
        self.patterns["main_dest"] = patterns

        # And show it on combobox
        self.builder.get_object('renamed_pattern_combo').append_text(text)


    def on_pattern_dest_edit_clicked(self, widget):
        pe = pyrenamer_pattern_editor.PyrenamerPatternEditor(self)
        pe.create_window('main_dest')


    def on_original_pattern_combo_changed (self, widget):
        text = widget.get_active_text()
        self.patterns_default["main_ori"] = text


    def on_renamed_pattern_combo_changed (self, widget):
        text = widget.get_active_text()
        self.patterns_default["main_dest"] = text


    def on_notebook_switch_page(self, notebook, page, page_num):
        """ Tab changed """
        if page_num != 3:
            self.selected_files.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)

        else:
            # Manual rename
            try:
                self.selected_files.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
                model, iter = self.selected_files.get_selection().get_selected()
                name = model.get_value(iter,0)
                newname = model.get_value(iter,2)
                if newname != None:
                    self.builder.get_object('manual').set_text(newname)
                else:
                    self.builder.get_object('manual').set_text(name)
            except: pass


    def on_copy_activate(self, widget):
        """ Copy to clipboard """
        w = self.builder.get_object('main_window').get_focus()
        if isinstance(w, Gtk.Entry):
            w.emit('copy-clipboard')


    def on_paste_activate(self, widget):
        """ Paste from clipboard """
        w = self.builder.get_object('main_window').get_focus()
        if isinstance(w, Gtk.Entry):
            w.emit('paste-clipboard')


    def on_cut_activate(self, widget):
        """ Cut to clipboard """
        w = self.builder.get_object('main_window').get_focus()
        if isinstance(w, Gtk.Entry):
            w.emit('cut-clipboard')


    def on_clear_activate(self, widget):
        """ Clear text widget """
        w = self.builder.get_object('main_window').get_focus()
        if isinstance(w, Gtk.Entry):
            w.set_text('')


    def on_select_all_activate(self, widget):
        """ Select every row on selected-files treeview """
        if self.builder.get_object('notebook').get_current_page() == 3:
            self.selected_files.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.selected_files.get_selection().select_all()


    def on_select_nothing_activate(self, widget):
        """ Select nothing on selected-files treeview """
        if self.builder.get_object('notebook').get_current_page() == 3:
            self.selected_files.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.selected_files.get_selection().unselect_all()


    def on_preferences_activate(self, widget):
        """ Preferences menu item clicked """
        self.prefs.create_preferences_dialog(self.glade_file, self.icon)


    def on_manual_key_press_event(self, widget, event):
        """ Key pressed on manual rename entry """

        if self.builder.get_object('notebook').get_current_page() == 3:
            self.selected_files.get_selection().set_mode(Gtk.SelectionMode.SINGLE)
            if event.keyval == Gdk.KEY_Page_Up:
                try:
                    self.preview_selected_row()
                    self.file_selected_model.foreach(self.enable_rename_and_clean)
                    model, iter = self.selected_files.get_selection().get_selected()
                    path = model.get_path(iter)
                    path = path[0]-1
                    if path < 0: return
                    iter = model.get_iter(path)
                    name = model.get_value(iter,0)
                    self.selected_files.get_selection().select_iter(iter)
                    self.builder.get_object('manual').handler_block(self.manual_signal)
                    self.selected_files.scroll_to_cell(path)
                    self.on_selected_files_cursor_changed(self.selected_files)
                    self.builder.get_object('manual').handler_unblock(self.manual_signal)
                except:
                    pass
            elif event.keyval == Gdk.KEY_Page_Down:
                try:
                    self.preview_selected_row()
                    self.file_selected_model.foreach(self.enable_rename_and_clean)
                    model, iter = self.selected_files.get_selection().get_selected()
                    iter = model.iter_next(iter)
                    if iter == None: return
                    path = model.get_path(iter)
                    name = model.get_value(iter,0)
                    self.selected_files.get_selection().select_iter(iter)
                    self.builder.get_object('manual').handler_block(self.manual_signal)
                    self.selected_files.scroll_to_cell(path)
                    self.on_selected_files_cursor_changed(self.selected_files)
                    self.builder.get_object('manual').handler_unblock(self.manual_signal)
                except:
                    pass
            elif event.keyval == Gdk.KEY_Return:
                try:
                    self.preview_selected_row()
                    self.file_selected_model.foreach(self.enable_rename_and_clean)
                    model, iter = self.selected_files.get_selection().get_selected()
                    iter = model.iter_next(iter)
                    if iter == None: return
                    path = model.get_path(iter)
                    name = model.get_value(iter,0)
                    self.selected_files.get_selection().select_iter(iter)
                    self.builder.get_object('manual').handler_block(self.manual_signal)
                    self.selected_files.scroll_to_cell(path)
                    self.on_selected_files_cursor_changed(self.selected_files)
                    self.builder.get_object('manual').handler_unblock(self.manual_signal)
                except:
                    pass
            self.selected_files.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)


    def on_menu_load_names_from_file_activate(self, widget):
        """ Get file names from a file """

        filename = ""
        f = Gtk.FileChooserDialog(_('Select file'),
                                  self.builder.get_object('main_window'),
                                 Gtk.FileChooserAction.OPEN,
                                  (Gtk.STOCK_CANCEL, Gtk.ResponseType.REJECT,
                                   Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                                   )
        response = f.run()
        if response == Gtk.ResponseType.ACCEPT:
            filename = f.get_filename()
        elif response == Gtk.ResponseType.REJECT:
            pass
        f.destroy()

        if filename != "":
            self.populate_from_file(filename)


    def on_main_quit(self, *args):
        """ Bye bye! But first, save preferences """
        self.populate_stop()
        self.prefs.preferences_save()
        Gtk.main_quit()

    def initialize_defaults(self):
        self.options_panel_state(self.options_shown)
        self.builder.get_object('menu_show_options').set_active(self.options_shown)
        self.builder.get_object('filedir_combo').set_active(self.filedir)
        self.builder.get_object('add_recursive').set_active(self.recursive)
        self.builder.get_object('extensions_check').set_active(self.keepext)
        self.builder.get_object('autopreview_check').set_active(self.autopreview)


#---------------------------------------------------------------------------------------
# Directory functions

    def dir_reload_current(self):
        """ An easy way to call dir_selected """
        self.dir_selected(None, self.active_dir)


    def dir_selected(self, obj, dir):
        """ The user has clicked on a directory on the left pane, so we need to load
        the files inside that dir on the right pane. """

        self.active_dir = dir
        self.populate_stop()

        self.stop_button.show()
        self.builder.get_object('clear_button').set_sensitive(False)
        self.builder.get_object('rename_button').set_sensitive(False)
        self.file_selected_model.clear()

        while Gtk.events_pending():
            Gtk.main_iteration()

        self.file_selected_model.clear()

        self.populate_selected_files(dir)
        self.selected_files.columns_autosize()
        self.builder.get_object('statusbar').push(self.statusbar_context, _("Reading contents of dir %s") % dir)


    def populate_stop(self):
        """ Stop populating the TreeView """

        renamerfilefuncs.set_stop(True)

        if self.listing_thread != None:
            while self.listing_thread.isAlive():
                self.listing_thread.join()

        self.stop_button.hide()
        for i in self.populate_id:
            removed = GObject.source_remove(i)
            self.populate_id.remove(i)

        self.selected_files.set_model(self.file_selected_model)
        self.progressbar.set_fraction(0)
        self.builder.get_object('statusbar').push(self.statusbar_context, _("Directory: %s - Files: %s") % (self.active_dir, self.count))


    def populate_get_listing(self, dir, pattern, recursive):
        """ Get the file listing using the utilities on renamerfilefuncs """

        # Add files from the current directory (and subdirs if needed)
        if recursive:
            self.listing = renamerfilefuncs.get_file_listing_recursive(dir, self.filedir, pattern)
        else:
            self.listing = renamerfilefuncs.get_file_listing(dir, self.filedir, pattern)

        GObject.idle_add(self.populate_get_listing_end)


    def populate_get_listing_end(self):
        """ The listing thread stuff is over, so now add things to the view """

        if renamerfilefuncs.get_stop():
            self.populate_stop()
        else:
            populate = self.populate_add_to_view(self.listing)
            self.populate_id.append(GObject.idle_add(populate.__next__))


    def populate_selected_files(self, dir):
        """ Get the file listing using the utilities on renamerfilefuncs.
        Then add it to the model while updating the gui """

        pattern = self.builder.get_object('file_pattern').get_text()
        recursive = self.builder.get_object('add_recursive').get_active()

        renamerfilefuncs.set_stop(False)

        self.listing_thread = threading.Thread(target=lambda:self.populate_get_listing(dir, pattern, recursive))
        self.listing_thread.start()

        return


    def populate_add_to_view(self, listing):
        """ Add files to the treeview """

        # Add items to treeview
        for elem in listing:
            iter = self.file_selected_model.insert_before(None, None)

            self.selected_files.set_model(None)
            self.file_selected_model.set_value(iter, 0, elem[0])
            self.file_selected_model.set_value(iter, 1, elem[1])
            #self.file_selected_model.set_value(iter, 4, self.get_icon(elem[1]))

            self.progressbar.pulse()
            self.builder.get_object('statusbar').push(self.statusbar_context, _("Adding file %s") % elem[1])
            self.count += 1
            yield True

        self.selected_files.set_model(self.file_selected_model)
        self.progressbar.set_fraction(0)
        self.builder.get_object('statusbar').push(self.statusbar_context, _("Directory: %s - Files: %s") % (self.active_dir, self.count))
        self.stop_button.hide()
        self.count = 0
        yield False


    def populate_from_file(self, filename):
        """ Populate file preview loading the names from a file """

        f = open(filename, 'r')
        iter = self.file_selected_model.get_iter_first()
        for line in f:
            line = line.rstrip()
            if len(line) > 255 or not isinstance(line, str) or line == "":
                line = None
                path = None

            if line != "" and line != None:
                oripath = self.file_selected_model.get_value(iter, 1)
                path = ospath.join(ospath.dirname(oripath), line)

            self.selected_files.set_model(None)
            self.file_selected_model.set_value(iter, 2, line)
            self.file_selected_model.set_value(iter, 3, path)

            self.count += 1
            iter = self.file_selected_model.iter_next(iter)
            if iter == None: break

        self.selected_files.set_model(self.file_selected_model)

        self.selected_files.columns_autosize()
        self.builder.get_object('clear_button').set_sensitive(True)
        self.builder.get_object('menu_clear_preview').set_sensitive(True)
        self.builder.get_object('rename_button').set_sensitive(True)
        self.builder.get_object('menu_rename').set_sensitive(True)

        f.close()


    def get_icon(self, path):

        icon_theme = Gtk.IconTheme.get_default()
        if ospath.isdir(path):
            try:
                icon = icon_theme.load_icon("gnome-fs-directory", 16, 0)
                return icon
            except GObject.GError as exc:
                try:
                    icon = icon_theme.load_icon("gtk-directory", 16, 0)
                    return icon
                except:
                    return None
        else:

            mime = "text-x-generic"

            audio = ["mp3", "ogg", "wav", "aiff"]
            image = ["jpg", "gif", "png", "tiff", "tif", "jpeg"]
            video = ["avi", "ogm", "mpg", "mpeg", "mov"]
            package = ["rar", "zip", "gz", "tar", "bz2", "tgz", "deb", "rpm"]

            file = path.split('/')[-1]
            ext = (file.split('.')[-1]).lower()

            if ext in audio:
                mime = "audio-x-generic"

            elif ext in image:
                mime = "image-x-generic"

            elif ext in video:
                mime = "video-x-generic"

            elif ext in package:
                mime = "package-x-generic"

            try:
                icon = icon_theme.load_icon(mime, Gtk.IconSize.MENU, 0)
                return icon
            except GObject.GError as exc:
                return None

    def display_error_dialog(self, text):
        """ Display an error message """

        dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.NONE, text)
        dialog.add_button(_("Ignore errors"), 1)
        dialog.add_button("gtk-ok", 0)
        self.ignore_errors = dialog.run()
        dialog.destroy()


    def about_info(self,event,data=None):
        """ Display the About dialog """

        about = Gtk.AboutDialog()
        about.set_name(self.name)
        about.set_version(self.version)
        
        about.set_authors(pyrenamerglob.authors)
        about.set_artists(pyrenamerglob.artists)
        about.set_translator_credits(_('translator-credits'))
        about.set_logo(GdkPixbuf.Pixbuf.new_from_file(self.icon))
        about.set_license(pyrenamerglob.license)
        about.set_wrap_license(True)
        about.set_comments(_(pyrenamerglob.description))
        about.set_copyright(pyrenamerglob.copyright)

        def openHomePage(widget,url,url2):
            import webbrowser
            webbrowser.open_new(url)

        about.set_website(pyrenamerglob.website)
        about.set_icon_from_file(pyrenamerglob.icon)
        about.run()
        about.destroy()

def parse_arguments():
    """Read arguments from the command line"""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-r", "--root_dir",
                        help="Start pyRenamer with a new root dir")
    parser.add_argument("-s", "--active_dir",
                help="Directory to select when pyRenamer starts")
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments() # Parse arguments
    GObject.threads_init() # Start threading
    py = pyRenamer(args.root_dir, args.active_dir) # Initialize program
    Gtk.main()
    

if __name__ == '__main__':
    main()
