#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import optparse

from diglib import about, main


if __name__ == '__main__':
    usage = 'diglib [options]'
    version = 'diglib ({name}) {version}\n{copyright}\n' \
        'You may redistribute copies of this program under the terms of\n' \
        'the GNU General Public License version 3 or later. You should\n' \
        'have received a copy of the GNU General Public License along\n' \
        'with this program. If not, see <http://www.gnu.org/licenses/>.' \
        .format(name=about.NAME, version=about.VERSION, copyright=about.COPYRIGHT)
    description = about.DESCRIPTION
    parser = optparse.OptionParser(usage=usage, version=version,
                                   description=description)
    parser.add_option('-l', '--library', metavar='DIR', dest='library_dir',
                      help='specify config file (default %default)')
    parser.set_defaults(library_dir='~/.diglib/')
    options, _ = parser.parse_args()
    main(os.path.expanduser(options.library_dir))
