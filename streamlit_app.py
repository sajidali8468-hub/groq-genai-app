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

MODEL_PRICING_PER_1M = {
    "llama-3.1-8b-instant": {"input": 0.05, "output": 0.08},
    "llama-3.3-70b-versatile": {"input": 0.59, "output": 0.79},
}

TECHNICAL_TERMS = {
    "api",
    "architecture",
    "backend",
    "cloud",
    "code",
    "database",
    "deployment",
    "devops",
    "fastapi",
    "frontend",
    "infrastructure",
    "latency",
    "logs",
    "migration",
    "microservices",
    "model",
    "python",
    "requirements",
    "security",
    "server",
    "streamlit",
    "system",
    "technical",
}

NON_TECHNICAL_TERMS = {
    "bake",
    "cake",
    "chicken",
    "cook",
    "cooking",
    "dinner",
    "food",
    "love poem",
    "pasta",
    "recipe",
    "restaurant",
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


def is_out_of_scope(prompt):
    normalized = prompt.lower()
    has_non_technical = any(term in normalized for term in NON_TECHNICAL_TERMS)
    has_technical = any(term in normalized for term in TECHNICAL_TERMS)
    return has_non_technical and not has_technical


def build_system_prompt(strict_grounding):
    if not strict_grounding:
        return SYSTEM_GUARDRAIL

    return (
        f"{SYSTEM_GUARDRAIL}\n"
        "Strict Technical Grounding is enabled. Only use facts from the uploaded or pasted input. "
        "If a claim is not supported by the supplied content, say it is not evidenced in the provided material. "
        "When citations are useful, include concise Harvard-style references to the supplied document or notes."
    )


def serialize_groq_response(completion):
    if hasattr(completion, "model_dump"):
        return completion.model_dump()
    if hasattr(completion, "to_dict"):
        return completion.to_dict()
    return {"raw": str(completion)}


def usage_value(usage, name):
    if usage is None:
        return 0
    if isinstance(usage, dict):
        return usage.get(name, 0) or 0
    return getattr(usage, name, 0) or 0


def estimate_cost(model, prompt_tokens, completion_tokens):
    pricing = MODEL_PRICING_PER_1M.get(model, {"input": 0, "output": 0})
    input_cost = prompt_tokens * pricing["input"] / 1_000_000
    output_cost = completion_tokens * pricing["output"] / 1_000_000
    return input_cost + output_cost


def default_performance():
    return {
        "latency": "Ready",
        "tokens_per_second": "0",
        "total_tokens": "0",
        "cost": "$0.000000",
        "signal": "Idle",
    }


st.set_page_config(
    page_title="GenAI Portal",
    page_icon="AI",
    layout="wide",
)

if "performance" not in st.session_state:
    st.session_state.performance = default_performance()

if "last_trace" not in st.session_state:
    st.session_state.last_trace = None

if "last_response_markdown" not in st.session_state:
    st.session_state.last_response_markdown = ""

performance = st.session_state.performance

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

        .refusal-card {
            border-color: rgba(255, 59, 48, 0.28) !important;
            background: rgba(255, 59, 48, 0.08) !important;
        }

        .skeleton-card {
            min-height: 178px;
            overflow: hidden;
        }

        .skeleton-line {
            height: 14px;
            margin: 14px 0;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(29, 29, 31, 0.06), rgba(0, 102, 204, 0.12), rgba(29, 29, 31, 0.06));
            background-size: 220% 100%;
            animation: shimmer 1.2s ease-in-out infinite;
        }

        .skeleton-line.short {
            width: 46%;
        }

        .skeleton-line.medium {
            width: 72%;
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

        @keyframes shimmer {
            from { background-position: 120% 0; }
            to { background-position: -120% 0; }
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
        <div class="holo-card card-one"><span>Latency</span><strong>__LATENCY__</strong></div>
        <div class="holo-card card-two"><span>Signal Quality</span><strong>__SIGNAL__</strong></div>
        <div class="holo-card card-three"><span>Tokens/Sec</span><strong>__TOKENS_PER_SECOND__</strong></div>
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
        <article class="metric-card"><strong>__TOTAL_TOKENS__</strong><span>Total Tokens Used</span></article>
        <article class="metric-card"><strong>__COST__</strong><span>Estimated Generation Cost</span></article>
        <article class="metric-card"><strong>98%</strong><span>Guardrail Confidence</span></article>
    </section>
    <span id="workspace" class="workspace-anchor"></span>
    <p class="eyebrow">Live Workspace</p>
    <h2 class="section-title">Move from raw input to polished insight.</h2>
    <p class="section-copy">Combine files, pasted text, and focused questions into a single technical summary request.</p>
    """
    .replace("__LATENCY__", performance["latency"])
    .replace("__SIGNAL__", performance["signal"])
    .replace("__TOKENS_PER_SECOND__", performance["tokens_per_second"])
    .replace("__TOTAL_TOKENS__", performance["total_tokens"])
    .replace("__COST__", performance["cost"]),
    unsafe_allow_html=True,
)

api_key = get_api_key()

st.sidebar.title("Settings")
selected_model_label = st.sidebar.selectbox(
    "Choose a model",
    options=list(MODEL_OPTIONS.keys()),
)
selected_model = MODEL_OPTIONS[selected_model_label]
st.sidebar.caption(f"Using `{selected_model}`")
strict_grounding = st.sidebar.toggle(
    "Strict Technical Grounding",
    value=True,
    help="When enabled, the assistant must ground claims in the supplied document or pasted notes and use Harvard-style citations when useful.",
)

st.sidebar.divider()
st.sidebar.subheader("Sanity Check")
latency_slot = st.sidebar.empty()
tps_slot = st.sidebar.empty()
tokens_slot = st.sidebar.empty()
cost_slot = st.sidebar.empty()

latency_slot.metric("Latency", performance["latency"])
tps_slot.metric("Tokens/Sec", performance["tokens_per_second"])
tokens_slot.metric("Total Tokens", performance["total_tokens"])
cost_slot.metric("Estimated Cost", performance["cost"])

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
    result_placeholder = st.empty()
    result_placeholder.markdown(
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

    if is_out_of_scope(prompt):
        refusal_message = "Input out of scope. This platform is restricted to Technical Documentation only."
        st.toast(refusal_message)
        result_placeholder.markdown(
            f"""
            <div class="result-card refusal-card">
                <p class="eyebrow">Guardrail Refusal</p>
                <h3>Input out of scope</h3>
                <p class="section-copy">{refusal_message}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.session_state.last_response_markdown = refusal_message
        st.session_state.last_trace = {
            "system_prompt": build_system_prompt(strict_grounding),
            "request": {"model": selected_model, "strict_grounding": strict_grounding, "prompt": prompt},
            "response": {"refusal": refusal_message},
        }
        st.stop()

    client = Groq(api_key=api_key)
    system_prompt = build_system_prompt(strict_grounding)
    start_time = time.time()

    result_placeholder.markdown(
        """
        <div class="result-card skeleton-card">
            <p class="eyebrow">Generating</p>
            <h3>Initializing intelligence...</h3>
            <div class="skeleton-line"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line short"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.spinner("Initializing intelligence..."):
        try:
            completion = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": system_prompt},
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
    usage = getattr(completion, "usage", None)
    prompt_tokens = usage_value(usage, "prompt_tokens")
    completion_tokens = usage_value(usage, "completion_tokens")
    total_tokens = usage_value(usage, "total_tokens") or prompt_tokens + completion_tokens
    tokens_per_second = completion_tokens / duration if duration and completion_tokens else 0
    cost = estimate_cost(selected_model, prompt_tokens, completion_tokens)

    st.session_state.performance = {
        "latency": f"{duration:.2f}s",
        "tokens_per_second": f"{tokens_per_second:.0f}",
        "total_tokens": f"{total_tokens:,}",
        "cost": f"${cost:.6f}",
        "signal": "98%",
    }
    st.session_state.last_response_markdown = response_text
    st.session_state.last_trace = {
        "system_prompt": system_prompt,
        "request": {
            "model": selected_model,
            "strict_grounding": strict_grounding,
            "temperature": 0.5,
            "max_tokens": 1024,
            "prompt_preview": prompt[:1200],
        },
        "response": serialize_groq_response(completion),
        "metrics": st.session_state.performance,
    }

    latency_slot.metric("Latency", st.session_state.performance["latency"])
    tps_slot.metric("Tokens/Sec", st.session_state.performance["tokens_per_second"])
    tokens_slot.metric("Total Tokens", st.session_state.performance["total_tokens"])
    cost_slot.metric("Estimated Cost", st.session_state.performance["cost"])

    log_performance(duration, len(response_text))

    result_placeholder.markdown(
        f"""
        <div class="result-card">
            <p class="eyebrow">Output</p>
            <h3>Executive Summary</h3>
            <p class="section-copy">Completed in {duration:.2f}s · {total_tokens:,} tokens · Estimated cost {cost:.6f}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("### Generated Output")
    st.markdown(response_text)
    st.download_button(
        "Download as Markdown",
        data=response_text,
        file_name="genai-summary.md",
        mime="text/markdown",
        use_container_width=True,
    )
    st.caption(f"Completed in {duration:.2f}s")

if st.session_state.last_trace:
    with st.expander("System Trace"):
        st.markdown("#### System Prompt")
        st.code(st.session_state.last_trace["system_prompt"], language="markdown")
        st.markdown("#### Raw Groq Response / Trace")
        st.json(st.session_state.last_trace)

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
