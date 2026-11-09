import streamlit as st
from db import sb
from kb import KB

def render():
    st.subheader("🛠 Admin")
    t1, t2 = st.tabs(["📢 Notices", "📚 Chat KB"])
    with t1:
        with st.form("nf", clear_on_submit=True):
            t = st.text_input("Title")
            b = st.text_area("Message")
            if st.form_submit_button("Post notice", use_container_width=True) and t:
                sb().table("notices").insert({"title": t, "body": b}).execute()
                st.rerun()
        for n in sb().table("notices").select("*").order("created_at", desc=True).limit(20).execute().data:
            with st.container(border=True):
                st.markdown(f"**{n['title']}**")
                st.caption((n["body"] or "")[:100])
                if st.button("🗑 Delete", key=f"dn{n['id']}"):
                    sb().table("notices").delete().eq("id", n["id"]).execute()
                    st.rerun()
    with t2:
        rows = sb().table("kb").select("*").order("id").execute().data
        if not rows and st.button("Import starter KB from kb.py", use_container_width=True):
            sb().table("kb").insert([{"keywords": e["k"], "answer": e["a"]} for e in KB]).execute()
            st.rerun()
        with st.form("kf", clear_on_submit=True):
            k = st.text_input("Keywords (space separated)")
            a = st.text_area("Answer")
            if st.form_submit_button("Add entry", use_container_width=True) and k and a:
                sb().table("kb").insert({"keywords": k, "answer": a}).execute()
                st.rerun()
        for r in rows:
            with st.expander(r["keywords"][:40]):
                k = st.text_input("Keywords", r["keywords"], key=f"k{r['id']}")
                a = st.text_area("Answer", r["answer"], key=f"a{r['id']}")
                c1, c2 = st.columns(2)
                if c1.button("Save", key=f"s{r['id']}", use_container_width=True):
                    sb().table("kb").update({"keywords": k, "answer": a}).eq("id", r["id"]).execute()
                    st.rerun()
                if c2.button("Delete", key=f"d{r['id']}", use_container_width=True):
                    sb().table("kb").delete().eq("id", r["id"]).execute()
                    st.rerun()