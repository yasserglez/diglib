# -*- coding: utf-8 -*-
#
# diglib: Personal digital document management software.
# Copyright (C) 2011-2015 Yasser Gonzalez <yasserglez@gmail.com>
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

import gtk

from diglib import about
from diglib.gui.util import open_url, open_email, get_image


class AboutDialog(gtk.AboutDialog):

    def __init__(self):
        super(AboutDialog, self).__init__()
        url_hook = lambda dialog, url, data: open_url(url)
        gtk.about_dialog_set_url_hook(url_hook, None)
        email_hook = lambda dialog, email, data: open_email(email)
        gtk.about_dialog_set_email_hook(email_hook, None)
        self.set_logo(gtk.gdk.pixbuf_new_from_file(get_image('diglib.svg')))
        self.set_name(about.NAME)
        self.set_program_name(about.NAME)
        self.set_version(about.VERSION)
        self.set_comments(about.DESCRIPTION)
        self.set_authors([about.AUTHOR])
        self.set_copyright(about.COPYRIGHT)
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
this program. If not, see http://www.gnu.org/licenses/.')
