import streamlit as st
import requests

# Your backend URL — local for testing, swap to Render URL once deployed
API_URL = "http://localhost:8000/v1/chat/completions"

st.title("ContextGuard 🧠")
st.caption("LLM cost optimization: compress prompts, cache repeats, cut token spend")

system_prompt = st.text_area(
    "System prompt (this gets compressed before sending to Groq)",
    height=100,
    placeholder="You are a helpful assistant that..."
)

user_prompt = st.text_area(
    "User prompt",
    height=100,
    placeholder="Explain quantum computing in simple terms"
)

if st.button("Send"):
    if not user_prompt.strip():
        st.warning("Please enter a user prompt.")
    else:
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 1024
        }

        with st.spinner("Calling ContextGuard..."):
            try:
                res = requests.post(API_URL, json=payload, timeout=60)
                data = res.json()
            except Exception as e:
                st.error(f"Request failed: {e}")
                st.stop()

        if "error" in data:
            st.error(f"Groq error: {data['details']}")
        else:
            report = data["token_report"]
            is_cache_hit = report["total_tokens"] == 0

            reply = data["response"]["choices"][0]["message"]["content"]

            st.subheader("Response")
            st.write(reply)

            st.subheader("Stats")
            col1, col2, col3 = st.columns(3)
            col1.metric("Input tokens", report["input_tokens"])
            col2.metric("Output tokens", report["output_tokens"])
            col3.metric("Total tokens", report["total_tokens"])

            if is_cache_hit:
                st.success("⚡ Cache hit — 0 tokens spent")
            else:
                st.info("Fresh Groq call")