import time, streamlit as st
from db import sb

def card(p):
    a = (f'<img src="{p["avatar_url"]}" style="width:84px;height:84px;border-radius:50%;object-fit:cover;border:3px solid #fff">'
         if p.get("avatar_url") else
         f'<div style="width:84px;height:84px;border-radius:50%;background:#ffffff40;color:#fff;display:flex;align-items:center;justify-content:center;font-size:36px">{(p.get("name") or "?")[:1].upper()}</div>')
    rows = [("🪪", p.get("reg_no")), ("🎓", p.get("branch")), ("✉️", p.get("univ_email")), ("📞", p.get("phone")), ("🏠", p.get("address"))]
    body = "".join(f'<div style="margin-top:5px;font-size:14px">{i} {v}</div>' for i, v in rows if v)
    st.markdown(f'<div class="pcard" style="background:linear-gradient(135deg,#8b0000,#c2410c);color:#fff;border-radius:18px;padding:18px;display:flex;gap:16px;align-items:center">{a}<div><div style="font-size:21px;font-weight:700">{p.get("name") or ""}</div>{body}</div></div>', unsafe_allow_html=True)

def edit(p):
    with st.form("prof"):
        v = {"name": st.text_input("Name", p.get("name") or ""),
             "univ_email": st.text_input("University email", p.get("univ_email") or ""),
             "reg_no": st.text_input("Registration no.", p.get("reg_no") or ""),
             "phone": st.text_input("Phone", p.get("phone") or ""),
             "address": st.text_area("Address", p.get("address") or ""),
             "branch": st.text_input("Branch", p.get("branch") or "")}
        pic = st.file_uploader("Profile picture", type=["png", "jpg", "jpeg"])
        rm = st.checkbox("Remove current photo")
        if st.form_submit_button("Save", use_container_width=True):
            try:
                if pic:
                    path = f"{p['id']}/avatar.png"
                    sb().storage.from_("avatars").upload(path, pic.getvalue(), {"content-type": pic.type, "upsert": "true"})
                    v["avatar_url"] = sb().storage.from_("avatars").get_public_url(path).rstrip("?") + f"?v={int(time.time())}"
                elif rm:
                    v["avatar_url"] = None
                st.session_state.profile = sb().table("students").update(v).eq("id", p["id"]).execute().data[0]
                st.rerun()
            except Exception as e:
                st.error(str(e))

def render():
    p = st.session_state.profile
    card(p)
    st.write("")
    st.link_button("🌐 Top Private University in Bangalore | Alliance University",
                   "https://www.alliance.edu.in/", use_container_width=True)
    st.markdown("#### 📢 Notices")
    ns = sb().table("notices").select("*").order("created_at", desc=True).limit(5).execute().data
    if not ns: st.caption("No notices yet.")
    for n in ns:
        with st.container(border=True):
            st.markdown(f"**{n['title']}**")
            st.write(n["body"])
            st.caption(n["created_at"][:10])
    with st.expander("✏️ Edit profile"):
        edit(p)
    d = st.toggle("🌙 Dark mode", value=st.session_state.get("dark", False))
    if d != st.session_state.get("dark", False):
        st.session_state.dark = d
        st.rerun()
    if st.button("Logout", use_container_width=True):
        sb().auth.sign_out()
        st.session_state._cc.remove("rt")
        time.sleep(0.7)
        st.session_state.clear()
        st.rerun()