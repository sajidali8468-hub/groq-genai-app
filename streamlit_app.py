import os
import time

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from core.prompts import SYSTEM_GUARDRAIL
from core.utils import log_performance


load_dotenv()


def get_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY")


st.set_page_config(
    page_title="GenAI Technical Assistant",
    page_icon="AI",
    layout="centered",
)

st.title("GenAI Technical Assistant")
st.caption("Transform messy technical input into a concise executive-level Markdown summary.")

api_key = get_api_key()

if not api_key:
    st.error("Missing GROQ_API_KEY. Add it to Streamlit Secrets or your local .env file.")
    st.stop()

client = Groq(api_key=api_key)

user_input = st.text_area(
    "Technical input",
    placeholder="Describe your technical problem, migration plan, architecture issue, or system notes...",
    height=180,
)

generate = st.button("Generate summary", type="primary")

if generate:
    prompt = user_input.strip()

    if not prompt:
        st.warning("Please enter a technical prompt first.")
        st.stop()

    start_time = time.time()

    with st.spinner("Generating..."):
        try:
            completion = client.chat.completions.create(
                model="llama3-8b-8192",
                messages=[
                    {"role": "system", "content": SYSTEM_GUARDRAIL},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.5,
                max_tokens=1024,
            )
        except Exception as exc:
            st.error(f"Generation failed: {exc}")
            st.stop()

    response_text = completion.choices[0].message.content
    duration = time.time() - start_time

    log_performance(duration, len(response_text))

    st.subheader("Generated Output")
    st.markdown(response_text)
    st.caption(f"Completed in {duration:.2f}s")
