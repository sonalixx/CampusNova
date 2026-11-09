import streamlit as st
from db import sb

KINDS = ["🏥 Medical", "🔥 Fire", "🚨 Harassment / Safety", "🚗 Accident", "❓ Other"]

def render():
    p, u = st.session_state.profile, st.session_state.user
    st.subheader("🚨 Emergency")
    a, b = st.columns(2)
    a.link_button("📞 Security", "tel:+918046199000", use_container_width=True)
    b.link_button("🏥 Health", "tel:+918046199112", use_container_width=True)
    st.link_button("☎️ National emergency 112", "tel:112", use_container_width=True)
    kind = st.selectbox("Type", KINDS)
    place = st.text_input("Where are you?", placeholder="Block, floor, landmark")
    if st.button("🚨 SEND SOS", type="primary", use_container_width=True):
        r = sb().table("alerts").insert({"student_id": u.id, "name": p["name"], "reg_no": p["reg_no"],
            "phone": p["phone"], "kind": kind, "place": place}).execute().data[0]
        st.session_state.setdefault("seen", set()).add(r["id"])
        st.success("SOS sent to all campus app users.")
    st.caption("For a real emergency, also call the numbers above.")
    for r in sb().table("alerts").select("*").eq("student_id", u.id).eq("active", True).execute().data:
        if st.button(f"✅ Mark resolved: {r['kind']}", key=f"r{r['id']}", use_container_width=True):
            sb().table("alerts").update({"active": False}).eq("id", r["id"]).execute()
            st.rerun()