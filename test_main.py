from compressor import compress_text
from counter import count_tokens
from cache import get_cached_response, set_cached_response, get_cache_key, r


def test_compression_reduces_tokens():
    original_text = "This is a very long system prompt that contains a lot of unnecessary filler words and repetitive phrasing that could definitely be shortened without losing the core meaning of the instructions."
    
    compressed_text = compress_text(original_text)
    
    original_tokens = count_tokens([{"role": "system", "content": original_text}])
    compressed_tokens = count_tokens([{"role": "system", "content": compressed_text}])
    
    assert compressed_tokens < original_tokens


def test_cache_miss_then_hit():
    test_prompt = "test_prompt_unique_12345"
    
    # clean up any leftover data from a previous test run
    key = get_cache_key(test_prompt)
    r.delete(key)
    
    # First check: should be a miss, nothing stored yet
    result = get_cached_response(test_prompt)
    assert result is None
    
    # Store something
    set_cached_response(test_prompt, "cached_answer_value")
    
    # Second check: should now be a hit
    result = get_cached_response(test_prompt)
    assert result == "cached_answer_value"


def test_cache_key_is_deterministic():
    text = "What is 2+2?"
    
    key1 = get_cache_key(text)
    key2 = get_cache_key(text)
    
    assert key1 == key2