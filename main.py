import httpx
import os
from fastapi import FastAPI
from dotenv import load_dotenv
from model import ChatRequest
from counter import count_tokens
from compressor import compress_text
import json
from cache import get_cached_response, set_cached_response


load_dotenv()

app = FastAPI()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

@app.post("/v1/chat/completions")
async def proxy(request: ChatRequest):

    # Step 2: compress system prompts
    messages = [m.model_dump() for m in request.messages]
    for message in messages:
        if message["role"] == "system":
            message["content"] = compress_text(message["content"])

    cache_input = json.dumps(messages, sort_keys=True)
    cached = get_cached_response(cache_input)
    if cached is not None:
        cached_data = json.loads(cached)
        
        return {
            "response": cached_data,
            "token_report":{
                "input_tokens":0,
                "output_tokens":0,
                "total_tokens":0
            }
        }

    

    # Step 3: count tokens after compression
    input_tokens = count_tokens(messages)

    # Step 4: forward to Groq
    try:
        async with httpx.AsyncClient() as client:
           response = await client.post(
              GROQ_URL,
              json={**request.model_dump(), "messages": messages},
              headers={"Authorization": f"Bearer {GROQ_API_KEY}"}
            )
        data = response.json()

        if "choices" not in data:
         return {"error": "Groq API request failed", "details": data}

    except Exception as e:
       return {"error": "Groq API request failed", "details": str(e)}


    # store this response in cache for next time
    set_cached_response(cache_input, json.dumps(data))

    # Step 5: count tokens after
    output_text = data["choices"][0]["message"]["content"]
    output_tokens = count_tokens([{"role": "assistant", "content": output_text}])

    # Step 6: return response + token report
    return {
        "response": data,
        "token_report": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens
        }
    }
