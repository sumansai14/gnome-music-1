from gi.repository import TotemPlParser, Grl, GLib, Gio, GObject
from gnomemusic.grilo import grilo

import os


class Playlists(GObject.GObject):
    __gsignals__ = {
        'playlist-created': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'playlist-deleted': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'song-added-to-playlist': (GObject.SIGNAL_RUN_FIRST, None, (str, Grl.Media)),
    }
    instance = None

    @classmethod
    def get_default(self):
        if self.instance:
            return self.instance
        else:
            self.instance = Playlists()
        return self.instance

    def __init__(self):
        GObject.GObject.__init__(self)
        self.playlist_dir = os.path.join(GLib.get_user_data_dir(),
                                         'gnome-music',
                                         'playlists')

    def create_playlist(self, name, iterlist=None):
        parser = TotemPlParser.Parser()
        playlist = TotemPlParser.Playlist()
        pl_file = Gio.file_new_for_path(self.get_path_to_playlist(name))
        if iterlist is not None:
            for _iter in iterlist:
                pass
        else:
            _iter = TotemPlParser.PlaylistIter()
            playlist.append(_iter)
        parser.save(playlist, pl_file, name, TotemPlParser.ParserType.PLS)
        self.emit('playlist-created', name)
        return False

    def get_playlists(self):
        playlist_files = [pl_file for pl_file in os.listdir(self.playlist_dir)
                          if os.path.isfile(os.path.join(self.playlist_dir,
                                                         pl_file))]
        playlist_names = []
        for playlist_file in playlist_files:
            name, ext = os.path.splitext(playlist_file)
            playlist_names.append(name)
        return playlist_names

    def add_to_playlist(self, playlist_name, uris):
        parser = TotemPlParser.Parser()
        playlist = TotemPlParser.Playlist()
        pl_file = Gio.file_new_for_path(self.get_path_to_playlist(playlist_name))

        def parse_callback(parser, uri, metadata, data):
            _iter = TotemPlParser.PlaylistIter()
            playlist.append(_iter)
            playlist.set_value(_iter, TotemPlParser.PARSER_FIELD_URI, uri)

        def end_callback(parser, uri, data):
            for uri in uris:
                _iter = TotemPlParser.PlaylistIter()
                playlist.append(_iter)
                playlist.set_value(_iter, TotemPlParser.PARSER_FIELD_URI, uri)

                def get_callback(source, param, item):
                    self.emit('song-added-to-playlist', playlist_name, item)
                grilo.get_media_from_uri(uri, get_callback)

            parser.save(playlist, pl_file, playlist_name, TotemPlParser.ParserType.PLS)

        parser.connect('entry-parsed', parse_callback, playlist)
        parser.connect('playlist-ended', end_callback, playlist)
        parser.parse_async(
            GLib.filename_to_uri(self.get_path_to_playlist(playlist_name), None),
            False, None, None, None
        )

    def delete_playlist(self, playlist_name):
        playlist_file = self.get_path_to_playlist(playlist_name)
        if os.path.isfile(playlist_file):
            os.remove(playlist_file)
            self.emit('playlist-deleted', playlist_name)

    def get_path_to_playlist(self, playlist_name):
        return os.path.join(self.playlist_dir, "%s.pls" % playlist_name)

    def parse_playlist(self, playlist_name, callback):
        parser = TotemPlParser.Parser()
        parser.connect('entry-parsed', self._on_entry_parsed, callback)
        parser.parse_async(
            GLib.filename_to_uri(self.get_path_to_playlist(playlist_name), None),
            False, None, None, None
        )

    def _on_entry_parsed(self, parser, uri, metadata, data=None):
        filename = GLib.filename_from_uri(uri)[0]
        if filename and not os.path.isfile(filename):
            return

        grilo.get_media_from_uri(uri, data)
