# =========================================================
# SQL/update.py (FULL CLEAN REWRITE — SAFE VERSION)
# =========================================================

import mysql.connector
import os
import datetime
from load import *
print(users)
# =========================================================
# CONNECTION
# =========================================================

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="IONOS",
        database="RAG"
    )


# =========================================================
# CORE SQL EXECUTOR (USED EVERYWHERE)
# =========================================================

def execute_sql(query, params=None, fetch=False, many=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if many:
            cursor.executemany(query, params or [])
        else:
            cursor.execute(query, params or ())

        # 🔥 ALWAYS clear result if exists
        result = None
        if cursor.with_rows:
            result = cursor.fetchall()

        conn.commit()

        return result if fetch else result

    finally:
        try:
            # 🔥 force cleanup of unread results
            while cursor.nextset():
                pass
        except:
            pass

        cursor.close()
        conn.close()

# =========================================================
# USER HELPERS
# =========================================================

def ensure_username_exists(username):

    global users

    rows = execute_sql(
        "SELECT User_id FROM User WHERE Username = %s LIMIT 1",
        (username,),
        fetch=True
    )

    if rows:
        user_id = rows[0]["User_id"]
        if username not in users:
            users[username] = {"Convo": 0, "User_id": user_id}
        return user_id

    rows = execute_sql(
        "SELECT COALESCE(MAX(User_id), 0) AS max_id FROM User",
        fetch=True
    )

    next_id = int(rows[0]["max_id"]) + 1

    execute_sql(
        "INSERT INTO User (User_id, Username) VALUES (%s, %s)",
        (next_id, username)
    )
    if username not in users:
        users[username] = {"Convo": 0, "User_id": next_id}
    return next_id


def ensure_user_exists(user_id, username=None):
    rows = execute_sql(
        "SELECT User_id FROM User WHERE User_id = %s",
        (user_id,),
        fetch=True
    )

    if not rows:
        if not username or not str(username).strip():
            username = f"user_{user_id}"

        execute_sql(
            "INSERT INTO User (User_id, Username) VALUES (%s, %s)",
            (user_id, username)
        )


# =========================================================
# CONVERSATION HELPERS
# =========================================================

def get_or_create_conversation(user_id, username):
    rows = execute_sql(
        "SELECT Conversation_id FROM Conversation WHERE User_id = %s",
        (user_id,),
        fetch=True
    )
    
    convo_num = users[username]["Convo"] if username in users else 0
    print("Existing conversations for user_id", user_id, ":", len(rows), " | convo_num:", convo_num)
    if len(rows) > convo_num:
        return rows[convo_num]["Conversation_id"]

    rows = execute_sql(
        "SELECT COALESCE(MAX(Conversation_id), 0) AS max_id FROM Conversation",
        fetch=True
    )

    conversation_id = int(rows[0]["max_id"]) + 1
    print("Creating conversation with ID:", conversation_id)
    execute_sql(
        "INSERT INTO Conversation (Conversation_id, User_id) VALUES (%s, %s)",
        (conversation_id, user_id)
    )

    return conversation_id


def update_conversation_full(conversation_id, user_id):
    ensure_user_exists(user_id)

    execute_sql(
        """
        UPDATE Conversation
        SET User_id = %s
        WHERE Conversation_id = %s
        """,
        (user_id, conversation_id)
    )


# =========================================================
# TURN HELPERS
# =========================================================

def get_next_turn_id(conversation_id):
    rows = execute_sql(
        """
        SELECT COALESCE(MAX(Turn_id), 0) AS max_turn_id
        FROM Turn
        WHERE Conversation_id = %s
        """,
        (conversation_id,),
        fetch=True
    )

    return int(rows[0]["max_turn_id"]) + 1


def insert_turn_auto(conversation_id, question, answer, rating):
    turn_id = get_next_turn_id(conversation_id)

    execute_sql(
        """
        INSERT INTO Turn (Turn_id, Conversation_id, question, answer, rating)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (turn_id, conversation_id, question, answer, rating)
    )

    return turn_id


def update_turn_metadata(turn_id, conversation_id, question=None, answer=None, rating=None, time_value=None):
    updates = []
    values = []

    if question is not None:
        updates.append("question = %s")
        values.append(question)

    if answer is not None:
        updates.append("answer = %s")
        values.append(answer)

    if rating is not None:
        updates.append("rating = %s")
        values.append(rating)

    if time_value is not None:
        updates.append("time = %s")
        values.append(time_value)

    if not updates:
        return

    values.extend([turn_id, conversation_id])

    execute_sql(
        f"""
        UPDATE Turn
        SET {', '.join(updates)}
        WHERE Turn_id = %s AND Conversation_id = %s
        """,
        tuple(values)
    )


# =========================================================
# 🔥 NEW SAFE INSERT ENTRY POINT (REPLACES OLD SYSTEM)
# =========================================================

def insert_turn_from_app(username, question, answer):
    user_id = ensure_username_exists(username)

    conversation_id = get_or_create_conversation(user_id, username)
    turn_id = get_next_turn_id(conversation_id)

    execute_sql(
        """
        INSERT INTO Turn (Turn_id, Conversation_id, question, answer, rating, time)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (turn_id, conversation_id, question, answer, 0, datetime.datetime.now())
    )

    return conversation_id, turn_id


# =========================================================
# DOCUMENT SYSTEM
# =========================================================

def insert_document_text(text_value):
    rows = execute_sql(
        "SELECT COALESCE(MAX(Document_id), 0) AS max_document_id FROM Document",
        fetch=True
    )

    next_id = int(rows[0]["max_document_id"]) + 1

    execute_sql(
        "INSERT INTO Document (Document_id, text) VALUES (%s, %s)",
        (next_id, text_value)
    )

    return next_id


def get_or_create_document(text_value):
    rows = execute_sql(
        "SELECT Document_id FROM Document WHERE text = %s LIMIT 1",
        (text_value,),
        fetch=True
    )

    if rows:
        return rows[0]["Document_id"]

    return insert_document_text(text_value)


def attach_document_to_turn(conversation_id, turn_id, document_text):
    document_id = get_or_create_document(document_text)

    execute_sql(
        """
        INSERT INTO Retrieval (Turn_id, Conversation_id, Document_id)
        VALUES (%s, %s, %s)
        """,
        (turn_id, conversation_id, document_id)
    )

    return document_id


# =========================================================
# REPORTING QUERIES (UNCHANGED)
# =========================================================

def get_all_conversations(order_time=True, order_rating=False):
    query = """
        SELECT
            c.Conversation_id,
            c.User_id,
            u.Username,
            MAX(t.time) AS latest_time,
            AVG(t.rating) AS avg_rating,
            COUNT(t.Turn_id) AS turn_count
        FROM Conversation c
        JOIN User u ON c.User_id = u.User_id
        LEFT JOIN Turn t ON c.Conversation_id = t.Conversation_id
        GROUP BY c.Conversation_id, c.User_id, u.Username
    """

    if order_time and order_rating:
        query += " ORDER BY latest_time DESC, avg_rating DESC"
    elif order_time:
        query += " ORDER BY latest_time DESC"
    elif order_rating:
        query += " ORDER BY avg_rating DESC"
    else:
        query += " ORDER BY c.Conversation_id ASC"

    return execute_sql(query, fetch=True)


def filter_user(username, order_time=True, order_rating=False):
    query = """
        SELECT
            c.Conversation_id,
            c.User_id,
            u.Username,
            MAX(t.time) AS latest_time,
            AVG(t.rating) AS avg_rating,
            COUNT(t.Turn_id) AS turn_count
        FROM Conversation c
        JOIN User u ON c.User_id = u.User_id
        LEFT JOIN Turn t ON c.Conversation_id = t.Conversation_id
        WHERE u.Username LIKE %s
        GROUP BY c.Conversation_id, c.User_id, u.Username
    """

    if order_time and order_rating:
        query += " ORDER BY latest_time DESC, avg_rating DESC"
    elif order_time:
        query += " ORDER BY latest_time DESC"
    elif order_rating:
        query += " ORDER BY avg_rating DESC"
    else:
        query += " ORDER BY c.Conversation_id ASC"

    return execute_sql(query, (f"%{username}%",), fetch=True)


def get_turns(conversation_id):
    return execute_sql(
        """
        SELECT
            Turn_id,
            Conversation_id,
            question,
            answer,
            rating,
            time
        FROM Turn
        WHERE Conversation_id = %s
        ORDER BY Turn_id ASC
        """,
        (conversation_id,),
        fetch=True
    )


def get_documents(turn_id, conversation_id):
    return execute_sql(
        """
        SELECT
            d.Document_id,
            d.text,
            COALESCE(SUM(t2.rating), 0) AS total_rating
        FROM Retrieval r
        JOIN Document d ON d.Document_id = r.Document_id
        LEFT JOIN Retrieval r2 ON r2.Document_id = d.Document_id
        LEFT JOIN Turn t2 ON t2.Turn_id = r2.Turn_id
           AND t2.Conversation_id = r2.Conversation_id
        WHERE r.Turn_id = %s AND r.Conversation_id = %s
        GROUP BY d.Document_id, d.text
        ORDER BY d.Document_id ASC
        """,
        (turn_id, conversation_id),
        fetch=True
    )


def get_all_documents(order_by_rating=True, keyword=""):
    query = """
        SELECT
            d.Document_id,
            d.text,
            COALESCE(SUM(t.rating), 0) AS total_rating,
            COUNT(r.Turn_id) AS usage_count
        FROM Document d
        LEFT JOIN Retrieval r ON r.Document_id = d.Document_id
        LEFT JOIN Turn t ON t.Turn_id = r.Turn_id
           AND t.Conversation_id = r.Conversation_id
    """

    params = []

    if keyword:
        query += " WHERE d.text LIKE %s"
        params.append(f"%{keyword}%")

    query += " GROUP BY d.Document_id, d.text"

    if order_by_rating:
        query += " ORDER BY total_rating DESC, d.Document_id ASC"
    else:
        query += " ORDER BY d.Document_id ASC"

    return execute_sql(query, tuple(params), fetch=True)


# =========================================================
# INIT
# =========================================================

BASE_DIR = os.path.dirname(__file__)

def run_sql_file(filename):
    path = os.path.join(BASE_DIR, filename)

    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for stmt in [s.strip() for s in sql.split(";") if s.strip()]:
            cursor.execute(stmt)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def initialize_all():
    run_sql_file("init_tables.sql")



def get_document_ids_from_contexts(expanded_contexts):
    """
    Takes a list of text chunks (expanded_contexts)
    and returns a list of corresponding Document_ids.

    - Skips None / "NO"
    - Strips whitespace
    - Deduplicates identical text (optional but recommended)
    - Uses get_or_create_document to ensure existence
    """

    doc_ids = []
    seen = set()  # prevent duplicate inserts

    for ctx in expanded_contexts:
        if ctx is None:
            continue

        ctx = ctx.strip()

        if not ctx or ctx == "NO":
            continue

        # optional dedupe (prevents duplicate DB rows)
        if ctx in seen:
            continue
        seen.add(ctx)

        doc_id = get_or_create_document(ctx)
        doc_ids.append(doc_id)

    return doc_ids


def update_turn_with_documents(
    conversation_id: int,
    turn_id: int = None,
    question: str = None,
    answer: str = None,
    rating: int = 0,
    doc_ids: list = None,
    overwrite_retrieval: bool = True
):
    """
    Updates or inserts a Turn AND updates Retrieval table.

    Order of operations (FK-safe):
    1. Ensure Turn exists (insert if needed)
    2. Optionally clear old Retrieval rows
    3. Insert Retrieval rows (Turn -> Document)

    Returns: turn_id
    """

    # -----------------------------
    # 1. ENSURE TURN EXISTS
    # -----------------------------
    if turn_id is None:
        # create new turn
        turn_id = get_next_turn_id(conversation_id)

        execute_sql(
            """
            INSERT INTO Turn (Turn_id, Conversation_id, question, answer, rating)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (turn_id, conversation_id, question or "", answer or "", rating)
        )
    else:
        # update existing turn metadata if provided
        update_turn_metadata(
            turn_id=turn_id,
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            rating=rating
        )

    # -----------------------------
    # 2. CLEAR OLD RETRIEVAL (OPTIONAL)
    # -----------------------------
    if overwrite_retrieval:
        execute_sql(
            """
            DELETE FROM Retrieval
            WHERE Turn_id = %s AND Conversation_id = %s
            """,
            (turn_id, conversation_id)
        )

    # -----------------------------
    # 3. INSERT NEW RETRIEVAL LINKS
    # -----------------------------
    if doc_ids:
        rows = [
            (turn_id, conversation_id, int(doc_id))
            for doc_id in doc_ids
        ]

        execute_sql(
            """
            INSERT INTO Retrieval (Turn_id, Conversation_id, Document_id)
            VALUES (%s, %s, %s)
            """,
            rows,
            many=True
        )

    return turn_id


def delete_turn_full(conversation_id: int, turn_id: int):
    """
    Safely deletes a Turn and all dependent rows.

    Order:
    1. Vote
    2. Retrieval
    3. Turn
    """

    # delete votes
    execute_sql(
        """
        DELETE FROM Vote
        WHERE Turn_id = %s AND Conversation_id = %s
        """,
        (turn_id, conversation_id)
    )

    # delete retrieval links
    execute_sql(
        """
        DELETE FROM Retrieval
        WHERE Turn_id = %s AND Conversation_id = %s
        """,
        (turn_id, conversation_id)
    )

    # delete turn
    execute_sql(
        """
        DELETE FROM Turn
        WHERE Turn_id = %s AND Conversation_id = %s
        """,
        (turn_id, conversation_id)
    )

def delete_conversation_full(conversation_id: int):
    """
    Safely deletes an entire conversation and all dependent rows.

    Order:
    1. Vote
    2. Retrieval
    3. Turn
    4. Conversation
    """

    # delete votes
    execute_sql(
        """
        DELETE v FROM Vote v
        JOIN Turn t ON t.Turn_id = v.Turn_id
        AND t.Conversation_id = v.Conversation_id
        WHERE t.Conversation_id = %s
        """,
        (conversation_id,)
    )

    # delete retrieval
    execute_sql(
        """
        DELETE FROM Retrieval
        WHERE Conversation_id = %s
        """,
        (conversation_id,)
    )

    # delete turns
    execute_sql(
        """
        DELETE FROM Turn
        WHERE Conversation_id = %s
        """,
        (conversation_id,)
    )

    # delete conversation
    execute_sql(
        """
        DELETE FROM Conversation
        WHERE Conversation_id = %s
        """,
        (conversation_id,)
    )

def delete_document_safe(document_id: int):
    """
    Deletes a document ONLY if not referenced.
    """

    usage = execute_sql(
        """
        SELECT COUNT(*) AS cnt
        FROM Retrieval
        WHERE Document_id = %s
        """,
        (document_id,),
        fetch=True
    )[0]["cnt"]

    if usage > 0:
        raise Exception("Document still in use")

    execute_sql(
        """
        DELETE FROM Document
        WHERE Document_id = %s
        """,
        (document_id,)
    )

def delete_retrieval_link(conversation_id: int, turn_id: int, document_id: int):
    """
    Removes a document from a turn safely.
    """

    execute_sql(
        """
        DELETE FROM Retrieval
        WHERE Turn_id = %s AND Conversation_id = %s AND Document_id = %s
        """,
        (turn_id, conversation_id, document_id)
    )
