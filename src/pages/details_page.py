# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

from datetime import date
from gettext import gettext as _

from gi.repository import Adw, Gio, GObject, Gtk
from PIL import Image, ImageStat

from .. import shared  # type: ignore
from ..dialogs.add_manual_dialog import AddManualDialog
from ..models.movie_model import MovieModel
from ..models.series_model import SeriesModel
from ..providers.local_provider import LocalProvider as local
from ..widgets.episode_row import EpisodeRow


@Gtk.Template(resource_path=shared.PREFIX + '/ui/pages/details_page.ui')
class DetailsView(Adw.NavigationPage):
    """
    Widget that represents the details view.

    Properties:
        content (MovieModel or SeriesModel): content associated to the information shown

    Methods:
        None

    Signals:
        deleted: emited when the user confirms the deletion of the content
        edited: emited when a user confirms the edits for manually added content
    """

    __gtype_name__ = 'DetailsView'

    content = GObject.Property(type=object)

    __gsignals__ = {
        'deleted': (GObject.SIGNAL_RUN_FIRST, None, ()),
        'edited': (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    _background_picture = Gtk.Template.Child()
    _poster_picture = Gtk.Template.Child()
    _title_lbl = Gtk.Template.Child()
    _tagline_lbl = Gtk.Template.Child()
    _genres_lbl = Gtk.Template.Child()
    _chip1_lbl = Gtk.Template.Child()
    _chip2_lbl = Gtk.Template.Child()
    _chip3_lbl = Gtk.Template.Child()
    _watched_btn = Gtk.Template.Child()
    _edit_btn = Gtk.Template.Child()
    _description_box = Gtk.Template.Child()
    _overview_lbl = Gtk.Template.Child()
    _creator_box = Gtk.Template.Child()
    _creator_lbl = Gtk.Template.Child()
    _seasons_box = Gtk.Template.Child()
    _seasons_group = Gtk.Template.Child()
    _additional_info_box = Gtk.Template.Child()
    _flow_box = Gtk.Template.Child()

    def __init__(self, content: MovieModel | SeriesModel):
        super().__init__()
        self.content = content

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the "map" signal.
        Based on the type of self.content, shows the relevant information. Backdrop and poster image, title, tagline, genres, release date, and overview are always showed.

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        self.set_title(self.content.title)

        # Both movies and tv series
        if self.content.backdrop_path:

            if not Adw.StyleManager.get_default().get_high_contrast():
                self._background_picture.set_file(Gio.File.new_for_uri(self.content.backdrop_path))
                with Image.open(self.content.backdrop_path[7:]) as image:
                    stat = ImageStat.Stat(image.convert('L'))

                    luminance = [
                        min((stat.mean[0] + stat.extrema[0][0]) / 510, 0.7),
                        max((stat.mean[0] + stat.extrema[0][1]) / 510, 0.3),
                    ]
                self._background_picture.set_opacity(1 - luminance[0]
                                                     if Adw.StyleManager.get_default().get_dark()
                                                     else luminance[1])

        self._poster_picture.set_file(Gio.File.new_for_uri(self.content.poster_path))

        self._title_lbl.set_text(self.content.title)

        if self.content.tagline:
            self._tagline_lbl.set_visible(True)
            self._tagline_lbl.set_text(self.content.tagline)

        if self.content.genres:
            self._genres_lbl.set_visible(True)
            self._genres_lbl.set_label(', '.join(self.content.genres))

        if self.content.release_date:
            self._chip1_lbl.set_visible(True)
            self._chip1_lbl.set_text(date.fromisoformat(self.content.release_date).strftime('%d %B %Y'))

        if self.content.watched:
            self._watched_btn.set_label(_('Watched'))
            self._watched_btn.set_icon_name('check-plain')
        else:
            self._watched_btn.set_label(_('In your watchlist'))
            self._watched_btn.set_icon_name('watchlist')

        if self.content.manual:
            self._edit_btn.set_visible(True)

        if self.content.overview:
            self._description_box.set_visible(True)
            self._overview_lbl.set_label(self.content.overview)

        # Movie specific
        if type(self.content) is MovieModel:
            if self.content.runtime:
                self._chip2_lbl.set_visible(True)
                self._chip2_lbl.set_text(self._format_runtime(self.content.runtime))

        # TV series specific
        if type(self.content) is SeriesModel:
            if self.content.seasons_number:
                self._chip2_lbl.set_visible(True)
                self._chip2_lbl.set_text(_('{num} Seasons').format(num=self.content.seasons_number))

            if self.content.episodes_number:
                self._chip3_lbl.set_visible(True)
                self._chip3_lbl.set_text(_('{num} Episodes').format(num=self.content.episodes_number))

            if self.content.created_by:
                self._creator_box.set_visible(True)
                self._creator_lbl.set_text(', '.join(self.content.created_by))

            self._seasons_box.set_visible(True)
            self._build_seasons_group()

        self._build_flow_box()

    def _build_seasons_group(self) -> None:
        """
        Creates the widgets needed to show season and episodes metadata.

        Args:
            None

        Returns:
            None
        """

        list_box = self._seasons_group.get_first_child().get_last_child().get_first_child()
        if list_box.get_row_at_index(0):
            return

        for season in self.content.seasons:
            season_row = Adw.ExpanderRow(title=season.title,
                                         subtitle=_('{num} Episodes').format(num=season.episodes_number))

            poster = Gtk.Picture(height_request=112,
                                 width_request=75,
                                 content_fit=Gtk.ContentFit.FILL,
                                 margin_top=12,
                                 margin_bottom=12)
            poster.add_css_class('still')
            poster.set_file(Gio.File.new_for_uri(season.poster_path))
            season_row.add_prefix(poster)

            check_btn = Gtk.CheckButton(label=('Watched'))
            check_btn.connect('toggled', self._on_season_check_btn_toggle, check_btn)
            season_row.add_suffix(check_btn)

            for episode in season.episodes:
                episode_row = EpisodeRow(episode)
                season_row.add_row(episode_row)

            self._seasons_group.add(season_row)

    def _build_flow_box(self) -> None:
        """
        Adds the available metadata to the 'additional information' section.

        Args:
            None

        Returns:
            None
        """

        if self._flow_box.get_child_at_index(0):
            return

        # Both movies and tv series
        if self.content.status:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Status'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=self.content.status))
            self._flow_box.append(box)

        if self.content.original_language and self.content.original_language.iso_name != 'xx':
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Original Language'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=self.content.original_language.name))
            self._flow_box.append(box)

        if self.content.original_title:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('Original Title'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=self.content.original_title))
            self._flow_box.append(box)

        # Movie specific
        if type(self.content) is MovieModel:
            if self.content.budget:
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                label = Gtk.Label(label=_('Budget'))
                label.add_css_class('heading')
                box.append(label)
                box.append(Gtk.Label(label=f'US$ {self.content.budget}'))
                self._flow_box.append(box)

            if self.content.revenue:
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
                label = Gtk.Label(label=_('Revenue'))
                label.add_css_class('heading')
                box.append(label)
                box.append(Gtk.Label(label=f'US$ {self.content.revenue}'))
                self._flow_box.append(box)

        # TV series specific
        if type(self.content) is SeriesModel:
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            label = Gtk.Label(label=_('In Production'))
            label.add_css_class('heading')
            box.append(label)
            box.append(Gtk.Label(label=_('Yes') if self.content.in_production else _('No')))
            self._flow_box.append(box)

        if self._flow_box.get_child_at_index(0) is None:
            self._additional_info_box.set_visible(False)

    def _format_runtime(self, runtime: str) -> str:
        """
        Formats the runtime in hours and minutes.

        Args:
            runtime (str): runtime in minutes

        Returns:
            formatted duration string in hours and minutes
        """

        h, m = divmod(int(runtime), 60)

        if h > 0:
            return _('{h}h {m}min').format(h=h, m=m)
        else:
            return _('{m}min').format(m=m)

    def _on_season_check_btn_toggle(self, check_btn: Gtk.CheckButton) -> None:
        # TODO implement
        pass

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

        if type(self.content) is MovieModel:
            local.mark_watched_movie(self.content.id, not self.content.watched)
        else:
            local.mark_watched_series(self.content.id, not self.content.watched)

        self.content.watched = not self.content.watched

        if self.content.watched:
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

        Args:
            user_data (object or None): additional data passed to the callback

        Returns:
            None
        """

        dialog = AddManualDialog(self.get_ancestor(Gtk.Window), True, self.content)
        dialog.connect('edit-saved', self._on_edit_saved)
        dialog.present()

    def _on_edit_saved(self, source: Gtk.Widget, content: MovieModel | SeriesModel) -> None:
        """
        Callback for "edit-saved" signal.
        Replaces the navigation stack with an updated top page resulting in a content refresh.

        Args:
            source (Gtk.Widget): caller widget
            content (MovieModel or SeriesModel): updated content to show

        Returns:
            None
        """

        root_page = self.get_ancestor(Adw.NavigationView).get_previous_page(self)
        self.get_ancestor(Adw.NavigationView).replace([root_page, DetailsView(content)])

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

        dialog = Adw.MessageDialog.new(self.get_ancestor(Adw.ApplicationWindow),
                                       _('Delete {title}?').format(title=self.content.title),
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

        if type(self.content) is MovieModel:
            local.delete_movie(self.content.id)
        else:
            local.delete_series(self.content.id)

        self.get_ancestor(Adw.NavigationView).pop()
        self.emit('deleted')
