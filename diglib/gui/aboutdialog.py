# -*- coding: utf-8 -*-

import os

import gtk

import diglib
import diglib.util


class AboutDialog(gtk.AboutDialog):

    def __init__(self):
        super(AboutDialog, self).__init__()
        self.set_position(gtk.WIN_POS_CENTER)
        url_hook = lambda dialog, url, data: diglib.util.open_url(url)
        gtk.about_dialog_set_url_hook(url_hook, None)
        email_hook = lambda dialog, email, data: diglib.util.open_email(email)
        gtk.about_dialog_set_email_hook(email_hook, None)
        logo_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'diglib.svg')
        self.set_logo(gtk.gdk.pixbuf_new_from_file(logo_file))
        self.set_name(diglib.NAME)
        self.set_program_name(diglib.NAME)
        self.set_version(diglib.VERSION)
        self.set_comments(diglib.DESCRIPTION)
        self.set_authors([diglib.AUTHOR])
        self.set_copyright(diglib.COPYRIGHT)
        self.set_wrap_license(True)
        self.set_license(
'This program is free software: you can redistribute it and/or \
modify it under the terms of the GNU General Public License as published \
by the Free Software Foundation, either version 3 of the License, or \
any later version.\n\n\
This program is distributed in the hope that it will be useful, but WITHOUT \
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or \
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for \
more details.\n\n\
You should have received a copy of the GNU General Public License along with \
this program. If not, see http://www.gnu.org/licenses/.'
)
