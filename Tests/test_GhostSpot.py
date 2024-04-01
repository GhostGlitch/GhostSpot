

import pytest
from PIL import Image
from ..GhostSpot import *
from ..GhostSpot import PlaybackType as PT
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
    props_mock.playback_type = MPT.MUSIC
    props_mock.subtitle = "Test Subtitle"

    # Mock the try_get_media_properties_async method
    tcs.try_get_media_properties_async.return_value = asyncio.Future()
    tcs.try_get_media_properties_async.return_value.set_result(props_mock)
    return tcs
    
def test_convert_to_PlaybackType():
    with pytest.warns() as Warn_list:
        # From MPT
        assert GhostConverters.to_PT(MPT.UNKNOWN) == PT.UNKNOWN
        assert GhostConverters.to_PT(MPT.MUSIC) == PT.AUDIO
        assert GhostConverters.to_PT(MPT.VIDEO) == PT.VIDEO
        assert GhostConverters.to_PT(MPT.IMAGE) == PT.IMAGE
        # From int
        assert GhostConverters.to_PT(0) == PT.UNKNOWN
        assert GhostConverters.to_PT(1) == PT.AUDIO
        assert GhostConverters.to_PT(2) == PT.VIDEO
        assert GhostConverters.to_PT(3) == PT.IMAGE
        assert len(Warn_list) == 0
        assert GhostConverters.to_PT(4) == PT.UNKNOWN
        assert len(Warn_list) == 1
        # From str
        assert GhostConverters.to_PT("UNKNOWN") == PT.UNKNOWN
        assert GhostConverters.to_PT("AUDIO") == PT.AUDIO
        assert GhostConverters.to_PT("VIDEO") == PT.VIDEO
        assert GhostConverters.to_PT("IMAGE") == PT.IMAGE
        assert GhostConverters.to_PT("audio") == PT.AUDIO
        assert GhostConverters.to_PT("vIdEo") == PT.VIDEO
        assert len(Warn_list) == 1
        assert GhostConverters.to_PT("") == PT.UNKNOWN
        assert GhostConverters.to_PT("XYZ") == PT.UNKNOWN
        assert len(Warn_list) == 3
        # From PT
        assert GhostConverters.to_PT(PT.AUDIO) == PT.AUDIO
        assert len(Warn_list) == 3
        # From None
        assert GhostConverters.to_PT(None) == PT.UNKNOWN
        # From other
        assert GhostConverters.to_PT(3.14) == PT.UNKNOWN
        assert GhostConverters.to_PT([1, 2, 3]) == PT.UNKNOWN
        assert len(Warn_list) == 6
        with pytest.raises(TypeError):
            GhostConverters.to_PT(1, 2)
    

def test_PySesh_default_vals():
    py_sesh = PySession()
    assert py_sesh.title == 'Unknown Title'
    assert py_sesh.artist == 'Unknown Artist'
    assert py_sesh.album_title == 'Unknown Album'
    assert py_sesh.album_artist == None
    assert py_sesh.genres == ()
    assert py_sesh.thumbnail is ERROR_THUMB
    assert py_sesh.track_number == 0
    assert py_sesh.album_track_count == 0
    assert py_sesh.playback_type == PT.UNKNOWN
    assert py_sesh.subtitle == None

def test_PySesh_empty_vals():
    py_sesh = PySession(title="", artist="", album_title="", album_artist="", genres=(), track_number=0, album_track_count=0, playback_type=0, subtitle="")
    print (repr(py_sesh))
    assert py_sesh.title == 'Unknown Title'
    assert py_sesh.artist == 'Unknown Artist'
    assert py_sesh.album_title == 'Unknown Album'
    assert py_sesh.album_artist == None
    assert py_sesh.genres == ()
    assert py_sesh.thumbnail is ERROR_THUMB
    assert py_sesh.track_number == 0
    assert py_sesh.album_track_count == 0
    assert py_sesh.playback_type == PT.UNKNOWN
    assert py_sesh.subtitle == None



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
    assert py_sesh.playback_type == PT.AUDIO
    assert py_sesh.subtitle == "Test Subtitle"