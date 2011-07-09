# -*- coding: utf-8 -*-

import gtk

import diglib
from diglib.gui.util import open_url, open_email, get_image


class AboutDialog(gtk.AboutDialog):

    def __init__(self):
        super(AboutDialog, self).__init__()
        self.set_position(gtk.WIN_POS_CENTER_ON_PARENT)
        url_hook = lambda dialog, url, data: open_url(url)
        gtk.about_dialog_set_url_hook(url_hook, None)
        email_hook = lambda dialog, email, data: open_email(email)
        gtk.about_dialog_set_email_hook(email_hook, None)
        self.set_logo(gtk.gdk.pixbuf_new_from_file(get_image('diglib.svg')))
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
