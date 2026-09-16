"""
LeadPilot - AI Sales Lead Qualifier
------------------------------------
A Streamlit chat app that has a natural conversation with an incoming
sales lead, asks qualifying questions, and produces a structured
hand-off summary for a sales rep.

Run locally:
    streamlit run app.py

Point it at your AMD Developer Cloud vLLM endpoint by setting:
    LEADPILOT_BASE_URL   e.g. http://YOUR_DROPLET_IP:8000/v1
    LEADPILOT_MODEL      e.g. the model name your vLLM Quick Start deployed
(You can also just edit the defaults below.)
"""

import os
import json
import streamlit as st
from openai import OpenAI

# ---------------------------------------------------------------------------
# Configuration - point this at your AMD Developer Cloud vLLM endpoint
# ---------------------------------------------------------------------------
BASE_URL = os.environ.get("LEADPILOT_BASE_URL", "http://YOUR_DROPLET_IP:8000/v1")
MODEL_NAME = os.environ.get("LEADPILOT_MODEL", "meta-llama/Llama-3.1-8B-Instruct")
API_KEY = os.environ.get("LEADPILOT_API_KEY", "not-required")  # vLLM doesn't need a real key

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

# ---------------------------------------------------------------------------
# The qualifying questions LeadPilot is trying to get answered.
# These map to a lightweight version of BANT (Budget, Authority, Need, Timeline).
# ---------------------------------------------------------------------------
QUALIFYING_FIELDS = [
    ("need", "What problem or goal are they trying to solve?"),
    ("budget", "What budget range are they working with?"),
    ("timeline", "How soon do they want/need to get started?"),
    ("authority", "Are they the decision maker, or who else is involved?"),
]

SYSTEM_PROMPT = f"""You are LeadPilot, a friendly AI assistant that qualifies inbound
sales leads on behalf of a sales team, before handing them off to a human rep.

Your job in this conversation:
1. Greet the lead warmly and ask what brought them here.
2. Naturally, over the course of the conversation, find out:
   - Need: {QUALIFYING_FIELDS[0][1]}
   - Budget: {QUALIFYING_FIELDS[1][1]}
   - Timeline: {QUALIFYING_FIELDS[2][1]}
   - Authority: {QUALIFYING_FIELDS[3][1]}
3. Ask ONE question at a time. Keep it conversational, not like a form.
4. Do not make up product details, pricing, or promises - if asked, say a
   rep will follow up with specifics.
5. Once you have a reasonable sense of all four points (or the lead clearly
   doesn't want to share more), thank them and let them know a team member
   will follow up shortly. Do not ask more than 6-7 questions total.

Keep every message short - 1-3 sentences.
"""

SUMMARY_PROMPT = """Based on the conversation above, extract what you learned about
this lead. Respond with ONLY valid JSON, no other text, in exactly this shape:

{{
  "need": "short summary of their need, or null if unknown",
  "budget": "short summary of budget signal, or null if unknown",
  "timeline": "short summary of timeline, or null if unknown",
  "authority": "short summary of decision-making authority, or null if unknown",
  "fit_score": <integer 0-100, your estimate of how qualified/sales-ready this lead is>,
  "recommended_action": "fast-track" | "nurture" | "disqualify",
  "rationale": "one sentence explaining the fit_score and recommended_action"
}}
"""


def call_model(messages, temperature=0.6):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content


def generate_summary(chat_history):
    messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + chat_history
        + [{"role": "user", "content": SUMMARY_PROMPT}]
    )
    raw = call_model(messages, temperature=0.1)
    # Models sometimes wrap JSON in code fences - strip those defensively.
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "Could not parse model output as JSON", "raw": raw}


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------
st.set_page_config(page_title="LeadPilot", page_icon=":airplane:")
st.title("LeadPilot")
st.caption("AI sales lead qualifier - built on AMD Developer Cloud")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.session_state.summary = None

# Render chat history (skip the system message)
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Kick off the conversation with a greeting if it's empty
if len(st.session_state.messages) == 1:
    greeting = "Hi! Thanks for reaching out - what brought you here today?"
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    with st.chat_message("assistant"):
        st.write(greeting)

user_input = st.chat_input("Type your reply...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    reply = call_model(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.write(reply)

st.divider()
if st.button("Generate lead summary for sales rep"):
    with st.spinner("Analyzing conversation..."):
        st.session_state.summary = generate_summary(st.session_state.messages[1:])

if st.session_state.summary:
    s = st.session_state.summary
    if "error" in s:
        st.error(s["error"])
        st.code(s.get("raw", ""))
    else:
        st.subheader("Lead summary")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Fit score", f"{s.get('fit_score', '?')}/100")
        with col2:
            st.metric("Recommended action", s.get("recommended_action", "?"))
        st.write(f"**Need:** {s.get('need')}")
        st.write(f"**Budget:** {s.get('budget')}")
        st.write(f"**Timeline:** {s.get('timeline')}")
        st.write(f"**Authority:** {s.get('authority')}")
        st.write(f"**Rationale:** {s.get('rationale')}")
