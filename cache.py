import redis
import hashlib

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

def get_cache_key(text):
    normalized_text = text.lower().strip()
    hash_object = hashlib.sha256( normalized_text.encode() )
    hexdigest = hash_object.hexdigest()
    return hexdigest

def get_cached_response(prompt):
    key = get_cache_key(prompt)
    cached_value = r.get(key)
    if cached_value is not None:
        return cached_value
    else:
        return None

def set_cached_response(prompt, response):
    key = get_cache_key(prompt)
    r.set(key, response)
    


