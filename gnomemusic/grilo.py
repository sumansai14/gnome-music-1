# Copyright (c) 2013 Vadim Rutkovsky <vrutkovs@redhat.com>
# Copyright (c) 2013 Arnel A. Borja <kyoushuu@yahoo.com>
# Copyright (c) 2013 Seif Lotfy <seif@lotfy.com>
# Copyright (c) 2013 Guillaume Quintard <guillaume.quintard@gmail.com>
#
# GNOME Music is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# GNOME Music is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with GNOME Music; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# The GNOME Music authors hereby grant permission for non-GPL compatible
# GStreamer plugins to be used and distributed together with GStreamer
# and GNOME Music.  This permission is above and beyond the permissions
# granted by the GPL license by which GNOME Music is covered.  If you
# modify this code, you may extend this exception to your version of the
# code, but you are not obligated to do so.  If you do not wish to do so,
# delete this exception statement from your version.


from gi.repository import Grl, GLib, GObject

from gnomemusic.query import Query


class Grilo(GObject.GObject):

    __gsignals__ = {
        'ready': (GObject.SIGNAL_RUN_FIRST, None, ())
    }

    METADATA_KEYS = [
        Grl.METADATA_KEY_ID, Grl.METADATA_KEY_TITLE,
        Grl.METADATA_KEY_ARTIST, Grl.METADATA_KEY_ALBUM,
        Grl.METADATA_KEY_DURATION,
        Grl.METADATA_KEY_CREATION_DATE]

    METADATA_THUMBNAIL_KEYS = [
        Grl.METADATA_KEY_ID,
        Grl.METADATA_KEY_THUMBNAIL,
    ]

    def __init__(self):
        GObject.GObject.__init__(self)
        self.playlist_path = GLib.build_filenamev([GLib.get_user_data_dir(),
                                                  "gnome-music", "playlists"])
        if not (GLib.file_test(self.playlist_path, GLib.FileTest.IS_DIR)):
            GLib.mkdir_with_parents(self.playlist_path, int("0755", 8))
        self.options = Grl.OperationOptions()
        self.options.set_flags(Grl.ResolutionFlags.FULL |
                               Grl.ResolutionFlags.IDLE_RELAY)

        self.sources = {}
        self.tracker = None

        self.registry = Grl.Registry.get_default()
        self.registry.connect('source_added', self._on_source_added)
        self.registry.connect('source_removed', self._on_source_removed)

        try:
            self.registry.load_all_plugins()
        except GLib.GError:
            print('Failed to load plugins.')

    def _on_source_added(self, pluginRegistry, mediaSource):
        id = mediaSource.get_id()
        if id == 'grl-tracker-source':
            ops = mediaSource.supported_operations()
            if ops & Grl.SupportedOps.SEARCH:
                print('Detected new source available: \'%s\' and it supports search' %
                      mediaSource.get_name())

                self.sources[id] = mediaSource
                self.tracker = mediaSource

                if self.tracker is not None:
                    self.emit('ready')

    def _on_source_removed(self, pluginRegistry, mediaSource):
        print('source removed')

    def populate_artists(self, offset, callback):
        self.populate_items(Query.ARTISTS, offset, callback)

    def populate_albums(self, offset, callback, count=50):
        self.populate_items(Query.ALBUMS, offset, callback, count)

    def populate_songs(self, offset, callback, count=-1):
        self.populate_items(Query.SONGS, offset, callback, count)

    def populate_album_songs(self, album_id, callback):
        self.populate_items(Query.album_songs(album_id), 0, callback)

    def populate_items(self, query, offset, callback, count=50):
        options = self.options.copy()
        options.set_skip(offset)
        if count != -1:
            options.set_count(count)

        def _callback(source, param, item, count, data, offset):
            callback(source, param, item)
        self.tracker.query(query, self.METADATA_KEYS, options, _callback, None)

    def _search_callback(self):
        print('yeah')

    def search(self, q):
        options = self.options.copy()
        for source in self.sources:
            print(source.get_name() + ' - ' + q)
            source.search(q, [Grl.METADATA_KEY_ID], 0, 10,
                          options, self._search_callback, source)

    def get_album_art_for_album_id(self, album_id, _callback):
        options = self.options.copy()
        query = Query.get_album_for_id(album_id)
        self.tracker.query(query, self.METADATA_THUMBNAIL_KEYS, options, _callback, None)

    def get_media_from_uri(self, uri, callback):
        options = self.options.copy()
        query = Query.get_song_with_url(uri)

        def _callback(source, param, item, count, data, error):
            if not error:
                callback(source, param, item)
                return

        self.tracker.query(query, self.METADATA_KEYS, options, _callback, None)

Grl.init(None)

grilo = Grilo()
