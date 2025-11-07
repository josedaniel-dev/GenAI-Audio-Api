from cache_manager import register_stem, get_cached_stem, load_index
from pathlib import Path

def test_register_and_retrieve_stem(tmp_path):
    path = tmp_path / "stem.wav"
    path.write_text("fake audio")
    register_stem("test_stem", "hello", str(path))
    cached = get_cached_stem("test_stem")
    assert cached is not None
    assert Path(cached).exists()
