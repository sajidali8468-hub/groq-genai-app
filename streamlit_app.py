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
    layout="wide",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --ink: #eaf6ff;
            --muted: rgba(234, 246, 255, 0.72);
            --cyan: #55d7ff;
            --blue: #4f8dff;
            --panel: rgba(9, 23, 46, 0.62);
            --line: rgba(119, 219, 255, 0.28);
        }

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
        }

        .stApp {
            color: var(--ink);
            background:
                radial-gradient(circle at 18% 18%, rgba(85, 215, 255, 0.26), transparent 28%),
                radial-gradient(circle at 78% 10%, rgba(79, 141, 255, 0.22), transparent 24%),
                linear-gradient(135deg, #030814 0%, #071322 42%, #03101c 100%);
        }

        .block-container {
            max-width: 1120px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background: rgba(4, 12, 24, 0.88);
            border-right: 1px solid rgba(117, 218, 255, 0.18);
        }

        [data-testid="stSidebar"] * {
            color: #eaf6ff;
        }

        .ai-hero {
            position: relative;
            min-height: 500px;
            overflow: hidden;
            border: 1px solid rgba(142, 226, 255, 0.24);
            border-radius: 26px;
            background:
                linear-gradient(115deg, rgba(7, 16, 33, 0.94), rgba(9, 30, 55, 0.84)),
                radial-gradient(circle at center, rgba(84, 215, 255, 0.16), transparent 42%);
            box-shadow: 0 28px 90px rgba(0, 0, 0, 0.42), inset 0 0 70px rgba(81, 203, 255, 0.08);
            isolation: isolate;
        }

        .ai-hero::before {
            content: "";
            position: absolute;
            inset: -35%;
            background:
                repeating-linear-gradient(90deg, transparent 0 68px, rgba(105, 208, 255, 0.08) 69px 70px),
                repeating-linear-gradient(0deg, transparent 0 58px, rgba(105, 208, 255, 0.055) 59px 60px);
            transform: perspective(700px) rotateX(62deg) translateY(16%);
            animation: gridDrift 14s linear infinite;
            opacity: 0.7;
            z-index: -3;
        }

        .ai-hero::after {
            content: "";
            position: absolute;
            inset: 0;
            background: linear-gradient(90deg, rgba(3, 8, 20, 0.72), transparent 30%, transparent 70%, rgba(3, 8, 20, 0.72));
            z-index: -1;
        }

        .data-stream {
            position: absolute;
            height: 1px;
            width: 46%;
            left: -12%;
            background: linear-gradient(90deg, transparent, rgba(119, 223, 255, 0.92), transparent);
            filter: drop-shadow(0 0 10px rgba(85, 215, 255, 0.78));
            animation: streamMove 5.5s ease-in-out infinite;
        }

        .data-stream.s1 { top: 21%; animation-delay: 0s; }
        .data-stream.s2 { top: 68%; animation-delay: 1.3s; width: 38%; }
        .data-stream.s3 { top: 42%; animation-delay: 2.5s; width: 52%; }

        .holo-panel {
            position: absolute;
            border: 1px solid var(--line);
            border-radius: 16px;
            background: linear-gradient(135deg, rgba(10, 35, 64, 0.44), rgba(123, 225, 255, 0.08));
            box-shadow: 0 0 34px rgba(75, 198, 255, 0.14), inset 0 0 24px rgba(86, 215, 255, 0.08);
            backdrop-filter: blur(14px);
            animation: panelFloat 6.5s ease-in-out infinite;
        }

        .holo-panel::before,
        .holo-panel::after {
            content: "";
            position: absolute;
            left: 18px;
            right: 18px;
            height: 1px;
            background: rgba(128, 225, 255, 0.35);
        }

        .holo-panel::before { top: 28px; }
        .holo-panel::after { bottom: 34px; width: 48%; }

        .panel-a { width: 210px; height: 132px; left: 8%; top: 16%; }
        .panel-b { width: 240px; height: 150px; right: 8%; top: 15%; animation-delay: 1.1s; }
        .panel-c { width: 170px; height: 104px; right: 16%; bottom: 14%; animation-delay: 2s; }

        .ai-figure {
            position: absolute;
            left: 50%;
            top: 49%;
            width: 255px;
            height: 330px;
            transform: translate(-50%, -50%);
            opacity: 0.38;
            filter: drop-shadow(0 0 32px rgba(93, 219, 255, 0.36));
            z-index: -2;
        }

        .ai-head {
            position: absolute;
            left: 91px;
            top: 18px;
            width: 74px;
            height: 90px;
            border-radius: 42% 42% 46% 46%;
            border: 1px solid rgba(153, 232, 255, 0.42);
            background: linear-gradient(160deg, rgba(230, 249, 255, 0.18), rgba(40, 122, 184, 0.06));
        }

        .ai-body {
            position: absolute;
            left: 66px;
            top: 116px;
            width: 124px;
            height: 178px;
            border-radius: 54px 54px 22px 22px;
            border: 1px solid rgba(153, 232, 255, 0.34);
            background: linear-gradient(180deg, rgba(220, 248, 255, 0.12), rgba(58, 158, 223, 0.05));
        }

        .ai-arm {
            position: absolute;
            top: 144px;
            width: 95px;
            height: 12px;
            border-radius: 999px;
            border: 1px solid rgba(153, 232, 255, 0.34);
            transform-origin: left center;
            animation: gesture 3.6s ease-in-out infinite;
        }

        .ai-arm.left { left: 24px; transform: rotate(-25deg); }
        .ai-arm.right { right: -3px; transform: rotate(22deg); animation-delay: 0.8s; }

        .hero-content {
            position: relative;
            z-index: 2;
            display: flex;
            min-height: 500px;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            max-width: 760px;
            margin: 0 auto;
            padding: 64px 28px;
            text-align: center;
        }

        .eyebrow {
            margin-bottom: 18px;
            color: #a9eaff;
            font-size: 0.78rem;
            font-weight: 800;
            letter-spacing: 0;
            text-transform: uppercase;
        }

        .hero-title {
            margin: 0;
            color: #f5fbff;
            font-size: clamp(2.7rem, 6vw, 5.4rem);
            font-weight: 800;
            line-height: 0.94;
        }

        .hero-copy {
            max-width: 610px;
            margin: 24px auto 0;
            color: var(--muted);
            font-size: 1.12rem;
            line-height: 1.7;
        }

        .hero-cta {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 188px;
            min-height: 48px;
            margin-top: 30px;
            padding: 0 24px;
            border: 1px solid rgba(221, 248, 255, 0.64);
            border-radius: 999px;
            color: #04101f;
            background: linear-gradient(135deg, #f5fcff 0%, #7ddfff 52%, #5c98ff 100%);
            box-shadow: 0 18px 52px rgba(75, 190, 255, 0.32);
            font-weight: 800;
        }

        div[data-testid="stTextArea"] textarea {
            min-height: 180px;
            color: #eefaff;
            border: 1px solid rgba(139, 223, 255, 0.28);
            border-radius: 18px;
            background: rgba(6, 18, 34, 0.78);
            box-shadow: inset 0 0 28px rgba(81, 203, 255, 0.06);
        }

        div[data-testid="stTextArea"] label,
        .stMarkdown h2,
        .stMarkdown h3 {
            color: #f5fbff;
        }

        .stButton > button {
            border: 1px solid rgba(151, 231, 255, 0.45);
            border-radius: 999px;
            background: linear-gradient(135deg, #eefbff 0%, #72dcff 48%, #4f8dff 100%);
            color: #04101f;
            font-weight: 800;
            box-shadow: 0 14px 42px rgba(76, 184, 255, 0.32);
        }

        .stButton > button:hover {
            border-color: rgba(233, 250, 255, 0.9);
            transform: translateY(-1px);
        }

        @keyframes gridDrift {
            from { transform: perspective(700px) rotateX(62deg) translateY(10%); }
            to { transform: perspective(700px) rotateX(62deg) translateY(22%); }
        }

        @keyframes streamMove {
            0% { transform: translateX(0); opacity: 0; }
            25% { opacity: 1; }
            100% { transform: translateX(280%); opacity: 0; }
        }

        @keyframes panelFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-15px); }
        }

        @keyframes gesture {
            0%, 100% { rotate: 0deg; }
            50% { rotate: 7deg; }
        }

        @media (max-width: 720px) {
            .ai-hero,
            .hero-content {
                min-height: 440px;
            }

            .holo-panel {
                opacity: 0.5;
            }

            .panel-a { left: -18%; }
            .panel-b { right: -22%; }
            .panel-c { display: none; }
        }
    </style>
    <section class="ai-hero" aria-label="AI assistant hero">
        <div class="data-stream s1"></div>
        <div class="data-stream s2"></div>
        <div class="data-stream s3"></div>
        <div class="holo-panel panel-a"></div>
        <div class="holo-panel panel-b"></div>
        <div class="holo-panel panel-c"></div>
        <div class="ai-figure" aria-hidden="true">
            <div class="ai-head"></div>
            <div class="ai-body"></div>
            <div class="ai-arm left"></div>
            <div class="ai-arm right"></div>
        </div>
        <div class="hero-content">
            <div class="eyebrow">Technical Transformation Assistant</div>
            <h1 class="hero-title">Intelligence, redefined.</h1>
            <p class="hero-copy">
                Convert complex technical input into clear, executive-ready Markdown with a focused AI workspace built for speed, structure, and trust.
            </p>
            <div class="hero-cta">Start Analysis</div>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

api_key = get_api_key()

if not api_key:
    st.error("Missing GROQ_API_KEY. Add it to Streamlit Secrets or your local .env file.")
    st.stop()

client = Groq(api_key=api_key)

MODEL_OPTIONS = {
    "Fast: Llama 3.1 8B Instant": "llama-3.1-8b-instant",
    "Higher quality: Llama 3.3 70B Versatile": "llama-3.3-70b-versatile",
}

st.sidebar.title("Settings")
selected_model_label = st.sidebar.selectbox(
    "Choose a model",
    options=list(MODEL_OPTIONS.keys()),
)
selected_model = MODEL_OPTIONS[selected_model_label]
st.sidebar.caption(f"Using `{selected_model}`")

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
                model=selected_model,
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
