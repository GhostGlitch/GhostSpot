__version__ = '0.7'
__author__ = 'Ghost Glitch'

import asyncio
import io
from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSessionManager as TCSManager
from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSession as TCS
from winsdk.windows.storage.streams \
    import Buffer, InputStreamOptions, DataReader, IRandomAccessStreamWithContentType
from PIL import Image
import threading


async def get_media_info() -> list:
    """ Returns a list of all active media as dicts of thier properties. """
    info: list[dict[str, str|Image.Image]] = []
    # Gets a list of all active TCS objects
    sessions= list((await TCSManager.request_async()).get_sessions()) # type: ignore
    if not sessions:
        return []
        # If no active sessions are found, returns an empty list.
    # Returns a list of dictionaries of media info properties for each active
    # session, unless none can be found.
    thread_dict: dict[str, threading.Thread] = {}
    for index, sesh in enumerate(sessions):
        props = await sesh.try_get_media_properties_async()
        stream = await props.thumbnail.open_read_async() # type: ignore
        thread_dict[f"thread{index}"] = threading.Thread(target=trans_sesh, args =(props, stream, info))
    for thread in thread_dict.values():
        thread.start()
    index = len(thread_dict) -1
    thread_dict[f"thread{index}"].join()

    return info


def trans_sesh(props, stream, tst: list[dict[str, str | int | list | Image.Image]]):
    """ Translates a Windows TCS object into a more Python friendly dictionary.
    Returns:
        A rougly organized dictionary of the TCS object's attributes. 
        Including the thumbnail as a PIL image and the genres as a list. 
    """
    # Creates a dictionary from a MediaProperties object.
    transed_sesh = {
        'title': props.title,
        'artist': props.artist,
        'album_title': props.album_title,
        'album_artist': props.album_artist,
        # Converts the genres property to a Python list.
        'genres': list(props.genres),
        # Converts the thumbnail property to a PIL image.
        'thumbnail': (ref_to_img(stream)),
        'track_number': props.track_number,
        'album_track_count': props.album_track_count,
        'playback_type': props.playback_type,
        'subtitle': props.subtitle
    } 
    tst.append(transed_sesh)
    return


def ref_to_img(stream:IRandomAccessStreamWithContentType) -> Image.Image:
    img_buffer = Buffer(stream.size)
    # Reads data from the stream into the buffer 
    stream.read_async(img_buffer, img_buffer.capacity, InputStreamOptions.READ_AHEAD)  # type: ignore 
    # Opens a stream from the reference
    image_bytes = bytearray(img_buffer.capacity)
    # Reads data from the buffer into the image_bytes bytearray.
    DataReader.from_buffer(img_buffer).read_bytes(image_bytes) # type: ignore
    # Converts the bytearray to a PIL image and returns it.

    return Image.open(io.BytesIO(image_bytes))


# only run if the module is run directly.
if __name__ == '__main__':
    sessions = asyncio.run(get_media_info())
    if sessions:
        for sesh in sessions:
            print(sesh)
            sesh['thumbnail'].show()