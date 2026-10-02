from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl

# ---------------------------------------------------------------------------
# ข้อมูลตัวอย่าง (จาก drink_recommender.py เดิม)
# ---------------------------------------------------------------------------
USERS = ["Guy", "May", "Nut", "Min", "Ball", "Fah", "Beam", "Praew", "Ton", "Fon"]

DRINKS = [
    "Bubble Milk Tea", "Cocoa", "Green Tea", "Lemon Tea", "Orange Juice",
    "Americano", "Latte", "Cappuccino", "มัทฉะLatte", "Fresh Milk",
]

LIKES = [
    ("Guy", "Bubble Milk Tea"), ("Guy", "Cocoa"),
    ("May", "Bubble Milk Tea"), ("May", "Cocoa"), ("May", "Green Tea"),
    ("Nut", "Bubble Milk Tea"), ("Nut", "Green Tea"), ("Nut", "มัทฉะLatte"),
    ("Min", "Cocoa"), ("Min", "Green Tea"), ("Min", "Fresh Milk"),
    ("Ball", "Americano"), ("Ball", "Latte"), ("Ball", "Cappuccino"),
    ("Fah", "Bubble Milk Tea"), ("Fah", "Fresh Milk"), ("Fah", "Cocoa"),
    ("Beam", "Americano"), ("Beam", "Latte"), ("Beam", "มัทฉะLatte"),
    ("Praew", "Lemon Tea"), ("Praew", "Orange Juice"), ("Praew", "Green Tea"),
    ("Ton", "Americano"), ("Ton", "Cappuccino"), ("Ton", "Latte"),
    ("Fon", "Lemon Tea"), ("Fon", "Orange Juice"), ("Fon", "Fresh Milk"),
]

# ความสัมพันธ์เพื่อน (FRIEND_OF) ตัวอย่าง: เก็บทิศเดียว แต่ query แบบไม่สนทิศ (ใช้แสดงผล ไม่ได้ถูกนำมาคิดคะแนนแนะนำ)
FRIENDS = [
    ("Guy", "May"), ("Guy", "Nut"), ("May", "Min"), ("May", "Praew"), ("Nut", "Fah"),
    ("Min", "Fah"), ("Ball", "Beam"), ("Ball", "Ton"), ("Beam", "Ton"), ("Praew", "Fon"), ("Fon", "Fah"),
]

DISLIKES = [
    ("Guy", "Americano"), ("May", "Lemon Tea"), ("Nut", "Cappuccino"),
    ("Min", "Americano"), ("Ball", "Bubble Milk Tea"), ("Fah", "Americano"),
    ("Beam", "Orange Juice"), ("Praew", "Cappuccino"), ("Ton", "Green Tea"),
    ("Fon", "Americano"),
]


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------
def _config() -> tuple[str, str, str, str | None]:
    cfg = st.secrets["neo4j"]
    return cfg["uri"], cfg["username"], cfg["password"], cfg.get("database") or None  # None = home database ของ instance


@st.cache_resource(show_spinner=False)
def get_driver():
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    _, _, _, database = _config()
    records, _, _ = get_driver().execute_query(
        cypher,
        parameters_=parameters or {},
        database_=database,
        routing_=RoutingControl.WRITE if write else RoutingControl.READ,
    )
    return [record.data() for record in records]


def ping() -> bool:
    rows = query("RETURN 1 AS ok")
    return bool(rows and rows[0]["ok"] == 1)


# ---------------------------------------------------------------------------
# Schema + seed
# ---------------------------------------------------------------------------
def create_schema() -> None:
    for stmt in (
        "CREATE CONSTRAINT user_name_unique IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
        "CREATE CONSTRAINT drink_name_unique IF NOT EXISTS FOR (d:Drink) REQUIRE d.name IS UNIQUE",
    ):
        query(stmt, write=True)


def seed_demo_data() -> None:
    """Idempotent (MERGE) - safe to run more than once."""
    create_schema()
    query("UNWIND $rows AS n MERGE (:User {name:n})", {"rows": USERS}, write=True)
    query("UNWIND $rows AS n MERGE (:Drink {name:n})", {"rows": DRINKS}, write=True)
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {name:row.u}), (d:Drink {name:row.d})
        MERGE (u)-[:LIKES]->(d)
        """,
        {"rows": [{"u": u, "d": d} for u, d in LIKES]},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MATCH (u:User {name:row.u}), (d:Drink {name:row.d})
        MERGE (u)-[:DISLIKES]->(d)
        """,
        {"rows": [{"u": u, "d": d} for u, d in DISLIKES]},
        write=True,
    )
    query(
        """
        UNWIND $rows AS r
        MATCH (a:User {name:r.a}), (b:User {name:r.b})
        WHERE a <> b AND NOT (a)-[:FRIEND_OF]-(b)
        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {"rows": [{"a": a, "b": b} for a, b in FRIENDS]},
        write=True,
    )


def reset_drink_data() -> None:
    """Delete only :User and :Drink nodes (other data in the DB is untouched)."""
    query("MATCH (n) WHERE n:User OR n:Drink DETACH DELETE n", write=True)


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------
def get_users() -> list[str]:
    return [r["name"] for r in query("MATCH (u:User) RETURN u.name AS name ORDER BY name")]


def get_drinks() -> list[str]:
    return [r["name"] for r in query("MATCH (d:Drink) RETURN d.name AS name ORDER BY name")]


def get_dashboard_metrics() -> dict[str, int]:
    rows = query(
        """
        RETURN COUNT { (:User) } AS users,
               COUNT { (:Drink) } AS drinks,
               COUNT { ()-[:LIKES]->() } AS likes,
               COUNT { ()-[:DISLIKES]->() } AS dislikes,
               COUNT { (:User)-[:FRIEND_OF]->(:User) } AS friendships
        """
    )
    return rows[0] if rows else {"users": 0, "drinks": 0, "likes": 0, "dislikes": 0, "friendships": 0}


def get_drink_stats(keyword: str = "") -> list[dict[str, Any]]:
    return query(
        """
        MATCH (d:Drink)
        WHERE $kw = '' OR toLower(d.name) CONTAINS toLower($kw)
        RETURN d.name AS drink,
               COUNT { (:User)-[:LIKES]->(d) } AS likes,
               COUNT { (:User)-[:DISLIKES]->(d) } AS dislikes
        ORDER BY likes DESC, drink
        """,
        {"kw": keyword.strip()},
    )


def get_preferences(user: str) -> dict[str, list[str]]:
    rows = query(
        """
        MATCH (u:User {name:$name})
        RETURN [(u)-[:LIKES]->(d:Drink) | d.name] AS liked,
               [(u)-[:DISLIKES]->(d:Drink) | d.name] AS disliked
        """,
        {"name": user},
    )
    if not rows:
        return {"liked": [], "disliked": []}
    return {"liked": sorted(rows[0]["liked"]), "disliked": sorted(rows[0]["disliked"])}


def recommend_drinks(user: str, limit: int = 8) -> list[dict[str, Any]]:
    """Collaborative filtering: drinks liked by people who share a liked drink with the user.
    score = number of (shared drink, other user) paths - same as the original script.
    Drinks the user already likes/dislikes are excluded."""
    return query(
        """
        MATCH (u:User {name:$name})
        MATCH (d:Drink)
        WHERE NOT (u)-[:LIKES]->(d) AND NOT (u)-[:DISLIKES]->(d)
        OPTIONAL MATCH (u)-[:LIKES]->(sd:Drink)<-[:LIKES]-(o:User)-[:LIKES]->(d)
        WHERE o <> u
        WITH d, count(o) AS score,
             collect(DISTINCT o.name) AS similar_users,
             collect(DISTINCT sd.name) AS shared_drinks
        WHERE score > 0
        RETURN d.name AS drink, score, similar_users, shared_drinks,
               COUNT { (:User)-[:LIKES]->(d) } AS like_count,
               COUNT { (:User)-[:DISLIKES]->(d) } AS dislike_count
        ORDER BY score DESC, drink
        LIMIT $limit
        """,
        {"name": user, "limit": int(limit)},
    )


def graph_neighborhood(user: str) -> list[dict[str, Any]]:
    """Edges around one user: own LIKES/DISLIKES, FRIEND_OF to friends, and what each friend likes/dislikes."""
    return query(
        """
        MATCH (u:User {name:$name})-[r:LIKES|DISLIKES]->(d:Drink)
        RETURN u.name AS source, type(r) AS relationship, d.name AS target, 'Drink' AS target_label
        UNION
        MATCH (u:User {name:$name})-[:FRIEND_OF]-(f:User)
        RETURN u.name AS source, 'FRIEND_OF' AS relationship, f.name AS target, 'User' AS target_label
        UNION
        MATCH (u:User {name:$name})-[:FRIEND_OF]-(f:User)-[r:LIKES|DISLIKES]->(d:Drink)
        RETURN f.name AS source, type(r) AS relationship, d.name AS target, 'Drink' AS target_label
        """,
        {"name": user},
    )


def get_friends_preferences(user: str) -> dict[str, dict[str, list[str]]]:
    """{friend: {"liked": [...], "disliked": [...]}} for every friend of the user (one query)."""
    rows = query(
        """
        MATCH (:User {name:$n})-[:FRIEND_OF]-(f:User)
        OPTIONAL MATCH (f)-[r:LIKES|DISLIKES]->(d:Drink)
        RETURN f.name AS friend, collect(CASE WHEN d IS NULL THEN null ELSE {drink: d.name, rel: type(r)} END) AS prefs
        ORDER BY friend
        """,
        {"n": user},
    )
    out: dict[str, dict[str, list[str]]] = {}
    for r in rows:
        prefs = [p for p in r["prefs"] if p]
        out[r["friend"]] = {
            "liked": sorted(p["drink"] for p in prefs if p["rel"] == "LIKES"),
            "disliked": sorted(p["drink"] for p in prefs if p["rel"] == "DISLIKES"),
        }
    return out


def get_friends(user: str) -> list[str]:
    rows = query(
        "MATCH (:User {name:$n})-[:FRIEND_OF]-(f:User) RETURN DISTINCT f.name AS name ORDER BY name", {"n": user}
    )
    return [r["name"] for r in rows]


def get_friend_pairs() -> list[dict[str, str]]:
    return query(
        "MATCH (a:User)-[:FRIEND_OF]->(b:User) RETURN a.name AS a, b.name AS b ORDER BY a, b"
    )


def set_friends(user: str, friends: list[str]) -> None:
    """Replace all friendships of a user (treated as symmetric)."""
    query("MATCH (:User {name:$n})-[r:FRIEND_OF]-(:User) DELETE r", {"n": user}, write=True)
    if friends:
        query(
            """
            MATCH (u:User {name:$n})
            UNWIND $fs AS fname
            MATCH (f:User {name:fname}) WHERE f <> u
            MERGE (u)-[:FRIEND_OF]->(f)
            """,
            {"n": user, "fs": list(friends)},
            write=True,
        )


# ---------------------------------------------------------------------------
# CRUD: User
# ---------------------------------------------------------------------------
def _exists(label: str, name: str) -> bool:
    assert label in ("User", "Drink")
    return bool(query(f"MATCH (n:{label} {{name:$n}}) RETURN 1 AS x", {"n": name}))


def create_user(name: str) -> bool:
    if _exists("User", name):
        return False
    query("CREATE (:User {name:$n})", {"n": name}, write=True)
    return True


def rename_user(old: str, new: str) -> bool:
    if old != new and _exists("User", new):
        return False
    query("MATCH (u:User {name:$old}) SET u.name=$new", {"old": old, "new": new}, write=True)
    return True


def delete_user(name: str) -> None:
    query("MATCH (u:User {name:$n}) DETACH DELETE u", {"n": name}, write=True)


# ---------------------------------------------------------------------------
# CRUD: Drink
# ---------------------------------------------------------------------------
def create_drink(name: str, image: str | None = None) -> bool:
    if _exists("Drink", name):
        return False
    query("CREATE (:Drink {name:$n})", {"n": name}, write=True)
    if image:
        set_drink_image(name, image)
    return True


def get_drink_images() -> dict[str, str]:
    """Uploaded photos stored on Drink nodes as data URIs (square JPEG)."""
    rows = query("MATCH (d:Drink) WHERE d.image IS NOT NULL RETURN d.name AS name, d.image AS image")
    return {r["name"]: r["image"] for r in rows}


def set_drink_image(name: str, data_uri: str) -> None:
    query("MATCH (d:Drink {name:$n}) SET d.image=$img", {"n": name, "img": data_uri}, write=True)


def clear_drink_image(name: str) -> None:
    query("MATCH (d:Drink {name:$n}) REMOVE d.image", {"n": name}, write=True)


def rename_drink(old: str, new: str) -> bool:
    if old != new and _exists("Drink", new):
        return False
    query("MATCH (d:Drink {name:$old}) SET d.name=$new", {"old": old, "new": new}, write=True)
    return True


def delete_drink(name: str) -> None:
    query("MATCH (d:Drink {name:$n}) DETACH DELETE d", {"n": name}, write=True)


# ---------------------------------------------------------------------------
# CRUD: Preferences (LIKES / DISLIKES)
# ---------------------------------------------------------------------------
def set_preference(user: str, drink: str, kind: str | None) -> None:
    """kind = 'LIKES' | 'DISLIKES' | None (clear). A user can't both like and dislike a drink."""
    if kind not in ("LIKES", "DISLIKES", None):
        raise ValueError("kind must be LIKES, DISLIKES or None")
    query(
        """
        MATCH (u:User {name:$u})-[r:LIKES|DISLIKES]->(d:Drink {name:$d})
        DELETE r
        """,
        {"u": user, "d": drink},
        write=True,
    )
    if kind:
        query(
            f"""
            MATCH (u:User {{name:$u}}), (d:Drink {{name:$d}})
            MERGE (u)-[:{kind}]->(d)
            """,
            {"u": user, "d": drink},
            write=True,
        )


def set_preferences(user: str, likes: list[str], dislikes: list[str]) -> None:
    """Replace all LIKES / DISLIKES of a user."""
    query("MATCH (:User {name:$u})-[r:LIKES|DISLIKES]->(:Drink) DELETE r", {"u": user}, write=True)
    if likes:
        query(
            """
            MATCH (u:User {name:$u})
            UNWIND $ds AS dn
            MATCH (d:Drink {name:dn})
            MERGE (u)-[:LIKES]->(d)
            """,
            {"u": user, "ds": likes},
            write=True,
        )
    if dislikes:
        query(
            """
            MATCH (u:User {name:$u})
            UNWIND $ds AS dn
            MATCH (d:Drink {name:dn})
            MERGE (u)-[:DISLIKES]->(d)
            """,
            {"u": user, "ds": dislikes},
            write=True,
        )