from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from neo4j_service import (
    create_drink,
    create_user,
    delete_drink,
    delete_user,
    get_dashboard_metrics,
    get_drink_stats,
    get_drinks,
    get_preferences,
    get_users,
    graph_neighborhood,
    ping,
    recommend_drinks,
    rename_drink,
    rename_user,
    reset_drink_data,
    seed_demo_data,
    set_preference,
    set_preferences,
)

st.set_page_config(page_title="DrinkGraph Recommender", page_icon="🍵", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
      .hero {
        padding: 1.4rem 1.6rem; border-radius: 22px;
        background: linear-gradient(120deg, #14532d 0%, #166534 50%, #a16207 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 {margin:0; font-size:2.15rem;}
      .hero p {opacity:.88; margin:.35rem 0 0 0;}
      .drink-card {
        padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px; margin-bottom: .75rem;
      }
      .score-pill {
        display:inline-block; padding:.2rem .55rem; border-radius:999px;
        background:#166534; color:white; font-size:.8rem; font-weight:700;
      }
      .muted {opacity:.72; font-size:.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


DRINK_EMOJI = {
    "Bubble Milk Tea": "🧋", "Cocoa": "🍫", "Green Tea": "🍵", "Lemon Tea": "🍋",
    "Orange Juice": "🍊", "Americano": "☕", "Latte": "☕", "Cappuccino": "☕",
    "มัทฉะLatte": "🍵", "Fresh Milk": "🥛",
}
_KEYWORDS = [("tea", "🍵"), ("ชา", "🍵"), ("coffee", "☕"), ("กาแฟ", "☕"), ("latte", "☕"),
             ("juice", "🧃"), ("น้ำ", "🧃"), ("milk", "🥛"), ("นม", "🥛"), ("soda", "🥤")]


def dlabel(name: str) -> str:
    """Emoji + drink name (exact match first, then keyword, else generic cup)."""
    emoji = DRINK_EMOJI.get(name)
    if not emoji:
        low = name.lower()
        emoji = next((e for k, e in _KEYWORDS if k in low), "🥤")
    return f"{emoji} {name}"


def flash(msg: str) -> None:
    st.session_state["_flash"] = msg


def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\n# database = "..."  # ไม่ต้องใส่ก็ได้ (ใช้ database หลักของ instance)',
            language="toml",
        )
        st.caption("นำค่าด้านบนไปใส่ใน Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def user_selector(key: str) -> str:
    users = get_users()
    if not users:
        st.info("ยังไม่มีผู้ใช้ กรุณาไปหน้า Admin / Setup แล้วสร้างข้อมูลตัวอย่าง หรือเพิ่มผู้ใช้ใน Manage Data")
        st.stop()
    return st.selectbox("เลือกผู้ใช้", users, key=key)


def explain_reason(row: dict) -> str:
    parts = []
    if row.get("similar_users"):
        parts.append("คนที่รสนิยมคล้ายกันชอบ: " + escape(", ".join(row["similar_users"])))
    if row.get("shared_drinks"):
        parts.append("เชื่อมผ่านเครื่องดื่มที่ชอบเหมือนกัน: " + escape(", ".join(row["shared_drinks"])))
    parts.append(f"ถูกใจ {row['like_count']} คน")
    if row.get("dislike_count"):
        parts.append(f"ไม่ชอบ {row['dislike_count']} คน")
    return " • ".join(parts)


require_connection()

with st.sidebar:
    st.markdown("## 🍵 DrinkGraph")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["Dashboard", "Recommendations", "Drink Search", "Like / Dislike", "Graph Explorer", "Manage Data (CRUD)", "Admin / Setup"],
    )
    st.divider()
    st.caption("Graph Database Project")

st.markdown(
    """
    <div class="hero">
      <h1>🍵 DrinkGraph Recommendation System</h1>
      <p>ระบบแนะนำเครื่องดื่มด้วย Graph Database (Collaborative Filtering) ที่อธิบายเหตุผลของคำแนะนำได้</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "_flash" in st.session_state:
    st.success(st.session_state.pop("_flash"))

# ============================================================ Dashboard
if page == "Dashboard":
    st.subheader("ภาพรวมระบบ")
    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Users", m.get("users", 0))
    c2.metric("Drinks", m.get("drinks", 0))
    c3.metric("LIKES", m.get("likes", 0))
    c4.metric("DISLIKES", m.get("dislikes", 0))

    stats = get_drink_stats()
    if stats:
        st.markdown("### ความนิยมของเครื่องดื่ม")
        st.bar_chart(pd.DataFrame(stats).set_index("drink")[["likes", "dislikes"]])

    st.divider()
    user = user_selector("dash_user")
    pref = get_preferences(user)
    l, r = st.columns(2)
    l.markdown(f"### ❤️ {user} ชอบ")
    l.write(", ".join(dlabel(x) for x in pref["liked"]) or "ยังไม่มี")
    r.markdown(f"### 😞 {user} ไม่ชอบ")
    r.write(", ".join(dlabel(x) for x in pref["disliked"]) or "ยังไม่มี")

# ============================================================ Recommendations
elif page == "Recommendations":
    st.subheader("✨ เครื่องดื่มที่แนะนำ")
    user = user_selector("rec_user")
    top_n = st.slider("จำนวนคำแนะนำ", 3, 10, 5)
    rows = recommend_drinks(user, top_n)
    st.caption(
        "score = จำนวนเส้นทาง (เครื่องดื่มที่ชอบเหมือนกัน → คนอื่นที่ชอบเหมือนกัน → เครื่องดื่มใหม่) "
        "และตัดเครื่องดื่มที่ผู้ใช้ชอบหรือไม่ชอบอยู่แล้วออก"
    )
    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้")
    for i, row in enumerate(rows, start=1):
        st.markdown(
            f"""
            <div class="drink-card">
              <span class="score-pill">#{i} · score {row['score']}</span>
              <h3 style="margin:.55rem 0 .2rem 0">{escape(dlabel(row['drink']))}</h3>
              <p><b>เหตุผล:</b> {explain_reason(row)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ============================================================ Search
elif page == "Drink Search":
    st.subheader("🔎 ค้นหาเครื่องดื่ม")
    kw = st.text_input("ชื่อเครื่องดื่ม", placeholder="เช่น Tea, Latte, มัทฉะ")
    rows = get_drink_stats(kw)
    st.write(f"พบ {len(rows)} รายการ")
    if rows:
        df = pd.DataFrame(rows)
        df["drink"] = df["drink"].map(dlabel)
        st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================================ Like / Dislike
elif page == "Like / Dislike":
    st.subheader("📝 บันทึกความชอบ")
    user = user_selector("pref_user")
    drinks = get_drinks()
    if not drinks:
        st.info("ยังไม่มีเครื่องดื่ม")
        st.stop()
    drink = st.selectbox("เครื่องดื่ม", drinks, format_func=dlabel)
    pref = get_preferences(user)
    status = "ชอบ" if drink in pref["liked"] else "ไม่ชอบ" if drink in pref["disliked"] else "ยังไม่ระบุ"
    st.caption(f"สถานะปัจจุบันของ {user} กับ {drink}: **{status}**")
    choice = st.radio("ความรู้สึก", ["❤️ ชอบ", "😞 ไม่ชอบ", "ล้างความรู้สึก"], horizontal=True)
    if st.button("บันทึก", type="primary", use_container_width=True):
        kind = {"❤️ ชอบ": "LIKES", "😞 ไม่ชอบ": "DISLIKES"}.get(choice)
        set_preference(user, drink, kind)
        flash("บันทึกแล้ว")
        st.rerun()

# ============================================================ Graph Explorer
elif page == "Graph Explorer":
    st.subheader("🕸️ Graph Explorer")
    st.caption("เส้นเขียว = LIKES, เส้นแดงประ = DISLIKES (แสดงผู้ใช้ที่ชอบเครื่องดื่มเดียวกันด้วย)")
    user = user_selector("graph_user")
    rows = graph_neighborhood(user)
    if not rows:
        st.info("ยังไม่มีข้อมูลความสัมพันธ์")
    else:
        dot = ["digraph G {", 'rankdir="LR";', 'node [shape=box, style="rounded,filled", fillcolor="#f8fafc"];']
        seen = set()
        for r in rows:
            for nid, label, name in [
                (r["source_id"], r["source_label"], r["source_name"]),
                (r["target_id"], r["target_label"], r["target_name"]),
            ]:
                if nid not in seen:
                    safe = str(name).replace('"', "'")
                    fill = "#dcfce7" if label == "Drink" else "#fef9c3"
                    dot.append(f'"{nid}" [label="{safe}\\n:{label}", fillcolor="{fill}"];')
                    seen.add(nid)
            style = 'color="#16a34a"' if r["relationship"] == "LIKES" else 'color="#dc2626", style=dashed'
            dot.append(f'"{r["source_id"]}" -> "{r["target_id"]}" [label="{r["relationship"]}", {style}];')
        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)
        with st.expander("ดูข้อมูล edge ที่ใช้วาดกราฟ"):
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ============================================================ CRUD
elif page == "Manage Data (CRUD)":
    st.subheader("🛠️ จัดการข้อมูล (เพิ่ม / แก้ไข / ลบ)")
    tab_u, tab_d, tab_p = st.tabs(["👤 ผู้ใช้", "🥤 เครื่องดื่ม", "❤️ ความชอบ"])

    # ---- Users
    with tab_u:
        with st.form("form_add_user", clear_on_submit=True):
            n = st.text_input("ชื่อผู้ใช้ใหม่")
            if st.form_submit_button("➕ เพิ่มผู้ใช้", type="primary"):
                if not n.strip():
                    st.error("กรุณากรอกชื่อ")
                elif create_user(n.strip()):
                    flash(f"เพิ่มผู้ใช้ {n.strip()} แล้ว")
                    st.rerun()
                else:
                    st.error("มีชื่อนี้อยู่แล้ว")
        users = get_users()
        if users:
            sel = st.selectbox("เลือกผู้ใช้เพื่อแก้ไข / ลบ", users, key="crud_user_sel")
            with st.form(f"form_edit_user_{sel}"):
                new = st.text_input("ชื่อใหม่", sel)
                if st.form_submit_button("💾 เปลี่ยนชื่อ", type="primary"):
                    if not new.strip():
                        st.error("ชื่อห้ามว่าง")
                    elif rename_user(sel, new.strip()):
                        flash("เปลี่ยนชื่อแล้ว")
                        st.rerun()
                    else:
                        st.error("มีชื่อนี้อยู่แล้ว")
            ok = st.checkbox("ยืนยันการลบ (ความชอบทั้งหมดของผู้ใช้นี้จะถูกลบ)", key=f"del_user_ok_{sel}")
            if st.button("🗑️ ลบผู้ใช้", disabled=not ok, key=f"del_user_{sel}"):
                delete_user(sel)
                flash(f"ลบ {sel} แล้ว")
                st.rerun()
        else:
            st.info("ยังไม่มีผู้ใช้")

    # ---- Drinks
    with tab_d:
        with st.form("form_add_drink", clear_on_submit=True):
            n = st.text_input("ชื่อเครื่องดื่มใหม่")
            if st.form_submit_button("➕ เพิ่มเครื่องดื่ม", type="primary"):
                if not n.strip():
                    st.error("กรุณากรอกชื่อ")
                elif create_drink(n.strip()):
                    flash(f"เพิ่ม {n.strip()} แล้ว")
                    st.rerun()
                else:
                    st.error("มีเครื่องดื่มนี้อยู่แล้ว")
        drinks = get_drinks()
        if drinks:
            sel = st.selectbox("เลือกเครื่องดื่มเพื่อแก้ไข / ลบ", drinks, key="crud_drink_sel")
            with st.form(f"form_edit_drink_{sel}"):
                new = st.text_input("ชื่อใหม่", sel)
                if st.form_submit_button("💾 เปลี่ยนชื่อ", type="primary"):
                    if not new.strip():
                        st.error("ชื่อห้ามว่าง")
                    elif rename_drink(sel, new.strip()):
                        flash("เปลี่ยนชื่อแล้ว")
                        st.rerun()
                    else:
                        st.error("มีเครื่องดื่มชื่อนี้อยู่แล้ว")
            ok = st.checkbox("ยืนยันการลบ (LIKES/DISLIKES ที่เกี่ยวข้องจะถูกลบ)", key=f"del_drink_ok_{sel}")
            if st.button("🗑️ ลบเครื่องดื่ม", disabled=not ok, key=f"del_drink_{sel}"):
                delete_drink(sel)
                flash(f"ลบ {sel} แล้ว")
                st.rerun()
        else:
            st.info("ยังไม่มีเครื่องดื่ม")

    # ---- Preferences
    with tab_p:
        user = user_selector("crud_pref_user")
        all_drinks = get_drinks()
        cur = get_preferences(user)
        with st.form(f"form_prefs_{user}"):
            likes = st.multiselect("❤️ ชอบ", all_drinks, default=[x for x in cur["liked"] if x in all_drinks], format_func=dlabel)
            dislikes = st.multiselect("😞 ไม่ชอบ", all_drinks, default=[x for x in cur["disliked"] if x in all_drinks], format_func=dlabel)
            if st.form_submit_button("💾 บันทึกความชอบ", type="primary"):
                both = set(likes) & set(dislikes)
                if both:
                    st.error("เครื่องดื่มเดียวกันเลือกทั้งชอบและไม่ชอบไม่ได้: " + ", ".join(sorted(both)))
                else:
                    set_preferences(user, likes, dislikes)
                    flash("อัปเดตความชอบแล้ว")
                    st.rerun()

# ============================================================ Admin
elif page == "Admin / Setup":
    st.subheader("⚙️ Setup ข้อมูลตัวอย่าง")
    st.markdown(
        """
        **Graph schema**
        - `(:User {name})-[:LIKES]->(:Drink {name})`
        - `(:User {name})-[:DISLIKES]->(:Drink {name})`
        """
    )
    st.warning("ปุ่มสร้างข้อมูลใช้ MERGE จึงกดซ้ำได้ ไม่ลบข้อมูลเดิม")
    if st.button("สร้าง Constraint + Demo Data", type="primary", use_container_width=True):
        with st.spinner("กำลังสร้างข้อมูล..."):
            seed_demo_data()
        flash("สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว")
        st.rerun()

    st.divider()
    st.error("โซนอันตราย: ลบ node :User และ :Drink ทั้งหมด (ข้อมูลอื่นใน database ไม่ถูกแตะ)")
    ok = st.checkbox("ยืนยันว่าต้องการล้างข้อมูลผู้ใช้และเครื่องดื่มทั้งหมด", key="reset_ok")
    if st.button("🗑️ ล้างข้อมูลทั้งหมด", disabled=not ok):
        reset_drink_data()
        flash("ล้างข้อมูลแล้ว")
        st.rerun()