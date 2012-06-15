#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011-2012 Yasser González Fernández <ygonzalezfernandez@gmail.com>
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

import os
import sys
from distutils.core import setup

# Allow running this script in source directory.
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(src_dir, 'packages')))

from diglib import about


setup(name='diglib',
      version=about.VERSION,
      description=about.DESCRIPTION,
      author=about.AUTHOR[:about.AUTHOR.find('<')-1],
      author_email=about.AUTHOR[about.AUTHOR.find('<'):],
      license='GNU General Public License version 3 or later',
      packages=['diglib', 'diglib.core', 'diglib.core.lang', 'diglib.gui'],
      package_dir = {'': 'packages'},
      package_data={'diglib.core.lang': ['blocks.txt', 'stopwords/*', 'trigraphs/*'],
                    'diglib.gui': ['images/*', '*.glade']},
      scripts=['scripts/diglib'],
      data_files=[('share/applications', ['packages/diglib/gui/diglib.desktop']),
                  ('share/icons/hicolor/scalable/apps', ['packages/diglib/gui/images/diglib.svg'])])
