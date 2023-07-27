# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _

from gi.repository import GObject


class LanguageModel(GObject.GObject):
    """
    This class rappresents a language object stored in the db.

    Properties:
        iso_name (str): ISO_639_1 code
        name (str): localized or English name

    Methods:
        None

    Signals:
        None
    """

    __gtype_name__ = 'LanguageModel'

    iso_name = GObject.Property(type=str, default='')
    name = GObject.Property(type=str, default='')

    def __init__(self, d=None):
        super().__init__()

        if d is not None:
            self.iso_name = d['iso_639_1']

            if d['name']:
                self.name = d['name']
            else:
                self.name = d['english_name']
