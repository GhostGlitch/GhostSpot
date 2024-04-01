__version__ = '0.8.8'
__author__ = 'Ghost Glitch'

from enum import Enum
from typing import Optional as Opt
import asyncio
from warnings import warn
import io
from threading import Thread
from functools import partial

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
        return cls.UNKNOWN

    def to_MPT(self) -> MPT:
        if self == self.AUDIO:
            return MPT.MUSIC
        elif self == self.VIDEO:
            return MPT.VIDEO
        elif self == self.IMAGE:
            return MPT.IMAGE
        return MPT.UNKNOWN

def coro_in_thread(coro, *args, **kwargs):
    def idk(future, coro, *args, **kwargs):
        future.set_result(asyncio.run(coro(*args, **kwargs)))
    future = asyncio.Future()
    thr = Thread(target=(idk), args=(future, coro, *args))
    thr.start()
    thr.join()
    return future.result()
@define(frozen=True, slots=True)
class GhostConverters:
    """Contains custom conversion functions for PySessions."""
    class Strs:
        """Contains conversion functions for strings."""
        @staticmethod
        def __base(arg, default, type) -> str:
            """base function for string conversion functions."""
            if arg == 0 or arg:  #allows only truthy values and 0
                try :
                    return str(arg)
                except Exception as e:
                    warn (f'{e}: Cannot convert {arg} to string for {type} conversion. Returning {default}')
            else:
                warn (f'{arg} is falsy. Returning {default} for {type}')
            return default
        
        @staticmethod
        def to_title(arg) -> str:
            """Converts a variety of types to a valid title."""
            return GhostConverters.Strs.__base(arg, 'Unknown Title', 'Title')
        @staticmethod
        def to_artist(arg) -> str:
            """Converts a variety of types to a valid artist."""
            return GhostConverters.Strs.__base(arg, 'Unknown Artist', 'Artist')
        @staticmethod
        def to_album_title(arg) -> str:
            """Converts a variety of types to a valid album title."""
            return GhostConverters.Strs.__base(arg, 'Unknown Album', 'Album Title')
        @classmethod
        def to_opt(cls, arg) -> Opt[str]:
            """Converts to an optional str"""
            return None if arg == 0 else cls.__base(arg, None, 'either Subtitle or Album Artist')
        
    @staticmethod
    def to_img(arg) -> Image.Image:
        """Converts a variety of types to a Pillow image."""
        if isinstance(arg, Image.Image):
            return arg
        if isinstance(arg, IRandomAccessStreamReference):
            warn ('Setting thumbnail directly from type IRandomAcessStreamReference not recommended. Automatic conversion can not be async, may block. Use GhostConverters.ref_to_thumb before setting.')
            return coro_in_thread(GhostConverters.ref_to_thumb, arg)
        
        if isinstance(arg, str):
            try:
                return Image.open(arg)
            except FileNotFoundError as e:
                warn(f'{e}: {arg} not found for Image conversion. Returning ERROR_THUMB.')
            except OSError as e:
                warn(f'{e}: File {arg} not a valid image for Image conversion. Returning ERROR_THUMB.')
            except Exception as e:
                warn(f'{e}: Cannot open file {arg} for Image conversion. Returning ERROR_THUMB.')
        elif isinstance(arg, bytes) or isinstance(arg, bytearray) or isinstance(arg, np.array):
            try:
                return Image.open(io.BytesIO(arg))
            except OSError as e:
                warn(f'{e}: Bytes {arg} not a valid image for Image conversion. Returning ERROR_THUMB.') #type: ignore
            except Exception as e:
                warn(f'{e}: Cannot open bytes {arg} for Image conversion. Returning ERROR_THUMB.') #type: ignore
        else:
            warn(f'TypeError: Type of {arg} ({type(arg)}) not valid for Image conversion. Returning ERROR_THUMB.')
        return ERROR_THUMB
    @staticmethod
    async def ref_to_thumb(stream_ref: IRandomAccessStreamReference |  None) -> Image.Image:
        """ Returns a Pillow image from a stream reference."""
        if isinstance(stream_ref, IRandomAccessStreamReference):
            try:
                # Opens a stream from the reference
                stream = await stream_ref.open_read_async()
                img_buffer = Buffer(stream.size)
                # Reads data from the stream into the buffer 
                await stream.read_async(img_buffer, img_buffer.capacity, InputStreamOptions.READ_AHEAD) 
                return (Image.open(io.BytesIO(img_buffer)))
            except Exception as e:
                warn(f'{e}: Error reading stream reference {stream_ref} for ref_to_thumb. Returning ERROR_THUMB.')
        else:
            warn(f'TypeError: Type of {stream_ref} ({type(stream_ref)}) not valid for ref_to_thumb. Returning ERROR_THUMB.')
        return ERROR_THUMB
    @staticmethod
    def to_PT(arg):
        """Converts a variety of types to a PlaybackType."""
        if isinstance(arg, MPT):
            return PlaybackType.from_MPT(arg)
        elif np.issubdtype(type(arg), np.integer):
            try:
                return PlaybackType(arg)
            except ValueError as e:
                warn(f'{e}: {arg} out of range 0-3 for PlaybackType conversion. Returning UNKNOWN.', )
        elif isinstance(arg, PlaybackType):
            return arg
        elif isinstance(arg, str): 
            try:
                return PlaybackType[arg.upper()]
            except KeyError as e:
                warn(f'{e}: Invalid string {arg} for PlaybackType conversion. Returning UNKNOWN.')
        else:
            warn(f'TypeError: Type of {arg} ({type(arg)}) not valid for PlaybackType conversion. Returning UNKNOWN.')
        return PlaybackType.UNKNOWN

class GhostValidators:
    """Contains custom validator functions for PySessions."""
    @staticmethod
    def int(inst, attr, val):
        """Currently unused. Potentially add support for np integers. in Pysession"""
        if not np.issubdtype(type(val), np.integer):
            raise TypeError(f'{attr} must be an integer.')
        
# Shortened aliases for PySession field definitions to make attribute definitions not 5000 characters long.
@define(frozen=True, slots=True)
class V:
    """Contains aliases for validators for PySessions. So fields fit on one line."""
    INS = v.instance_of
    '''validators.instance_of'''
    STR = INS(str)
    '''validators.instance_of(str)'''
    INT = INS(int)
    '''validators.instance_of(int)'''
    TUPLE = INS(tuple)
    '''validators.instance_of(tuple)'''
    IMG = INS(Image.Image)
    '''validators.instance_of(Image.Image)'''
    PT = INS(PlaybackType)
    '''validators.instance_of(PlaybackType)'''
    DI = v.deep_iterable
    class OPT:
        '''contains aliases for some variants of validators.optional()'''
        @staticmethod
        def B(type):
            return v.optional(v.instance_of(type))
        STR = B(str)
        '''validators.optional(validators.instance_of(str))'''
        INT = B(int)
        '''validators.optional(validators.instance_of(int))'''
    class TUP:
        B = partial(v.deep_iterable, iterable_validator=v.instance_of(tuple))

        STR = B(member_validator=v.instance_of(str))

    TUP_STR = DI(iterable_validator=TUPLE, member_validator=STR)
@define(frozen=True, slots=True)
class C:
    """Contains aliases for converters for PySessions. So fields fit on one line."""
    class STR:
        '''contains aliases for GhostConverters.Strs functions.
        \n- B = GhostConverters.Strs \n- TIT = to_title \n- ART = to_artist \n- ALB = to_album_title'''
        B = GhostConverters.Strs
        '''GhostConverters.Strs:'''
        TIT = B.to_title
        '''GhostConverters.Strs.to_title:'''

        ART = B.to_artist
        '''GhostConverters.Strs.to_artist:'''
        ALB = B.to_album_title
        '''GhostConverters.Strs.to_album_title:'''
        OPT = B.to_opt
        '''GhostConverters.Strs.to_opt:'''
    PT = GhostConverters.to_PT
    '''GhostConverters.to_PT:'''
    IMG = GhostConverters.to_img
    '''GhostConverters.to_Image'''
    class OPT:
        '''contains aliases for some variants of converters.optional()
        \n- B = converters.optional \n- INT = optional(int) \n- STR = optional(str)'''
        B = c.optional
        '''converters.optional:'''
        INT = B(int)
        '''converters.optional(int)'''
        STR = B(str)
        '''converters.optional(str)'''
@define(frozen=True, slots=True)
class D:
    '''Contains aliases for defaults for PySession. So fields fit on one line.'''
    ''''''
    TIT = "Unknown Title"
    '''"Unknown Title"'''
    ART = "Unknown Artist"
    '''"Unknown Artist"'''
    ALB  = "Unknown Album"
    '''"Unknown Album"'''
    """Contains aliases for default values for PySessions. So fields fit on one line."""
    PT = PlaybackType.UNKNOWN
    '''PlaybackType.UNKNOWN'''
    ET = ERROR_THUMB


# Fuck you MyPy! Throws a fit if I set a default to anything other than None and adds Any to type hints and puts an error on the validator.
# Also throws an error if converter is from a class or alias. too bad, I'm doing it anyway... 

@define(slots=True)
class PySession():
    title: str = field(default=D.TIT, converter=C.STR.TIT, validator=V.STR)#type: ignore
    artist: str = field(default=D.ART, converter=C.STR.ART, validator=V.STR)#type: ignore
    album_title: str = field(default=D.ALB, converter=C.STR.ALB, validator=V.STR)#type: ignore
    album_artist: Opt[str] = field(default=None, converter=C.STR.OPT, validator=V.OPT.STR)# type: ignore
    genres: tuple[str] = field(factory=tuple[str], converter=tuple, validator=V.TUP.STR)# type: ignore
    thumbnail: Image.Image = field(default=D.ET, converter=C.IMG, validator=V.IMG)#type: ignore
    track_number: Opt[int] = field(default=0, converter=C.OPT.INT, validator=V.OPT.INT)# type: ignore
    album_track_count: Opt[int] = field(default=0, converter=C.OPT.INT, validator=V.OPT.INT)#type: ignore
    playback_type: PlaybackType = field(default=D.PT, converter=C.PT, validator=V.PT)#type: ignore
    subtitle: Opt[str] = field(default=None, converter=C.STR.OPT, validator=V.OPT.STR)#type: ignore

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
            title=props.title,
            artist=props.artist,
            album_title=props.album_title,
            album_artist=props.album_artist,
            genres=props.genres,
            thumbnail = await GhostConverters.ref_to_thumb(props.thumbnail),
            track_number=props.track_number,
            album_track_count=props.album_track_count,
            playback_type=props.playback_type,
            subtitle=props.subtitle
        )


async def get_media_info() -> list[PySession]:
    """ Returns a list of PySessions for each active media session."""
    # Gets a tuple of all active TCS objects
    sessions= (await TCSManager.request_async()).get_sessions()  # type: ignore
    return await asyncio.gather (*[PySession.from_TCS_async(sesh) for sesh in sessions])# type: ignore

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