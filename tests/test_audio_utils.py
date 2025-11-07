import pytest
from pydub import AudioSegment
from audio_utils import normalize_audio, describe

def test_normalization_does_not_crash():
    tone = AudioSegment.silent(duration=1000)
    result = normalize_audio(tone)
    assert isinstance(result, AudioSegment)

def test_describe_returns_metadata():
    tone = AudioSegment.silent(duration=500)
    info = describe(tone)
    assert "duration_sec" in info
