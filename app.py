import streamlit as st
from streamlit_cookies_controller import CookieController
from auth import auth_page, _login
from db import sb
import time

st.set_page_config(page_title="Campus App", page_icon="🏫", layout="centered",
                   initial_sidebar_state="collapsed")

cc = CookieController()
st.session_state._cc = cc
ck = cc.getAll() or {}
if "dark" not in st.session_state and ck:
    st.session_state.dark = str(ck.get("theme")) == "dark"
dark = st.session_state.get("dark", False)
if "dark" in st.session_state and str(ck.get("theme")) != ("dark" if dark else "light"):
    cc.set("theme", "dark" if dark else "light", max_age=31536000)

st.markdown("""<style>
.block-container{padding:1rem 1rem 5.5rem}
.st-key-nav{position:fixed;bottom:0;left:0;right:0;z-index:99;background:#fff;
  border-top:1px solid #ddd;padding:6px 4px}
.st-key-nav [role=radiogroup]{justify-content:space-around;width:100%}
.stButton>button{min-height:48px}
</style>""", unsafe_allow_html=True)
if dark:
    st.markdown("""<style>
    .stApp{filter:invert(1) hue-rotate(180deg)}
    .stApp img,.stApp iframe,.pcard{filter:invert(1) hue-rotate(180deg)}
    .stApp .pcard img{filter:none}
    </style>""", unsafe_allow_html=True)

if "user" not in st.session_state:
    if not ck and not st.session_state.get("boot"):
        with st.spinner("Loading..."):
            time.sleep(1.5)
        st.session_state.boot = True
        st.rerun()
    if ck.get("rt"):
        with st.spinner("Signing you in..."):
            try:
                s = sb().auth.refresh_session(str(ck["rt"]))
                _login(s.user, s.session)
            except Exception:
                cc.remove("rt")
    auth_page()
    st.stop()

@st.dialog("🚨 CAMPUS EMERGENCY")
def show_alert(a):
    st.error(f"{a['kind']} at {a.get('place') or 'unknown location'}")
    st.write(f"**{a['name']}** ({a['reg_no']}) · 📞 {a['phone']}")
    st.link_button("📞 Call Security", "tel:+918046199000", use_container_width=True)
    if st.button("OK, got it", use_container_width=True):
        st.session_state.seen.add(a["id"]); st.session_state.popup = None; st.rerun()

@st.fragment(run_every="10s")
def watch():
    seen = st.session_state.setdefault("seen", set())
    for a in sb().table("alerts").select("*").eq("active", True).order("created_at", desc=True).limit(5).execute().data:
        if a["id"] not in seen:
            if a["student_id"] == st.session_state.user.id: seen.add(a["id"])
            else: st.session_state.popup = a; st.rerun()
watch()
if st.session_state.get("popup"):
    show_alert(st.session_state.popup)

PAGES = ["🏠 Home", "🧭 Map", "🤖 Chat", "🚨 SOS"] + (["🛠 Admin"] if st.session_state.profile.get("is_admin") else [])
page = st.radio("nav", PAGES, horizontal=True, key="nav", label_visibility="collapsed")

if page == PAGES[0]:
    import home_page; home_page.render()
elif page == PAGES[1]:
    import nav_page; nav_page.render()
elif page == PAGES[2]:
    import chat_page; chat_page.render()
elif page == PAGES[3]:
    import sos_page; sos_page.render()
else:
    import admin_page; admin_page.render()