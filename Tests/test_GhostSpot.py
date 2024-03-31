
import sys
sys.path.append("..") # Adds higher directory to python modules path.
import pytest
from PIL import Image
from ..GhostSpot import *
from ..GhostSpot import PlaybackType as PT
from ..GhostSpot import Gcon as CV
import asyncio
from pytest_mock import mocker
from winsdk.windows.media.control \
    import GlobalSystemMediaTransportControlsSessionManager as TCSManager, \
        GlobalSystemMediaTransportControlsSession as TCS
from winsdk.windows.media import MediaPlaybackType as MPT
from winsdk.windows.storage.streams \
    import Buffer, InputStreamOptions, IRandomAccessStreamReference
from PIL import Image

@pytest.fixture
def tcs_mock(mocker):
    # Mock the TCS object
    tcs = mocker.Mock()

    # Mock the media properties
    props_mock = mocker.Mock()
    props_mock.title = "Test Title"
    props_mock.artist = "Test Artist"
    props_mock.album_title = "Test Album"
    props_mock.album_artist = "Test Album Artist"
    props_mock.genres = ["Genre1", "Genre2"]
    props_mock.thumbnail = None
    props_mock.track_number = 1
    props_mock.album_track_count = 10
    props_mock.playback_type = PT.UNKNOWN
    props_mock.subtitle = "Test Subtitle"

    # Mock the try_get_media_properties_async method
    tcs.try_get_media_properties_async.return_value = asyncio.Future()
    tcs.try_get_media_properties_async.return_value.set_result(props_mock)
    return tcs
    
def test_convert_to_PlaybackType():
    with pytest.warns() as Warn_list:
        # From MPT
        assert PT.from_Any(MPT.UNKNOWN) == PT.UNKNOWN
        assert PT.from_Any(MPT.MUSIC) == PT.AUDIO
        assert PT.from_Any(MPT.VIDEO) == PT.VIDEO
        assert PT.from_Any(MPT.IMAGE) == PT.IMAGE
        # From int
        assert PT.from_Any(0) == PT.UNKNOWN
        assert PT.from_Any(1) == PT.AUDIO
        assert PT.from_Any(2) == PT.VIDEO
        assert PT.from_Any(3) == PT.IMAGE
        assert len(Warn_list) == 0
        assert PT.from_Any(4) == PT.UNKNOWN
        assert len(Warn_list) == 1
        # From str
        assert PT.from_Any("UNKNOWN") == PT.UNKNOWN
        assert PT.from_Any("AUDIO") == PT.AUDIO
        assert PT.from_Any("VIDEO") == PT.VIDEO
        assert PT.from_Any("IMAGE") == PT.IMAGE
        assert PT.from_Any("audio") == PT.AUDIO
        assert PT.from_Any("vIdEo") == PT.VIDEO
        assert len(Warn_list) == 1
        assert PT.from_Any("") == PT.UNKNOWN
        assert PT.from_Any("XYZ") == PT.UNKNOWN
        assert len(Warn_list) == 3
        # From PT
        assert PT.from_Any(PT.AUDIO) == PT.AUDIO
        assert len(Warn_list) == 3
        # From None
        assert PT.from_Any(None) == PT.UNKNOWN
        # From other
        assert PT.from_Any(3.14) == PT.UNKNOWN
        assert PT.from_Any([1, 2, 3]) == PT.UNKNOWN
        assert len(Warn_list) == 6
        with pytest.raises(TypeError):
            PT.from_Any(1, 2)
    

def test_PySesh_default_vals():
    py_sesh = PySession()
    assert py_sesh.title == 'Unknown Title'
    assert py_sesh.artist == 'Unknown Artist'
    assert py_sesh.album_title == 'Unknown Album'
    assert py_sesh.album_artist == ''
    assert py_sesh.genres == ()
    assert isinstance(py_sesh.thumbnail, Image.Image)
    assert py_sesh.track_number == 0
    assert py_sesh.album_track_count == 0
    assert py_sesh.playback_type == PT.UNKNOWN
    assert py_sesh.subtitle == ''

def test_PySesh_bad_vals():
    session = PySession(title="", artist="", album_title="", album_artist="", genres=(), track_number=-5, album_track_count=np.int16(5), playback_type=0, subtitle="")
    print ("done")

@pytest.mark.asyncio
async def test_create_PySesh_from_TCS(tcs_mock, mocker):

    # Call the from_TCS_async method to create a PySession object
    py_sesh = await PySession.from_TCS_async(tcs_mock)

    # Assert that the PySession object has the correct attributes
    assert py_sesh.title == "Test Title"
    assert py_sesh.artist == "Test Artist"
    assert py_sesh.album_title == "Test Album"
    assert py_sesh.album_artist == "Test Album Artist"
    assert py_sesh.genres == ("Genre1", "Genre2")
    assert isinstance(py_sesh.thumbnail, Image.Image)
    assert py_sesh.track_number == 1
    assert py_sesh.album_track_count == 10
    assert py_sesh.playback_type == PT.UNKNOWN
    assert py_sesh.subtitle == "Test Subtitle"