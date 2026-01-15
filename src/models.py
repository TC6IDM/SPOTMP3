from typing import List, Optional


class Playlist:
    name: str
    playlist_url: str
    length: int
    songs: Optional[List['Song']]
    def __init__(self, playlist_url: str, name: str = "", length: int = 0, songs: Optional[List['Song']] = None):
        self.name = name
        self.playlist_url = playlist_url
        self.length = length
        self.songs = songs or []
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "playlist_url": self.playlist_url,
            "length": self.length,
            "songs": [song.to_dict() for song in self.songs]
        }
        
class Song:
    title: str
    artists: List[str]
    song_url: str
    playlist_url: str
    error: str
    playlist: Playlist
    list_position: str

    def __init__(self, song_url: str, playlist_url: str = None, error: str = "", title: str = "", artists: Optional[List[str]] = None, playlist: Playlist = None, list_position: str = ""):
        self.title = title
        self.artists = artists or []
        self.song_url = song_url
        self.playlist_url = playlist_url
        self.error = error
        if playlist == None: self.playlist = Playlist(playlist_url)
        else: self.playlist = playlist
        self.list_position = list_position
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "artists": self.artists,
            "song_url": self.song_url,
            "playlist_url": self.playlist_url,
            "error": self.error,
            "playlist": self.playlist.to_dict(),
            "list_position": self.list_position
        }