# -*- coding: utf-8 -*-

import math

import gtk
import pango

from diglib.gui.util import get_icon
from diglib.gui.xmlwidget import XMLWidget
from diglib.gui.aboutdialog import AboutDialog
from diglib.gui.searchentry import SearchEntry


class MainWindow(XMLWidget):

    def __init__(self, library):
        super(MainWindow, self).__init__('main_window')
        self._library = library
        self._search_timeout = 1000 # Miliseconds.
        self._tags = set()
        self._query = ''
        # Initialize child widgets.
        self._init_toolbar()
        self._init_tags_treeview()
        self._init_docs_iconview()
        self._update_all()

    def _init_toolbar(self):
        # The combo box with the size of the icons.
        iconsize_toolitem = self._builder.get_object('iconsize_toolitem')
        iconsize_combobox = gtk.combo_box_new_text()
        iconsize_combobox.append_text('Small Icons')
        iconsize_combobox.append_text('Normal Icons')
        iconsize_combobox.append_text('Large Icons')
        iconsize_combobox.set_active(1)
        iconsize_toolitem.add(iconsize_combobox)
        iconsize_toolitem.show_all()
        # The search text entry.
        search_toolitem = self._builder.get_object('search_toolitem')
        search_entry = SearchEntry(self._search_timeout)
        search_entry.set_width_chars(30)
        search_entry.connect('activate-timeout', self.on_search_entry_activate_timeout)
        search_toolitem.add(search_entry)
        search_toolitem.show_all()

    def _init_tags_treeview(self):
        tags_treeview = self._builder.get_object('tags_treeview')
        # Column type.
        self.TAGS_COLUMN_TYPE = 0
        self.TAGS_COLUMN_TAG = 1
        self.TAGS_COLUMN_FONT = 2
        # Row type.
        self.TAGS_ROW_ALL = 0
        self.TAGS_ROW_SEPARATOR = 1
        self.TAGS_ROW_TAG = 2
        # Initialize the list store, cell renderer and the column of the tree view.
        self._tags_liststore = gtk.ListStore(int, str, pango.FontDescription)
        tags_treeview.set_model(self._tags_liststore)
        renderer = gtk.CellRendererText()
        renderer.set_property('xalign', 0.5)
        column = gtk.TreeViewColumn(None, renderer)
        column.add_attribute(renderer, 'text', self.TAGS_COLUMN_TAG)
        column.add_attribute(renderer, 'font_desc', self.TAGS_COLUMN_FONT)
        # Function to disable edition of the "special" tags.
        f = lambda column, renderer, model, iter: renderer.set_property('editable',  model.get_value(iter, self.TAGS_COLUMN_TYPE) == self.TAGS_ROW_TAG)
        column.set_cell_data_func(renderer, f)
        tags_treeview.append_column(column)
        # Function to draw the separator.
        f = lambda model, iter: model.get_value(iter, self.TAGS_COLUMN_TYPE) == self.TAGS_ROW_SEPARATOR
        tags_treeview.set_row_separator_func(f)
        # Setup sorting.
        self._tags_liststore.set_sort_func(self.TAGS_COLUMN_TAG, self._tags_liststore_sort_func)
        self._tags_liststore.set_sort_column_id(self.TAGS_COLUMN_TAG, gtk.SORT_ASCENDING)
        # Initialize the selection.
        selection = tags_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.connect('changed', self.on_tags_selection_changed)
        # Other tree view settings.
        tags_treeview.set_headers_visible(False)
        tags_treeview.set_search_column(self.TAGS_COLUMN_TAG)

    def _init_docs_iconview(self):
        docs_iconview = self._builder.get_object('docs_iconview')
        # Column type.
        self.DOCS_COLUMN_HASH = 0
        self.DOCS_COLUMN_ICON = 1
        self._docs_liststore = gtk.ListStore(str, gtk.gdk.Pixbuf)
        docs_iconview.set_model(self._docs_liststore)
        docs_iconview.set_pixbuf_column(self.DOCS_COLUMN_ICON)
        docs_iconview.set_selection_mode(gtk.SELECTION_MULTIPLE)

    def _update_all(self):
        self._update_tags_treeview()
        self._update_docs_iconview()

    def _update_tags_treeview(self):
        self._tags_liststore.clear()
        # Add the special rows.
        self._tags_liststore.append((self.TAGS_ROW_ALL, 'All Documents', pango.FontDescription()))
        self._tags_liststore.append((self.TAGS_ROW_SEPARATOR, None, pango.FontDescription()))
        # Add one row for each tag.
        default_size = self._widget.get_style().font_desc.get_size()
        # Smallest and largest font sizes.
        s = 0.5 * default_size
        S = 1.5 * default_size
        tags = self._library.get_tags()
        tag_freqs = [self._library.get_tag_frequency(tag) for tag in tags]
        # Minimum and maximum frequencies.
        f = math.log1p(min(tag_freqs))
        F = math.log1p(max(tag_freqs))
        for tag in tags:
            font_desc = pango.FontDescription()
            if f != F:
                t = math.log1p(self._library.get_tag_frequency(tag)) # Tag frequency.
                font_size = int(s + (S - s) * ((t - f) / (F - f)))
                font_desc.set_size(font_size)
            self._tags_liststore.append([self.TAGS_ROW_TAG, tag, font_desc])
        # Update the selection.
#        tags_treeview = self._builder.get_object('tags_treeview')
#        selection = tags_treeview.get_selection()
#        selection.select_iter(self._tags_liststore.get_iter_first())

    def _update_docs_iconview(self):
        self._docs_liststore.clear()
        for md5_hash in self._library.search(self._query, self._tags):
            doc = self._library.get(md5_hash)
            thumbnail = doc.small_thumbnail_abspath
            if not thumbnail:
                thumbnail = get_icon('diglib-directory-add.svg')
            pixbuf = gtk.gdk.pixbuf_new_from_file(thumbnail)
            self._docs_liststore.append([doc.hash_md5, pixbuf])
        self._update_statusbar()
        
    def _update_statusbar(self):
        pass

    def _tags_liststore_sort_func(self, model, iter1, iter2):
        # The 'All Documents' special row goes first, then a separator,
        # and finally all tags in alphanumeric order.
        row1_type = model.get_value(iter1, self.TAGS_COLUMN_TYPE)
        row2_type = model.get_value(iter2, self.TAGS_COLUMN_TYPE)
        if row1_type == self.TAGS_ROW_ALL:
            return -1
        elif row2_type == self.TAGS_ROW_ALL:
            return 1
        elif row1_type == self.TAGS_ROW_SEPARATOR:
            return -1
        elif row2_type == self.TAGS_ROW_SEPARATOR:
            return 1
        else:
            row1_tag = model.get_value(iter1, self.TAGS_COLUMN_TAG)
            row2_tag = model.get_value(iter2, self.TAGS_COLUMN_TAG)
            return cmp(row1_tag, row2_tag)

    def on_main_window_destroy(self, widget):
        gtk.main_quit()

    def on_close_menuitem_activate(self, widget):
        self.destroy()

    def on_about_menuitem_activate(self, widget):
        dialog = AboutDialog()
        dialog.run()
        dialog.destroy()

    def on_search_entry_activate_timeout(self, widget):
        self._query = widget.get_text()
        self._update_docs_iconview()

    def on_importfile(self, widget):
        print 'importfile'

    def on_importdir(self, widget):
        print 'importdir'

    def on_addtag(self, widget):
        print 'addtag'

    def on_renametag(self, widget):
        print 'renametag'

    def on_deletetag(self, widget):
        print 'deletetag'

    def on_opendoc(self, widget):
        print 'opendoc'

    def on_copydoc(self, widget):
        print 'copydoc'

    def on_deletedoc(self, widget):
        print 'deletedoc'

    def on_docproperties(self, widget):
        print 'docproperties'

    def on_tags_selection_changed(self, selection):
        model, paths =  selection.get_selected_rows()
        self._tags.clear()
        for path in paths:
            iter = model.get_iter(path)
            type = model.get_value(iter, self.TAGS_COLUMN_TYPE)
            if type == self.TAGS_ROW_ALL:
                break
            elif type == self.TAGS_ROW_TAG:
                tag = model.get_value(iter, self.TAGS_COLUMN_TAG)
                self._tags.add(tag)
        self._update_docs_iconview()
