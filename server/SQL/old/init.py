# init_db.py

import mysql.connector

TABLES = {
    "User": """
        CREATE TABLE User (
            User_id INT,
            Username VARCHAR(255),
            PRIMARY KEY (User_id)
        )
    """,

    "Conversation": """
        CREATE TABLE Conversation (
            Conversation_id INT,
            User_id INT,
            PRIMARY KEY (Conversation_id),
            FOREIGN KEY (User_id) REFERENCES User(User_id)
        )
    """,

    "Turn": """
        CREATE TABLE Turn (
            Turn_id INT,
            Conversation_id INT,
            question TEXT,
            answer TEXT,
            rating INT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (Turn_id, Conversation_id),
            FOREIGN KEY (Conversation_id) REFERENCES Conversation(Conversation_id)
        )
    """,

    "Document": """
        CREATE TABLE Document (
            Document_id INT,
            text TEXT,
            PRIMARY KEY (Document_id)
        )
    """,

    "Retrieval": """
        CREATE TABLE Retrieval (
            Turn_id INT,
            Conversation_id INT,
            Document_id INT,
            PRIMARY KEY (Turn_id, Conversation_id, Document_id),
            FOREIGN KEY (Turn_id, Conversation_id)
                REFERENCES Turn(Turn_id, Conversation_id),
            FOREIGN KEY (Conversation_id)
                REFERENCES Conversation(Conversation_id),
            FOREIGN KEY (Document_id)
                REFERENCES Document(Document_id)
        )
    """
}


def table_exists(cursor, table_name):
    cursor.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
        AND table_name = %s
    """, (table_name,))
    return cursor.fetchone()[0] == 1


def initialize_database():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="IONOS",
        database="RAG"
    )

    cursor = conn.cursor()

    for table_name, create_sql in TABLES.items():
        if table_exists(cursor, table_name):
            print(f"Table '{table_name}' already exists.")
        else:
            print(f"Creating table '{table_name}'...")
            cursor.execute(create_sql)

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    initialize_database()
