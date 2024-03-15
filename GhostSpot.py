__version__ = '0.8.5'
__author__ = 'Ghost Glitch'

import asyncio
from enum import Enum
import io
from typing import Any
from dataclasses import dataclass

from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSessionManager as TCSManager, \
        GlobalSystemMediaTransportControlsSession as TCS
from winsdk.windows.media import MediaPlaybackType
from winsdk.windows.storage.streams \
    import Buffer, InputStreamOptions, DataReader, IRandomAccessStreamReference
from PIL import Image
import sys
print(sys.version)



@dataclass
class PySession():
    """ A dataclass to store the properties of a TCS object in a more Pythonic way. """

    def __init__(self, title: str, artist: str, album_title: str, album_artist: str, genres: list[str], thumbnail: Image.Image, track_number: int, album_track_count: int, playback_type: MediaPlaybackType | None, subtitle: str) -> None:
        self.title = title
        self.artist = artist
        self.album_title = album_title
        self.album_artist = album_artist
        self.genres = genres
        self.thumbnail = thumbnail
        self.track_number = track_number
        self.album_track_count = album_track_count
        self.playback_type = playback_type
        self.subtitle = subtitle
    def __str__(self) -> str:
        attributes = {
            'Album Artist': self.album_artist,
            'Genres': self.genres,
            'Track Number': self.track_number,
            'Album Track Count': self.album_track_count,
            'Playback Type': self.playback_type.name,
            'Subtitle': self.subtitle
        }
        basic = (f'”{self.title}” BY {self.artist} ON {self.album_title} \n')
        return basic + ' | '.join(f'{name}: {value}' for name, value in attributes.items() if value)
    
    def __setattr__(self, __name: str, __value: Any) -> None:
        match __name:
            case "title":
                __value = "Unknown Title" if not __value else __value 
            case "artist":
                __value = "Unknown Artist" if not __value else __value 
            case "album_title":
                __value = "Unknown Album" if not __value else __value 
            case "album_artist":
                __value = None if not __value or __value == self.artist else __value
            case "genres" | "track_number" | "album_track_count" | "subtitle" | "thumbnail":
                __value = None if not __value else __value 
            case "playback_type":
                __value = MediaPlaybackType.UNKNOWN if not __value else __value 
            case _:
                raise ValueError(f'Invalid attribute name: {__name}')
        super().__setattr__(__name, __value)


async def get_media_info() -> list[PySession]:
    """ Returns a list of all active media as dicts of thier properties. """
    # Gets a list of all active TCS objects
    sessions= list((await TCSManager.request_async()).get_sessions())  # type: ignore
    # Returns a list of PySessions for each active
    # session, unless none can be found.
    return [] if not sessions else \
        await asyncio.gather (*[trans_sesh(sesh) for sesh in sessions])


async def trans_sesh(sesh: TCS) -> PySession:
    """ Translates a Windows TCS object into PySession Object. """
    props = await sesh.try_get_media_properties_async()
    assert props.thumbnail is not None
    return PySession(props.title, props.artist, props.album_title, props.album_artist, list(props.genres), await ref_to_img(props.thumbnail), props.track_number, props.album_track_count, props.playback_type, props.subtitle) # type: ignore


async def ref_to_img(stream_ref: IRandomAccessStreamReference) -> Image.Image:
    """ Converts an IRandomAccessStreamReference object to a PIL image. """    # Opens a stream from the reference
    stream = await stream_ref.open_read_async()
    img_buffer = Buffer(stream.size)
    image_bytes = bytearray(stream.size)
    # Reads data from the stream into the buffer 
    await stream.read_async(img_buffer, img_buffer.capacity, InputStreamOptions.READ_AHEAD) # type: ignore
    # Reads data from the buffer into the image_bytes bytearray.
    DataReader.from_buffer(img_buffer).read_bytes(image_bytes) # type: ignore
    # Converts the bytearray to a PIL image and returns it.

    return Image.open(io.BytesIO(image_bytes))


if __name__ == '__main__':
    sessions = asyncio.run(get_media_info())
    if sessions:
        for i, sesh in enumerate(sessions):
            print (f'\nMedia {i+1}:')
            print (sesh)
            sesh.thumbnail.show()
    else:
        print('No active media found.')
