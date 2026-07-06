import httpx
import os
from fastapi import FastAPI
from fastapi import Request
from dotenv import load_dotenv
from model import ChatRequest
from counter import count_tokens
from compressor import compress_text
import json
from cache import get_cached_response, set_cached_response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

load_dotenv()

app = FastAPI()

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


@app.post("/v1/chat/completions")
@limiter.limit("5/minute")
async def proxy(request: Request, chat_request: ChatRequest):

    # Step 1: capture messages, and count tokens BEFORE compression
    messages = [m.model_dump() for m in chat_request.messages]
    original_tokens = count_tokens(messages)

    # Step 2: compress system prompts
    for message in messages:
        if message["role"] == "system":
            message["content"] = compress_text(message["content"])

    # Step 2b: count tokens AFTER compression
    compressed_tokens = count_tokens(messages)

    # Step 2c: work out how much compression actually saved
    tokens_saved = original_tokens - compressed_tokens
    if original_tokens > 0:
        compression_percent = round((tokens_saved / original_tokens) * 100, 1)
    else:
        compression_percent = 0

    compression_report = {
        "original_tokens": original_tokens,
        "compressed_tokens": compressed_tokens,
        "tokens_saved": tokens_saved,
        "compression_percent": compression_percent
    }

    cache_input = json.dumps(messages, sort_keys=True)
    cached = get_cached_response(cache_input)
    if cached is not None:
        cached_data = json.loads(cached)

        return {
            "response": cached_data,
            "token_report": {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0
            },
            "compression_report": compression_report
        }

    # Step 3: count tokens after compression (this is the input sent to Groq)
    input_tokens = compressed_tokens

    # Step 4: forward to Groq
    try:
        async with httpx.AsyncClient() as client:
           response = await client.post(
              GROQ_URL,
              json={**chat_request.model_dump(), "messages": messages},
              headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
            )
        data = response.json()

        if "choices" not in data:
            # NEW: check specifically for Groq's rate-limit error code.
            # data.get("error", {}) safely returns an empty dict if "error"
            # isn't in the response at all, so this never crashes even if
            # Groq sends back a totally different error shape.
            error_code = data.get("error", {}).get("code")

            if error_code == "rate_limit_exceeded":
                return {
                    "error": "rate_limit",
                    "details": "This demo is popular right now! Please try again in a minute."
                }

            return {"error": "Groq API request failed", "details": data}

    except Exception as e:
       return {"error": "Groq API request failed", "details": str(e)}


    # store this response in cache for next time
    set_cached_response(cache_input, json.dumps(data))

    # Step 5: count tokens after
    output_text = data["choices"][0]["message"]["content"]
    output_tokens = count_tokens([{"role": "assistant", "content": output_text}])

    # Step 6: return response + token report + compression report
    return {
        "response": data,
        "token_report": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        },
        "compression_report": compression_report
    }