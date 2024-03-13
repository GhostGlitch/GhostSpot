__version__ = '0.8'
__author__ = 'Ghost Glitch'

import asyncio
import io
from typing import Any
from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSessionManager as TCSManager
from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSession as TCS
from winsdk.windows.storage.streams \
    import Buffer, InputStreamOptions, DataReader, IRandomAccessStreamReference
from PIL import Image



async def get_media_info() -> list:
    """ Returns a list of all active media as dicts of thier properties. """
    # Gets a list of all active TCS objects
    sessions= list((await TCSManager.request_async()).get_sessions()) # type: ignore
    # Returns a list of dictionaries of media info properties for each active
        # session, unless none can be found.
    coroutines = [trans_sesh(sesh) for sesh in sessions]
    return await asyncio.gather(*coroutines) if sessions else []


async def trans_sesh(sesh: TCS) -> dict[str, Any]:
    """ Translates a Windows TCS object into a more Python friendly dictionary.
    Returns:
        A rougly organized dictionary of the TCS object's attributes. 
        Including the thumbnail as a PIL image and the genres as a list. 
    """
    props = await sesh.try_get_media_properties_async()
    # Creates a dictionary from a MediaProperties object.
    transed_sesh = {
        'title': props.title,
        'artist': props.artist,
        'album_title': props.album_title,
        'album_artist': props.album_artist,
        # Converts the genres property to a Python list.
        'genres': list(props.genres), # type: ignore
        # Converts the thumbnail property to a PIL image.
        'thumbnail': await ref_to_img(props.thumbnail), # type: ignore
        'track_number': props.track_number,
        'album_track_count': props.album_track_count,
        'playback_type': props.playback_type.value, # type: ignore
        'subtitle': props.subtitle
    }
    return transed_sesh


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


# only run if the module is run directly.
if __name__ == '__main__':
    sessions = asyncio.run(get_media_info())
    if sessions:
        print(sessions)
        for i, sesh in enumerate(sessions):
            print (f'\nMedia {i+1}:')
            print(sesh)
            sesh['thumbnail'].show()
    else:
        print ( 'No active media found.')