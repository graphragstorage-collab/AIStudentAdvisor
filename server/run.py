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
from typing import Optional   # <<< FIXED

from load import *  # GraphRAG, translate_text_multilingual

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


# =================================================================
# 1. LOAD GRAPH-RAG
# =================================================================

print("Loading GraphRAG…")
# graph_rag = GraphRAG()
# graph_rag.load_from_disk(
#     vector_store_path="vector_store.json",
#     graph_path="knowledge_graph.json"
# )

# Load new nodes (unchanged)
graph_rag2 = GraphRAG(initialize_empty=False)
uploads = os.listdir("./user_uploads")
for upload in uploads:
    if upload.endswith(".txt"):
        add_document_to_graphrag(graph_rag2, os.path.join("./user_uploads", upload))
        # add_document_to_graphrag(graph_rag, os.path.join("./user_uploads", upload))

print("✓ GraphRAG Loaded.")


# =================================================================
# 2. APP SETUP (FASTAPI + REACT)
# =================================================================

app = FastAPI()

if os.path.exists(REACT_BUILD_DIR):
    app.mount("/static", StaticFiles(directory=os.path.join(REACT_BUILD_DIR, "static")), name="static")
    print(f"Serving React from {REACT_BUILD_DIR}")
else:
    print(f"React build directory not found at {REACT_BUILD_DIR}. Run 'npm run build'") # shouldn't happen unless build dir doesn't exist


#app.mount("/static", StaticFiles(directory="/root/GraphPackage/assets"), name="static")

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
        path="/",      # MUST match original path
    )


def get_session_username(session_cookie: Optional[str]):  # <<< FIXED
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


# add this to sql database later? have to account for multiple histories
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
# 4.  STATUS (LOGIN PAGE IS IN WEBSITE/SRC/COMPONENTS)
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

    # Extract just the current question (remove history and separator)
    # if "\n\n==============================\ncurrent question: " in decoded_query:
    #     current_question = "user: " + decoded_query.split("\n\n==============================\ncurrent question: ")[-1]
    # else:
    #     current_question = decoded_query  # Fallback if format doesn't match

   
     
    current_question = decoded_query  # Fallback if format doesn't match
    


    try:
        answer = graph_rag2.query(current_question)  # Use current_question instead
        # answer = graph_rag.query(current_question)
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
    """
    Upload and process a file: extract text, check relevance with GPT,
    chunk it, save it, and add to GraphRAG knowledge base.
    """
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

# =================================================================
# 12. START SERVER
# =================================================================

if __name__ == "__main__":
    print("🚀 Starting GraphRAG Chat Server at http://localhost:8000/")
    print("React should be working...")
    uvicorn.run(app, host="0.0.0.0", port=8000)


