# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk


@Gtk.Template(resource_path='/me/iepure/ticketbooth/ui/window.ui')
class TicketboothWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'TicketboothWindow'

    label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
