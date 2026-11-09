import time
import streamlit as st
from db import sb

def _login(user, session=None):
    d = sb().table("students").select("*").eq("id", user.id).execute().data
    if not d:
        m = user.user_metadata or {}
        d = sb().table("students").upsert({"id": user.id, "name": m.get("name"),
            "reg_no": m.get("reg_no"), "phone": m.get("phone")}).execute().data
    st.session_state.user = user
    st.session_state.profile = d[0]
    if session:
        st.session_state._cc.set("rt", session.refresh_token, max_age=2592000)
        time.sleep(0.7)
    st.rerun()

def auth_page():
    st.title("🏫 Campus App")
    t1, t2 = st.tabs(["Login", "Sign up"])
    with t1, st.form("login"):
        e = st.text_input("Email", key="le")
        p = st.text_input("Password", type="password", key="lp")
        if st.form_submit_button("Login", use_container_width=True):
            try:
                with st.spinner("Logging in..."):
                    r = sb().auth.sign_in_with_password({"email": e, "password": p})
                    _login(r.user, r.session)
            except Exception as ex:
                st.error(str(ex))
    with t2, st.form("signup"):
        n = st.text_input("Full name")
        r = st.text_input("Registration no.")
        ph = st.text_input("Phone")
        e = st.text_input("Email", key="se")
        p = st.text_input("Password (min 6)", type="password", key="sp")
        if st.form_submit_button("Create account", use_container_width=True):
            try:
                with st.spinner("Creating your account..."):
                    res = sb().auth.sign_up({"email": e, "password": p,
                        "options": {"data": {"name": n, "reg_no": r, "phone": ph}}})
                    _login(res.user, res.session)
            except Exception as ex:
                st.error(str(ex))