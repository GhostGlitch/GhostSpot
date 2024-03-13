__version__ = '0.7'
__author__ = 'Ghost Glitch'

import asyncio
import io
from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSessionManager as TCSManager
from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSession as TCS
from winsdk.windows.storage.streams \
    import Buffer, InputStreamOptions, DataReader, IRandomAccessStreamReference
from PIL import Image
import threading
tst = []
tst2 = []


async def get_media_info() -> list:
    """ Returns a list of all active media as dicts of thier properties. """
    # Gets a list of all active TCS objects
    sessions= list((await TCSManager.request_async()).get_sessions())
    # Returns a list of dictionaries of media info properties for each active
        # session, unless none can be found.
    threaddict = {}
    threaddict2 = {}
    for index, sesh in enumerate(sessions):
        props = await sesh.try_get_media_properties_async()
        threaddict[f"thread{index}"] = threading.Thread(target=trans_sesh, args =(props, index))
    for thread in threaddict.values():
        thread.start()
    index = len(threaddict) -1
    threaddict[f"thread{index}"].join()
    for index, sesh in enumerate(tst):
        stream = await tst[index]['thumbnail'].open_read_async()
        threaddict[f"thread{index}"] = threading.Thread(target=ref_to_img, args =(stream, index))
    for thread in threaddict.values():
        thread.start()
    threaddict[f"thread{index}"].join()


    return tst

    return None



def trans_sesh(props, index):
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
        'thumbnail': (props.thumbnail),
        'track_number': props.track_number,
        'album_track_count': props.album_track_count,
        'playback_type': props.playback_type,
        'subtitle': props.subtitle
    } 
    tst.append(transed_sesh)
    return transed_sesh


def ref_to_img(stream, index) -> Image:
    img_buffer = Buffer(stream.size)
        # Reads data from the stream into the buffer 
    stream.read_async(img_buffer, img_buffer.capacity, \
    InputStreamOptions.READ_AHEAD)
    """ Converts an IRandomAccessStreamReference object to a PIL image. """    # Opens a stream from the reference
    image_bytes = bytearray(img_buffer.capacity)
    # Reads data from the buffer into the image_bytes bytearray.
    DataReader.from_buffer(img_buffer).read_bytes(image_bytes)
    # Converts the bytearray to a PIL image and returns it.
    img = Image.open(io.BytesIO(image_bytes))
    tst2.append(Image.open(io.BytesIO(image_bytes)))  
    return 


# only run if the module is run directly.
if __name__ == '__main__':
    sessions = asyncio.run(get_media_info())
    if tst:
         print (tst)
         [i.show() for i in tst2]
