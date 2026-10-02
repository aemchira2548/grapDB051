from __future__ import annotations

from base64 import b64decode, b64encode
from html import escape
from io import BytesIO
from pathlib import Path

import pandas as pd
import streamlit as st
from PIL import Image, ImageOps

from neo4j_service import (
    create_drink,
    create_user,
    clear_drink_image,
    delete_drink,
    delete_user,
    get_dashboard_metrics,
    get_drink_images,
    get_drink_stats,
    get_drinks,
    get_friend_pairs,
    get_friends,
    get_friends_preferences,
    get_preferences,
    get_users,
    graph_neighborhood,
    ping,
    recommend_drinks,
    rename_drink,
    rename_user,
    reset_drink_data,
    seed_demo_data,
    set_drink_image,
    set_friends,
    set_preference,
    set_preferences,
)


st.set_page_config(page_title="DrinkGraph", page_icon="🍵", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+Thai:wght@400;500;600&family=Mitr:wght@400;500;600&display=swap');
:root{--deep:#17301F;--leaf:#2F5D3A;--pearl:#2B1B14;--caramel:#C98B2B;--paper:#F4F6F1;--line:#D5DCCF;
      --like:#2E8B47;--dislike:#C8322B;--muted:#5E6B5F;--ink:#1B2A20;}
.stApp{background:var(--paper);font-family:'IBM Plex Sans Thai',system-ui,sans-serif;color:var(--ink)}
h1,h2,h3,h4,.mitr{font-family:'Mitr','IBM Plex Sans Thai',sans-serif !important;font-weight:500 !important;letter-spacing:0 !important}
.block-container{padding-top:3.4rem;max-width:1120px}
[data-testid="stElementContainer"],[data-testid="stMarkdownContainer"]{min-width:0;max-width:100%;width:100%}
[data-testid="stMain"]{overflow-x:hidden}
#MainMenu,footer{visibility:hidden}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#1B3A27 0%,var(--deep) 45%,#0F2217 100%)}
section[data-testid="stSidebar"] *{color:#E6EFE0}
section[data-testid="stSidebar"] [data-testid="stSidebarContent"]{padding-top:.5rem}
.brand{display:flex;align-items:center;gap:.7rem;margin:1.2rem 0 1.4rem}
.brand .logo{width:46px;height:46px;border-radius:15px;background:#F4F6F1;display:flex;align-items:center;justify-content:center;font-size:1.6rem;flex:none;
             box-shadow:0 4px 0 rgba(0,0,0,.25);transform:rotate(-6deg)}
.brand .t{font-family:'Mitr',sans-serif;font-size:1.45rem;line-height:1.05;color:#fff}
.brand .s{font-size:.75rem;opacity:.65;margin-top:.15rem}
.nav-label{font-size:.75rem;opacity:.55;margin:0 0 .35rem .5rem}
section[data-testid="stSidebar"] div[role="radiogroup"]{gap:.15rem}
section[data-testid="stSidebar"] .stRadio,
section[data-testid="stSidebar"] [data-testid="stRadioGroup"],
section[data-testid="stSidebar"] [data-testid="stElementContainer"]:has([data-testid="stRadioGroup"]),
section[data-testid="stSidebar"] div[role="radiogroup"]>div{width:100% !important}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"],
section[data-testid="stSidebar"] label[data-baseweb="radio"]{display:flex !important;width:100% !important;box-sizing:border-box;margin:0;
             padding:.62rem 1rem;border-radius:16px;transition:background .15s;cursor:pointer}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]),
section[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-child{display:none !important}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"] p,
section[data-testid="stSidebar"] label[data-baseweb="radio"] p{font-size:.98rem}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover,
section[data-testid="stSidebar"] label[data-baseweb="radio"]:hover{background:rgba(255,255,255,.08)}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"],
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked){background:#F4F6F1;box-shadow:inset 5px 0 0 var(--caramel)}
section[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] *,
section[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) *{color:var(--deep) !important;font-weight:600}
.side-foot{margin-top:2rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,.12);font-size:.75rem;opacity:.6;line-height:1.6}
.stButton>button{border-radius:999px;font-weight:600}
.stButton>button[kind="primary"]{background-color:var(--leaf) !important;border-color:var(--leaf) !important;color:#fff !important}
.stButton>button[kind="primary"]:hover{background-color:var(--deep) !important}
.stTabs [aria-selected="true"]{color:var(--leaf) !important}
.stTabs div[data-baseweb="tab-highlight"]{background-color:var(--leaf) !important}
div[data-baseweb="slider"] div[role="slider"]{background-color:var(--leaf) !important}
div[data-baseweb="select"]>div,.stTextInput input{border-radius:14px}
.stTabs [data-baseweb="tab"]{font-family:'Mitr',sans-serif}


/* ---------- top nav (แทน sidebar: ใช้ได้ดีบนมือถือ) ---------- */
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stExpandSidebarButton"]{display:none !important}
.topbar{display:flex;align-items:center;gap:.75rem;margin:.2rem 0 .8rem}
.topbar .logo{width:44px;height:44px;border-radius:14px;background:var(--deep);display:flex;align-items:center;justify-content:center;
              font-size:1.5rem;flex:none;transform:rotate(-6deg);box-shadow:0 3px 0 var(--caramel)}
.topbar .t{font-family:'Mitr',sans-serif;font-size:1.4rem;line-height:1.05}
.topbar .s{font-size:.75rem;color:var(--muted);margin-top:.1rem}
.st-key-nav{overflow:hidden;max-width:100%;width:100%}
.st-key-nav div[role="radiogroup"]{display:flex !important;flex-direction:row !important;flex-wrap:nowrap !important;gap:.45rem;
              overflow-x:auto;padding:.15rem .1rem .55rem;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.st-key-nav div[role="radiogroup"]::-webkit-scrollbar{display:none}
@media (min-width:900px){.st-key-nav div[role="radiogroup"]{flex-wrap:wrap !important;overflow:visible}.st-key-nav label[data-testid="stRadioOption"]{padding:.45rem .78rem}.st-key-nav div[role="radiogroup"]{gap:.3rem}.st-key-nav label[data-testid="stRadioOption"] p{font-size:.88rem}}
.st-key-nav div[role="radiogroup"]>div{flex:none !important;width:auto !important}
.st-key-nav label[data-testid="stRadioOption"]{display:flex !important;width:auto !important;padding:.5rem 1.05rem;border-radius:999px;
              background:#fff;border:1px solid var(--line);cursor:pointer;white-space:nowrap;transition:background .15s}
.st-key-nav label[data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]){display:none !important}
.st-key-nav label[data-testid="stRadioOption"] p{font-size:.92rem;margin:0}
.st-key-nav label[data-testid="stRadioOption"]:hover{background:#E7ECE1}
.st-key-nav label[data-testid="stRadioOption"][data-selected="true"]{background:var(--deep);border-color:var(--deep);box-shadow:0 3px 0 var(--caramel)}
.st-key-nav label[data-testid="stRadioOption"][data-selected="true"] *{color:#fff !important;font-weight:600}

.st-key-topn div[role="radiogroup"]{display:flex !important;flex-direction:row !important;flex-wrap:nowrap !important;gap:.45rem;
              overflow-x:auto;padding:.15rem .1rem .55rem;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.st-key-topn div[role="radiogroup"]::-webkit-scrollbar{display:none}
@media (min-width:900px){.st-key-topn div[role="radiogroup"]{flex-wrap:wrap !important;overflow:visible}.st-key-topn label[data-testid="stRadioOption"]{padding:.45rem .78rem}.st-key-topn div[role="radiogroup"]{gap:.3rem}.st-key-topn label[data-testid="stRadioOption"] p{font-size:.88rem}}
.st-key-topn div[role="radiogroup"]>div{flex:none !important;width:auto !important}
.st-key-topn label[data-testid="stRadioOption"]{display:flex !important;width:auto !important;padding:.5rem 1.05rem;border-radius:999px;
              background:#fff;border:1px solid var(--line);cursor:pointer;white-space:nowrap;transition:background .15s}
.st-key-topn label[data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]){display:none !important}
.st-key-topn label[data-testid="stRadioOption"] p{font-size:.92rem;margin:0}
.st-key-topn label[data-testid="stRadioOption"]:hover{background:#E7ECE1}
.st-key-topn label[data-testid="stRadioOption"][data-selected="true"]{background:var(--deep);border-color:var(--deep);box-shadow:0 3px 0 var(--caramel)}
.st-key-topn label[data-testid="stRadioOption"][data-selected="true"] *{color:#fff !important;font-weight:600}

.st-key-pref_choice div[role="radiogroup"]{display:flex !important;flex-direction:row !important;flex-wrap:nowrap !important;gap:.45rem;
              overflow-x:auto;padding:.15rem .1rem .55rem;scrollbar-width:none;-webkit-overflow-scrolling:touch}
.st-key-pref_choice div[role="radiogroup"]::-webkit-scrollbar{display:none}
@media (min-width:900px){.st-key-pref_choice div[role="radiogroup"]{flex-wrap:wrap !important;overflow:visible}.st-key-pref_choice label[data-testid="stRadioOption"]{padding:.45rem .78rem}.st-key-pref_choice div[role="radiogroup"]{gap:.3rem}.st-key-pref_choice label[data-testid="stRadioOption"] p{font-size:.88rem}}
.st-key-pref_choice div[role="radiogroup"]>div{flex:none !important;width:auto !important}
.st-key-pref_choice label[data-testid="stRadioOption"]{display:flex !important;width:auto !important;padding:.5rem 1.05rem;border-radius:999px;
              background:#fff;border:1px solid var(--line);cursor:pointer;white-space:nowrap;transition:background .15s}
.st-key-pref_choice label[data-testid="stRadioOption"] > div > div:not([data-testid="stMarkdownContainer"]){display:none !important}
.st-key-pref_choice label[data-testid="stRadioOption"] p{font-size:.92rem;margin:0}
.st-key-pref_choice label[data-testid="stRadioOption"]:hover{background:#E7ECE1}
.st-key-pref_choice label[data-testid="stRadioOption"][data-selected="true"]{background:var(--deep);border-color:var(--deep);box-shadow:0 3px 0 var(--caramel)}
.st-key-pref_choice label[data-testid="stRadioOption"][data-selected="true"] *{color:#fff !important;font-weight:600}


/* ---------- form polish ---------- */
[data-testid="stForm"]{background:#fff;border:1px solid var(--line);border-radius:22px;padding:1.2rem 1.3rem}
[data-testid="stExpander"] details{background:#fff;border:1px solid var(--line) !important;border-radius:18px}
div[data-baseweb="input"]>div,div[data-baseweb="select"]>div,.stTextInput input{background:#fff !important;border:1px solid var(--line) !important;border-radius:14px}
div[data-testid="stAlert"]{border-radius:16px;border:0}
button[kind="primaryFormSubmit"]{background-color:var(--leaf) !important;border-color:var(--leaf) !important;color:#fff !important;border-radius:999px;font-weight:600}
button[kind="primaryFormSubmit"]:hover{background-color:var(--deep) !important}
button[kind="secondaryFormSubmit"],.stButton>button[kind="secondary"]{border-radius:999px;background:#fff;border:1px solid var(--line);color:var(--ink)}
.st-key-topn label[data-testid="stRadioOption"],.st-key-pref_choice label[data-testid="stRadioOption"]{padding:.4rem .95rem}

/* ---------- hero ---------- */
.hero{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:1rem;background:var(--deep);color:#F1F6EC;
      border-radius:28px;padding:1.6rem 2rem 1.6rem 2.2rem;margin-bottom:1.6rem;overflow:hidden}
.hero h1{font-size:2.2rem;margin:0;color:#fff;line-height:1.25}
.hero p{margin:.6rem 0 0;max-width:30ch;opacity:.85;line-height:1.5}
.hero .facts{margin-top:1rem;display:flex;gap:1.2rem;font-size:.85rem;opacity:.8;flex-wrap:wrap}
.hero .facts b{font-family:'Mitr',sans-serif;font-weight:500;font-size:1.15rem;color:#F4D58D;margin-right:.25rem}
.pols{display:flex;padding:.4rem .6rem .2rem 0}
.pol{background:#fff;padding:7px 7px 24px;border-radius:6px;box-shadow:0 8px 20px rgba(0,0,0,.35);margin-left:-26px;position:relative}
.pol:first-child{margin-left:0}
.pol img,.pol .ph{width:112px;height:112px;object-fit:cover;display:block;border-radius:3px}
.pol span{position:absolute;left:0;right:0;bottom:5px;text-align:center;font-size:.68rem;color:#444}

/* ---------- section titles & menu rows ---------- */
.sec{font-size:1.5rem;margin:.4rem 0 .9rem;padding-top:.7rem;border-top:3px solid var(--ink)}
.sub{color:var(--muted);font-size:.9rem;margin:-.5rem 0 1rem}
.mrow{display:flex;align-items:center;gap:.8rem;padding:.45rem 0}
.mrow img,.mrow .ph{width:48px;height:48px;border-radius:14px;object-fit:cover;flex:none}
.mrow .nm{font-weight:600}
.dots{flex:1;border-bottom:2px dotted #AEBBA9;min-width:20px;transform:translateY(5px)}
.val{display:flex;align-items:center;gap:.35rem;font-size:.85rem;color:var(--muted)}
.val b{font-weight:600;min-width:.9rem}
.pearls{display:inline-flex;gap:3px;flex-wrap:wrap;max-width:110px;justify-content:flex-end}
.pearls i{display:block;width:10px;height:10px;border-radius:50%}
.pearls.like i{background:var(--pearl)}
.pearls.dislike i{background:var(--dislike);opacity:.85}
.pearls.score i{background:var(--leaf)}
.like-n{color:var(--like)}.dislike-n{color:var(--dislike)}

/* ---------- recommendation list ---------- */
.ritem{display:flex;gap:1.2rem;align-items:center;padding:1.1rem 0;border-bottom:1px solid var(--line)}
.rank{font-family:'Mitr',sans-serif;font-size:2.4rem;color:#B5C2AF;width:2.2rem;text-align:center;flex:none}
.ritem>img,.ritem>.ph{width:140px;height:140px;border-radius:24px;object-fit:cover;flex:none}
.rbody{flex:1;min-width:0}
.rtitle{display:flex;align-items:baseline;gap:.6rem}
.rtitle .nm{font-family:'Mitr',sans-serif;font-size:1.45rem}
.rtitle .sc{display:flex;align-items:center;gap:.4rem;font-family:'Mitr',sans-serif;color:var(--leaf)}
.why{font-size:.86rem;color:var(--muted);margin-top:.35rem;line-height:1.7}
.why .lab{color:var(--ink);font-weight:600;margin-right:.3rem}

/* ---------- chips / avatar ---------- */
.chip{display:inline-block;padding:.1rem .6rem;border-radius:999px;font-size:.8rem;margin:.1rem .25rem .1rem 0;border:1px solid transparent}
.chip.like{background:#E2F2E4;color:#1F5F31;border-color:#BFE0C5}
.chip.dislike{background:#FBE4E1;color:#8E231D;border-color:#F2C2BD}
.chip.user{background:#FBF0D6;color:#7A5212;border-color:#EBD59B}
.chip.friend{background:#E6ECFA;color:#27408B;border-color:#C5D2F2}
.chip.drink{background:#fff;color:#33463a;border-color:var(--line)}
.avatar{display:inline-flex;align-items:center;justify-content:center;border-radius:50%;color:#fff;font-family:'Mitr',sans-serif;flex:none}
.profile{display:flex;gap:1rem;align-items:center;margin-bottom:.8rem}
.profile h3{margin:0;font-size:1.6rem}

/* ---------- drink tiles ---------- */
.tiles{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:1.4rem 1.1rem}
.tile img,.tile .ph{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:20px;display:block}
.tile .nm{font-family:'Mitr',sans-serif;margin-top:.5rem;font-size:1rem}
.tile .pearls{max-width:none;justify-content:flex-start;margin-top:.15rem}
.ph{display:flex;align-items:center;justify-content:center;background:#E4EBDD;font-size:2.4rem}
.big img,.big .ph{width:100%;max-width:300px;aspect-ratio:1/1;object-fit:cover;border-radius:28px;display:block}

@media (max-width:720px){
  .hero{padding:1.2rem}.hero h1{font-size:1.7rem}.pol{padding:5px 5px 18px;margin-left:-22px}.pol img,.pol .ph{width:72px;height:72px}.pol span{font-size:.55rem;bottom:3px}
  .ritem>img,.ritem>.ph{width:92px;height:92px}.rank{display:none}
}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}}
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


_BASE = Path(__file__).parent
_IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp")
# ชื่อเครื่องดื่มในฐานข้อมูล -> ชื่อไฟล์ (ตัวพิมพ์เล็ก ไม่รวมนามสกุล)
_IMG_ALIASES = {"มัทฉะlatte": "matcha_latte"}


@st.cache_data(show_spinner=False)
def _image_index() -> dict[str, Path]:
    """Map lowercase file stem -> path. Case-insensitive (Streamlit Cloud runs on Linux).
    Priority: images/photos/* > photos in images/ (jpg/webp) > drawn icons (png in images/)."""
    best: dict[str, tuple[tuple[int, int], Path]] = {}
    for folder in ("images", "images/photos"):
        d = _BASE / folder
        if not d.is_dir():
            continue
        for p in d.iterdir():
            ext = p.suffix.lower()
            if ext not in _IMG_EXTS:
                continue
            rank = (0 if (ext == ".png" and folder == "images") else 1, 1 if folder.endswith("photos") else 0)
            key = p.stem.lower()
            if key not in best or rank > best[key][0]:
                best[key] = (rank, p)
    return {k: v[1] for k, v in best.items()}


def drink_image_path(name: str) -> Path | None:
    idx = _image_index()
    key = name.strip().lower()
    key = _IMG_ALIASES.get(key, key).replace(" ", "_")
    return idx.get(key) or idx.get(name.strip().lower().replace(" ", "_"))


IMG_SIZE = 400  # ทุกรูปถูกครอปกลางภาพเป็นสี่เหลี่ยมจัตุรัสขนาดเท่ากัน


def to_square_data_uri(uploaded, size: int = IMG_SIZE) -> str:
    """Uploaded file -> square JPEG data URI (center-crop, EXIF-rotated, transparent -> white)."""
    im = ImageOps.exif_transpose(Image.open(uploaded))
    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGB", im.size, "white")
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert("RGB")
    im = ImageOps.fit(im, (size, size), Image.LANCZOS)
    buf = BytesIO()
    im.save(buf, format="JPEG", quality=85)
    return "data:image/jpeg;base64," + b64encode(buf.getvalue()).decode()


@st.cache_data(ttl=600, show_spinner=False)
def _db_images() -> dict[str, str]:
    try:
        return get_drink_images()
    except Exception:
        return {}


def refresh_images() -> None:
    _db_images.clear()


@st.cache_data(show_spinner=False)
def _file_image_data(name: str) -> tuple[bytes, str] | None:
    p = drink_image_path(name)
    if not p:
        return None
    try:
        im = ImageOps.exif_transpose(Image.open(p))
        buf = BytesIO()
        if p.suffix.lower() == ".png":
            ImageOps.fit(im.convert("RGBA"), (IMG_SIZE, IMG_SIZE), Image.LANCZOS).save(buf, format="PNG")
            return buf.getvalue(), "image/png"
        ImageOps.fit(im.convert("RGB"), (IMG_SIZE, IMG_SIZE), Image.LANCZOS).save(buf, format="JPEG", quality=85)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return None


def drink_image_source(name: str) -> str | None:
    """'db' = uploaded in the app, 'file' = from images/ folder, None = no image."""
    if name in _db_images():
        return "db"
    return "file" if drink_image_path(name) else None


def drink_image_data(name: str) -> tuple[bytes, str] | None:
    """Priority: image uploaded via the app (stored in Neo4j) > file in images/ > drawn icon."""
    uri = _db_images().get(name)
    if uri:
        try:
            head, b64 = uri.split(",", 1)
            return b64decode(b64), head[5:].split(";")[0]
        except Exception:
            pass
    return _file_image_data(name)


def drink_image_uri(name: str) -> str:
    d = drink_image_data(name)
    return f"data:{d[1]};base64," + b64encode(d[0]).decode() if d else ""




# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------
AVATAR_COLORS = ["#2F5D3A", "#C98B2B", "#2B6C8F", "#7A4E8C", "#B4443A", "#3E7C74", "#8A6D1E", "#4A5BA8"]


def emoji_of(name: str) -> str:
    return dlabel(name).split(" ", 1)[0]


def thumb(name: str) -> str:
    uri = drink_image_uri(name)
    if uri:
        return f'<img src="{uri}" alt="{escape(name)}">'
    return f'<div class="ph">{emoji_of(name)}</div>'


def avatar(name: str, size: int = 44) -> str:
    color = AVATAR_COLORS[sum(map(ord, name)) % len(AVATAR_COLORS)]
    return (f'<span class="avatar" style="width:{size}px;height:{size}px;background:{color};'
            f'font-size:{int(size * 0.45)}px">{escape(name[:1].upper())}</span>')


def chips(items, kind: str = "drink", with_emoji: bool = False) -> str:
    return "".join(
        f'<span class="chip {kind}">{escape(dlabel(x) if with_emoji else x)}</span>' for x in items
    ) or '<span class="chip drink">-</span>'


def pearls(n: int, kind: str) -> str:
    n = int(n)
    return f'<span class="pearls {kind}">' + "<i></i>" * min(n, 12) + "</span>"


def sec(title: str, sub: str = "") -> None:
    st.markdown(f'<div class="sec">{escape(title)}</div>' + (f'<div class="sub">{escape(sub)}</div>' if sub else ""),
                unsafe_allow_html=True)


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


def user_selector(key: str, label: str = "เลือกผู้ใช้") -> str:
    users = get_users()
    if not users:
        st.info("ยังไม่มีผู้ใช้ กรุณาไปหน้า Admin / Setup แล้วสร้างข้อมูลตัวอย่าง หรือเพิ่มผู้ใช้ใน Manage Data")
        st.stop()
    return st.selectbox(label, users, key=key)


def hero(m: dict) -> str:
    all_d = get_drinks()
    prefer = [d for d in ("มัทฉะLatte", "Bubble Milk Tea", "Cocoa", "Lemon Tea", "Green Tea", "Orange Juice") if d in all_d]
    names = ([d for d in prefer if drink_image_uri(d)] or [d for d in all_d if drink_image_uri(d)] or all_d)[:4]
    tilts = [-7, 3, -3, 6]
    pols = "".join(
        f'<div class="pol" style="transform:rotate({tilts[i % 4]}deg)">{thumb(n)}<span>{escape(n)}</span></div>'
        for i, n in enumerate(names)
    )
    return (
        '<div class="hero"><div>'
        '<h1>ดูว่าคนที่ชอบเหมือนคุณ<br>ดื่มอะไร</h1>'
        '<p>แล้วเลือกแก้วถัดไปอย่างมีเหตุผล</p>'
        f'<div class="facts"><span><b>{m.get("users", 0)}</b>ผู้ใช้</span><span><b>{m.get("drinks", 0)}</b>เครื่องดื่ม</span>'
        f'<span><b>{m.get("likes", 0)}</b>ความชอบ</span><span><b>{m.get("friendships", 0)}</b>คู่เพื่อน</span></div></div>'
        f'<div class="pols">{pols}</div></div>'
    )


def rec_item(i: int, row: dict) -> str:
    return (
        f'<div class="ritem"><div class="rank">{i}</div>{thumb(row["drink"])}<div class="rbody">'
        f'<div class="rtitle"><span class="nm">{escape(dlabel(row["drink"]))}</span><span class="dots"></span>'
        f'<span class="sc">{pearls(row["score"], "score")}{row["score"]}</span></div>'
        f'<div class="why"><span class="lab">คนที่ชอบแบบเดียวกัน</span>{chips(row["similar_users"], "user")}</div>'
        f'<div class="why"><span class="lab">เชื่อมผ่านเครื่องดื่มที่ชอบเหมือนกัน</span>{chips(row["shared_drinks"], "drink", True)}</div>'
        f'<div class="why">ถูกใจ {row["like_count"]} คน'
        + (f' · ไม่ชอบ {row["dislike_count"]} คน' if row["dislike_count"] else "")
        + '</div></div></div>'
    )


def friend_graph_svg(user: str, likes: list, dislikes: list, friends_prefs: dict) -> str:
    """Compact graph (inline SVG). Left: the user (gold) and friends. Right: drink photo bubbles.
    Every person is linked to the drinks they like (green) or dislike (red dashed); friendships are gold arcs on the left."""
    GREEN, RED, GOLD, INKC, GREY = "#2E8B47", "#C8322B", "#C98B2B", "#1B2A20", "#AEBBA9"
    rel = {d: "LIKES" for d in likes} | {d: "DISLIKES" for d in dislikes}
    fnames = list(friends_prefs)
    k = len(fnames) // 2
    persons = fnames[:k] + [user] + fnames[k:]                      # user sits in the middle so arcs go up and down
    others = sorted({d for p in friends_prefs.values() for d in p["liked"] + p["disliked"]} - set(rel))
    drinks = list(likes) + list(dislikes) + others
    W = 520
    H = max(len(persons) * 92, max(len(drinks), 1) * 62, 220) + 52
    PX, DX = 96, 352

    def ys(n):
        step = (H - 52) / max(n, 1)
        return [44 + step * (i + 0.5) for i in range(n)]

    py = dict(zip(persons, ys(len(persons))))
    dy = dict(zip(drinks, ys(len(drinks))))
    radius = lambda p: 28 if p == user else 22
    edges, arcs, nodes = [], [], []

    for f in fnames:                                                  # friendship arcs (left)
        x0, x1 = PX - radius(user), PX - radius(f)
        arcs.append(f'<path d="M {x0} {py[user]} C {PX - 78} {py[user]}, {PX - 78} {py[f]}, {x1} {py[f]}" fill="none" stroke="{GOLD}" stroke-width="3" stroke-linecap="round"/>')

    def link(p, d, kind, mine):                                       # person -> drink
        col = GREEN if kind == "LIKES" else RED
        x0, x1, y0, y1 = PX + radius(p), DX - 29, py[p], dy[d]
        mx = (x0 + x1) / 2
        dash = "" if kind == "LIKES" else ' stroke-dasharray="6 5"'
        w, op = (3, 1) if mine else (2.2, 0.8)
        return (f'<path d="M {x0} {y0} C {mx} {y0}, {mx} {y1}, {x1} {y1}" fill="none" stroke="{col}" '
                f'stroke-width="{w}" opacity="{op}"{dash} stroke-linecap="round"/>')

    for f in fnames:
        for d in friends_prefs[f]["liked"]:
            edges.append(link(f, d, "LIKES", False))
        for d in friends_prefs[f]["disliked"]:
            edges.append(link(f, d, "DISLIKES", False))
    for d in likes:
        edges.append(link(user, d, "LIKES", True))
    for d in dislikes:
        edges.append(link(user, d, "DISLIKES", True))

    for p in persons:                                                 # people
        r, y = radius(p), py[p]
        if p == user:
            nodes.append(f'<circle cx="{PX}" cy="{y}" r="{r + 8}" fill="{GOLD}" opacity=".18"/><circle cx="{PX}" cy="{y}" r="{r}" fill="{GOLD}"/>')
        else:
            nodes.append(f'<circle cx="{PX}" cy="{y}" r="{r}" fill="{AVATAR_COLORS[sum(map(ord, p)) % len(AVATAR_COLORS)]}"/>')
        nodes.append(f'<text x="{PX}" y="{y + r * 0.36}" text-anchor="middle" font-size="{r * 0.62:.0f}" font-weight="600" fill="#fff">{escape(p[:1].upper())}</text>'
                     f'<text x="{PX}" y="{y + r + 17}" text-anchor="middle" font-size="14" font-weight="{600 if p == user else 400}" fill="{INKC}">{escape(p)}</text>')

    for n, d in enumerate(drinks):                                    # drinks
        y, kind = dy[d], rel.get(d)
        col = GREEN if kind == "LIKES" else RED if kind == "DISLIKES" else GREY
        uri = drink_image_uri(d)
        pic = (f'<clipPath id="dc{n}"><circle cx="{DX}" cy="{y}" r="22"/></clipPath>'
               f'<image href="{uri}" x="{DX - 22}" y="{y - 22}" width="44" height="44" clip-path="url(#dc{n})" preserveAspectRatio="xMidYMid slice"/>'
               if uri else f'<text x="{DX}" y="{y + 8}" text-anchor="middle" font-size="22">{emoji_of(d)}</text>')
        sub = (f'<text x="{DX + 36}" y="{y + 16}" font-size="11.5" fill="{col}">{"ชอบ" if kind == "LIKES" else "ไม่ชอบ"}</text>' if kind else "")
        nodes.append(f'<circle cx="{DX}" cy="{y}" r="25" fill="#fff" stroke="{col}" stroke-width="3"/>{pic}'
                     f'<text x="{DX + 36}" y="{y + (-1 if kind else 5)}" font-size="14" font-weight="600" fill="{INKC}">{escape(d)}</text>{sub}')

    if not drinks:
        nodes.append(f'<text x="{DX}" y="{H / 2}" text-anchor="middle" font-size="13" fill="#8A968B">ยังไม่มีเครื่องดื่ม</text>')
    heads = (f'<text x="{PX}" y="18" text-anchor="middle" font-size="12" fill="#8A968B">คุณและเพื่อน</text>'
             f'<text x="{DX + 40}" y="18" text-anchor="middle" font-size="12" fill="#8A968B">เครื่องดื่ม</text>')
    return (f'<div style="background:#fff;border:1px solid var(--line);border-radius:24px;padding:.8rem .4rem;margin:.4rem 0 1rem">'
            f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:{W}px;height:auto;display:block;margin:0 auto" '
            f'font-family="\'IBM Plex Sans Thai\', Tahoma, sans-serif">{heads}{"".join(arcs)}{"".join(edges)}{"".join(nodes)}</svg></div>')


# ---------------------------------------------------------------------------
# App shell
# ---------------------------------------------------------------------------
require_connection()

PAGES = {
    "Dashboard": "📊 ภาพรวม",
    "Recommendations": "✨ แนะนำ",
    "Drink Search": "🔎 ค้นหา",
    "Like / Dislike": "❤️ ความชอบ",
    "Graph Explorer": "🕸️ กราฟ",
    "Manage Data (CRUD)": "🛠️ จัดการข้อมูล",
    "Admin / Setup": "⚙️ ตั้งค่า",
}

st.markdown('<div class="topbar"><div class="logo">🍵</div><div><div class="t">DrinkGraph</div>'
            '<div class="s">ระบบแนะนำเครื่องดื่มจากกราฟความชอบ</div></div></div>', unsafe_allow_html=True)
page = st.radio("เมนู", list(PAGES), format_func=PAGES.get, horizontal=True, label_visibility="collapsed", key="nav")

if page == "Dashboard":
    st.markdown(hero(get_dashboard_metrics()), unsafe_allow_html=True)

if "_flash" in st.session_state:
    st.success(st.session_state.pop("_flash"))

# ============================================================ Dashboard
if page == "Dashboard":
    left, right = st.columns([3, 2], gap="large")
    with left:
        sec("เมนูยอดนิยม", "เม็ดไข่มุกดำ = คนที่ชอบ  ·  เม็ดแดง = คนที่ไม่ชอบ")
        stats = get_drink_stats()
        rows = "".join(
            f'<div class="mrow">{thumb(s["drink"])}<span class="nm">{escape(dlabel(s["drink"]))}</span><span class="dots"></span>'
            f'<span class="val">{pearls(s["likes"], "like")}<b class="like-n">{s["likes"]}</b>'
            f'{pearls(s["dislikes"], "dislike")}<b class="dislike-n">{s["dislikes"]}</b></span></div>'
            for s in stats
        )
        st.markdown(rows or "<p>ยังไม่มีเครื่องดื่ม</p>", unsafe_allow_html=True)
    with right:
        sec("โปรไฟล์ผู้ใช้")
        user = user_selector("dash_user", "ดูความชอบของ")
        pref = get_preferences(user)
        st.markdown(
            f'<div class="profile">{avatar(user, 64)}<h3>{escape(user)}</h3></div>'
            f'<div class="why"><span class="lab">ชอบ</span>{chips(pref["liked"], "like", True)}</div>'
            f'<div class="why"><span class="lab">ไม่ชอบ</span>{chips(pref["disliked"], "dislike", True)}</div>'
            f'<div class="why"><span class="lab">เพื่อน</span>{chips(get_friends(user), "friend")}</div>',
            unsafe_allow_html=True,
        )

# ============================================================ Recommendations
elif page == "Recommendations":
    sec("แก้วถัดไปของคุณ")
    c1, c2 = st.columns([2, 1])
    with c1:
        user = user_selector("rec_user", "แนะนำให้")
    with c2:
        top_n = st.radio("จำนวนคำแนะนำ", [3, 5, 8], index=1, horizontal=True, key="topn")
    rows = recommend_drinks(user, top_n)
    if not rows:
        st.info("ยังไม่มีคำแนะนำสำหรับผู้ใช้นี้ ลองเพิ่มความชอบในเมนู บันทึกความชอบ")
    else:
        st.markdown("".join(rec_item(i, r) for i, r in enumerate(rows, 1)), unsafe_allow_html=True)
    with st.expander("score คำนวณอย่างไร"):
        st.write(
            "score = จำนวนเส้นทางในกราฟ: เครื่องดื่มที่ผู้ใช้ชอบ → คนอื่นที่ชอบเหมือนกัน → เครื่องดื่มอื่นที่คนกลุ่มนั้นชอบ "
            "(ตัดเครื่องดื่มที่ผู้ใช้ชอบหรือไม่ชอบอยู่แล้วออก) ยิ่งมีเส้นทางมากยิ่งแนะนำน้ำหนักมาก  ·  เพื่อน (FRIEND_OF) ใช้แสดงในโปรไฟล์และกราฟ ไม่ได้นำมาคิดคะแนน"
        )

# ============================================================ Search
elif page == "Drink Search":
    sec("ค้นหาเครื่องดื่ม")
    kw = st.text_input("ชื่อเครื่องดื่ม", placeholder="เช่น Tea, Latte, มัทฉะ", label_visibility="collapsed")
    rows = get_drink_stats(kw)
    st.caption(f"พบ {len(rows)} รายการ")
    if rows:
        tiles = "".join(
            f'<div class="tile">{thumb(r["drink"])}<div class="nm">{escape(dlabel(r["drink"]))}</div>'
            f'<div class="val">{pearls(r["likes"], "like")}<b class="like-n">{r["likes"]}</b>'
            f'{pearls(r["dislikes"], "dislike")}<b class="dislike-n">{r["dislikes"]}</b></div></div>'
            for r in rows
        )
        st.markdown(f'<div class="tiles">{tiles}</div>', unsafe_allow_html=True)
        with st.expander("ดูเป็นตาราง"):
            df = pd.DataFrame(rows)
            df["drink"] = df["drink"].map(dlabel)
            st.dataframe(df, use_container_width=True, hide_index=True)

# ============================================================ Like / Dislike
elif page == "Like / Dislike":
    sec("บอกว่าคุณชอบอะไร")
    c1, c2 = st.columns(2)
    with c1:
        user = user_selector("pref_user", "ผู้ใช้")
    drinks = get_drinks()
    if not drinks:
        st.info("ยังไม่มีเครื่องดื่ม")
        st.stop()
    with c2:
        drink = st.selectbox("เครื่องดื่ม", drinks, format_func=dlabel)
    pref = get_preferences(user)
    status = "❤️ ชอบอยู่" if drink in pref["liked"] else "😞 ไม่ชอบอยู่" if drink in pref["disliked"] else "ยังไม่ระบุ"
    pa, pb = st.columns([1, 1], gap="large")
    with pa:
        st.markdown(f'<div class="big">{thumb(drink)}</div>', unsafe_allow_html=True)
    with pb:
        st.markdown(f'<h3 style="margin:.2rem 0">{escape(dlabel(drink))}</h3><div class="sub">สถานะของ {escape(user)}: {status}</div>',
                    unsafe_allow_html=True)
        choice = st.radio("ความรู้สึก", ["❤️ ชอบ", "😞 ไม่ชอบ", "ล้างความรู้สึก"], horizontal=True, key="pref_choice")
        if st.button("บันทึก", type="primary"):
            kind = {"❤️ ชอบ": "LIKES", "😞 ไม่ชอบ": "DISLIKES"}.get(choice)
            set_preference(user, drink, kind)
            flash("บันทึกแล้ว")
            st.rerun()

# ============================================================ Graph Explorer
elif page == "Graph Explorer":
    sec("กราฟความสัมพันธ์", "เส้นเขียว = ชอบ  ·  เส้นแดงประ = ไม่ชอบ  ·  เส้นเหลือง = เป็นเพื่อนกัน  ·  ขอบรูปบอกความรู้สึกของผู้ใช้ที่เลือก")
    user = user_selector("graph_user", "เลือกผู้ใช้")
    pref = get_preferences(user)
    st.markdown(friend_graph_svg(user, pref["liked"], pref["disliked"], get_friends_preferences(user)), unsafe_allow_html=True)
    with st.expander("ดูข้อมูลความสัมพันธ์เป็นตาราง"):
        edges = graph_neighborhood(user)
        st.dataframe(pd.DataFrame(edges).rename(columns={"source": "จาก", "relationship": "ความสัมพันธ์", "target": "ถึง", "target_label": "ชนิด"}),
                     use_container_width=True, hide_index=True)

# ============================================================ CRUD
elif page == "Manage Data (CRUD)":
    sec("จัดการข้อมูล", "เพิ่ม แก้ไข ลบ ผู้ใช้ เครื่องดื่ม ความชอบ และรูป")
    tab_u, tab_d, tab_p, tab_f = st.tabs(["👤 ผู้ใช้", "🥤 เครื่องดื่ม", "❤️ ความชอบ", "👥 เพื่อน"])

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
        with st.expander("➕ เพิ่มเครื่องดื่มใหม่"):
            with st.form("form_add_drink", clear_on_submit=True):
                n = st.text_input("ชื่อเครื่องดื่มใหม่")
                up = st.file_uploader(
                    "รูปเครื่องดื่ม (ไม่บังคับ) ระบบจะครอปเป็นสี่เหลี่ยมจัตุรัสให้เท่ากันอัตโนมัติ",
                    type=["jpg", "jpeg", "png", "webp"],
                )
                if st.form_submit_button("➕ เพิ่มเครื่องดื่ม", type="primary"):
                    if not n.strip():
                        st.error("กรุณากรอกชื่อ")
                    else:
                        try:
                            img = to_square_data_uri(up) if up else None
                        except Exception:
                            img = None
                            st.error("อ่านไฟล์รูปไม่ได้ ลองไฟล์อื่น")
                        else:
                            if create_drink(n.strip(), img):
                                refresh_images()
                                flash(f"เพิ่ม {n.strip()} แล้ว")
                                st.rerun()
                            else:
                                st.error("มีเครื่องดื่มนี้อยู่แล้ว")

        drinks = get_drinks()
        if drinks:
            sel = st.selectbox("เลือกเครื่องดื่มเพื่อแก้ไข / ลบ", drinks, key="crud_drink_sel")
            src = drink_image_source(sel)
            c_img, c_form = st.columns([1, 3])
            with c_img:
                d = drink_image_data(sel)
                if d:
                    st.image(d[0], use_container_width=True)
                else:
                    st.caption("ยังไม่มีรูป")
                st.caption(
                    {"db": "รูปที่อัปโหลดในระบบ", "file": "รูปจากโฟลเดอร์ images (อัปโหลดใหม่ทับได้)", None: "ไม่มีรูป"}[src]
                )
            with c_form:
                with st.form(f"form_edit_drink_{sel}"):
                    new = st.text_input("ชื่อใหม่", sel)
                    up = st.file_uploader(
                        "เพิ่ม / เปลี่ยนรูป", type=["jpg", "jpeg", "png", "webp"], key=f"up_drink_{sel}"
                    )
                    rm = st.checkbox("ลบรูปที่อัปโหลด", disabled=src != "db")
                    if st.form_submit_button("💾 บันทึกการแก้ไข", type="primary"):
                        target = new.strip()
                        if not target:
                            st.error("ชื่อห้ามว่าง")
                        elif target != sel and not rename_drink(sel, target):
                            st.error("มีเครื่องดื่มชื่อนี้อยู่แล้ว")
                        else:
                            try:
                                if up:
                                    set_drink_image(target, to_square_data_uri(up))
                                elif rm:
                                    clear_drink_image(target)
                            except Exception:
                                st.error("อ่านไฟล์รูปไม่ได้ ลองไฟล์อื่น (ชื่อถูกบันทึกแล้ว)")
                            else:
                                refresh_images()
                                flash("บันทึกการแก้ไขแล้ว")
                                st.rerun()
            ok = st.checkbox("ยืนยันการลบ (LIKES/DISLIKES และรูปที่อัปโหลดจะถูกลบ)", key=f"del_drink_ok_{sel}")
            if st.button("🗑️ ลบเครื่องดื่ม", disabled=not ok, key=f"del_drink_{sel}"):
                delete_drink(sel)
                refresh_images()
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

    # ---- Friends
    with tab_f:
        fuser = user_selector("crud_friend_user", "เลือกผู้ใช้")
        others = [u for u in get_users() if u != fuser]
        cur_friends = [x for x in get_friends(fuser) if x in others]
        with st.form(f"form_friends_{fuser}"):
            picked_friends = st.multiselect("เพื่อนของผู้ใช้นี้ (ความเป็นเพื่อนเป็นแบบสองทาง)", others, default=cur_friends)
            if st.form_submit_button("💾 บันทึกเพื่อน", type="primary"):
                set_friends(fuser, picked_friends)
                flash("อัปเดตเพื่อนแล้ว")
                st.rerun()
        pairs = get_friend_pairs()
        with st.expander(f"ความเป็นเพื่อนทั้งหมด ({len(pairs)} คู่)"):
            if pairs:
                st.dataframe(pd.DataFrame(pairs).rename(columns={"a": "ผู้ใช้ A", "b": "ผู้ใช้ B"}),
                             use_container_width=True, hide_index=True)
            else:
                st.caption("ยังไม่มีความเป็นเพื่อน")

# ============================================================ Admin
elif page == "Admin / Setup":
    sec("ตั้งค่าระบบ", "สร้างข้อมูลตัวอย่าง และล้างข้อมูล")
    st.caption("โครงสร้างกราฟ (Graph schema)")
    st.code("(:User {name})-[:LIKES]->(:Drink {name})\n(:User {name})-[:DISLIKES]->(:Drink {name})\n(:User {name})-[:FRIEND_OF]-(:User {name})", language="text")
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