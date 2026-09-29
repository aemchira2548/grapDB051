from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from neo4j_service import (
    create_author,
    create_book,
    create_category,
    create_student,
    delete_author,
    delete_book,
    delete_borrow,
    delete_category,
    delete_student,
    get_book,
    get_friend_ids,
    get_student,
    list_authors,
    list_borrows,
    rename_category,
    set_friends,
    set_interests,
    update_author,
    update_book,
    update_borrow,
    update_student,
    get_dashboard_metrics,
    get_profile,
    get_students,
    graph_neighborhood,
    list_categories,
    ping,
    recommend_books,
    record_borrow,
    search_books,
    seed_demo_data,
)

st.set_page_config(
    page_title="GraphBook Recommender",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
      .hero {
        padding: 1.4rem 1.6rem; border-radius: 22px;
        background: linear-gradient(120deg, #111827 0%, #1f2937 55%, #0f766e 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 {margin:0; font-size:2.15rem;}
      .hero p {opacity:.88; margin:.35rem 0 0 0;}
      .book-card {
        padding: 1rem 1.1rem; border: 1px solid rgba(128,128,128,.25);
        border-radius: 16px; margin-bottom: .75rem;
      }
      .score-pill {
        display:inline-block; padding:.2rem .55rem; border-radius:999px;
        background:#0f766e; color:white; font-size:.8rem; font-weight:700;
      }
      .muted {opacity:.72; font-size:.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


def require_connection() -> None:
    try:
        if not ping():
            raise RuntimeError("Neo4j did not return a healthy response")
    except Exception as exc:
        st.error("ยังเชื่อมต่อ Neo4j Aura ไม่สำเร็จ")
        st.code(
            '[neo4j]\nuri = "neo4j+s://YOUR_INSTANCE.databases.neo4j.io"\n'
            'username = "neo4j"\npassword = "YOUR_PASSWORD"\ndatabase = "neo4j"',
            language="toml",
        )
        st.caption("ให้นำค่าด้านบนไปใส่ใน Streamlit Secrets และห้าม commit password ลง GitHub")
        st.exception(exc)
        st.stop()


def student_selector(key: str = "student") -> str:
    students = get_students()
    if not students:
        st.info("ยังไม่มีข้อมูลนักศึกษา กรุณาไปหน้า Admin / Setup แล้วสร้างข้อมูลตัวอย่าง")
        st.stop()
    labels = {f"{x['student_id']} — {x['name']}": x["student_id"] for x in students}
    chosen = st.selectbox("เลือกผู้ใช้", list(labels), key=key)
    return labels[chosen]


def explain_reason(row: dict) -> str:
    parts = []
    if row.get("friend_count", 0):
        friends = ", ".join(row.get("friend_names") or [])
        parts.append(f"เพื่อน {row['friend_count']} คนเคยยืม" + (f" ({friends})" if friends else ""))
    if row.get("interest_matches", 0):
        cats = ", ".join(row.get("matched_categories") or [])
        parts.append(f"ตรงกับความสนใจ {row['interest_matches']} หมวด" + (f" ({cats})" if cats else ""))
    if row.get("popularity", 0):
        parts.append(f"ถูกยืมแล้ว {row['popularity']} ครั้ง")
    if row.get("avg_rating", 0):
        parts.append(f"คะแนนเฉลี่ย {row['avg_rating']:.2f}/5")
    return " • ".join(parts) or "แนะนำจากข้อมูลพฤติกรรมโดยรวม"


def flash(msg: str) -> None:
    st.session_state["_flash"] = msg


require_connection()

with st.sidebar:
    st.markdown("## 📚 GraphBook")
    st.caption("Neo4j Aura + Streamlit")
    page = st.radio(
        "เมนู",
        ["Dashboard", "Recommendations", "Book Search", "Borrow / Rate", "Graph Explorer", "Manage Data (CRUD)", "Admin / Setup"],
    )
    st.divider()
    st.caption("Bachelor-level Graph Database Project")

st.markdown(
    """
    <div class="hero">
      <h1>📚 GraphBook Recommendation System</h1>
      <p>ระบบแนะนำหนังสือด้วย Graph Database ที่อธิบายเหตุผลของคำแนะนำได้</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "_flash" in st.session_state:
    st.success(st.session_state.pop("_flash"))

if page == "Dashboard":
    st.subheader("ภาพรวมระบบ")
    m = get_dashboard_metrics()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Students", m.get("students", 0))
    c2.metric("Books", m.get("books", 0))
    c3.metric("Borrowed relationships", m.get("borrows", 0))
    c4.metric("Friend relationships", m.get("friendships", 0))

    st.divider()
    student_id = student_selector("dash_student")
    profile = get_profile(student_id)
    if profile:
        left, right = st.columns([1, 2])
        with left:
            st.markdown(f"### {profile['name']}")
            st.write(f"**รหัส:** {profile['student_id']}")
            st.write(f"**สาขา:** {profile['major']}")
            st.write(f"**ชั้นปี:** {profile['year']}")
            st.write("**ความสนใจ:** " + (", ".join(profile["interests"]) or "ยังไม่มี"))
        with right:
            st.markdown("### ประวัติการยืม")
            if profile["borrowed"]:
                st.dataframe(pd.DataFrame(profile["borrowed"]), use_container_width=True, hide_index=True)
            else:
                st.info("ยังไม่มีประวัติการยืม")

elif page == "Recommendations":
    st.subheader("✨ หนังสือที่แนะนำ")
    student_id = student_selector("rec_student")
    top_n = st.slider("จำนวนคำแนะนำ", 3, 12, 6)
    rows = recommend_books(student_id, top_n)

    st.caption("คะแนนตัวอย่าง = เพื่อน × 3 + หมวดความสนใจ × 2 + ความนิยม × 0.20 + rating เฉลี่ย × 0.50")
    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้")
    for i, row in enumerate(rows, start=1):
        authors = ", ".join(row.get("authors") or []) or "ไม่ระบุผู้แต่ง"
        categories = ", ".join(row.get("categories") or []) or "ไม่ระบุหมวด"
        st.markdown(
            f"""
            <div class="book-card">
              <span class="score-pill">#{i} · score {row['score']:.2f}</span>
              <h3 style="margin:.55rem 0 .2rem 0">{row['title']}</h3>
              <div class="muted">{row['book_id']} · {authors} · {categories}</div>
              <p><b>เหตุผล:</b> {explain_reason(row)}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

elif page == "Book Search":
    st.subheader("🔎 ค้นหาหนังสือ")
    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("ชื่อหนังสือหรือผู้แต่ง", placeholder="เช่น Python, Neo4j, Kanya")
    categories = [""] + list_categories()
    category = c2.selectbox("หมวด", categories, format_func=lambda x: "ทุกหมวด" if x == "" else x)
    rows = search_books(keyword, category)
    st.write(f"พบ {len(rows)} รายการ")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Borrow / Rate":
    st.subheader("📝 บันทึกการยืมและให้คะแนน")
    student_id = student_selector("borrow_student")
    books = search_books()
    if not books:
        st.info("ยังไม่มีหนังสือ")
        st.stop()
    book_labels = {f"{b['book_id']} — {b['title']}": b["book_id"] for b in books}
    selected = st.selectbox("หนังสือ", list(book_labels))
    borrow_date = st.date_input("วันที่ยืม", value=date.today())
    use_rating = st.checkbox("ให้คะแนนพร้อมกัน")
    rating = st.slider("คะแนน", 1.0, 5.0, 4.0, 0.5, disabled=not use_rating)
    if st.button("บันทึก", type="primary", use_container_width=True):
        record_borrow(student_id, book_labels[selected], borrow_date.isoformat(), rating if use_rating else None)
        st.success("บันทึกความสัมพันธ์ BORROWED แล้ว")

elif page == "Graph Explorer":
    st.subheader("🕸️ Graph Explorer")
    student_id = student_selector("graph_student")
    rows = graph_neighborhood(student_id)
    if not rows:
        st.info("ยังไม่มี neighborhood graph")
    else:
        dot = ["digraph G {", 'rankdir="LR";', 'node [shape=box, style="rounded,filled", fillcolor="#f8fafc"];']
        seen_nodes = set()
        for r in rows:
            for nid, label, name in [
                (r["source_id"], r["source_label"], r["source_name"]),
                (r["target_id"], r["target_label"], r["target_name"]),
            ]:
                if nid not in seen_nodes:
                    safe_name = str(name).replace('"', "'")
                    dot.append(f'"{nid}" [label="{safe_name}\\n:{label}"];')
                    seen_nodes.add(nid)
            dot.append(f'"{r["source_id"]}" -> "{r["target_id"]}" [label="{r["relationship"]}"];')
        dot.append("}")
        st.graphviz_chart("\n".join(dot), use_container_width=True)
        with st.expander("ดูข้อมูล edge ที่ใช้วาดกราฟ"):
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

elif page == "Manage Data (CRUD)":
    st.subheader("🛠️ จัดการข้อมูล (เพิ่ม / แก้ไข / ลบ)")
    tab_s, tab_b, tab_a, tab_c, tab_r = st.tabs(
        ["👤 นักศึกษา", "📗 หนังสือ", "✍️ ผู้แต่ง", "🏷️ หมวดหมู่", "🔗 ความสัมพันธ์"]
    )

    # ---------------------------------------------------------- Students
    with tab_s:
        with st.expander("➕ เพิ่มนักศึกษาใหม่"):
            with st.form("form_add_student", clear_on_submit=True):
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                n_id = c1.text_input("รหัส (เช่น S007)")
                n_name = c2.text_input("ชื่อ")
                n_major = c3.text_input("สาขา")
                n_year = c4.number_input("ชั้นปี", 1, 8, 1)
                if st.form_submit_button("เพิ่ม", type="primary"):
                    if not n_id.strip() or not n_name.strip():
                        st.error("กรุณากรอกรหัสและชื่อ")
                    elif create_student(n_id.strip(), n_name.strip(), n_major.strip(), int(n_year)):
                        flash(f"เพิ่มนักศึกษา {n_id.strip()} แล้ว")
                        st.rerun()
                    else:
                        st.error("รหัสนี้มีอยู่แล้ว")

        students = get_students()
        if students:
            st.dataframe(pd.DataFrame(students), use_container_width=True, hide_index=True)
            labels = {f"{x['student_id']} — {x['name']}": x["student_id"] for x in students}
            chosen = st.selectbox("เลือกนักศึกษาเพื่อแก้ไข / ลบ", list(labels), key="crud_stu_sel")
            sid = labels[chosen]
            cur = get_student(sid)
            with st.form(f"form_edit_student_{sid}"):
                c1, c2, c3 = st.columns([2, 2, 1])
                e_name = c1.text_input("ชื่อ", cur["name"] or "")
                e_major = c2.text_input("สาขา", cur["major"] or "")
                e_year = c3.number_input("ชั้นปี", 1, 8, int(cur["year"] or 1))
                if st.form_submit_button("💾 บันทึกการแก้ไข", type="primary"):
                    if not e_name.strip():
                        st.error("ชื่อห้ามว่าง")
                    else:
                        update_student(sid, e_name.strip(), e_major.strip(), int(e_year))
                        flash(f"แก้ไข {sid} แล้ว")
                        st.rerun()
            ok = st.checkbox("ยืนยันการลบ (ความสัมพันธ์ทั้งหมดของคนนี้จะถูกลบด้วย)", key=f"del_stu_ok_{sid}")
            if st.button("🗑️ ลบนักศึกษา", disabled=not ok, key=f"del_stu_{sid}"):
                delete_student(sid)
                flash(f"ลบ {sid} แล้ว")
                st.rerun()
        else:
            st.info("ยังไม่มีนักศึกษา")

    # ------------------------------------------------------------- Books
    with tab_b:
        authors_all = list_authors()
        author_labels = {a["author_id"]: f"{a['author_id']} — {a['name']}" for a in authors_all}
        cats_all = list_categories()

        with st.expander("➕ เพิ่มหนังสือใหม่"):
            with st.form("form_add_book", clear_on_submit=True):
                c1, c2, c3 = st.columns([1, 3, 1])
                b_id = c1.text_input("รหัส (เช่น B109)")
                b_title = c2.text_input("ชื่อหนังสือ")
                b_year = c3.number_input("ปีพิมพ์", 1900, 2100, date.today().year)
                b_authors = st.multiselect("ผู้แต่ง", list(author_labels), format_func=lambda x: author_labels[x])
                b_cats = st.multiselect("หมวดหมู่", cats_all)
                if st.form_submit_button("เพิ่ม", type="primary"):
                    if not b_id.strip() or not b_title.strip():
                        st.error("กรุณากรอกรหัสและชื่อหนังสือ")
                    elif create_book(b_id.strip(), b_title.strip(), int(b_year), b_authors, b_cats):
                        flash(f"เพิ่มหนังสือ {b_id.strip()} แล้ว")
                        st.rerun()
                    else:
                        st.error("รหัสนี้มีอยู่แล้ว")

        books = search_books()
        if books:
            st.dataframe(pd.DataFrame(books), use_container_width=True, hide_index=True)
            blabels = {f"{b['book_id']} — {b['title']}": b["book_id"] for b in books}
            chosen = st.selectbox("เลือกหนังสือเพื่อแก้ไข / ลบ", list(blabels), key="crud_book_sel")
            bid = blabels[chosen]
            cur = get_book(bid)
            with st.form(f"form_edit_book_{bid}"):
                c1, c2 = st.columns([3, 1])
                e_title = c1.text_input("ชื่อหนังสือ", cur["title"] or "")
                e_year = c2.number_input("ปีพิมพ์", 1900, 2100, int(cur["year"] or date.today().year))
                e_authors = st.multiselect(
                    "ผู้แต่ง", list(author_labels),
                    default=[x for x in cur["author_ids"] if x in author_labels],
                    format_func=lambda x: author_labels[x],
                )
                e_cats = st.multiselect(
                    "หมวดหมู่", cats_all, default=[x for x in cur["categories"] if x in cats_all]
                )
                if st.form_submit_button("💾 บันทึกการแก้ไข", type="primary"):
                    if not e_title.strip():
                        st.error("ชื่อหนังสือห้ามว่าง")
                    else:
                        update_book(bid, e_title.strip(), int(e_year), e_authors, e_cats)
                        flash(f"แก้ไข {bid} แล้ว")
                        st.rerun()
            ok = st.checkbox("ยืนยันการลบหนังสือเล่มนี้ (ประวัติการยืมจะถูกลบด้วย)", key=f"del_book_ok_{bid}")
            if st.button("🗑️ ลบหนังสือ", disabled=not ok, key=f"del_book_{bid}"):
                delete_book(bid)
                flash(f"ลบ {bid} แล้ว")
                st.rerun()
        else:
            st.info("ยังไม่มีหนังสือ")

    # ----------------------------------------------------------- Authors
    with tab_a:
        with st.expander("➕ เพิ่มผู้แต่งใหม่"):
            with st.form("form_add_author", clear_on_submit=True):
                c1, c2 = st.columns([1, 3])
                a_id = c1.text_input("รหัส (เช่น A05)")
                a_name = c2.text_input("ชื่อผู้แต่ง")
                if st.form_submit_button("เพิ่ม", type="primary"):
                    if not a_id.strip() or not a_name.strip():
                        st.error("กรุณากรอกรหัสและชื่อ")
                    elif create_author(a_id.strip(), a_name.strip()):
                        flash(f"เพิ่มผู้แต่ง {a_id.strip()} แล้ว")
                        st.rerun()
                    else:
                        st.error("รหัสนี้มีอยู่แล้ว")

        authors_now = list_authors()
        if authors_now:
            st.dataframe(pd.DataFrame(authors_now), use_container_width=True, hide_index=True)
            alabels = {f"{a['author_id']} — {a['name']}": a for a in authors_now}
            chosen = st.selectbox("เลือกผู้แต่งเพื่อแก้ไข / ลบ", list(alabels), key="crud_author_sel")
            au = alabels[chosen]
            with st.form(f"form_edit_author_{au['author_id']}"):
                e_name = st.text_input("ชื่อผู้แต่ง", au["name"] or "")
                if st.form_submit_button("💾 บันทึกการแก้ไข", type="primary"):
                    if not e_name.strip():
                        st.error("ชื่อห้ามว่าง")
                    else:
                        update_author(au["author_id"], e_name.strip())
                        flash("แก้ไขผู้แต่งแล้ว")
                        st.rerun()
            ok = st.checkbox("ยืนยันการลบผู้แต่ง", key=f"del_au_ok_{au['author_id']}")
            if st.button("🗑️ ลบผู้แต่ง", disabled=not ok, key=f"del_au_{au['author_id']}"):
                delete_author(au["author_id"])
                flash("ลบผู้แต่งแล้ว")
                st.rerun()
        else:
            st.info("ยังไม่มีผู้แต่ง")

    # -------------------------------------------------------- Categories
    with tab_c:
        with st.form("form_add_cat", clear_on_submit=True):
            c_name = st.text_input("ชื่อหมวดใหม่")
            if st.form_submit_button("➕ เพิ่มหมวด", type="primary"):
                if not c_name.strip():
                    st.error("กรุณากรอกชื่อหมวด")
                elif create_category(c_name.strip()):
                    flash(f"เพิ่มหมวด {c_name.strip()} แล้ว")
                    st.rerun()
                else:
                    st.error("มีหมวดนี้อยู่แล้ว")

        cats_now = list_categories()
        if cats_now:
            sel = st.selectbox("เลือกหมวดเพื่อเปลี่ยนชื่อ / ลบ", cats_now, key="crud_cat_sel")
            with st.form(f"form_edit_cat_{sel}"):
                new_name = st.text_input("ชื่อใหม่", sel)
                if st.form_submit_button("💾 เปลี่ยนชื่อ", type="primary"):
                    if not new_name.strip():
                        st.error("ชื่อห้ามว่าง")
                    elif rename_category(sel, new_name.strip()):
                        flash("เปลี่ยนชื่อหมวดแล้ว")
                        st.rerun()
                    else:
                        st.error("มีหมวดชื่อนี้อยู่แล้ว")
            ok = st.checkbox("ยืนยันการลบหมวด (ความสัมพันธ์กับหนังสือ/ความสนใจจะถูกลบ)", key=f"del_cat_ok_{sel}")
            if st.button("🗑️ ลบหมวด", disabled=not ok, key=f"del_cat_{sel}"):
                delete_category(sel)
                flash(f"ลบหมวด {sel} แล้ว")
                st.rerun()
        else:
            st.info("ยังไม่มีหมวดหมู่")

    # ----------------------------------------------------- Relationships
    with tab_r:
        st.caption("จัดการเพื่อน ความสนใจ และประวัติการยืมของนักศึกษาแต่ละคน (การเพิ่มการยืมใหม่ใช้เมนู Borrow / Rate)")
        rel_sid = student_selector("crud_rel_student")
        all_students = get_students()
        stu_labels = {x["student_id"]: f"{x['student_id']} — {x['name']}" for x in all_students}

        st.markdown("#### 🤝 เพื่อน")
        cur_friends = [x for x in get_friend_ids(rel_sid) if x in stu_labels]
        with st.form(f"form_friends_{rel_sid}"):
            picked = st.multiselect(
                "เพื่อนของผู้ใช้นี้",
                [x for x in stu_labels if x != rel_sid],
                default=cur_friends,
                format_func=lambda x: stu_labels[x],
            )
            if st.form_submit_button("💾 บันทึกเพื่อน", type="primary"):
                set_friends(rel_sid, picked)
                flash("อัปเดตเพื่อนแล้ว")
                st.rerun()

        st.markdown("#### 🏷️ ความสนใจ")
        all_cats = list_categories()
        cur_interests = get_profile(rel_sid)["interests"]
        with st.form(f"form_interests_{rel_sid}"):
            picked_cats = st.multiselect(
                "หมวดที่สนใจ", all_cats, default=[x for x in cur_interests if x in all_cats]
            )
            if st.form_submit_button("💾 บันทึกความสนใจ", type="primary"):
                set_interests(rel_sid, picked_cats)
                flash("อัปเดตความสนใจแล้ว")
                st.rerun()

        st.markdown("#### 📖 ประวัติการยืม")
        borrows = list_borrows(rel_sid)
        if not borrows:
            st.info("ยังไม่มีประวัติการยืม")
        else:
            st.dataframe(pd.DataFrame(borrows), use_container_width=True, hide_index=True)
            bl = {f"{x['book_id']} — {x['title']}": x for x in borrows}
            chosen = st.selectbox("เลือกรายการยืมเพื่อแก้ไข / ลบ", list(bl), key=f"crud_borrow_sel_{rel_sid}")
            br = bl[chosen]
            key_sfx = f"{rel_sid}_{br['book_id']}"
            with st.form(f"form_edit_borrow_{key_sfx}"):
                e_date = st.date_input(
                    "วันที่ยืม",
                    value=date.fromisoformat(br["borrow_date"]) if br["borrow_date"] else date.today(),
                )
                has_rating = st.checkbox("มีคะแนน", value=br["rating"] is not None)
                e_rating = st.slider("คะแนน", 1.0, 5.0, float(br["rating"] or 4.0), 0.5)
                if st.form_submit_button("💾 บันทึกการแก้ไข", type="primary"):
                    update_borrow(rel_sid, br["book_id"], e_date.isoformat(), e_rating if has_rating else None)
                    flash("แก้ไขรายการยืมแล้ว")
                    st.rerun()
            ok = st.checkbox("ยืนยันการลบรายการยืมนี้", key=f"del_borrow_ok_{key_sfx}")
            if st.button("🗑️ ลบรายการยืม", disabled=not ok, key=f"del_borrow_{key_sfx}"):
                delete_borrow(rel_sid, br["book_id"])
                flash("ลบรายการยืมแล้ว")
                st.rerun()

elif page == "Admin / Setup":
    st.subheader("⚙️ Setup ข้อมูลตัวอย่าง")
    st.warning("ปุ่มนี้ไม่ลบข้อมูลเดิม และใช้ MERGE จึงสามารถกดซ้ำได้")
    st.markdown(
        """
        **Graph schema**
        - `(:Student)-[:FRIEND_OF]-(:Student)`
        - `(:Student)-[:BORROWED {borrow_date, rating}]->(:Book)`
        - `(:Student)-[:INTERESTED_IN]->(:Category)`
        - `(:Book)-[:IN_CATEGORY]->(:Category)`
        - `(:Author)-[:WROTE]->(:Book)`
        """
    )
    if st.button("สร้าง Constraint + Demo Data", type="primary", use_container_width=True):
        with st.spinner("กำลังสร้างข้อมูล..."):
            seed_demo_data()
        st.success("สร้างข้อมูลตัวอย่างเรียบร้อยแล้ว")
        st.rerun()