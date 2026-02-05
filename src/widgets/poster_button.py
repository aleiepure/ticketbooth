# Copyright (C) 2023 Alessandro Iepure
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
PosterButton - Widget for displaying movie/series poster in grid views.

Supports widget recycling for Gtk.GridView:
- update_content(): Update widget with new model data
- reset_state(): Clear state before recycling

Async Image Loading:
- Uses Gdk.Texture.new_from_filename() in background thread
- GLib.idle_add() for main thread UI updates
- Prevents scrollbar jitter during fast drag
"""

import logging
import threading
from gi.repository import Gdk, Gio, GLib, GObject, Gtk
from pathlib import Path
from .. import shared  # type: ignore
from ..models.movie_model import MovieModel
from ..models.series_model import SeriesModel


@Gtk.Template(resource_path=shared.PREFIX + '/ui/widgets/poster_button.ui')
# =============================================================================
# POSTER BUTTON - Widget Recycling Worker
# =============================================================================
# This widget represents each movie/series card on the main screen.
# It is the most important part of GridView's "Recycling" mechanism.
#
# WHY IS IT IMPORTANT?
# - A new button is NOT created on each scroll.
# - The update_content() method only changes the data (title, image)
#   inside the existing button. This saves CPU and prevents RAM bloat.
#
# CRITICAL METHODS:
# 1. update_content: Binds new movie data to the button.
# 2. reset_state: Clears the button from old data (before new data arrives).
# =============================================================================
class PosterButton(Gtk.Box):
    """
    Widget shown in the main view with poster, title, and release year.

    Properties:
        title (str): content's title
        year (str): content's release year
        tmdb_id (str): content's tmdb id
        poster_path (str): content's poster uri

    Methods:
        update_content(): Update widget for new model (recycling)
        reset_state(): Clear state before recycling

    Signals:
        clicked(content: MovieModel or SeriesModel): emited when the user clicks on the widget
    """

    __gtype_name__ = 'PosterButton'

    _poster_box = Gtk.Template.Child()
    _picture = Gtk.Template.Child()
    _spinner = Gtk.Template.Child()
    _year_lbl = Gtk.Template.Child()
    _status_lbl = Gtk.Template.Child()
    _watched_lbl = Gtk.Template.Child()
    _new_release_badge = Gtk.Template.Child()
    _soon_release_badge = Gtk.Template.Child()
    _watched_badge = Gtk.Template.Child()


    # Properties
    title = GObject.Property(type=str, default='')
    year = GObject.Property(type=str, default='')
    status = GObject.Property(type=str, default='')
    tmdb_id = GObject.Property(type=str, default='')
    poster_path = GObject.Property(type=str, default='')
    watched = GObject.Property(type=bool, default=False)
    content = GObject.Property(type=object, default=None)

    __gsignals__ = {
        'clicked': (GObject.SIGNAL_RUN_FIRST, None, (object,)),
    }

    def __init__(self, content: MovieModel | SeriesModel | None = None):
        super().__init__()
        
        # Initialize state variables
        self.activate_notification = False
        self.badge_color_light = False
        self.new_release = False
        self.soon_release = False
        self.recent_change = False
        
        # Async image loading cancellation token
        self._load_id = 0
        
        # Jitter Fix: By fixing only the vertical height, we disable GridView's
        # estimation mechanism. Width (-1) remains automatic to preserve UI responsivity.
        self.set_size_request(-1, 315)
        
        # If content provided, update immediately
        if content is not None:
            self.update_content(content)

    def update_content(self, content: MovieModel | SeriesModel) -> None:
        """
        Update widget with new model data.
        Called by GridView's bind callback for widget recycling.
        
        NOTE: reset_state() is NOT called here because according to GTK4 factory
        lifecycle, unbind already runs before bind and reset happens there.
        Reference: https://docs.gtk.org/gtk4/class.SignalListItemFactory.html
        """
        # Store content reference
        self.content = content
        
        # Update properties from model
        self.activate_notification = content.activate_notification
        self.title = content.title
        self.badge_color_light = content.color
        self.year = content.release_date[0:4] if content.release_date else ''
        self.tmdb_id = content.id
        self.poster_path = content.poster_path
        self.watched = content.watched
        self.status = content.status
        self.new_release = content.new_release
        self.soon_release = content.soon_release
        self.recent_change = content.recent_change
        
        # Apply visual state
        self._apply_visual_state()

    def reset_state(self) -> None:
        """
        Reset widget state before recycling.
        Called by GridView's unbind callback.
        """
        # Cancel any pending async image loads
        self._load_id += 1
        
        # Clear content reference
        self.content = None
        
        # Reset properties
        self.title = ''
        self.year = ''
        self.status = ''
        self.tmdb_id = ''
        self.poster_path = ''
        self.watched = False
        self.activate_notification = False
        self.badge_color_light = False
        self.new_release = False
        self.soon_release = False
        self.recent_change = False
        
        # Reset visual state
        self._reset_visual_state()

    def _apply_visual_state(self) -> None:
        """
        Apply visual properties based on current content.
        
        5-Layer Verification:
        - Layer 5 (Logic): Spinner visibility is managed per load type:
          - Sync (resource://): Hide spinner immediately after set_resource.
          - Async (file://): Keep spinner visible; callbacks will hide it.
          - No path: Hide spinner.
        """
        logging.info(f"[PosterButton] Applying visual state for: {self.title}, Path: {self.poster_path}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # POSTER LOADING LOGIC (LAYER 5: CORRECT SPINNER STATE)
        # ═══════════════════════════════════════════════════════════════════════
        if self.poster_path:
            if self.poster_path.startswith('resource://'):
                # SYNC: Resource scheme -> In-memory, loads instantly
                resource_path = self.poster_path.replace('resource://', '')
                self._picture.set_resource(resource_path)
                # SYNC LOAD COMPLETE: Hide spinner now
                self._spinner.set_visible(False)
            else:
                # ASYNC: File scheme or plain path -> Threaded load
                # Spinner will be shown by _load_image_async
                # Spinner will be hidden by _set_texture_main or _on_load_error
                self._load_image_async(self.poster_path)
                # DO NOT HIDE SPINNER HERE! Async callback will do it.
        else:
            # NO PATH: Nothing to load, hide spinner
            self._spinner.set_visible(False)
        
        # ═══════════════════════════════════════════════════════════════════════
        # BADGE LOGIC
        # ═══════════════════════════════════════════════════════════════════════
        badge_visible = False
        if self.activate_notification:
            if self.recent_change:
                self._poster_box.add_css_class("pulse")
                self._picture.add_css_class("shadow")
            
            if self.new_release:
                self._new_release_badge.set_visible(True)
                badge_visible = True
                if self.badge_color_light:
                    self._new_release_badge.add_css_class("light")
                else:
                    self._new_release_badge.add_css_class("dark")
            elif self.soon_release:
                self._soon_release_badge.set_visible(True)
                badge_visible = True
                if self.badge_color_light:
                    self._soon_release_badge.add_css_class("light")
                else:
                    self._soon_release_badge.add_css_class("dark")
        
        # Year label
        self._year_lbl.set_visible(bool(self.year))
        
        # Status label
        self._status_lbl.set_visible(bool(self.status))
        
        # Watched badge
        if self.watched and not badge_visible:
            self._watched_badge.set_visible(True)
            if self.badge_color_light:
                self._watched_badge.add_css_class("light")
            else:
                self._watched_badge.add_css_class("dark")


    def _load_image_async(self, uri: str) -> None:
        """Async image loading with debug logs."""
        self._load_id += 1
        current_id = self._load_id
        
        # 1. Check: Is it in cache?
        if uri in shared.TEXTURE_CACHE:
            self._picture.set_paintable(shared.TEXTURE_CACHE[uri])
            self._spinner.set_visible(False)
            return

        # 2. Start the spinner
        self._spinner.set_visible(True)

        def load_thread():
            # Check if button was recycled immediately
            if self._load_id != current_id:
                return

            try:
                logging.debug(f"[PosterButton] Loading: {uri}")
                
                # Check for file:// protocol and strip it to use new_for_path
                # This avoids any URI encoding ambiguity (spaces etc)
                if uri.startswith('file://'):
                    clean_path = uri[7:] # strip file://
                    # Verify existence before hitting Gdk
                    path_obj = Path(clean_path)
                    if not path_obj.exists():
                        raise FileNotFoundError(f"File not found: {clean_path}")
                        
                    file = Gio.File.new_for_path(clean_path)
                elif uri.startswith('resource://'):
                    file = Gio.File.new_for_uri(uri)
                else:
                    # Fallback for plain paths (just in case)
                    file = Gio.File.new_for_path(uri)
                
                # Load texture (thread-safe in GTK4)
                texture = Gdk.Texture.new_from_file(file)
                
                # Cache success
                shared.TEXTURE_CACHE[uri] = texture
                logging.debug(f"[PosterButton] Loaded: {uri}")
                
                # Update UI
                GLib.idle_add(self._set_texture_main, texture, current_id)
            except Exception as e:
                logging.error(f"[PosterButton] Error loading {uri}: {e}")
                GLib.idle_add(self._on_load_error, current_id)

        # Threading is safe for Gdk.Texture.new_from_file
        thread = threading.Thread(target=load_thread, daemon=True)
        thread.start()

    def _on_load_error(self, load_id: int) -> bool:
        if load_id == self._load_id:
            self._spinner.set_visible(False)
            # Fallback to blank poster on error
            try:
                self._picture.set_resource(f"{shared.PREFIX}/blank_poster.jpg")
            except Exception:
                pass # fail silently if resource missing
        return False

    def _set_texture_main(self, texture: Gdk.Texture, load_id: int) -> bool:
        """Update UI and stop spinner."""
        if load_id == self._load_id:
            self._picture.set_paintable(texture)
            self._spinner.set_visible(False)
        return False


    def _reset_visual_state(self) -> None:
        """Reset all visual state for recycling."""
        # Clear image and show spinner
        self._picture.set_file(None)
        self._spinner.set_visible(True)
        
        # Reset badges
        self._new_release_badge.set_visible(False)
        self._soon_release_badge.set_visible(False)
        self._watched_badge.set_visible(False)
        
        # Remove css classes
        self._poster_box.remove_css_class("pulse")
        self._picture.remove_css_class("shadow")
        self._new_release_badge.remove_css_class("light")
        self._new_release_badge.remove_css_class("dark")
        self._soon_release_badge.remove_css_class("light")
        self._soon_release_badge.remove_css_class("dark")
        self._watched_badge.remove_css_class("light")
        self._watched_badge.remove_css_class("dark")
        
        # Reset labels visibility
        self._year_lbl.set_visible(True)
        self._status_lbl.set_visible(True)

    @Gtk.Template.Callback('_on_map')
    def _on_map(self, user_data: object | None) -> None:
        """
        Callback for the 'map' signal.
        For GridView recycling, visual state is set in update_content().
        This is kept for backward compatibility with FlowBox.
        """
        # Only apply if content exists and not using GridView recycling
        if self.content and self.poster_path:
            self._apply_visual_state()

    @Gtk.Template.Callback('_on_poster_btn_clicked')
    def _on_poster_btn_clicked(self, user_data: object | None) -> None:
        if self.content:
            self.emit('clicked', self.content)

