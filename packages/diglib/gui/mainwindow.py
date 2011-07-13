# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011 Yasser González-Fernández <ygonzalezfernandez@gmail.com>
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. If not, see <http://www.gnu.org/licenses/>.

import math
import urllib

import gtk
import pango
import gobject

from diglib import about
from diglib.core import error
from diglib.gui.util import open_file, get_image
from diglib.gui.xmlwidget import XMLWidget
from diglib.gui.searchentry import SearchEntry
from diglib.gui.aboutdialog import AboutDialog
from diglib.gui.addtagdialog import AddTagDialog
from diglib.gui.importfiledialog import ImportFileDialog
from diglib.gui.importdirwindow import ImportDirectoryWindow


class MainWindow(XMLWidget):

    TAGS_TREEVIEW_COLUMN_TYPE = 0
    TAGS_TREEVIEW_COLUMN_TAG = 1
    TAGS_TREEVIEW_COLUMN_FONT = 2

    TAGS_TREEVIEW_ROW_ALL = 0
    TAGS_TREEVIEW_ROW_SEPARATOR = 1
    TAGS_TREEVIEW_ROW_TAG = 2

    DOCS_TREEVIEW_COLUMN_ID = 0
    DOCS_TREEVIEW_COLUMN_ICON = 1

    DOC_ICON_SMALL = 0
    DOC_ICON_NORMAL = 1
    DOC_ICON_LARGE = 2

    def __init__(self, library):
        super(MainWindow, self).__init__('main_window')
        # Instance attributes for widgets.
        self._main_window = self._builder.get_object('main_window')
        self._tags_treeview = self._builder.get_object('tags_treeview')
        self._tags_scrolledwindow = self._builder.get_object('tags_scrolledwindow')
        self._tags_menu = self._builder.get_object('tags_menu')
        self._docs_iconview = self._builder.get_object('docs_iconview')
        self._docs_menu = self._builder.get_object('docs_menu')
        self._doc_tags_menu = self._builder.get_object('doc_tags_menu')
        self._statusbar = self._builder.get_object('statusbar')
        self._docs_menuitem = self._builder.get_object('docs_menuitem')
        self._small_icons_menuitem = self._builder.get_object('small_icons_menuitem')
        self._normal_icons_menuitem = self._builder.get_object('normal_icons_menuitem')
        self._large_icons_menuitem = self._builder.get_object('large_icons_menuitem')
        self._rename_tag_menuitem = self._builder.get_object('rename_tag_menuitem')
        self._delete_tags_menuitem = self._builder.get_object('delete_tags_menuitem')
        self._delete_tags_toolbutton = self._builder.get_object('delete_tags_toolbutton')
        self._open_docs_toolbutton = self._builder.get_object('open_docs_toolbutton')
        self._copy_docs_toolbutton = self._builder.get_object('copy_docs_toolbutton')
        self._delete_docs_toolbutton = self._builder.get_object('delete_docs_toolbutton')
        self._search_entry = SearchEntry()
        # Other instance attributes.
        self._library = library
        self._search_timeout_id = 0
        self._search_timeout = 1000 # milliseconds.
        # Initialize widgets.
        self._main_window.set_title(about.NAME)
        self._init_tags_treeview()
        self._init_docs_iconview()
        self._init_toolbar()
        self._init_menubar()
        self._query = ''
        self._old_query = None
        self._selected_tags = set()
        self._old_selected_tags = None
        self._select_all_docs_tag()

    def _init_toolbar(self):
        # The combo box with the size of the icons.
        icon_size_toolitem = self._builder.get_object('icon_size_toolitem')
        self._icon_size_combobox = gtk.combo_box_new_text()
        self._icon_size_combobox.append_text('Small Icons')
        self._icon_size_combobox.append_text('Normal Icons')
        self._icon_size_combobox.append_text('Large Icons')
        self._icon_size_combobox.connect('changed', self.on_icons_size_combobox_changed)
        self._icon_size_combobox.set_active(self.DOC_ICON_NORMAL)
        icon_size_toolitem.add(self._icon_size_combobox)
        icon_size_toolitem.show_all()
        # The search text entry.
        search_toolitem = self._builder.get_object('search_toolitem')
        self._search_entry.set_width_chars(35)
        self._search_entry.connect('changed', self.on_search_entry_changed)
        search_toolitem.add(self._search_entry)
        search_toolitem.show_all()

    def _init_menubar(self):
        # The check menu item for the tags pane.
        show_tags_menuitem = self._builder.get_object('show_tags_menuitem')
        show_tags_menuitem.set_active(True)
        # The radio menu items for the size of the icons.
        self._normal_icons_menuitem.set_group(self._small_icons_menuitem)
        self._large_icons_menuitem.set_group(self._small_icons_menuitem)
        self._normal_icons_menuitem.set_active(True)
        self._small_icons_menuitem.connect('toggled', self.on_icons_size_menuitem_toggled, self.DOC_ICON_SMALL)
        self._normal_icons_menuitem.connect('toggled', self.on_icons_size_menuitem_toggled, self.DOC_ICON_NORMAL)
        self._large_icons_menuitem.connect('toggled', self.on_icons_size_menuitem_toggled, self.DOC_ICON_LARGE)

    def _init_tags_treeview(self):
        # Initialize the list store, the cell renderer and the column of the tree view.
        self._tags_liststore = gtk.ListStore(int, str, pango.FontDescription)
        self._tags_treeview.set_model(self._tags_liststore)
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self.on_tag_cellrenderer_edited)
        renderer.set_property('xalign', 0.5)
        column = gtk.TreeViewColumn(None, renderer)
        column.add_attribute(renderer, 'text', self.TAGS_TREEVIEW_COLUMN_TAG)
        column.add_attribute(renderer, 'font_desc', self.TAGS_TREEVIEW_COLUMN_FONT)
        # Function to disable edition of the "special" tags.
        f = lambda column, renderer, model, iter: renderer.set_property('editable', model.get_value(iter, self.TAGS_TREEVIEW_COLUMN_TYPE) == self.TAGS_TREEVIEW_ROW_TAG)
        column.set_cell_data_func(renderer, f)
        self._tags_treeview.append_column(column)
        # Function to draw the separator.
        f = lambda model, iter: model.get_value(iter, self.TAGS_TREEVIEW_COLUMN_TYPE) == self.TAGS_TREEVIEW_ROW_SEPARATOR
        self._tags_treeview.set_row_separator_func(f)
        # Setup sorting.
        self._tags_liststore.set_sort_func(self.TAGS_TREEVIEW_COLUMN_TAG, self._tags_liststore_sort_func)
        self._tags_liststore.set_sort_column_id(self.TAGS_TREEVIEW_COLUMN_TAG, gtk.SORT_ASCENDING)
        # Initialize the selection.
        selection = self._tags_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.connect('changed', self.on_tags_treeview_selection_changed)
        # Other tree view settings.
        self._tags_treeview.set_headers_visible(False)
        self._tags_treeview.set_search_column(self.TAGS_TREEVIEW_COLUMN_TAG)

    def _init_docs_iconview(self):
        # Initialize the list store and the icon view.
        self._docs_liststore = gtk.ListStore(str, gtk.gdk.Pixbuf)
        self._docs_iconview.set_model(self._docs_liststore)
        self._docs_iconview.set_pixbuf_column(self.DOCS_TREEVIEW_COLUMN_ICON)
        self._docs_iconview.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self._docs_iconview.connect('selection-changed', self.on_docs_iconview_selection_changed)
        self._docs_icon_size = self.DOC_ICON_NORMAL
        # Default document icons.
        self._docs_icon_small = gtk.gdk.pixbuf_new_from_file_at_size(get_image('diglib-document.svg'), self._library.THUMBNAIL_SIZE_SMALL, self._library.THUMBNAIL_SIZE_SMALL)
        self._docs_icon_normal = gtk.gdk.pixbuf_new_from_file_at_size(get_image('diglib-document.svg'), self._library.THUMBNAIL_SIZE_NORMAL, self._library.THUMBNAIL_SIZE_NORMAL)
        self._docs_icon_large = gtk.gdk.pixbuf_new_from_file_at_size(get_image('diglib-document.svg'), self._library.THUMBNAIL_SIZE_LARGE, self._library.THUMBNAIL_SIZE_LARGE)

    def on_import_file(self, *args):
        dialog = ImportFileDialog()
        response = dialog.run()
        filename = dialog.get_filename()
        tags = dialog.get_tags()
        dialog.destroy()
        if response == gtk.RESPONSE_OK:
            try:
                self._library.add_doc(filename, tags)
            except error.DocumentDuplicatedExact:
                error = 'The document is already in the library.'
            except error.DocumentDuplicatedSimilar:
                error = 'A similar document is already in the library.'
            except error.DocumentNotRetrievable:
                error = 'The document is not retrievable.'
            except error.DocumentNotSupported:
                error = 'The format of the document not supported.'
            else:
                error = None
            if error:
                dialog = gtk.MessageDialog(self._main_window, gtk.DIALOG_MODAL,
                                           gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                           'Could not import the document.')
                dialog.format_secondary_text(error)
                dialog.run()
                dialog.destroy()
            else:
                self._select_all_docs_tag()

    def on_import_dir(self, *args):
        window = ImportDirectoryWindow(self._library)
        response = window.run()
        if response == gtk.RESPONSE_OK:
            self._select_all_docs_tag()

    def on_open_docs(self, *args):
        for hash_md5 in self._iter_selected_docs():
            doc = self._library.get_doc(hash_md5)
            open_file(doc.document_abspath)

    def on_copy_docs(self, *args):
        doc_paths = [self._library.get_doc(hash_md5).document_abspath 
                     for hash_md5 in self._iter_selected_docs()]
        if doc_paths:
            def get_func(clipboard, selectiondata, info, data):
                uris = ['file://%s' % urllib.quote(path) for path in doc_paths]
                text = 'copy\n%s' % "\n".join(uris)
                selectiondata.set(selectiondata.get_target(), 8, text)
            clipboard = gtk.clipboard_get()
            targets = [('x-special/gnome-copied-files', 0, 0)]
            clipboard.set_with_data(targets, get_func, lambda clipboard, data: None)

    def on_delete_docs(self, *args):
        selection = list(self._iter_selected_docs())
        num_docs = len(selection)
        if num_docs > 0:
            message = 'Delete the %s?' % \
                (('%s selected documents' % num_docs)
                 if num_docs > 1 else 'selected document')
            secondary_text = 'The %s will be permanently lost.' % \
                ('documents' if num_docs > 1 else 'document')
            dialog = gtk.MessageDialog(self._main_window, gtk.DIALOG_MODAL, 
                                       gtk.MESSAGE_QUESTION, 
                                       gtk.BUTTONS_YES_NO, message)
            dialog.format_secondary_text(secondary_text)
            response = dialog.run()
            dialog.destroy()
            if response == gtk.RESPONSE_YES:
                for hash_md5 in selection:
                    self._library.delete_doc(hash_md5)
                self._select_all_docs_tag()

    def on_delete_tags(self, *args):
        selection = list(self._iter_selected_tags())
        num_tags = len(selection)
        if num_tags > 0:
            message = 'Delete the %s?' % \
                (('%s selected tags' % num_tags)
                 if num_tags > 1 else 'selected tag')
            secondary_text = \
                'The documents associated with the %s will not be removed.' % \
                    ('tags' if num_tags > 1 else 'tag')
            dialog = gtk.MessageDialog(self._main_window, 
                                       gtk.DIALOG_MODAL, gtk.MESSAGE_QUESTION, 
                                       gtk.BUTTONS_YES_NO, message)
            dialog.format_secondary_text(secondary_text)
            response = dialog.run()
            dialog.destroy()
            if response == gtk.RESPONSE_YES:
                try:
                    for tag in selection:
                        self._library.delete_tag(tag)
                except error.DocumentNotRetrievable:
                    message = 'Could not delete the tag "%s".' % tag
                    secondary_text = 'If the tag is deleted at least ' \
                        'one document could not be retrieved.'
                    dialog = gtk.MessageDialog(self._main_window,
                                               gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                                               gtk.BUTTONS_OK, message)
                    dialog.format_secondary_text(secondary_text)
                    dialog.run()
                    dialog.destroy()
                self._select_all_docs_tag()

    def on_add_tag(self, *args):
        dialog = AddTagDialog()
        response = dialog.run()
        tag = dialog.get_tag()
        dialog.destroy()
        if response == gtk.RESPONSE_ACCEPT:
            try:
                self._library.add_tag(tag)
            except error.TagDuplicated:
                message = 'Could not add the tag "%s".' % tag
                secondary_text = 'The tag already exists in the database.'
                dialog = gtk.MessageDialog(self._main_window,
                                           gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_OK, message)
                dialog.format_secondary_text(secondary_text)
                dialog.run()
                dialog.destroy()
            else:
                self._update_tags_treeview()

    def on_close_menuitem_activate(self, menuitem):
        self._main_window.destroy()

    def on_about_menuitem_activate(self, menuitem):
        dialog = AboutDialog()
        dialog.run()
        dialog.destroy()
        
    def on_show_tags_menuitem_toggled(self, checkmenuitem):
        if checkmenuitem.get_active():
            self._tags_scrolledwindow.show()
        else:
            self._tags_scrolledwindow.hide()

    def on_tag_menuitem_toggled(self, checkmenuitem):
        tag = checkmenuitem.get_label()
        docs = [self._library.get_doc(hash_md5) 
                for hash_md5 in self._iter_selected_docs()]
        try:
            for doc in docs:
                if checkmenuitem.get_active():
                    doc.tags.add(tag)
                else:
                    doc.tags.discard(tag)
                self._library.update_tags(doc.hash_md5, doc.tags)
        except error.DocumentNotRetrievable:
            message = 'Could not remove the tag "%s".' % tag
            secondary_text = 'If the tag is removed from one of the ' \
                'selected documents it could not be retrieved.'
            dialog = gtk.MessageDialog(self._main_window,
                                       gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                                       gtk.BUTTONS_OK, message)
            dialog.format_secondary_text(secondary_text)
            dialog.run()
            dialog.destroy()
        self._update_tags_treeview()

    def on_icons_size_menuitem_toggled(self, radiomenuitem, new_size):
        if radiomenuitem.get_active() and self._docs_icon_size != new_size:
            self._docs_icon_size = new_size
            self._update_icons_size_widgets()
            self._update_docs_iconview(True)

    def on_icons_size_combobox_changed(self, combobox):
        new_size = combobox.get_active()
        if self._docs_icon_size != new_size:
            self._docs_icon_size = new_size
            self._update_icons_size_widgets()
            self._update_docs_iconview(True)

    def on_rename_tag_menuitem_activate(self, menuitem):
        selection = self._tags_treeview.get_selection()
        tags_liststore, paths = selection.get_selected_rows()
        for path in paths:
            iter = tags_liststore.get_iter(path)
            type = tags_liststore.get_value(iter, self.TAGS_TREEVIEW_COLUMN_TYPE)
            if type == self.TAGS_TREEVIEW_ROW_TAG:
                self._tags_treeview.set_cursor(path, self._tags_treeview.get_column(0), True)
                break # Rename the first selected tag.

    def on_tags_treeview_button_press_event(self, treeview, event):
        if event.button == 3: # Right button.
            path = treeview.get_path_at_pos(int(event.x), int(event.y))
            if path:
                path = path[0]
                selection = treeview.get_selection()
                if not selection.path_is_selected(path):    
                    selection.unselect_all()
                    selection.select_path(path)
                self._tags_menu.popup(None, None, None, event.button, event.time)
                self._tags_menu.show()

    def on_docs_iconview_button_press_event(self, iconview, event):
        if event.button == 3: # Right button.
            path = iconview.get_path_at_pos(int(event.x), int(event.y))
            if path:
                if not iconview.path_is_selected(path):
                    iconview.unselect_all()
                    iconview.select_path(path)
                self._docs_menu.popup(None, None, None, event.button, event.time)
                self._docs_menu.show()
                
    def on_main_window_destroy(self, widget):
        gtk.main_quit()

    def on_tag_cellrenderer_edited(self, renderer, path, new_name):
        iter = self._tags_liststore.get_iter(path)
        new_name = new_name.strip()
        old_name = self._tags_liststore.get_value(iter, self.TAGS_TREEVIEW_COLUMN_TAG)
        if old_name != new_name:
            try:
                self._library.rename_tag(old_name, new_name)
            except error.TagDuplicated:
                message = 'Could not rename the tag "%s".' % old_name
                secondary_text = 'The tag "%s" exists in the database.' % new_name
                dialog = gtk.MessageDialog(self._main_window,
                                           gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
                                           gtk.BUTTONS_OK, message)
                dialog.format_secondary_text(secondary_text)
                dialog.run()
                dialog.destroy()
            else:
                self._update_tags_treeview()

    def on_tags_treeview_selection_changed(self, *args):
        self._selected_tags = set(self._iter_selected_tags())
        self._rename_tag_menuitem.set_sensitive(len(self._selected_tags) == 1)
        self._delete_tags_menuitem.set_sensitive(len(self._selected_tags) > 0)
        self._delete_tags_toolbutton.set_sensitive(len(self._selected_tags) > 0)
        if self._search_timeout_id > 0:
            gobject.source_remove(self._search_timeout_id)
        self._search_timeout_id = gobject.timeout_add(self._search_timeout, 
                                                      self._search_timeout_callback)

    def on_search_entry_changed(self, *tags):
        self._query = self._search_entry.get_text()
        if self._search_timeout_id > 0:
            gobject.source_remove(self._search_timeout_id)
        self._search_timeout_id = gobject.timeout_add(self._search_timeout, 
                                                      self._search_timeout_callback)        

    def on_docs_iconview_selection_changed(self, iconview):
        selected_docs = list(self._iter_selected_docs())
        sensitive = len(selected_docs) > 0
        self._docs_menuitem.set_sensitive(sensitive)
        self._open_docs_toolbutton.set_sensitive(sensitive)
        self._copy_docs_toolbutton.set_sensitive(sensitive)
        self._delete_docs_toolbutton.set_sensitive(sensitive)
        self._update_doc_tags_menu()
        self._update_statusbar()

    def _update_doc_tags_menu(self):
        callback = lambda menuitem: self._doc_tags_menu.remove(menuitem)
        self._doc_tags_menu.foreach(callback)
        tag_sets = [self._library.get_doc(hash_md5).tags
                    for hash_md5 in self._iter_selected_docs()]
        if tag_sets:
            first_set = tag_sets[0]
            other_sets = tag_sets[1:]
            active_tags = first_set.intersection(*other_sets)
            for model_row in self._tags_liststore:
                if model_row[self.TAGS_TREEVIEW_COLUMN_TYPE] == self.TAGS_TREEVIEW_ROW_TAG:
                    tag = model_row[self.TAGS_TREEVIEW_COLUMN_TAG]
                    menuitem = gtk.CheckMenuItem(tag)
                    if tag in active_tags:
                        menuitem.activate()
                    menuitem.connect('toggled', self.on_tag_menuitem_toggled)
                    self._doc_tags_menu.append(menuitem)
            self._doc_tags_menu.show_all()

    def _update_tags_treeview(self):
        self._tags_liststore.clear()
        # Add the special rows.
        self._tags_liststore.append((self.TAGS_TREEVIEW_ROW_ALL, 'All Documents', pango.FontDescription()))
        self._tags_liststore.append((self.TAGS_TREEVIEW_ROW_SEPARATOR, None, pango.FontDescription()))
        default_size = self._main_window.get_style().font_desc.get_size()
        # Smallest and largest font sizes.
        s = 0.75 * default_size
        S = 1.5 * default_size
        # Add one row for each tag.
        tags = self._library.get_all_tags()
        tag_freqs = [self._library.get_tag_freq(tag) for tag in tags]
        if tag_freqs:
            # Minimum and maximum frequencies.
            f = math.log1p(min(tag_freqs))
            F = math.log1p(max(tag_freqs))
            for tag in tags:
                font_desc = pango.FontDescription()
                if F > f:
                    t = math.log1p(self._library.get_tag_freq(tag)) # Tag frequency.
                    font_size = int(s + (S - s) * ((t - f) / (F - f)))
                    font_desc.set_size(font_size)
                self._tags_liststore.append([self.TAGS_TREEVIEW_ROW_TAG, tag, font_desc])

    def _update_docs_iconview(self, force=False):
        if (force or self._query != self._old_query or
            self._selected_tags != self._old_selected_tags):
            self._old_query = self._query
            self._old_selected_tags = self._selected_tags
            self._docs_liststore.clear()
            for doc_id in self._library.search(self._query, self._selected_tags):
                doc = self._library.get_doc(doc_id)
                if doc.normal_thumbnail_abspath:
                    if self._docs_icon_size == self.DOC_ICON_SMALL:
                        pixbuf = gtk.gdk.pixbuf_new_from_file(doc.small_thumbnail_abspath)
                    elif self._docs_icon_size == self.DOC_ICON_NORMAL:
                        pixbuf = gtk.gdk.pixbuf_new_from_file(doc.normal_thumbnail_abspath)
                    elif self._docs_icon_size == self.DOC_ICON_LARGE:
                        pixbuf = gtk.gdk.pixbuf_new_from_file(doc.large_thumbnail_abspath)
                else:
                    if self._docs_icon_size == self.DOC_ICON_SMALL:
                        pixbuf = self._docs_icon_small
                    elif self._docs_icon_size == self.DOC_ICON_NORMAL:
                        pixbuf = self._docs_icon_normal
                    elif self._docs_icon_size == self.DOC_ICON_LARGE:
                        pixbuf = self._docs_icon_large
                self._docs_liststore.append([doc.hash_md5, pixbuf])
            self._update_statusbar()

    def _update_statusbar(self):
        text = ''
        num_docs = len(self._docs_liststore)
        if num_docs:
            text += '%s %s' % (num_docs, 'documents' if num_docs > 1 else 'document')
            selected_docs = len(list(self._iter_selected_docs()))
            if selected_docs:
                text += ' (%s selected)' % selected_docs
        self._statusbar.push(0, text)

    def _update_icons_size_widgets(self):
        self._icon_size_combobox.set_active(self._docs_icon_size)
        if self._docs_icon_size == self.DOC_ICON_SMALL:
            self._small_icons_menuitem.set_active(True)
        elif self._docs_icon_size == self.DOC_ICON_NORMAL:
            self._normal_icons_menuitem.set_active(True)
        elif self._docs_icon_size == self.DOC_ICON_LARGE:
            self._large_icons_menuitem.set_active(True)

    def _tags_liststore_sort_func(self, model, iter1, iter2):
        # The 'All Documents' special row goes first, then a separator,
        # and finally all the tags in alphanumeric order.
        row1_type = model.get_value(iter1, self.TAGS_TREEVIEW_COLUMN_TYPE)
        row2_type = model.get_value(iter2, self.TAGS_TREEVIEW_COLUMN_TYPE)
        if row1_type == self.TAGS_TREEVIEW_ROW_ALL:
            return -1
        elif row2_type == self.TAGS_TREEVIEW_ROW_ALL:
            return 1
        elif row1_type == self.TAGS_TREEVIEW_ROW_SEPARATOR:
            return -1
        elif row2_type == self.TAGS_TREEVIEW_ROW_SEPARATOR:
            return 1
        else:
            row1_tag = model.get_value(iter1, self.TAGS_TREEVIEW_COLUMN_TAG)
            row2_tag = model.get_value(iter2, self.TAGS_TREEVIEW_COLUMN_TAG)
            return cmp(row1_tag, row2_tag)

    def _search_timeout_callback(self):
        self._search_timeout_id = 0
        self._update_docs_iconview()
        return False # Do not call the function again.

    def _select_all_docs_tag(self): # The tag filter.
        self._query = ''
        self._selected_tags = set()
        self._update_tags_treeview()
        selection = self._tags_treeview.get_selection()
        selection.select_path((0, ))
        self._update_docs_iconview(True)

    def _iter_selected_docs(self):
        paths = self._docs_iconview.get_selected_items()
        for path in paths:
            iter = self._docs_liststore.get_iter(path)
            doc_id = self._docs_liststore.get_value(iter, self.DOCS_TREEVIEW_COLUMN_ID)
            yield doc_id
            
    def _iter_selected_tags(self):
        selection = self._tags_treeview.get_selection()
        tags_liststore, paths =  selection.get_selected_rows()
        for path in paths:
            iter = tags_liststore.get_iter(path)
            type = tags_liststore.get_value(iter, self.TAGS_TREEVIEW_COLUMN_TYPE)
            if type == self.TAGS_TREEVIEW_ROW_ALL:
                break
            elif type == self.TAGS_TREEVIEW_ROW_TAG:
                tag = tags_liststore.get_value(iter, self.TAGS_TREEVIEW_COLUMN_TAG)
                yield tag
