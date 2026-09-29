from __future__ import annotations

from typing import Any

import streamlit as st
from neo4j import GraphDatabase, RoutingControl


def _config() -> tuple[str, str, str, str]:
    cfg = st.secrets["neo4j"]
    return (
        cfg["uri"],
        cfg["username"],
        cfg["password"],
        cfg.get("database", "91f3924e"),
    )


@st.cache_resource(show_spinner=False)
def get_driver():
    """Create one thread-safe Neo4j Driver for the Streamlit process."""
    uri, username, password, _ = _config()
    driver = GraphDatabase.driver(uri, auth=(username, password))
    driver.verify_connectivity()
    return driver


def query(cypher: str, parameters: dict[str, Any] | None = None, *, write: bool = False) -> list[dict[str, Any]]:
    """Execute parameterized Cypher and return rows as dictionaries."""
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


def create_schema() -> None:
    statements = [
        "CREATE CONSTRAINT student_id_unique IF NOT EXISTS FOR (s:Student) REQUIRE s.student_id IS UNIQUE",
        "CREATE CONSTRAINT book_id_unique IF NOT EXISTS FOR (b:Book) REQUIRE b.book_id IS UNIQUE",
        "CREATE CONSTRAINT author_id_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.author_id IS UNIQUE",
        "CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE",
    ]
    for stmt in statements:
        query(stmt, write=True)


def seed_demo_data() -> None:
    """Idempotent sample dataset: safe to run more than once."""
    create_schema()

    students = [
        {"student_id": "S001", "name": "Anan", "major": "Computer Science", "year": 2},
        {"student_id": "S002", "name": "Mali", "major": "Computer Science", "year": 2},
        {"student_id": "S003", "name": "Krit", "major": "Information Technology", "year": 3},
        {"student_id": "S004", "name": "Nida", "major": "Data Science", "year": 2},
        {"student_id": "S005", "name": "Ploy", "major": "Business Computer", "year": 3},
        {"student_id": "S006", "name": "Ton", "major": "Computer Science", "year": 1},
    ]
    books = [
        {"book_id": "B101", "title": "Python Programming", "year": 2025},
        {"book_id": "B102", "title": "Artificial Intelligence Basics", "year": 2026},
        {"book_id": "B103", "title": "Data Science for Students", "year": 2025},
        {"book_id": "B104", "title": "Introduction to Database", "year": 2024},
        {"book_id": "B105", "title": "Graph Databases with Neo4j", "year": 2026},
        {"book_id": "B106", "title": "Machine Learning Foundations", "year": 2025},
        {"book_id": "B107", "title": "Web Application Development", "year": 2024},
        {"book_id": "B108", "title": "Algorithms and Problem Solving", "year": 2023},
    ]
    authors = [
        {"author_id": "A01", "name": "Somchai Tech"},
        {"author_id": "A02", "name": "Narin Data"},
        {"author_id": "A03", "name": "Kanya AI"},
        {"author_id": "A04", "name": "Preecha DB"},
    ]
    categories = ["Programming", "AI", "Data Science", "Database", "Web Development", "Algorithms"]

    query(
        """
        UNWIND $rows AS row
        MERGE (s:Student {student_id: row.student_id})
        SET s.name = row.name, s.major = row.major, s.year = row.year
        """,
        {"rows": students},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MERGE (b:Book {book_id: row.book_id})
        SET b.title = row.title, b.year = row.year
        """,
        {"rows": books},
        write=True,
    )
    query(
        """
        UNWIND $rows AS row
        MERGE (a:Author {author_id: row.author_id})
        SET a.name = row.name
        """,
        {"rows": authors},
        write=True,
    )
    query(
        "UNWIND $rows AS name MERGE (:Category {name:name})",
        {"rows": categories},
        write=True,
    )

    friendships = [
        ["S001", "S002"], ["S001", "S003"], ["S001", "S004"],
        ["S002", "S005"], ["S003", "S004"], ["S004", "S006"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (a:Student {student_id: row[0]}), (b:Student {student_id: row[1]})
        MERGE (a)-[:FRIEND_OF]->(b)
        """,
        {"rows": friendships},
        write=True,
    )

    borrows = [
        {"s": "S001", "b": "B101", "date": "2026-08-01", "rating": 4.0},
        {"s": "S001", "b": "B108", "date": "2026-08-14", "rating": 4.0},
        {"s": "S002", "b": "B103", "date": "2026-08-05", "rating": 5.0},
        {"s": "S002", "b": "B102", "date": "2026-08-18", "rating": 4.0},
        {"s": "S003", "b": "B103", "date": "2026-08-07", "rating": 4.0},
        {"s": "S003", "b": "B104", "date": "2026-08-20", "rating": 5.0},
        {"s": "S004", "b": "B105", "date": "2026-08-09", "rating": 5.0},
        {"s": "S004", "b": "B103", "date": "2026-08-24", "rating": 5.0},
        {"s": "S005", "b": "B107", "date": "2026-08-11", "rating": 4.0},
        {"s": "S006", "b": "B106", "date": "2026-08-12", "rating": 4.0},
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (s:Student {student_id: row.s}), (b:Book {book_id: row.b})
        MERGE (s)-[r:BORROWED]->(b)
        SET r.borrow_date = date(row.date), r.rating = row.rating
        """,
        {"rows": borrows},
        write=True,
    )

    interests = [
        ["S001", "Programming"], ["S001", "Database"],
        ["S002", "AI"], ["S002", "Data Science"],
        ["S003", "Database"], ["S003", "Data Science"],
        ["S004", "AI"], ["S004", "Data Science"],
        ["S005", "Web Development"], ["S006", "Programming"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (s:Student {student_id: row[0]}), (c:Category {name: row[1]})
        MERGE (s)-[:INTERESTED_IN]->(c)
        """,
        {"rows": interests},
        write=True,
    )

    book_categories = [
        ["B101", "Programming"], ["B102", "AI"], ["B103", "Data Science"],
        ["B104", "Database"], ["B105", "Database"], ["B106", "AI"],
        ["B106", "Data Science"], ["B107", "Web Development"],
        ["B108", "Algorithms"], ["B108", "Programming"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (b:Book {book_id: row[0]}), (c:Category {name: row[1]})
        MERGE (b)-[:IN_CATEGORY]->(c)
        """,
        {"rows": book_categories},
        write=True,
    )

    wrote = [
        ["A01", "B101"], ["A03", "B102"], ["A02", "B103"], ["A04", "B104"],
        ["A04", "B105"], ["A03", "B106"], ["A01", "B107"], ["A01", "B108"],
    ]
    query(
        """
        UNWIND $rows AS row
        MATCH (a:Author {author_id: row[0]}), (b:Book {book_id: row[1]})
        MERGE (a)-[:WROTE]->(b)
        """,
        {"rows": wrote},
        write=True,
    )


def get_students() -> list[dict[str, Any]]:
    return query("MATCH (s:Student) RETURN s.student_id AS student_id, s.name AS name, s.major AS major, s.year AS year ORDER BY s.student_id")


def get_dashboard_metrics() -> dict[str, int]:
    # COUNT subqueries always return a row, even when a count is 0
    rows = query(
        """
        RETURN COUNT { (:Student) } AS students,
               COUNT { (:Book) } AS books,
               COUNT { ()-[:BORROWED]->() } AS borrows,
               COUNT { ()-[:FRIEND_OF]->() } AS friendships
        """
    )
    return rows[0] if rows else {"students": 0, "books": 0, "borrows": 0, "friendships": 0}


def get_profile(student_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (s:Student {student_id:$student_id})
        OPTIONAL MATCH (s)-[:INTERESTED_IN]->(c:Category)
        OPTIONAL MATCH (s)-[:BORROWED]->(b:Book)
        RETURN s.student_id AS student_id, s.name AS name, s.major AS major, s.year AS year,
               collect(DISTINCT c.name) AS interests,
               collect(DISTINCT {book_id:b.book_id, title:b.title}) AS borrowed
        """,
        {"student_id": student_id},
    )
    if not rows:
        return None
    row = rows[0]
    row["borrowed"] = [x for x in row["borrowed"] if x.get("book_id")]
    return row


def recommend_books(student_id: str, limit: int = 8) -> list[dict[str, Any]]:
    """Explainable hybrid score: social + interests + popularity + ratings."""
    return query(
        """
        MATCH (u:Student {student_id:$student_id})
        MATCH (b:Book)
        WHERE NOT (u)-[:BORROWED]->(b)

        OPTIONAL MATCH (u)-[:FRIEND_OF]-(f:Student)-[:BORROWED]->(b)
        WITH u, b, count(DISTINCT f) AS friend_count,
             [x IN collect(DISTINCT f.name) WHERE x IS NOT NULL][0..3] AS friend_names

        OPTIONAL MATCH (u)-[:INTERESTED_IN]->(c:Category)<-[:IN_CATEGORY]-(b)
        WITH b, friend_count, friend_names,
             count(DISTINCT c) AS interest_matches,
             [x IN collect(DISTINCT c.name) WHERE x IS NOT NULL] AS matched_categories

        OPTIONAL MATCH (:Student)-[br:BORROWED]->(b)
        WITH b, friend_count, friend_names, interest_matches, matched_categories,
             count(br) AS popularity,
             avg(br.rating) AS avg_rating

        WITH b, friend_count, friend_names, interest_matches, matched_categories,
             popularity, coalesce(avg_rating, 0.0) AS avg_rating,
             (friend_count * 3.0) + (interest_matches * 2.0) +
             (popularity * 0.20) + (coalesce(avg_rating, 0.0) * 0.50) AS score
        WHERE friend_count > 0 OR interest_matches > 0 OR popularity > 0

        OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
        OPTIONAL MATCH (b)-[:IN_CATEGORY]->(allc:Category)
        RETURN b.book_id AS book_id, b.title AS title, b.year AS year,
               collect(DISTINCT a.name) AS authors,
               collect(DISTINCT allc.name) AS categories,
               friend_count, friend_names, interest_matches, matched_categories,
               popularity, round(avg_rating * 100) / 100.0 AS avg_rating,
               round(score * 100) / 100.0 AS score
        ORDER BY score DESC, b.title
        LIMIT $limit
        """,
        {"student_id": student_id, "limit": int(limit)},
    )


def search_books(keyword: str = "", category: str | None = None) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (b:Book)
        OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
        OPTIONAL MATCH (b)-[:IN_CATEGORY]->(c:Category)
        WITH b, collect(DISTINCT a.name) AS authors, collect(DISTINCT c.name) AS categories
        WHERE ($keyword = '' OR toLower(b.title) CONTAINS toLower($keyword)
               OR any(x IN authors WHERE toLower(x) CONTAINS toLower($keyword)))
          AND ($category = '' OR $category IN categories)
        RETURN b.book_id AS book_id, b.title AS title, b.year AS year,
               authors, categories
        ORDER BY b.title
        """,
        {"keyword": keyword.strip(), "category": category or ""},
    )


def list_categories() -> list[str]:
    return [row["name"] for row in query("MATCH (c:Category) RETURN c.name AS name ORDER BY c.name")]


def record_borrow(student_id: str, book_id: str, borrow_date: str, rating: float | None = None) -> None:
    query(
        """
        MATCH (s:Student {student_id:$student_id}), (b:Book {book_id:$book_id})
        MERGE (s)-[r:BORROWED]->(b)
        SET r.borrow_date = date($borrow_date)
        FOREACH (_ IN CASE WHEN $rating IS NULL THEN [] ELSE [1] END | SET r.rating = $rating)
        """,
        {"student_id": student_id, "book_id": book_id, "borrow_date": borrow_date, "rating": rating},
        write=True,
    )


def graph_neighborhood(student_id: str, limit: int = 40) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (u:Student {student_id:$student_id})
        OPTIONAL MATCH p=(u)-[:FRIEND_OF|BORROWED|INTERESTED_IN*1..2]-(x)
        WITH u, collect(p)[0..$limit] AS paths
        UNWIND paths AS p
        UNWIND relationships(p) AS r
        WITH DISTINCT startNode(r) AS s, r, endNode(r) AS t
        RETURN elementId(s) AS source_id, labels(s)[0] AS source_label,
               coalesce(s.name, s.title, s.student_id, s.book_id) AS source_name,
               type(r) AS relationship,
               elementId(t) AS target_id, labels(t)[0] AS target_label,
               coalesce(t.name, t.title, t.student_id, t.book_id) AS target_name
        LIMIT $limit
        """,
        {"student_id": student_id, "limit": int(limit)},
    )


# =====================================================================
# CRUD: Student
# =====================================================================
def get_student(student_id: str) -> dict[str, Any] | None:
    rows = query(
        "MATCH (s:Student {student_id:$id}) "
        "RETURN s.student_id AS student_id, s.name AS name, s.major AS major, s.year AS year",
        {"id": student_id},
    )
    return rows[0] if rows else None


def create_student(student_id: str, name: str, major: str, year: int) -> bool:
    """Return False if student_id already exists."""
    if get_student(student_id):
        return False
    query(
        "CREATE (:Student {student_id:$id, name:$name, major:$major, year:$year})",
        {"id": student_id, "name": name, "major": major, "year": year},
        write=True,
    )
    return True


def update_student(student_id: str, name: str, major: str, year: int) -> None:
    query(
        "MATCH (s:Student {student_id:$id}) SET s.name=$name, s.major=$major, s.year=$year",
        {"id": student_id, "name": name, "major": major, "year": year},
        write=True,
    )


def delete_student(student_id: str) -> None:
    query("MATCH (s:Student {student_id:$id}) DETACH DELETE s", {"id": student_id}, write=True)


# =====================================================================
# CRUD: Author
# =====================================================================
def list_authors() -> list[dict[str, Any]]:
    return query("MATCH (a:Author) RETURN a.author_id AS author_id, a.name AS name ORDER BY a.author_id")


def create_author(author_id: str, name: str) -> bool:
    if query("MATCH (a:Author {author_id:$id}) RETURN 1 AS x", {"id": author_id}):
        return False
    query("CREATE (:Author {author_id:$id, name:$name})", {"id": author_id, "name": name}, write=True)
    return True


def update_author(author_id: str, name: str) -> None:
    query("MATCH (a:Author {author_id:$id}) SET a.name=$name", {"id": author_id, "name": name}, write=True)


def delete_author(author_id: str) -> None:
    query("MATCH (a:Author {author_id:$id}) DETACH DELETE a", {"id": author_id}, write=True)


# =====================================================================
# CRUD: Category
# =====================================================================
def create_category(name: str) -> bool:
    if query("MATCH (c:Category {name:$n}) RETURN 1 AS x", {"n": name}):
        return False
    query("CREATE (:Category {name:$n})", {"n": name}, write=True)
    return True


def rename_category(old: str, new: str) -> bool:
    """Return False if the new name is already used by another category."""
    if old != new and query("MATCH (c:Category {name:$n}) RETURN 1 AS x", {"n": new}):
        return False
    query("MATCH (c:Category {name:$old}) SET c.name=$new", {"old": old, "new": new}, write=True)
    return True


def delete_category(name: str) -> None:
    query("MATCH (c:Category {name:$n}) DETACH DELETE c", {"n": name}, write=True)


# =====================================================================
# CRUD: Book
# =====================================================================
def get_book(book_id: str) -> dict[str, Any] | None:
    rows = query(
        """
        MATCH (b:Book {book_id:$id})
        OPTIONAL MATCH (a:Author)-[:WROTE]->(b)
        OPTIONAL MATCH (b)-[:IN_CATEGORY]->(c:Category)
        RETURN b.book_id AS book_id, b.title AS title, b.year AS year,
               collect(DISTINCT a.author_id) AS author_ids,
               collect(DISTINCT c.name) AS categories
        """,
        {"id": book_id},
    )
    return rows[0] if rows else None


def set_book_relations(book_id: str, author_ids: list[str], categories: list[str]) -> None:
    """Replace the WROTE and IN_CATEGORY relationships of a book."""
    query("MATCH (:Author)-[w:WROTE]->(:Book {book_id:$id}) DELETE w", {"id": book_id}, write=True)
    query("MATCH (b:Book {book_id:$id})-[r:IN_CATEGORY]->(:Category) DELETE r", {"id": book_id}, write=True)
    if author_ids:
        query(
            """
            MATCH (b:Book {book_id:$id})
            UNWIND $ids AS aid
            MATCH (a:Author {author_id:aid})
            MERGE (a)-[:WROTE]->(b)
            """,
            {"id": book_id, "ids": author_ids},
            write=True,
        )
    if categories:
        query(
            """
            MATCH (b:Book {book_id:$id})
            UNWIND $cats AS cname
            MATCH (c:Category {name:cname})
            MERGE (b)-[:IN_CATEGORY]->(c)
            """,
            {"id": book_id, "cats": categories},
            write=True,
        )


def create_book(book_id: str, title: str, year: int, author_ids: list[str], categories: list[str]) -> bool:
    if get_book(book_id):
        return False
    query("CREATE (:Book {book_id:$id, title:$title, year:$year})",
          {"id": book_id, "title": title, "year": year}, write=True)
    set_book_relations(book_id, author_ids, categories)
    return True


def update_book(book_id: str, title: str, year: int, author_ids: list[str], categories: list[str]) -> None:
    query("MATCH (b:Book {book_id:$id}) SET b.title=$title, b.year=$year",
          {"id": book_id, "title": title, "year": year}, write=True)
    set_book_relations(book_id, author_ids, categories)


def delete_book(book_id: str) -> None:
    query("MATCH (b:Book {book_id:$id}) DETACH DELETE b", {"id": book_id}, write=True)


# =====================================================================
# CRUD: Relationships
# =====================================================================
def get_friend_ids(student_id: str) -> list[str]:
    rows = query(
        "MATCH (:Student {student_id:$id})-[:FRIEND_OF]-(f:Student) RETURN DISTINCT f.student_id AS fid",
        {"id": student_id},
    )
    return [r["fid"] for r in rows]


def set_friends(student_id: str, friend_ids: list[str]) -> None:
    """Replace all friendships of a student (treated as symmetric)."""
    query("MATCH (:Student {student_id:$id})-[r:FRIEND_OF]-(:Student) DELETE r", {"id": student_id}, write=True)
    if friend_ids:
        query(
            """
            MATCH (s:Student {student_id:$id})
            UNWIND $ids AS fid
            MATCH (f:Student {student_id:fid}) WHERE f <> s
            MERGE (s)-[:FRIEND_OF]->(f)
            """,
            {"id": student_id, "ids": friend_ids},
            write=True,
        )


def set_interests(student_id: str, categories: list[str]) -> None:
    query("MATCH (:Student {student_id:$id})-[r:INTERESTED_IN]->(:Category) DELETE r", {"id": student_id}, write=True)
    if categories:
        query(
            """
            MATCH (s:Student {student_id:$id})
            UNWIND $cats AS cname
            MATCH (c:Category {name:cname})
            MERGE (s)-[:INTERESTED_IN]->(c)
            """,
            {"id": student_id, "cats": categories},
            write=True,
        )


def list_borrows(student_id: str) -> list[dict[str, Any]]:
    return query(
        """
        MATCH (:Student {student_id:$id})-[r:BORROWED]->(b:Book)
        RETURN b.book_id AS book_id, b.title AS title,
               toString(r.borrow_date) AS borrow_date, r.rating AS rating
        ORDER BY r.borrow_date DESC
        """,
        {"id": student_id},
    )


def update_borrow(student_id: str, book_id: str, borrow_date: str, rating: float | None) -> None:
    """Setting rating to None removes the rating property."""
    query(
        """
        MATCH (:Student {student_id:$sid})-[r:BORROWED]->(:Book {book_id:$bid})
        SET r.borrow_date = date($d), r.rating = $rating
        """,
        {"sid": student_id, "bid": book_id, "d": borrow_date, "rating": rating},
        write=True,
    )


def delete_borrow(student_id: str, book_id: str) -> None:
    query(
        "MATCH (:Student {student_id:$sid})-[r:BORROWED]->(:Book {book_id:$bid}) DELETE r",
        {"sid": student_id, "bid": book_id},
        write=True,
    )