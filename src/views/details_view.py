# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import date
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, GObject, Gtk
from PIL import Image, ImageStat

from .. import shared  # type: ignore
from ..models.movie_model import MovieModel
from ..providers.local_provider import LocalProvider as local


@Gtk.Template(resource_path=shared.PREFIX + '/ui/views/details_view.ui')
class DetailsView(Adw.Window):
    """
    Widget that represents the details view.

    Properties:
        movie (MovieModel): movie associated to the information shown

    Methods:
        None

    Signals:
        deleted: emited when the user confirms the deletion of a movie
        edited: emited when a user confirmas the edits for manually added content
    """

    __gtype_name__ = 'DetailsView'

    movie = GObject.Property(type=MovieModel)

    __gsignals__ = {
        'deleted': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'edited': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    _background_picture = Gtk.Template.Child()
    _poster_picture = Gtk.Template.Child()
    _genres_lbl = Gtk.Template.Child()
    _watched_btn = Gtk.Template.Child()
    _flow_box = Gtk.Template.Child()

    def __init__(self, movie: MovieModel):
        super().__init__()
        self.movie = movie

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the "map" signal.
        Sets a blurred background image matching the active color scheme, the poster image, formats the genres label, sets the icon for the button and builds the additional information.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        if self.movie.backdrop_path:
            self._background_picture.set_file(Gio.File.new_for_uri(self.movie.backdrop_path))
            with Image.open(self.movie.backdrop_path[7:]) as image:
                stat = ImageStat.Stat(image.convert('L'))

                luminance = [
                    min((stat.mean[0] + stat.extrema[0][0]) / 510, 0.7),
                    max((stat.mean[0] + stat.extrema[0][1]) / 510, 0.3),
                ]
            self._background_picture.set_opacity(1 - luminance[0]
                                                 if Adw.StyleManager.get_default().get_dark()
                                                 else luminance[1])

        self._poster_picture.set_file(Gio.File.new_for_uri(self.movie.poster_path))
        self._genres_lbl.set_label(', '.join(self.movie.genres))

        if self.movie.watched:
            self._watched_btn.set_label(_('Watched'))
            self._watched_btn.set_icon_name('check-plain')
        else:
            self._watched_btn.set_label(_('In your watchlist'))
            self._watched_btn.set_icon_name('watchlist')

        self._build_flow_box()

    def _build_flow_box(self) -> None:
        """
        Adds the available metadata to the 'additional information' section.

        Args:
            None

        Returns:
            None
        """

        if self.movie.status:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Status'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=self.movie.status))
            self._flow_box.append(box)

        if self.movie.budget:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Budget'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=f'US$ {self.movie.budget}'))
            self._flow_box.append(box)

        if self.movie.revenue:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Revenue'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=f'US$ {self.movie.revenue}'))
            self._flow_box.append(box)

        if self.movie.original_language:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Original Language'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=self.movie.original_language.name))
            self._flow_box.append(box)

        if self.movie.original_title:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Original Title'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=self.movie.original_title))
            self._flow_box.append(box)

    @Gtk.Template.Callback('_format_release_date')
    def _format_release_date(self, source: Gtk.Widget, release_date: str) -> str:
        """
        Closure to format the release date.

        Args:
            source (Gtk.Widget): caller widget
            release_date (str): date string to format

        Returns:
            formatted date string
        """

        return date.fromisoformat(release_date).strftime('%d %B %Y')

    @Gtk.Template.Callback('_format_runtime')
    def _format_runtime(self, source: Gtk.Widget, runtime: str) -> str:
        """
        Closure to compute runtime in hours and minutes.

        Args:
            source (Gtk.Widget): caller widget
            runtime (int): runtime in minutes

        Returns:
            formatted duration string in hours and minutes
        """

        h, m = divmod(int(runtime), 60)
        return f'{h}h {m}min'

    @Gtk.Template.Callback('_set_visibility')
    def _set_visibility(self, source: Gtk.Widget, text: str) -> bool:
        """
        Closure to return the visibility of a widget if a string is present.

        Args:
            source (Gtk.Widget): caller widget
            text (str): text to check if it is available

        Returns:
            bool
        """

        return True if text else False

    @Gtk.Template.Callback('_on_watched_btn_clicked')
    def _on_watched_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Updates the watched flag for the content in the db and changes the button text accordingly.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        local.mark_watched_movie(self.movie.id, not self.movie.watched)
        self.movie.watched = not self.movie.watched
        if self.movie.watched:
            self._watched_btn.set_label(_('Watched'))
            self._watched_btn.set_icon_name('check-plain')
        else:
            self._watched_btn.set_label(_('In your watchlist'))
            self._watched_btn.set_icon_name('watchlist')

    @Gtk.Template.Callback('_on_edit_btn_clicked')
    def _on_edit_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Opens the edit window to change the metadata of the content. Available only for manually added content.
        TODO: unimplemented

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """
        pass

    @Gtk.Template.Callback('_on_delete_btn_clicked')
    def _on_delete_btn_clicked(self, user_data: object | None) -> None:
        """
        Callback for the "clicked" signal.
        Asks the user for a confirmation after a delete request.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        dialog = Adw.MessageDialog.new(self,
                                       _('Delete {title}?').format(title=self.movie.title),
                                       _('This title will be deleted from your watchlist.')
                                       )
        dialog.add_response('cancel', _('_Cancel'))
        dialog.add_response('delete', _('_Delete'))
        dialog.set_response_appearance('delete', Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.choose(None, self._on_message_dialog_choose, None)

    def _on_message_dialog_choose(self, source: GObject.Object | None, result: Gio.AsyncResult, user_data: object | None) -> None:
        """
        Callback for the message dialog.
        Finishes the async operation and retrieves the user response. If the later is positive, delete the content from the db.

        Args:
            source (Gtk.Widget): object that started the async operation
            result (Gio.AsyncResult): a Gio.AsyncResult
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        result = Adw.MessageDialog.choose_finish(source, result)
        if result == 'cancel':
            return
        local.delete_movie(self.movie.id)
        self.close()
        self.emit('deleted')
