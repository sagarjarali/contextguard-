import redis
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

r = redis.Redis(
    host="picked-thrush-84969.upstash.io",
    port=6379,
    password=REDIS_PASSWORD,
    ssl=True,
    decode_responses=True
)

def get_cache_key(text):
    normalized_text = text.lower().strip()
    hash_object = hashlib.sha256( normalized_text.encode() )
    hexdigest = hash_object.hexdigest()
    return hexdigest

def get_cached_response(cache_input):
    key = get_cache_key(cache_input)
    return r.get(key)

def set_cached_response(cache_input, response_json):
    key = get_cache_key(cache_input)
    r.set(key, response_json)