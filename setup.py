#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
