# A simple test to verify our imports and config load correctly
def test_config_loads():
    from src.config import Settings
    settings = Settings()
    assert settings.host == "127.0.0.1"
    assert settings.port == 8765
    assert settings.default_model == "whisper_tiny"


def test_whisper_tiny_registered():
    from src.engines import ENGINE_REGISTRY
    from src.engines.whisper_engine import WhisperTinyEngine

    assert ENGINE_REGISTRY["whisper_tiny"] is WhisperTinyEngine
    assert WhisperTinyEngine().get_info().name == "whisper_tiny"
