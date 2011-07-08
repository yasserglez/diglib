# -*- coding: utf-8 -*-

import math
import urllib

import gtk
import pango

from diglib.gui.xmlwidget import XMLWidget
from diglib.util import open_file
from diglib.gui.util import get_icon
from diglib.gui.aboutdialog import AboutDialog
from diglib.gui.addtagdialog import AddTagDialog
from diglib.gui.searchentry import SearchEntry
from diglib.core import NotRetrievableError


class MainWindow(XMLWidget):

    def __init__(self, library):
        super(MainWindow, self).__init__('main_window')
        self._library = library
        self._search_timeout = 1000 # msecs.
        self._query = ''
        self._tags = set()
        # Initialize child widgets.
        self._init_tags_treeview()
        self._init_docs_iconview()
        self._init_toolbar()
        self._init_menubar()
        self._update_tags_treeview()
        self._update_docs_iconview()

    def _init_toolbar(self):
        # The combo box with the size of the icons.
        icons_size_toolitem = self._builder.get_object('icons_size_toolitem')
        self._icons_size_combobox = gtk.combo_box_new_text()
        self._icons_size_combobox.append_text('Small Icons')
        self._icons_size_combobox.append_text('Normal Icons')
        self._icons_size_combobox.append_text('Large Icons')
        self._icons_size_combobox.connect('changed', self.on_icons_size_combobox_changed)
        self._icons_size_combobox.set_active(self.DOC_ICONS_NORMAL)
        icons_size_toolitem.add(self._icons_size_combobox)
        icons_size_toolitem.show_all()
        # The search text entry.
        search_toolitem = self._builder.get_object('search_toolitem')
        search_entry = SearchEntry(self._search_timeout)
        search_entry.set_width_chars(30)
        search_entry.connect('activate-timeout', self.on_search_entry_activate_timeout)
        search_toolitem.add(search_entry)
        search_toolitem.show_all()

    def _init_menubar(self):
        # The check menu item for the tags pane.
        show_tags_menuitem = self._builder.get_object('show_tags_menuitem')
        show_tags_menuitem.set_active(True)
        # The radio menu items for the size of the icons.
        small_icons_menuitem = self._builder.get_object('small_icons_menuitem')
        normal_icons_menuitem = self._builder.get_object('normal_icons_menuitem')
        large_icons_menuitem = self._builder.get_object('large_icons_menuitem')
        normal_icons_menuitem.set_group(small_icons_menuitem)
        large_icons_menuitem.set_group(small_icons_menuitem)
        normal_icons_menuitem.set_active(True)
        small_icons_menuitem.connect('toggled', self.on_icons_size_menuitem_toggled, self.DOC_ICONS_SMALL)
        normal_icons_menuitem.connect('toggled', self.on_icons_size_menuitem_toggled, self.DOC_ICONS_NORMAL)
        large_icons_menuitem.connect('toggled', self.on_icons_size_menuitem_toggled, self.DOC_ICONS_LARGE)

    def _init_tags_treeview(self):
        tags_treeview = self._builder.get_object('tags_treeview')
        self.TAG_COLUMN_TYPE = 0
        self.TAG_COLUMN_TAG = 1
        self.TAG_COLUMN_FONT = 2
        self.TAG_ROW_ALL = 0
        self.TAG_ROW_SEPARATOR = 1
        self.TAG_ROW_TAG = 2
        # Initialize the list store, the cell renderer and the column of the tree view.
        self._tags_liststore = gtk.ListStore(int, str, pango.FontDescription)
        tags_treeview.set_model(self._tags_liststore)
        renderer = gtk.CellRendererText()
        renderer.connect('edited', self.on_tag_cellrenderer_edited)
        renderer.set_property('xalign', 0.5)
        column = gtk.TreeViewColumn(None, renderer)
        column.add_attribute(renderer, 'text', self.TAG_COLUMN_TAG)
        column.add_attribute(renderer, 'font_desc', self.TAG_COLUMN_FONT)
        # Function to disable edition of the "special" tags.
        f = lambda column, renderer, model, iter: renderer.set_property('editable', model.get_value(iter, self.TAG_COLUMN_TYPE) == self.TAG_ROW_TAG)
        column.set_cell_data_func(renderer, f)
        tags_treeview.append_column(column)
        # Function to draw the separator.
        f = lambda model, iter: model.get_value(iter, self.TAG_COLUMN_TYPE) == self.TAG_ROW_SEPARATOR
        tags_treeview.set_row_separator_func(f)
        # Setup sorting.
        self._tags_liststore.set_sort_func(self.TAG_COLUMN_TAG, self._tags_liststore_sort_func)
        self._tags_liststore.set_sort_column_id(self.TAG_COLUMN_TAG, gtk.SORT_ASCENDING)
        # Initialize the selection.
        selection = tags_treeview.get_selection()
        selection.set_mode(gtk.SELECTION_MULTIPLE)
        selection.connect('changed', self.on_tags_selection_changed)
        # Other tree view settings.
        tags_treeview.set_headers_visible(False)
        tags_treeview.set_search_column(self.TAG_COLUMN_TAG)
        
    def on_import_file(self, *args):
        print 'import file'

    def on_import_dir(self, *args):
        print 'import dir'        

    def on_open_docs(self, *args):
        for doc_id in self._iter_selected_docs():
            doc = self._library.get_doc(doc_id)
            open_file(doc.document_abspath)

    def on_copy_docs(self, *args):
        abspaths = [self._library.get_doc(doc_id).document_abspath 
                    for doc_id in self._iter_selected_docs()]
        if abspaths:
            def get_func(clipboard, selectiondata, info, data):
                uris = ['file://%s' % urllib.quote(path) for path in abspaths]
                text = 'copy\n%s' % "\n".join(uris)
                selectiondata.set(selectiondata.get_target(), 8, text)
            clipboard = gtk.clipboard_get()
            targets = [('x-special/gnome-copied-files', 0, 0)]
            clipboard.set_with_data(targets, get_func, lambda clipboard, data: None)

    def on_delete_docs(self, *args):
        selected = list(self._iter_selected_docs())
        selected_count = len(selected)
        if selected_count > 0:
            message = 'Delete the %s?' % \
                (('%s selected documents' % selected_count)
                 if selected_count > 1 else 'selected document')
            secondary_text = 'The %s will be permanently lost.' % \
                ('documents' if selected_count > 1 else 'document')
            dialog = gtk.MessageDialog(self._widget, gtk.DIALOG_MODAL, 
                                       gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                       message)
            dialog.format_secondary_text(secondary_text)
            response = dialog.run()
            dialog.destroy()
            if response == gtk.RESPONSE_YES:
                for hash_md5 in selected:
                    self._library.delete_doc(hash_md5)
                self._update_tags_treeview()
                self._update_docs_iconview()

    def on_delete_tags(self, *args):
        selected = list(self._iter_selected_tags())
        selected_count = len(selected)
        if selected_count > 0:
            message = 'Delete the %s?' % \
                (('%s selected tags' % selected_count)
                 if selected_count > 1 else 'selected tag')
            secondary_text = \
                'The documents associated with the %s will not be removed.' % \
                    ('tags' if selected_count > 1 else 'tag')
            dialog = gtk.MessageDialog(self._widget, gtk.DIALOG_MODAL,
                                       gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO,
                                       message)
            dialog.format_secondary_text(secondary_text)
            response = dialog.run()
            dialog.destroy()
            if response == gtk.RESPONSE_YES:
                update = False
                for tag in selected:
                    try:
                        self._library.delete_tag(tag)
                        update = True
                    except NotRetrievableError:
                        message = 'Could not delete the tag "%s".' % tag
                        secondary_text = 'If the tag is deleted at least ' \
                            'one document could not be retrieved.'
                        dialog = gtk.MessageDialog(self._widget, gtk.DIALOG_MODAL,
                                                   gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                                                   message)
                        dialog.format_secondary_text(secondary_text)
                        response = dialog.run()
                        dialog.destroy()
                        break
                if update:
                    self._update_all()

    def on_add_tag(self, *args):
        dialog = AddTagDialog()
        response = dialog.run()
        dialog.destroy()
        if response == gtk.RESPONSE_ACCEPT and dialog.tag:
            self._library.add_tag(dialog.tag)
            self._update_tags_treeview()

    def on_close_menuitem_activate(self, menuitem):
        self.destroy()

    def on_about_menuitem_activate(self, menuitem):
        dialog = AboutDialog()
        dialog.run()
        dialog.destroy()
        
    def on_show_tags_menuitem_toggled(self, checkmenuitem):
        tags_scrolledwindow = self._builder.get_object('tags_scrolledwindow')
        if checkmenuitem.get_active():
            tags_scrolledwindow.show()
        else:
            tags_scrolledwindow.hide()

    def on_icons_size_menuitem_toggled(self, radiomenuitem, new_size):
        if radiomenuitem.get_active() and self._doc_icons_size != new_size:
            self._doc_icons_size = new_size
            self._sync_icons_size_widgets()
            self._update_docs_iconview()

    def on_icons_size_combobox_changed(self, combobox):
        new_size = combobox.get_active()
        if self._doc_icons_size != new_size:
            self._doc_icons_size = new_size
            self._sync_icons_size_widgets()
            self._update_docs_iconview()

    def on_rename_tag_menuitem_activate(self, menuitem):
        tags_treeview = self._builder.get_object('tags_treeview')
        selection = tags_treeview.get_selection()
        tags_liststore, paths = selection.get_selected_rows()
        for path in paths:
            iter = tags_liststore.get_iter(path)
            type = tags_liststore.get_value(iter, self.TAG_COLUMN_TYPE)
            if type == self.TAG_ROW_TAG:
                tags_treeview.set_cursor(path, tags_treeview.get_column(0), True)
                break

    def on_main_window_destroy(self, widget):
        gtk.main_quit()

    def on_tag_cellrenderer_edited(self, renderer, path, new_name):
        iter = self._tags_liststore.get_iter(path)
        new_name = new_name.strip()
        old_name = self._tags_liststore.get_value(iter, self.TAG_COLUMN_TAG)
        if old_name != new_name:
            self._library.rename_tag(old_name, new_name)
            self._update_tags_treeview()

    def on_search_entry_activate_timeout(self, search_entry):
        self._query = search_entry.get_text()
        self._update_docs_iconview()

    def on_tags_selection_changed(self, *args):
        self._tags.clear()
        for tag in self._iter_selected_tags():
            self._tags.add(tag)
        self._update_docs_iconview()

    def on_doc_properties(self, *args):
        pass

    def _init_docs_iconview(self):
        docs_iconview = self._builder.get_object('docs_iconview')
        self.DOC_COLUMN_ID = 0
        self.DOC_COLUMN_ICON = 1
        self.DOC_ICONS_SMALL = 0
        self.DOC_ICONS_NORMAL = 1
        self.DOC_ICONS_LARGE = 2
        # Initialize the list store and the icon view.
        self._docs_liststore = gtk.ListStore(str, gtk.gdk.Pixbuf)
        docs_iconview.set_model(self._docs_liststore)
        docs_iconview.set_pixbuf_column(self.DOC_COLUMN_ICON)
        docs_iconview.set_selection_mode(gtk.SELECTION_MULTIPLE)
        self._doc_icons_size = self.DOC_ICONS_NORMAL
        # Default document icons.
        doc_icon = get_icon('diglib-document.svg')
        self._doc_icon_small = gtk.gdk.pixbuf_new_from_file_at_size(doc_icon, self._library.THUMBNAIL_SIZE_SMALL, self._library.THUMBNAIL_SIZE_SMALL)
        self._doc_icon_normal = gtk.gdk.pixbuf_new_from_file_at_size(doc_icon, self._library.THUMBNAIL_SIZE_NORMAL, self._library.THUMBNAIL_SIZE_NORMAL)
        self._doc_icon_large = gtk.gdk.pixbuf_new_from_file_at_size(doc_icon, self._library.THUMBNAIL_SIZE_LARGE, self._library.THUMBNAIL_SIZE_LARGE)

    def _update_tags_treeview(self):
        self._tags_liststore.clear()
        # Add the special rows.
        self._tags_liststore.append((self.TAG_ROW_ALL, 'All Documents', pango.FontDescription()))
        self._tags_liststore.append((self.TAG_ROW_SEPARATOR, None, pango.FontDescription()))
        # Add one row for each tag.
        default_size = self._widget.get_style().font_desc.get_size()
        # Smallest and largest font sizes.
        s = 0.75 * default_size
        S = 1.5 * default_size
        tags = self._library.get_all_tags()
        tag_freqs = [self._library.get_tag_freq(tag) for tag in tags]
        # Minimum and maximum frequencies.
        f = math.log1p(min(tag_freqs))
        F = math.log1p(max(tag_freqs))
        for tag in tags:
            font_desc = pango.FontDescription()
            if F > f:
                t = math.log1p(self._library.get_tag_freq(tag)) # Tag frequency.
                font_size = int(s + (S - s) * ((t - f) / (F - f)))
                font_desc.set_size(font_size)
            self._tags_liststore.append([self.TAG_ROW_TAG, tag, font_desc])
        # Update the selection.
#        tags_treeview = self._builder.get_object('tags_treeview')
#        selection = tags_treeview.get_selection()
#        selection.select_iter(self._tags_liststore.get_iter_first())

    def _update_docs_iconview(self):
        self._docs_liststore.clear()
        for doc_id in self._library.search(self._query, self._tags):
            doc = self._library.get_doc(doc_id)
            if doc.normal_thumbnail_abspath:
                if self._doc_icons_size == self.DOC_ICONS_SMALL:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(doc.small_thumbnail_abspath)
                elif self._doc_icons_size == self.DOC_ICONS_NORMAL:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(doc.normal_thumbnail_abspath)
                elif self._doc_icons_size == self.DOC_ICONS_LARGE:
                    pixbuf = gtk.gdk.pixbuf_new_from_file(doc.large_thumbnail_abspath)
            else:
                if self._doc_icons_size == self.DOC_ICONS_SMALL:
                    pixbuf = self._doc_icon_small
                elif self._doc_icons_size == self.DOC_ICONS_NORMAL:
                    pixbuf = self._doc_icon_normal
                elif self._doc_icons_size == self.DOC_ICONS_LARGE:
                    pixbuf = self._doc_icon_large
            self._docs_liststore.append([doc.hash_md5, pixbuf])
        self._update_statusbar()

    def _update_statusbar(self):
        pass

    def _tags_liststore_sort_func(self, model, iter1, iter2):
        # The 'All Documents' special row goes first, then a separator,
        # and finally all the tags in alphanumeric order.
        row1_type = model.get_value(iter1, self.TAG_COLUMN_TYPE)
        row2_type = model.get_value(iter2, self.TAG_COLUMN_TYPE)
        if row1_type == self.TAG_ROW_ALL:
            return -1
        elif row2_type == self.TAG_ROW_ALL:
            return 1
        elif row1_type == self.TAG_ROW_SEPARATOR:
            return -1
        elif row2_type == self.TAG_ROW_SEPARATOR:
            return 1
        else:
            row1_tag = model.get_value(iter1, self.TAG_COLUMN_TAG)
            row2_tag = model.get_value(iter2, self.TAG_COLUMN_TAG)
            return cmp(row1_tag, row2_tag)

    def _iter_selected_docs(self):
        docs_iconview = self._builder.get_object('docs_iconview')
        paths = docs_iconview.get_selected_items()
        for path in paths:
            iter = self._docs_liststore.get_iter(path)
            doc_id = self._docs_liststore.get_value(iter, self.DOC_COLUMN_ID)
            yield doc_id
            
    def _iter_selected_tags(self):
        tags_treeview = self._builder.get_object('tags_treeview')
        selection = tags_treeview.get_selection()
        tags_liststore, paths =  selection.get_selected_rows()
        for path in paths:
            iter = tags_liststore.get_iter(path)
            type = tags_liststore.get_value(iter, self.TAG_COLUMN_TYPE)
            if type == self.TAG_ROW_ALL:
                break
            elif type == self.TAG_ROW_TAG:
                tag = tags_liststore.get_value(iter, self.TAG_COLUMN_TAG)
                yield tag

    def _sync_icons_size_widgets(self):
        self._icons_size_combobox.set_active(self._doc_icons_size)
        if self._doc_icons_size == self.DOC_ICONS_SMALL:
            menuitem = self._builder.get_object('small_icons_menuitem')
            menuitem.set_active(True)
        elif self._doc_icons_size == self.DOC_ICONS_NORMAL:
            menuitem = self._builder.get_object('normal_icons_menuitem')
            menuitem.set_active(True)
        elif self._doc_icons_size == self.DOC_ICONS_LARGE:
            menuitem = self._builder.get_object('large_icons_menuitem')
            menuitem.set_active(True)
