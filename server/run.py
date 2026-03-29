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

    try:
        answer = graph_rag2.query(current_question)
        print("Model answer")
        if target_lang == "none":
            print("No translation requested, returning original answer.")
            append_conversation(username, current_question + "\n\nmodel: " + answer)
            print("Conversation appended without translation.")
            return {"answer": answer}

        print("Translating answer to", target_lang)
        translated = translate_text_multilingual(
            answer, target_language=target_lang.capitalize()
        )
        print("Translation complete")

        append_conversation(
            username,
            current_question + f"\n\n---\n\n[Translated to {target_lang}]:\n\n" + translated
        )
        print("Conversation appended")
        return {"answer": translated}

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


# =================================================================
# 11. REACT FRONTEND
# =================================================================

@app.get("/", response_class=HTMLResponse)
@app.get("/login", response_class=HTMLResponse)
@app.get("/signup", response_class=HTMLResponse)
@app.get("/chat", response_class=HTMLResponse)
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
# 12. START SERVER
# =================================================================

if __name__ == "__main__":
    print("🚀 Starting GraphRAG Chat Server at http://localhost:8000/")
    print("React should be working...")
    uvicorn.run(app, host="0.0.0.0", port=8000)