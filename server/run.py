import uvicorn
from fastapi import FastAPI, Response, Request, Depends, Cookie, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import UploadFile, File
from pydantic import BaseModel
from itsdangerous import Signer, BadSignature
import os
import time
import datetime
import zlib
from typing import Optional

from load import *

from utils.transform import transform_raw_text
from utils.header_maker import create_header
from utils.upload_handler import process_upload

from pypdf import PdfReader
import re


# =================================================================
# 0. INITIAL SETUP
# =================================================================

ACCOUNTS_DIR = "./accounts"
CONVO_DIR = "./conversations"
USER_UPLOADS_DIR = "./user_uploads"
REACT_BUILD_DIR = "../website/build"

os.makedirs(ACCOUNTS_DIR, exist_ok=True)
os.makedirs(CONVO_DIR, exist_ok=True)
os.makedirs(USER_UPLOADS_DIR, exist_ok=True)

COOKIE_SIGNER = Signer("SUPER_SECRET_KEY_CHANGE_ME")

from SQL.update import *
from fastapi.responses import HTMLResponse
from fastapi import HTTPException, Request

ADMIN_PASSWORD = "IONOS"


# =================================================================
# 1. LOAD GRAPH-RAG
# =================================================================

print("Loading GraphRAG…")

graph_rag2 = GraphRAG(initialize_empty=False)
uploads = os.listdir("./user_uploads")
for upload in uploads:
    if upload.endswith(".txt"):
        add_document_to_graphrag(graph_rag2, os.path.join("./user_uploads", upload))

print("✓ GraphRAG Loaded.")


# =================================================================
# 2. APP SETUP (FASTAPI + REACT)
# =================================================================

app = FastAPI()

if os.path.exists(REACT_BUILD_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(REACT_BUILD_DIR, "static")), name="static")
    print(f"Serving React from {REACT_BUILD_DIR}")
else:
    print(f"React build directory not found at {REACT_BUILD_DIR}. Run 'npm run build'")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =================================================================
# 3. HELPER FUNCTIONS
# =================================================================

def get_client_ip(request: Request):
    return request.client.host


def username_to_user_id(username: str) -> int:
    return zlib.crc32(str(username).encode("utf-8")) & 0x7FFFFFFF


def get_current_user_id(session: Optional[str]) -> int:
    username = get_session_username(session)
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")
    return username_to_user_id(username)


def user_owns_conversation(user_id: int, conversation_id: int) -> bool:
    rows = execute_sql(
        """
        SELECT 1
        FROM Conversation
        WHERE Conversation_id = %s AND User_id = %s
        LIMIT 1
        """,
        (conversation_id, user_id),
        fetch=True
    )
    return bool(rows)


def get_next_conversation_id() -> int:
    rows = execute_sql(
        "SELECT COALESCE(MAX(Conversation_id), 0) AS max_conversation_id FROM Conversation",
        fetch=True
    )
    return int(rows[0]["max_conversation_id"]) + 1


def create_conversation_for_user(username: str) -> int:
    user_id = username_to_user_id(username)
    ensure_user_exists(user_id, username)
    conversation_id = get_next_conversation_id()
    insert_conversation(conversation_id, user_id)
    return conversation_id


def extract_user_question(query_text: str) -> str:
    marker = "current question:"
    if marker in query_text:
        return query_text.split(marker, 1)[1].strip()
    return query_text.strip()


def set_session(response: Response, username: str):
    signed = COOKIE_SIGNER.sign(username.encode()).decode()
    response.set_cookie("session", signed, httponly=True, max_age=86400*7, path="/")


def clear_session(response):
    response.delete_cookie(
        key="session",
        path="/",
    )


def get_session_username(session_cookie: Optional[str]):
    if not session_cookie:
        return None
    try:
        raw = COOKIE_SIGNER.unsign(session_cookie).decode()
        return raw
    except BadSignature:
        return None


def read_account(username: str):
    path = f"{ACCOUNTS_DIR}/{username}.txt"
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        first = f.readline().strip()

    parts = first.split(",")
    if len(parts) != 3:
        return None

    password, ip, ts = parts
    try:
        ts = float(ts)
    except:
        ts = 0

    return password, ip, ts


def update_account_login(username: str, new_ip: str):
    path = f"{ACCOUNTS_DIR}/{username}.txt"
    if not os.path.exists(path):
        return False

    with open(path, "r") as f:
        lines = f.readlines()

    timestamp = time.time()
    lines[0] = f"{lines[0].split(',')[0]},{new_ip},{timestamp}\n"

    with open(path, "w") as f:
        f.writelines(lines)

    return True


def append_conversation(username: str, history_text: str):
    try:
        path = f"{CONVO_DIR}/{username}_history.txt"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n===============================\n")
            f.write(now + "\n")
            f.write(history_text + "\n")
    except Exception as e:
        print(f"⚠️  ERROR in append_conversation: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


initialize_all()


# =================================================================
# 4. STATUS
# =================================================================

@app.get("/api/auth/status")
async def auth_status(session: Optional[str] = Cookie(default=None)):
    username = get_session_username(session)
    if username and read_account(username):
        return {"authenticated": True, "username": username}
    return {"authenticated": False}


# =================================================================
# 5. LOGIN
# =================================================================

@app.post("/api/login")
async def login_post(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    client_ip = get_client_ip(request)

    acc = read_account(username)
    if not acc:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Incorrect username or password."}
        )
    stored_pw, stored_ip, last_ts = acc

    if password != stored_pw:
        return JSONResponse(
            status_code=401,
            content={"success": False, "error": "Incorrect username or password."}
        )

    update_account_login(username, client_ip)

    response = JSONResponse(content={"success": True})
    set_session(response, username)
    return response


# =================================================================
# 6. SIGNUP + LOGOUT
# =================================================================

@app.post("/api/signup")
async def signup_post(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    confirm = form.get("confirm", "")

    if "," in password:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Password cannot contain commas."}
        )
    if password != confirm:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Passwords do not match."}
        )
    acc_path = f"{ACCOUNTS_DIR}/{username}.txt"
    if os.path.exists(acc_path):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "Username already exists."}
        )
    with open(acc_path, "w") as f:
        f.write(f"{password},none,0\n")

    return {"success": True}


@app.post("/api/logout")
async def logout_post():
    response = JSONResponse(content={"success": True})
    clear_session(response)
    return response


# =================================================================
# 8. MODEL INTERACTION ENDPOINT
# =================================================================

class PromptInput(BaseModel):
    query: str
    lang: str = "none"
    conversation_id: Optional[int] = None


@app.post("/api/prompt")
async def prompt(
    request: Request,
    request_data: PromptInput,
    session: Optional[str] = Cookie(default=None)
):
    username = get_session_username(session)
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")

    decoded_query = request_data.query
    target_lang = (request_data.lang or "none").lower()

    print("\n======== RECEIVED QUERY ========")
    print(decoded_query[:500], "...")
    print("Language:", target_lang)
    print("================================\n")

    current_question = decoded_query
    user_id = username_to_user_id(username)
    conversation_id = request_data.conversation_id

    if conversation_id is None:
        conversation_id = create_conversation_for_user(username)
    elif not user_owns_conversation(user_id, int(conversation_id)):
        raise HTTPException(status_code=403, detail="Conversation does not belong to the current user")

    question_for_storage = extract_user_question(decoded_query)

    try:
        answer = graph_rag2.query(current_question)
        print("Model answer")
        if target_lang == "none":
            insert_turn_auto(int(conversation_id), question_for_storage, answer, 0)
            print("No translation requested, returning original answer.")
            append_conversation(username, current_question + "\n\nmodel: " + answer)
            print("Conversation appended without translation.")
            return {"answer": answer, "conversation_id": int(conversation_id)}

        print("Translating answer to", target_lang)
        translated = translate_text_multilingual(
            answer, target_language=target_lang.capitalize()
        )
        print("Translation complete")
        insert_turn_auto(int(conversation_id), question_for_storage, translated, 0)

        append_conversation(
            username,
            current_question + f"\n\n---\n\n[Translated to {target_lang}]:\n\n" + translated
        )
        print("Conversation appended")
        return {"answer": translated, "conversation_id": int(conversation_id)}

    except Exception as e:
        print(f"❌ EXCEPTION IN /prompt: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Server error. TRY AGAIN LATER.")


# =================================================================
# 9. HEALTH CHECK
# =================================================================

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "GraphRAG Chat Server"}


# =================================================================
# 10. FILE UPLOAD ENDPOINT
# =================================================================

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    session: Optional[str] = Cookie(default=None),
):
    username = get_session_username(session)
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")

    success, message = await process_upload(file, username, graph_rag2)

    if not success:
        raise HTTPException(status_code=400, detail=message)

    return {"success": True, "message": message}


@app.get("/api/my/conversations")
def get_my_conversations(
    session: Optional[str] = Cookie(default=None),
    order_time: bool = True,
    order_rating: bool = False
):
    username = get_session_username(session)
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")

    user_id = username_to_user_id(username)
    ensure_user_exists(user_id, username)

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
        WHERE c.User_id = %s
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

    return execute_sql(query, (user_id,), fetch=True)


@app.post("/api/my/conversations")
def create_my_conversation(session: Optional[str] = Cookie(default=None)):
    username = get_session_username(session)
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")

    conversation_id = create_conversation_for_user(username)
    return {"conversation_id": conversation_id}


@app.get("/api/my/conversation/{conversation_id}")
def get_my_conversation_turns(
    conversation_id: int,
    session: Optional[str] = Cookie(default=None)
):
    user_id = get_current_user_id(session)
    if not user_owns_conversation(user_id, conversation_id):
        raise HTTPException(status_code=403, detail="Conversation does not belong to the current user")

    return get_turns(conversation_id)


@app.post("/api/vote")
async def vote(request: Request, session: Optional[str] = Cookie(default=None)):
    data = await request.json()
    turn_id = int(data["turn_id"])
    conversation_id = int(data["conversation_id"])
    vote_value = int(data["vote"])

    if vote_value not in (-1, 0, 1):
        raise HTTPException(status_code=400, detail="Vote must be -1, 0, or 1")

    user_id = get_current_user_id(session)
    if not user_owns_conversation(user_id, conversation_id):
        raise HTTPException(status_code=403, detail="Conversation does not belong to the current user")

    if vote_value == 0:
        execute_sql(
            """
            DELETE FROM Vote
            WHERE Turn_id = %s AND Conversation_id = %s AND User_id = %s
            """,
            (turn_id, conversation_id, user_id)
        )
    else:
        execute_sql(
            """
            INSERT INTO Vote (User_id, Turn_id, Conversation_id, vote)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE vote = VALUES(vote)
            """,
            (user_id, turn_id, conversation_id, vote_value)
        )

    return {"success": True}


@app.get("/api/votes/{turn_id}")
def get_vote_score(
    turn_id: int,
    conversation_id: Optional[int] = None,
    session: Optional[str] = Cookie(default=None)
):
    where_clauses = ["Turn_id = %s"]
    params = [turn_id]

    if conversation_id is not None:
        user_id = get_current_user_id(session)
        if not user_owns_conversation(user_id, conversation_id):
            raise HTTPException(status_code=403, detail="Conversation does not belong to the current user")
        where_clauses.append("Conversation_id = %s")
        params.append(conversation_id)

    score_rows = execute_sql(
        f"""
        SELECT COALESCE(SUM(vote), 0) AS score
        FROM Vote
        WHERE {' AND '.join(where_clauses)}
        """,
        tuple(params),
        fetch=True
    )

    user_vote = 0
    username = get_session_username(session)
    if username:
        user_rows = execute_sql(
            f"""
            SELECT vote
            FROM Vote
            WHERE {' AND '.join(where_clauses)} AND User_id = %s
            LIMIT 1
            """,
            tuple(params + [username_to_user_id(username)]),
            fetch=True
        )
        if user_rows:
            user_vote = int(user_rows[0]["vote"])

    return {
        "score": int(score_rows[0]["score"]) if score_rows else 0,
        "user_vote": user_vote,
    }


# =================================================================
# 11. REACT FRONTEND
# =================================================================

@app.get("/login", response_class=HTMLResponse)
@app.get("/signup", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
@app.get("/vote", response_class=HTMLResponse)
@app.get("/planner", response_class=HTMLResponse)
async def serve_react_app():
    index_path = os.path.join(REACT_BUILD_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return HTMLResponse(f"""
        <html>
            <head><title>React App Not Built</title></head>
            <body style="font-family: Arial; padding: 40px; background: #f5f5f5;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; border: 2px solid #DAA520;">
                    <h1>React App Not Built</h1>
                    <p>build the React app first by creating the build dir in website:</p>
                    <pre style="background: #f0f0f0; padding: 10px; border-radius: 5px;">
cd website
npm install
npm run build
                    </pre>
                    <p>Expected build path: <code>{REACT_BUILD_DIR}</code></p>
                    <p>API endpoints are still available at <code>/api/*</code></p>
                </div>
            </body>
        </html>
        """)


@app.get("/", response_class=HTMLResponse)
async def root_login_redirect():
    return RedirectResponse("/login", status_code=302)


# =========================
# REPORTING / SQL ROUTES
# =========================

@app.post("/reporting/auth")
def reporting_auth(password: str):
    if password != ADMIN_PASSWORD:
        raise HTTPException(status_code=403)
    return {"status": "ok"}


@app.get("/reporting/init")
def init_db():
    initialize_all()
    return {"status": "initialized"}


@app.get("/reporting/conversations")
def conversations(order_time: bool = True, order_rating: bool = False):
    return get_all_conversations(order_time, order_rating)


@app.get("/reporting/conversation/{conversation_id}")
def conversation(conversation_id: int):
    return get_turns(conversation_id)


@app.get("/reporting/documents/{conversation_id}/{turn_id}")
def documents(conversation_id: int, turn_id: int):
    return get_documents(turn_id, conversation_id)


@app.get("/reporting/filter")
def filter_conv(username: str = "", order_time: bool = True, order_rating: bool = False):
    username = str(username).strip()

    if username == "":
        return get_all_conversations(order_time, order_rating)

    result = filter_user(username, order_time, order_rating)

    # if no matches → return ALL (do nothing behavior)
    if not result:
        return get_all_conversations(order_time, order_rating)

    return result


@app.get("/reporting/all_documents")
def all_documents(keyword: str = "", order_by_rating: bool = True):
    return get_all_documents(order_by_rating=order_by_rating, keyword=keyword)


@app.post("/reporting/add_conversation_full")
async def add_conversation_full(request: Request):
    data = await request.json()

    cid = int(data["conversation_id"])
    uid = int(data["user_id"])
    username = data.get("username", f"user_{uid}")

    ensure_user_exists(uid, username)

    existing = execute_sql(
        "SELECT Conversation_id FROM Conversation WHERE Conversation_id = %s",
        (cid,),
        fetch=True
    )
    if existing:
        raise HTTPException(status_code=400, detail="Conversation already exists")

    insert_conversation(cid, uid)
    return {"status": "added"}


@app.post("/reporting/update_conversation")
async def update_conversation_api(request: Request):
    data = await request.json()

    cid = int(data["conversation_id"])
    uid = int(data["user_id"])
    username = data.get("username", f"user_{uid}")

    ensure_user_exists(uid, username)
    update_conversation_full(cid, uid)
    return {"status": "updated"}


@app.post("/reporting/add_turn")
async def add_turn_api(request: Request):
    data = await request.json()

    conversation_id = int(data["conversation_id"])
    question = data.get("question", "")
    answer = data.get("answer", "")
    rating = int(data.get("rating", 0))

    turn_id = insert_turn_auto(conversation_id, question, answer, rating)
    return {"status": "turn added", "turn_id": turn_id}


@app.post("/reporting/update_turn")
async def update_turn_api(request: Request):
    data = await request.json()

    turn_id = int(data["turn_id"])
    conversation_id = int(data["conversation_id"])

    update_turn_metadata(
        turn_id=turn_id,
        conversation_id=conversation_id,
        question=data.get("question"),
        answer=data.get("answer"),
        rating=data.get("rating"),
        time_value=data.get("time")
    )
    return {"status": "updated"}


@app.post("/reporting/add_document_to_turn")
async def add_document_to_turn_api(request: Request):
    data = await request.json()

    conversation_id = int(data["conversation_id"])
    turn_id = int(data["turn_id"])
    text_value = data.get("text", "")

    if not str(text_value).strip():
        raise HTTPException(status_code=400, detail="Document text cannot be blank")

    document_id = attach_document_to_turn(conversation_id, turn_id, text_value)
    return {"status": "document added", "document_id": document_id}


@app.post("/reporting/run_sql")
async def run_sql_api(request: Request):
    data = await request.json()
    query = data.get("query", "")
    params = data.get("params", [])
    fetch = bool(data.get("fetch", False))

    if not query.strip():
        raise HTTPException(status_code=400, detail="Query is required")

    upper = query.strip().upper()
    allowed = upper.startswith("SELECT") or upper.startswith("UPDATE") or upper.startswith("INSERT") or upper.startswith("DELETE")
    if not allowed:
        raise HTTPException(status_code=400, detail="Only SELECT/INSERT/UPDATE/DELETE allowed")

    result = execute_sql(query, tuple(params), fetch=fetch)
    return {"status": "ok", "result": result}


# =========================
# ADMIN UI
# =========================

@app.get("/admin", response_class=HTMLResponse)
def admin_ui():
    js_path = os.path.join("SQL", "admin.js")

    with open(js_path, "r", encoding="utf-8") as f:
        admin_js = f.read()

    return admin_js


@app.post("/reporting/upload_document_to_turn")
async def upload_document_to_turn(
    file: UploadFile = File(...),
    conversation_id: int = 0,
    turn_id: int = 0
):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    document_id = attach_document_to_turn(conversation_id, turn_id, text)

    return {"status": "uploaded", "document_id": document_id}


@app.post("/reporting/upload_document")
async def upload_document(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    doc_id = insert_document_text(text)
    return {"document_id": doc_id}


@app.post("/reporting/attach_existing_document")
async def attach_existing_doc(request: Request):
    data = await request.json()

    execute_sql(
        "INSERT INTO Retrieval (Turn_id, Conversation_id, Document_id) VALUES (%s,%s,%s)",
        (data["turn_id"], data["conversation_id"], data["document_id"])
    )

    return {"status": "attached"}

@app.post("/reporting/delete_conversation")
def delete_conversation(data: dict):
    cid = data["conversation_id"]

    execute_sql("DELETE FROM Retrieval WHERE Conversation_id = %s", (cid,))
    execute_sql("DELETE FROM Turn WHERE Conversation_id = %s", (cid,))
    execute_sql("DELETE FROM Conversation WHERE Conversation_id = %s", (cid,))

    return {"status": "ok"}

# =================================================================
# 12. ADMIN SQL ROUTES (from recov)
# =================================================================

@app.get("/reporting/table/{table_name}")
def get_table(table_name: str):
    allowed = {"User", "Conversation", "Turn", "Document", "Retrieval", "Vote"}

    if table_name not in allowed:
        raise HTTPException(status_code=400, detail="Invalid table")

    rows = execute_sql(f"SELECT * FROM {table_name} LIMIT 1000", fetch=True)

    return rows


@app.post("/reporting/delete_row")
async def delete_row(request: Request):
    data = await request.json()

    table = data.get("table")
    where = data.get("where") or {}
    force = bool(data.get("force", False))

    if not table or not where:
        raise HTTPException(status_code=400, detail="Missing table or where")

    if table == "Vote":
        delete_vote_safe(
            conversation_id=int(where["Conversation_id"]),
            turn_id=int(where["Turn_id"]),
            user_id=int(where["User_id"])
        )
        return {"status": "deleted"}

    if table == "Retrieval":
        delete_retrieval_link(
            conversation_id=int(where["Conversation_id"]),
            turn_id=int(where["Turn_id"]),
            document_id=int(where["Document_id"])
        )
        return {"status": "deleted"}

    if table == "Turn":
        delete_turn_full(
            conversation_id=int(where["Conversation_id"]),
            turn_id=int(where["Turn_id"])
        )
        return {"status": "deleted"}

    if table == "Conversation":
        delete_conversation_full(
            conversation_id=int(where["Conversation_id"])
        )
        return {"status": "deleted"}

    if table == "Document":
        delete_document_safe(
            document_id=int(where["Document_id"]),
            force=force
        )
        return {"status": "deleted"}

    if table == "User":
        delete_user_full(
            user_id=int(where["User_id"])
        )
        return {"status": "deleted"}

    raise HTTPException(status_code=400, detail="Unsupported table")


@app.post("/reporting/update_row")
async def update_row(request: Request):
    data = await request.json()

    table = data.get("table")
    updates = data.get("updates")
    where = data.get("where")

    allowed_tables = {"User", "Conversation", "Turn", "Document", "Retrieval", "Vote"}

    if table not in allowed_tables:
        raise HTTPException(status_code=400, detail="Invalid table")

    if not updates or not where:
        raise HTTPException(status_code=400, detail="Missing updates or where")

    set_clause = ", ".join([f"{k} = %s" for k in updates])
    where_clause = " AND ".join([f"{k} = %s" for k in where])

    params = list(updates.values()) + list(where.values())

    query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

    execute_sql(query, tuple(params))

    return {"status": "updated"}


@app.post("/api/recompute_ratings")
def recompute_ratings(session: Optional[str] = Cookie(default=None)):
    """
    Recompute Turn.rating from Vote table.
    rating = SUM(votes) for each turn
    """
    username = get_session_username(session)
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")

    user_id = username_to_user_id(username)

    execute_sql(
        """
        UPDATE Turn t
        JOIN Conversation c ON t.Conversation_id = c.Conversation_id
        LEFT JOIN (
            SELECT Turn_id, Conversation_id, SUM(vote) AS score
            FROM Vote
            GROUP BY Turn_id, Conversation_id
        ) v ON t.Turn_id = v.Turn_id AND t.Conversation_id = v.Conversation_id
        SET t.rating = COALESCE(v.score, 0)
        WHERE c.User_id = %s
        """,
        (user_id,)
    )

    return {"success": True}


@app.get("/reporting/conversation_ratings/{conversation_id}")
async def get_conversation_ratings(conversation_id: int):
    """
    Fetches ratings for all turns in a specific conversation.
    """
    query = """
        SELECT Turn_id, rating
        FROM Turn
        WHERE Conversation_id = %s
    """
    rows = execute_sql(query, (conversation_id,), fetch=True)
    return rows


# =================================================================
# 13. START SERVER
# =================================================================

if __name__ == "__main__":
    print("🚀 Starting GraphRAG Chat Server at http://localhost:8000/")
    print("React should be working...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
