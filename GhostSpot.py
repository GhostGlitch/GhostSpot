__version__ = '0.8'
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




@dataclass()
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
        return (f'Title: {self.title} | '
                f'Artist: {self.artist} | '
                f'Album Title: {self.album_title} | '
                f'Album Artist: {self.album_artist} | '
                f'Genres: {self.genres} | '
                f'Track Number: {self.track_number} | '
                f'Album Track Count: {self.album_track_count} | '
                f'Playback Type: {self.playback_type.name} | '
                f'Subtitle: {self.subtitle} | ')


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

async def output(sesh : PySession, i: int) -> None:
    print (f'\nMedia {i+1}:')
    print (sesh)
    sesh.thumbnail.show()
    return


if __name__ == '__main__':
    sessions = asyncio.run(get_media_info())
    if sessions:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = [output(sesh, i) for i, sesh in enumerate(sessions)]
        loop.run_until_complete(asyncio.gather(*tasks))
    else:
        print('No active media found.')
