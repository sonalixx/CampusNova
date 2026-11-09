import re, streamlit as st
from kb import KB
from db import sb

MODEL = "openai/gpt-oss-20b"

def load_kb():
    try:
        d = sb().table("kb").select("keywords,answer").execute().data
        if d: return [{"k": r["keywords"], "a": r["answer"]} for r in d]
    except Exception:
        pass
    return KB

def llm(q, ctx):
    from groq import Groq
    sys = ("You are a friendly campus assistant for Alliance University. "
        "If the question relates to anything in the campus info below, answer from it and use its exact details. "
        "If it is about finding or reaching a place, give any info you have and tell them to use the Map tab for directions. "
        "Otherwise answer normally and briefly.\n\nCampus info:\n" + ctx)
    msgs = [{"role": "system", "content": sys}]
    msgs += [{"role": r, "content": t} for r, t in st.session_state.get("chat_hist", [])[-6:]]
    msgs.append({"role": "user", "content": q})
    r = Groq(api_key=st.secrets["GROQ_API_KEY"]).chat.completions.create(model=MODEL, max_tokens=400, messages=msgs)
    return r.choices[0].message.content

def top(q, n=3):
    w = set(re.findall(r"\w+", q.lower()))
    s = sorted(((len(w & set(e["k"].split())), e) for e in load_kb()), key=lambda x: -x[0])
    return [e for sc, e in s[:n] if sc > 0]

def answer(q):
    ctx = "\n".join(f"- {e['k']}: {e['a']}" for e in load_kb())
    try:
        return llm(q, ctx)
    except Exception as e:
        return f"⚠️ LLM error: {e}"

NAV = re.compile(r"route|direction|navigate|how (do i|to) (get|reach|go)|way to|nearest|\bmap\b|path to|distance|how far", re.I)

def is_map_q(q):
    from nav_page import graph
    g = graph()
    names = [n.strip().lower() for p in g[3] for n in p["name"].split(" / ")] if g else []
    ql = q.lower()
    return any(n and n in ql for n in names) or bool(NAV.search(ql)) or ("where" in ql and bool(top(q)))

def render():
    st.subheader("🤖 Campus Assistant")
    h = st.session_state.setdefault("chat_hist", [])
    for r, t in h:
        st.chat_message(r).write(t)
    if st.session_state.get("map_hint"):
        st.button("🧭 Open Map for directions", use_container_width=True,
                  on_click=lambda: st.session_state.update(nav="🧭 Map", map_hint=False))
    with st.form("chat_form", clear_on_submit=True):
        q = st.text_input("Ask about campus", placeholder="Where is the library?")
        if st.form_submit_button("Send", use_container_width=True) and q.strip():
            st.session_state.map_hint = is_map_q(q)
            h += [("user", q), ("assistant", answer(q))]
            st.rerun()