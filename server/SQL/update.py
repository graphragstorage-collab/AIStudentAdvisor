# db_operations.py

import mysql.connector

import os


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="IONOS",
        database="RAG"
    )


# =========================
# USER
# =========================

def insert_user(user_id, username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO User VALUES (%s, %s)",
        (user_id, username)
    )
    conn.commit()
    conn.close()


def delete_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM User WHERE User_id = %s",
        (user_id,)
    )
    conn.commit()
    conn.close()


def update_user(user_id, new_username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE User SET Username = %s WHERE User_id = %s",
        (new_username, user_id)
    )
    conn.commit()
    conn.close()


# =========================
# CONVERSATION
# =========================

def insert_conversation(conversation_id, user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Conversation VALUES (%s, %s)",
        (conversation_id, user_id)
    )
    conn.commit()
    conn.close()


def delete_conversation(conversation_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Conversation WHERE Conversation_id = %s",
        (conversation_id,)
    )
    conn.commit()
    conn.close()


def update_conversation(conversation_id, new_user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Conversation SET User_id = %s WHERE Conversation_id = %s",
        (new_user_id, conversation_id)
    )
    conn.commit()
    conn.close()


# =========================
# TURN
# =========================

def insert_turn(turn_id, conversation_id, question, answer, rating):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO Turn (Turn_id, Conversation_id, question, answer, rating) VALUES (%s,%s,%s,%s,%s)",
        (turn_id, conversation_id, question, answer, rating)
    )

    conn.commit()
    conn.close()


def delete_turn(turn_id, conversation_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Turn WHERE Turn_id = %s AND Conversation_id = %s",
        (turn_id, conversation_id)
    )
    conn.commit()
    conn.close()


def update_turn(turn_id, conversation_id, question=None, answer=None, rating=None, time=None):
    conn = get_connection()
    cursor = conn.cursor()

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
    if time is not None:
        updates.append("time = %s")
        values.append(time)

    values.extend([turn_id, conversation_id])

    sql = f"UPDATE Turn SET {', '.join(updates)} WHERE Turn_id = %s AND Conversation_id = %s"
    cursor.execute(sql, values)

    conn.commit()
    conn.close()


# =========================
# DOCUMENT
# =========================

def insert_document(document_id, text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Document VALUES (%s, %s)",
        (document_id, text)
    )
    conn.commit()
    conn.close()


def delete_document(document_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM Document WHERE Document_id = %s",
        (document_id,)
    )
    conn.commit()
    conn.close()


def update_document(document_id, new_text):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Document SET text = %s WHERE Document_id = %s",
        (new_text, document_id)
    )
    conn.commit()
    conn.close()


# =========================
# RETRIEVAL
# =========================

def insert_retrieval(turn_id, conversation_id, document_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO Retrieval VALUES (%s, %s, %s)",
        (turn_id, conversation_id, document_id)
    )
    conn.commit()
    conn.close()


def delete_retrieval(turn_id, conversation_id, document_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM Retrieval
        WHERE Turn_id = %s AND Conversation_id = %s AND Document_id = %s
        """,
        (turn_id, conversation_id, document_id)
    )
    conn.commit()
    conn.close()


def update_retrieval(turn_id, conversation_id, old_document_id, new_document_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Retrieval
        SET Document_id = %s
        WHERE Turn_id = %s AND Conversation_id = %s AND Document_id = %s
        """,
        (new_document_id, turn_id, conversation_id, old_document_id)
    )
    conn.commit()
    conn.close()



# =========================
# INIT + SQL FILE RUNNER
# =========================

BASE_DIR = os.path.dirname(__file__)

def run_sql_file(filename):
    conn = get_connection()
    cursor = conn.cursor()

    path = os.path.join(BASE_DIR, filename)

    with open(path, "r") as f:
        sql = f.read()

    for stmt in sql.split(";"):
        stmt = stmt.strip()
        if stmt:
            cursor.execute(stmt)

    conn.commit()
    conn.close()


def initialize_all():
    run_sql_file("init_tables.sql")
    run_sql_file("triggers.sql")


# =========================
# REPORTING (READ ONLY)
# =========================

def get_all_conversations(order_time=True, order_rating=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT 
            c.Conversation_id,
            u.Username,
            MAX(t.time) AS latest_time,
            AVG(t.rating) AS avg_rating
        FROM Conversation c
        JOIN User u ON c.User_id = u.User_id
        LEFT JOIN Turn t ON c.Conversation_id = t.Conversation_id
        GROUP BY c.Conversation_id, u.Username
    """

    if order_time and order_rating:
        query += " ORDER BY latest_time DESC, avg_rating DESC"
    elif order_time:
        query += " ORDER BY latest_time DESC"
    elif order_rating:
        query += " ORDER BY avg_rating DESC"

    cursor.execute(query)
    res = cursor.fetchall()
    conn.close()
    return res


def get_turns(conversation_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT Turn_id, question, answer, rating, time
        FROM Turn
        WHERE Conversation_id = %s
        ORDER BY time ASC
    """, (conversation_id,))

    res = cursor.fetchall()
    conn.close()
    return res




def filter_user(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            c.Conversation_id,
            u.Username,
            MAX(t.time) AS latest_time,
            AVG(t.rating) AS avg_rating
        FROM Conversation c
        JOIN User u ON c.User_id = u.User_id
        LEFT JOIN Turn t ON c.Conversation_id = t.Conversation_id
        WHERE u.Username LIKE %s
        GROUP BY c.Conversation_id, u.Username
    """, (f"%{username}%",))

    res = cursor.fetchall()
    conn.close()
    return res



# =========================
# DIRECT SQL EXECUTION
# =========================

import os

BASE_DIR = os.path.dirname(__file__)

def execute_sql(query, params=None, fetch=False, many=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        if many:
            cursor.executemany(query, params or [])
        else:
            cursor.execute(query, params or ())

        if fetch:
            result = cursor.fetchall()
        else:
            result = None

        conn.commit()
        return result
    finally:
        cursor.close()
        conn.close()


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


# =========================
# SAFE UPSERT HELPERS
# =========================

def ensure_user_exists(user_id, username=None):
    rows = execute_sql(
        "SELECT User_id FROM User WHERE User_id = %s",
        (user_id,),
        fetch=True
    )
    if not rows:
        if username is None or str(username).strip() == "":
            username = f"user_{user_id}"
        insert_user(user_id, username)


def get_next_turn_id(conversation_id):
    rows = execute_sql(
        "SELECT COALESCE(MAX(Turn_id), 0) AS max_turn_id FROM Turn WHERE Conversation_id = %s",
        (conversation_id,),
        fetch=True
    )
    return int(rows[0]["max_turn_id"]) + 1


# =========================
# UPDATED INSERTS / EDITS
# =========================

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

    rows = execute_sql(
        "SELECT COALESCE(MAX(Document_id), -1) AS max_id FROM Document",
        fetch=True
    )
    next_id = int(rows[0]["max_id"]) + 1

    execute_sql(
        "INSERT INTO Document (Document_id, text) VALUES (%s, %s)",
        (next_id, text_value)
    )

    return next_id


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


# =========================
# REPORTING QUERIES
# =========================

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
        JOIN Document d
            ON d.Document_id = r.Document_id
        LEFT JOIN Retrieval r2
            ON r2.Document_id = d.Document_id
        LEFT JOIN Turn t2
            ON t2.Turn_id = r2.Turn_id
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
        LEFT JOIN Retrieval r
            ON r.Document_id = d.Document_id
        LEFT JOIN Turn t
            ON t.Turn_id = r.Turn_id
           AND t.Conversation_id = r.Conversation_id
    """
    params = []

    if keyword and str(keyword).strip():
        query += " WHERE d.text LIKE %s"
        params.append(f"%{keyword}%")

    query += " GROUP BY d.Document_id, d.text"

    if order_by_rating:
        query += " ORDER BY total_rating DESC, d.Document_id ASC"
    else:
        query += " ORDER BY d.Document_id ASC"

    return execute_sql(query, tuple(params), fetch=True)
