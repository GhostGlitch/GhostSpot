import asyncio
import io
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as MediaManager
from winsdk.windows.storage.streams import Buffer, InputStreamOptions, DataReader
from PIL import Image

READ_AHEAD = InputStreamOptions.READ_AHEAD

"""prints or displays the media info for all active media sessions on the system."""
async def get_media_info():
    # Gets a list of GlobalSystemMediaTransportControlsSession objects, which represent media sessions that can be controlled.
    sessions= list((await MediaManager.request_async()).get_sessions())

    # Loops through all active media sessions, gets info for each, 
        # outputs that info
    for sesh in sessions:
        sesh_info = await trans_sesh(sesh)
        print (sesh_info)
        sesh_info['thumbnail'].show()


async def trans_sesh(sesh):
    """
    Translates a Windows...Session object into a more Python friendly dictionary.

    Returns:
         A dictionary of the Session object's attributes. Including the thumbnail as a PIL image and the genres unpacked into a list.
    """
    props = await sesh.try_get_media_properties_async()
    #Creates a dictionary of media info properties from a MediaProperties object. (prop_name[0] != '_' strips system attributes as they all start with a '_')
    transed_sesh = {prop_name: getattr(props, prop_name) for prop_name in dir(props) if prop_name[0] != '_'}
    # Unpacks the genres property into a Python list.
    transed_sesh['genres'] = list(transed_sesh['genres'])
    transed_sesh['thumbnail'] = await ref_to_img(transed_sesh['thumbnail'])
    return transed_sesh


async def ref_to_img(stream_ref):
    """
    Converts an IRandomAccessStreamReference object to a PIL image.

    Parameters:
    stream_ref (IRandomAccessStreamReference): The IRandomAccessStreamReference object to convert.

    Returns:
    image (PIL.Image.Image): The converted PIL image.
    """
    # Opens a stream from the reference
    stream = await stream_ref.open_read_async()
    buffer = Buffer(stream.size)
    image_bytes = bytearray(stream.size)
    # Reads data from the stream into the buffer 
    await stream.read_async(buffer, buffer.capacity, READ_AHEAD)
    # Reads data from the buffer into the image_bytes bytearray.
    DataReader.from_buffer(buffer).read_bytes(image_bytes)
    # Converts the bytearray to a PIL image and returns it.  
    return Image.open(io.BytesIO(image_bytes))    

# only run if the module is run directly.
if __name__ == '__main__':
    asyncio.run(get_media_info())
