import os
import time

import streamlit as st
from dotenv import load_dotenv
from groq import Groq

from core.prompts import SYSTEM_GUARDRAIL
from core.utils import log_performance


load_dotenv()


MODEL_OPTIONS = {
    "Fast: Llama 3.1 8B Instant": "llama-3.1-8b-instant",
    "Higher quality: Llama 3.3 70B Versatile": "llama-3.3-70b-versatile",
}


def get_api_key():
    try:
        return st.secrets["GROQ_API_KEY"]
    except Exception:
        return os.getenv("GROQ_API_KEY")


def read_uploaded_text(uploaded_file):
    if uploaded_file is None:
        return ""

    if uploaded_file.type == "application/pdf":
        return f"Uploaded file: {uploaded_file.name}. PDF parsing is not enabled, so summarize based on the pasted text and question."

    try:
        return uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        return f"Uploaded file: {uploaded_file.name}. The file could not be decoded as text."


st.set_page_config(
    page_title="GenAI Portal",
    page_icon="AI",
    layout="wide",
)

st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        :root {
            --ink: #eefaff;
            --muted: rgba(238, 250, 255, 0.72);
            --cyan: #67dcff;
            --blue: #5b92ff;
            --panel: rgba(8, 22, 42, 0.72);
            --line: rgba(130, 222, 255, 0.24);
        }

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
        }

        .stApp {
            color: var(--ink);
            background:
                radial-gradient(circle at 18% 12%, rgba(103, 220, 255, 0.20), transparent 28%),
                radial-gradient(circle at 82% 8%, rgba(91, 146, 255, 0.18), transparent 24%),
                linear-gradient(135deg, #020612 0%, #071426 48%, #020b17 100%);
        }

        .block-container {
            max-width: 1180px;
            padding-top: 1.7rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background: rgba(4, 12, 24, 0.90);
            border-right: 1px solid rgba(117, 218, 255, 0.18);
        }

        [data-testid="stSidebar"] * {
            color: #eaf6ff;
        }

        .hero {
            position: relative;
            min-height: 590px;
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 30px;
            background:
                linear-gradient(115deg, rgba(7, 16, 33, 0.95), rgba(9, 30, 55, 0.86)),
                radial-gradient(circle at center, rgba(84, 215, 255, 0.16), transparent 42%);
            box-shadow: 0 28px 90px rgba(0, 0, 0, 0.42), inset 0 0 70px rgba(81, 203, 255, 0.08);
            isolation: isolate;
        }

        .hero::before {
            content: "";
            position: absolute;
            inset: -38%;
            z-index: -4;
            background:
                repeating-linear-gradient(90deg, transparent 0 68px, rgba(105, 208, 255, 0.08) 69px 70px),
                repeating-linear-gradient(0deg, transparent 0 58px, rgba(105, 208, 255, 0.055) 59px 60px);
            opacity: 0.7;
            transform: perspective(760px) rotateX(62deg) translateY(16%);
            animation: gridDrift 14s linear infinite;
        }

        .hero::after {
            content: "";
            position: absolute;
            inset: 0;
            z-index: -1;
            background: linear-gradient(90deg, rgba(3, 8, 20, 0.76), transparent 30%, transparent 70%, rgba(3, 8, 20, 0.76));
        }

        .particles,
        .particles::before,
        .particles::after {
            position: absolute;
            inset: 0;
            background-image:
                radial-gradient(circle, rgba(164, 236, 255, 0.78) 0 1px, transparent 1.5px),
                radial-gradient(circle, rgba(98, 179, 255, 0.58) 0 1px, transparent 1.5px);
            background-size: 120px 120px, 190px 190px;
            animation: particles 18s linear infinite;
            opacity: 0.46;
        }

        .particles::before,
        .particles::after {
            content: "";
        }

        .particles::before {
            animation-duration: 24s;
            transform: translateX(30px);
        }

        .particles::after {
            animation-duration: 32s;
            transform: translateY(40px);
        }

        .holo-card {
            position: absolute;
            z-index: 2;
            width: 205px;
            min-height: 126px;
            padding: 18px;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(10, 35, 64, 0.48), rgba(123, 225, 255, 0.08));
            box-shadow: 0 0 34px rgba(75, 198, 255, 0.14), inset 0 0 24px rgba(86, 215, 255, 0.08);
            backdrop-filter: blur(14px);
            animation: cardFloat 6.5s ease-in-out infinite;
        }

        .holo-card span {
            display: block;
            color: var(--muted);
            font-size: 0.82rem;
        }

        .holo-card strong {
            display: block;
            margin-top: 16px;
            font-size: 1.9rem;
        }

        .card-one { left: 7%; top: 18%; }
        .card-two { right: 7%; top: 16%; animation-delay: 1s; }
        .card-three { right: 13%; bottom: 13%; animation-delay: 2s; }

        .ai-figure {
            position: absolute;
            left: 50%;
            top: 50%;
            z-index: 0;
            width: 270px;
            height: 345px;
            opacity: 0.32;
            filter: drop-shadow(0 0 32px rgba(93, 219, 255, 0.38));
            transform: translate(-50%, -50%);
        }

        .ai-head,
        .ai-body,
        .ai-arm {
            position: absolute;
            border: 1px solid rgba(153, 232, 255, 0.38);
            background: linear-gradient(160deg, rgba(230, 249, 255, 0.16), rgba(40, 122, 184, 0.05));
        }

        .ai-head {
            left: 96px;
            top: 18px;
            width: 78px;
            height: 94px;
            border-radius: 42% 42% 46% 46%;
        }

        .ai-body {
            left: 68px;
            top: 122px;
            width: 136px;
            height: 190px;
            border-radius: 58px 58px 24px 24px;
        }

        .ai-arm {
            top: 155px;
            width: 102px;
            height: 12px;
            border-radius: 999px;
            transform-origin: left center;
            animation: gesture 3.6s ease-in-out infinite;
        }

        .ai-arm.left { left: 20px; transform: rotate(-25deg); }
        .ai-arm.right { right: -8px; transform: rotate(22deg); animation-delay: 0.8s; }

        .hero-content {
            position: relative;
            z-index: 3;
            display: flex;
            min-height: 590px;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            max-width: 800px;
            margin: 0 auto;
            padding: 74px 28px;
            text-align: center;
        }

        .eyebrow {
            margin: 0 0 18px;
            color: #a9eaff;
            font-size: 0.78rem;
            font-weight: 800;
            text-transform: uppercase;
        }

        .hero-title {
            margin: 0;
            color: #f5fbff;
            font-size: clamp(3rem, 7vw, 6.4rem);
            font-weight: 800;
            line-height: 0.95;
        }

        .hero-copy {
            max-width: 650px;
            margin: 24px auto 30px;
            color: var(--muted);
            font-size: 1.15rem;
            line-height: 1.7;
        }

        .hero-cta {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 188px;
            min-height: 50px;
            padding: 0 26px;
            border: 1px solid rgba(221, 248, 255, 0.64);
            border-radius: 999px;
            color: #04101f !important;
            background: linear-gradient(135deg, #f5fcff 0%, #7ddfff 52%, #5c98ff 100%);
            box-shadow: 0 18px 52px rgba(75, 190, 255, 0.34);
            font-weight: 800;
            text-decoration: none !important;
            transition: transform 180ms ease, box-shadow 180ms ease;
        }

        .hero-cta:hover {
            transform: translateY(-2px) scale(1.025);
            box-shadow: 0 24px 68px rgba(90, 198, 255, 0.44);
        }

        .metric-grid,
        .trust-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            margin: 28px 0;
        }

        .metric-card,
        .trust-card,
        .result-card {
            border: 1px solid var(--line);
            border-radius: 24px;
            background: var(--panel);
            box-shadow: 0 22px 80px rgba(0, 0, 0, 0.28), inset 0 0 34px rgba(99, 205, 255, 0.05);
            backdrop-filter: blur(22px);
        }

        .metric-card {
            padding: 28px;
        }

        .metric-card strong {
            display: block;
            color: #f5fbff;
            font-size: clamp(2.1rem, 4vw, 4rem);
            line-height: 1;
        }

        .metric-card span,
        .trust-card p,
        .section-copy {
            color: var(--muted);
        }

        .workspace-anchor {
            display: block;
            height: 1px;
            margin-top: 48px;
        }

        .section-title {
            margin: 0 0 10px;
            color: #f5fbff;
            font-size: clamp(2rem, 4vw, 3.6rem);
            line-height: 1;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input,
        div[data-testid="stFileUploader"] section {
            color: #eefaff;
            border: 1px solid rgba(139, 223, 255, 0.28);
            border-radius: 18px;
            background: rgba(6, 18, 34, 0.78);
            box-shadow: inset 0 0 28px rgba(81, 203, 255, 0.06);
        }

        div[data-testid="stTextArea"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stFileUploader"] label,
        .stMarkdown h2,
        .stMarkdown h3 {
            color: #f5fbff;
        }

        .stButton > button {
            min-height: 48px;
            border: 1px solid rgba(151, 231, 255, 0.45);
            border-radius: 999px;
            background: linear-gradient(135deg, #eefbff 0%, #72dcff 48%, #4f8dff 100%);
            color: #04101f;
            font-weight: 800;
            box-shadow: 0 14px 42px rgba(76, 184, 255, 0.32);
            transition: transform 180ms ease, box-shadow 180ms ease;
        }

        .stButton > button:hover {
            border-color: rgba(233, 250, 255, 0.9);
            transform: translateY(-1px) scale(1.01);
            box-shadow: 0 20px 58px rgba(76, 184, 255, 0.42);
        }

        .result-card,
        .trust-card {
            padding: 24px;
        }

        .trust-card h3 {
            margin: 0 0 10px;
            color: #f5fbff;
        }

        @keyframes gridDrift {
            from { transform: perspective(760px) rotateX(62deg) translateY(10%); }
            to { transform: perspective(760px) rotateX(62deg) translateY(22%); }
        }

        @keyframes particles {
            from { background-position: 0 0, 0 0; }
            to { background-position: 220px 180px, -260px 220px; }
        }

        @keyframes cardFloat {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-16px); }
        }

        @keyframes gesture {
            0%, 100% { rotate: 0deg; }
            50% { rotate: 7deg; }
        }

        @media (max-width: 820px) {
            .hero,
            .hero-content {
                min-height: 540px;
            }

            .holo-card {
                opacity: 0.45;
            }

            .card-one { left: -92px; }
            .card-two { right: -112px; }
            .card-three { display: none; }
            .metric-grid,
            .trust-grid {
                grid-template-columns: 1fr;
            }
        }

        /* Apple-inspired GenAI dashboard color system */
        :root {
            --ink: #1D1D1F;
            --muted: rgba(29, 29, 31, 0.68);
            --cyan: #0066CC;
            --blue: #0066CC;
            --panel: rgba(255, 255, 255, 0.72);
            --line: rgba(29, 29, 31, 0.10);
        }

        .stApp {
            color: #1D1D1F;
            background: #FFFFFF;
        }

        [data-testid="stSidebar"] {
            background: rgba(245, 245, 247, 0.86);
            border-right: 1px solid rgba(29, 29, 31, 0.10);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }

        [data-testid="stSidebar"] * {
            color: #1D1D1F;
        }

        .hero {
            border: 1px solid rgba(29, 29, 31, 0.10);
            background:
                radial-gradient(circle at 50% 24%, rgba(0, 102, 204, 0.12), transparent 34%),
                linear-gradient(180deg, #FFFFFF 0%, #F5F5F7 100%);
            box-shadow: 0 28px 90px rgba(29, 29, 31, 0.10);
        }

        .hero::before {
            background:
                repeating-linear-gradient(90deg, transparent 0 68px, rgba(29, 29, 31, 0.035) 69px 70px),
                repeating-linear-gradient(0deg, transparent 0 58px, rgba(29, 29, 31, 0.03) 59px 60px);
        }

        .hero::after {
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.82), transparent 30%, transparent 70%, rgba(255, 255, 255, 0.82));
        }

        .particles,
        .particles::before,
        .particles::after {
            background-image:
                radial-gradient(circle, rgba(0, 102, 204, 0.18) 0 1px, transparent 1.5px),
                radial-gradient(circle, rgba(29, 29, 31, 0.10) 0 1px, transparent 1.5px);
            opacity: 0.36;
        }

        .hero-title,
        .holo-card strong,
        .metric-card strong,
        .section-title,
        .trust-card h3,
        .stMarkdown h2,
        .stMarkdown h3 {
            color: #1D1D1F;
        }

        .hero-copy,
        .holo-card span,
        .metric-card span,
        .trust-card p,
        .section-copy {
            color: rgba(29, 29, 31, 0.68);
        }

        .eyebrow {
            color: #0066CC;
        }

        .hero-cta,
        .stButton > button {
            border: 1px solid #0066CC;
            color: #FFFFFF !important;
            background: #0066CC;
            box-shadow: 0 16px 38px rgba(0, 102, 204, 0.22);
        }

        .hero-cta:hover,
        .stButton > button:hover {
            box-shadow: 0 22px 54px rgba(0, 102, 204, 0.26);
        }

        .metric-card,
        .trust-card,
        .result-card,
        .holo-card {
            border: 1px solid rgba(29, 29, 31, 0.10);
            background: rgba(255, 255, 255, 0.72);
            box-shadow: 0 24px 70px rgba(29, 29, 31, 0.08);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
        }

        .ai-head,
        .ai-body,
        .ai-arm {
            border-color: rgba(29, 29, 31, 0.10);
            background: rgba(255, 255, 255, 0.56);
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input,
        div[data-testid="stFileUploader"] section {
            color: #1D1D1F;
            border: 1px solid rgba(29, 29, 31, 0.10);
            background: rgba(255, 255, 255, 0.82);
            box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.36);
        }

        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stTextInput"] input:focus {
            border-color: rgba(0, 102, 204, 0.34);
            box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.08);
        }

        div[data-testid="stTextArea"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stFileUploader"] label {
            color: #1D1D1F;
        }
    </style>
    <section class="hero">
        <div class="particles"></div>
        <div class="holo-card card-one"><span>Latency</span><strong>0.82s</strong></div>
        <div class="holo-card card-two"><span>Signal Quality</span><strong>98%</strong></div>
        <div class="holo-card card-three"><span>Reports</span><strong>Live</strong></div>
        <div class="ai-figure" aria-hidden="true">
            <div class="ai-head"></div>
            <div class="ai-body"></div>
            <div class="ai-arm left"></div>
            <div class="ai-arm right"></div>
        </div>
        <div class="hero-content">
            <p class="eyebrow">AI Technical Transformation Platform</p>
            <h1 class="hero-title">Intelligence, redefined.</h1>
            <p class="hero-copy">
                Upload notes, paste architecture context, ask your assistant, and turn messy technical input into executive-ready Markdown in seconds.
            </p>
            <a class="hero-cta" href="#workspace">Start Analysis</a>
        </div>
    </section>
    <section class="metric-grid">
        <article class="metric-card"><strong>12,480</strong><span>Reports Generated</span></article>
        <article class="metric-card"><strong>98%</strong><span>Accuracy</span></article>
        <article class="metric-card"><strong>7,420</strong><span>Users Helped</span></article>
    </section>
    <span id="workspace" class="workspace-anchor"></span>
    <p class="eyebrow">Live Workspace</p>
    <h2 class="section-title">Move from raw input to polished insight.</h2>
    <p class="section-copy">Combine files, pasted text, and focused questions into a single technical summary request.</p>
    """,
    unsafe_allow_html=True,
)

api_key = get_api_key()

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

left_col, right_col = st.columns([1.05, 0.95], gap="large")

with left_col:
    uploaded_file = st.file_uploader(
        "Upload document",
        type=["txt", "md", "csv", "json", "pdf"],
        help="Text-like files are read directly. PDF names are included, but PDF parsing is not enabled.",
    )
    pasted_text = st.text_area(
        "Paste technical context",
        placeholder="Paste architecture notes, incident details, migration plans, logs, or rough meeting notes...",
        height=210,
    )
    ask_input = st.text_input(
        "Ask AI",
        placeholder="Example: summarize risks and recommended next actions",
    )
    generate = st.button("Generate Summary", type="primary", use_container_width=True)

with right_col:
    st.markdown(
        """
        <div class="result-card">
            <p class="eyebrow">Output</p>
            <h3>Executive Summary</h3>
            <p class="section-copy">Your generated summary, risks, recommendations, and next steps will appear below after analysis.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

if generate:
    if not api_key:
        st.error("Missing GROQ_API_KEY. Add it to Streamlit Secrets before deploying.")
        st.stop()

    uploaded_text = read_uploaded_text(uploaded_file)
    prompt_parts = [uploaded_text.strip(), pasted_text.strip(), ask_input.strip()]
    prompt = "\n\n".join(part for part in prompt_parts if part)

    if not prompt:
        st.warning("Please upload a document, paste technical context, or ask a technical question first.")
        st.stop()

    client = Groq(api_key=api_key)
    start_time = time.time()

    with st.spinner("Initializing intelligence..."):
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

    st.markdown("### Generated Output")
    st.markdown(response_text)
    st.caption(f"Completed in {duration:.2f}s")

st.markdown(
    """
    <section class="trust-grid">
        <article class="trust-card">
            <h3>Secure</h3>
            <p>Secrets are loaded from Streamlit Secrets or your local environment, never from the public frontend.</p>
        </article>
        <article class="trust-card">
            <h3>Fast</h3>
            <p>Groq-backed generation keeps the workflow quick for summaries, risks, and next steps.</p>
        </article>
        <article class="trust-card">
            <h3>Enterprise Ready</h3>
            <p>Structured inputs, model selection, and clean Markdown output make it feel like a real product.</p>
        </article>
    </section>
    """,
    unsafe_allow_html=True,
)
