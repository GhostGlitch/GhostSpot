__version__ = '0.8.8'
__author__ = 'Ghost Glitch'

from enum import Enum
from typing import Optional as Opt
import asyncio
from warnings import warn as warning
import io
from threading import Thread

from attrs import define, field
from attrs import validators as v, converters as c
import numpy as np

from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSession as TCS, \
        GlobalSystemMediaTransportControlsSessionManager as TCSManager
from winsdk.windows.media import MediaPlaybackType as MPT
from winsdk.windows.storage.streams \
    import Buffer, InputStreamOptions, IRandomAccessStreamReference
from PIL import Image
ERROR_PINK = (255, 0, 220)
ERROR_THUMB = Image.new("RGB", (300, 300), ERROR_PINK)

class PlaybackType(Enum):
    UNKNOWN = 0
    AUDIO = 1
    VIDEO = 2
    IMAGE = 3
    @classmethod
    def from_MPT(cls, mpt: MPT) -> 'PlaybackType':
        if mpt == MPT.MUSIC:
            return cls.AUDIO
        elif mpt == MPT.VIDEO:
            return cls.VIDEO
        elif mpt == MPT.IMAGE:
            return cls.IMAGE
        else:
            return cls.UNKNOWN
    @classmethod
    def default(cls) -> 'PlaybackType':
        return cls.UNKNOWN

    def to_MPT(self) -> MPT:
        if self == self.AUDIO:
            return MPT.MUSIC
        elif self == self.VIDEO:
            return MPT.VIDEO
        elif self == self.IMAGE:
            return MPT.IMAGE
        else:
            return MPT.UNKNOWN

def coro_in_thread(coro, *args, **kwargs):
    def idk(future, coro, *args, **kwargs):
        future.set_result(asyncio.run(coro(*args, **kwargs)))
    future = asyncio.Future()
    thr = Thread(target=(idk), args=(future, coro, *args))
    thr.start()
    thr.join()
    return future.result()

def Image_catch(arg) -> Image.Image:

    if isinstance(arg, Image.Image):
        return arg
    elif isinstance(arg, IRandomAccessStreamReference):
        return coro_in_thread(ref_to_thumb, arg)

    elif isinstance(arg, str):
        try:
            return Image.open(arg)
        except FileNotFoundError:
            warning(f'File {arg} not found for Image conversion. Returning ERROR_THUMB.')
            return ERROR_THUMB
        except OSError:
            warning(f'File {arg} not a valid image for Image conversion. Returning ERROR_THUMB.')
            return ERROR_THUMB
    elif isinstance(arg, bytes) or isinstance(arg, bytearray) or isinstance(arg, np.array):
        try:
            return Image.open(io.BytesIO(arg))
        except OSError:
            warning(f'Bytes not a valid image for Image conversion. Returning ERROR_THUMB.')
            return ERROR_THUMB
    else:
        warning(f'Invalid type {type(arg)} for Image conversion. Returning ERROR_THUMB.')
        return ERROR_THUMB

async def ref_to_thumb(stream_ref: IRandomAccessStreamReference |  None) -> Image.Image:
    if not stream_ref:
        return ERROR_THUMB
    """ Converts an IRandomAccessStreamReference object to a PIL image. """    
    # Opens a stream from the reference
    stream = await stream_ref.open_read_async()
    img_buffer = Buffer(stream.size)
    # Reads data from the stream into the buffer 
    await stream.read_async(img_buffer, img_buffer.capacity, InputStreamOptions.READ_AHEAD) 
    return (Image.open(io.BytesIO(img_buffer)))

def to_PT(arg):
    if isinstance(arg, MPT):
        return PlaybackType.from_MPT(arg)
    elif np.issubdtype(type(arg), np.integer):
        try:
            return PlaybackType(arg)
        except ValueError:
            warning(f'{arg} out of range for PlaybackType conversion. Returning UNKNOWN.', )
            return PlaybackType.UNKNOWN
    elif isinstance(arg, PlaybackType):
        return arg
    elif isinstance(arg, str): 
        try:
            return PlaybackType[arg.upper()]
        except KeyError:
            warning(f'Invalid string {arg} for PlaybackType conversion. Returning UNKNOWN.')
            return PlaybackType.UNKNOWN
    else:
        warning(f'Invalid type {type(arg)} for PlaybackType conversion. Returning UNKNOWN.')
        return PlaybackType.UNKNOWN

class Gval:
    @staticmethod
    def int(inst, attr, val):
        if not np.issubdtype(type(val), np.integer):
            raise TypeError(f'{attr} must be an integer.')



V_STR = v.instance_of(str)
V_INT = v.instance_of(int)
V_TUPLE = v.instance_of(tuple)
V_IMG = v.instance_of(Image.Image)
V_PT = v.instance_of(PlaybackType)
V_OPT = v.optional
V_DI = v.deep_iterable
V_OPT_INT = V_OPT(V_INT)
V_OPT_STR = V_OPT(V_STR)
V_TUPLE_OF_STR = V_DI(iterable_validator=V_TUPLE, member_validator=V_STR)
C_OPT_INT = c.optional(int)



# Fuck  you, MyPy! Throws a fit if I set defaults in fields to anything other than None...

@define
class PySession():
    title: str = field(default='Unknown Title', validator=V_STR)
    artist: str = field(default='Unknown Artist', validator=V_STR)
    album_title: str = field(default='Unknown Album', validator=V_STR)
    album_artist: Opt[str] = field(validator=V_OPT_STR)
    genres: tuple[str] = field(factory=tuple[str], validator=V_TUPLE_OF_STR)
    thumbnail: Image.Image = field(default=ERROR_THUMB,converter=Image_catch)
    track_number: Opt[int] = field(converter=c.optional(int), validator=V_OPT_INT) 
    album_track_count: Opt[int] = field(converter=c.optional(int), validator=V_OPT_INT) 
    playback_type: PlaybackType = field(converter=to_PT, validator=V_PT)
    subtitle: Opt[str] = field(validator=V_OPT_STR)
    def __attrs_post_init__(self):
        pass


    # Setting defaults here because otherwise MyPy adds type Any to the hint and claims the validators are invalid.
    @track_number.default
    @album_track_count.default
    def _zero_default(self) -> int:
        return 0
    @playback_type.default
    def _playback_type_default(self) -> PlaybackType:
        return PlaybackType.UNKNOWN
    @album_artist.default
    @subtitle.default
    def _empty_string_default(self) -> str:
        return ''
    def __str__(self) -> str:
        attributes = {
            'Album Artist': self.album_artist,
            'Genres': self.genres,
            'Track Number': self.track_number,
            'Album Track Count': self.album_track_count,
            'Playback Type': self.playback_type.name, # type: ignore
            'Subtitle': self.subtitle
        }
        basic = (f'”{self.title}” BY {self.artist} ON {self.album_title} \n')
        return basic + ' | '.join(f'{name}: {value}' for name, value in attributes.items() if value)
    @classmethod
    async def from_TCS_async(cls, sesh: TCS) -> 'PySession':
        props = await sesh.try_get_media_properties_async()
        return cls(
            title=props.title if props.title else 'Unknown Title',
            artist=props.artist if props.artist else 'Unknown Artist',
            album_title=props.album_title if props.album_title else 'Unknown Album',
            album_artist=props.album_artist,
            genres=tuple(props.genres),
            thumbnail = props.thumbnail,
            track_number=props.track_number,
            album_track_count=props.album_track_count,
            playback_type=props.playback_type,
            subtitle=props.subtitle
        )


async def get_media_info() -> list[PySession]:
    """ Returns a list of PySessions for each active media session."""
    # Gets a tuple of all active TCS objects
    sessions= (await TCSManager.request_async()).get_sessions()  # type: ignore
    return await asyncio.gather (*[PySession.from_TCS_async(sesh) for sesh in sessions])

if __name__ == '__main__':
    sessions = asyncio.run(get_media_info())
    if sessions:
        for i, sesh in enumerate(sessions):
            print (f'\nMedia {i+1}:')
            print (sesh)
            sesh.thumbnail.show()
            #print (repr(sesh))

    else:
        print('No active media found.')