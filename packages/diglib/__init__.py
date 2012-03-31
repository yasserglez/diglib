# -*- coding: utf-8 -*-
#
# diglib: Digital Library
# Copyright (C) 2011-2012 Yasser González-Fernández <ygonzalezfernandez@gmail.com>
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

from diglib.core import DigitalLibrary
from diglib.core.index import XapianIndex
from diglib.core.database import SQLAlchemyDatabase
from diglib.gui import GUI


def main(library_dir):
    try:
        library = DigitalLibrary(library_dir, XapianIndex, SQLAlchemyDatabase)
        gui = GUI(library)
        gui.start()
        library.close()
    except KeyboardInterrupt:
        pass # Exit process silently using CTRL-C.
