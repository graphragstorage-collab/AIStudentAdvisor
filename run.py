import uvicorn
from fastapi import FastAPI, Response, Request, Depends, Cookie, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
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

from pypdf import PdfReader
import re


# =================================================================
# 0. INITIAL SETUP
# =================================================================

ACCOUNTS_DIR = "./accounts"
CONVO_DIR = "./conversations"

os.makedirs(ACCOUNTS_DIR, exist_ok=True)
os.makedirs(CONVO_DIR, exist_ok=True)

COOKIE_SIGNER = Signer("SUPER_SECRET_KEY_CHANGE_ME")


# =================================================================
# 1. LOAD GRAPH-RAG
# =================================================================

print("Loading GraphRAG…")
graph_rag = GraphRAG()
graph_rag.load_from_disk(
    vector_store_path="vector_store.json",
    graph_path="knowledge_graph.json"
)

# Load new nodes (unchanged)
uploads = os.listdir("./user_uploads")
for upload in uploads:
    if upload.endswith(".txt"):
        add_document_to_graphrag(graph_rag, os.path.join("./user_uploads", upload))

print("✓ GraphRAG Loaded.")


# =================================================================
# 2. FASTAPI APP SETUP
# =================================================================

app = FastAPI()

app.mount("/static", StaticFiles(directory="/root/GraphPackage/assets"), name="static")

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
    response.set_cookie("session", signed, httponly=True, max_age=86400*7)

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


def append_conversation(username: str, history_text: str):
    path = f"{CONVO_DIR}/{username}_history.txt"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a") as f:
        f.write("\n===============================\n")
        f.write(now + "\n")
        f.write(history_text + "\n")


# =================================================================
# 4. LOGIN PAGE (GET)
# =================================================================

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, session: Optional[str] = Cookie(default=None)):
    return RedirectResponse("/login")

@app.get("/logout")
async def logout_page():
    response = RedirectResponse("/login", status_code=302)
    clear_session(response)
    return response


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, session: Optional[str] = Cookie(default=None)):   # <<< FIXED
    # Auto-login if 24-hour IP rule passes
    username = get_session_username(session)
    if username:
        acc = read_account(username)
        if acc:
            stored_pw, stored_ip, last_ts = acc
            client_ip = get_client_ip(request)
            if stored_ip == client_ip and (time.time() - last_ts) < 86400:
                return RedirectResponse("/chat")

    # Show login page
    html = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Purdue Login</title>
    <style>
        body {
            margin: 0; background: #fdfdfd;
            font-family: Arial, sans-serif;
            display: flex; align-items: center; justify-content: center;
            height: 100vh;
        }
        .container {
            width: 90%; max-width: 400px;
            padding: 30px;
            border-radius: 12px;
            background: white;
            border: 2px solid #DAA520;
            box-shadow: 0 0 10px rgba(0,0,0,0.15);
        }
        h2 {
            margin-top: 0; color: black;
            text-align: center;
        }
        input {
            width: 100%; padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            border: 1px solid #ccc;
        }
        button {
            width: 100%;
            padding: 14px;
            background: black;
            color: gold;
            border-radius: 8px;
            cursor: pointer;
            border: none;
            font-weight: bold;
        }
        button:hover { opacity: 0.8; }
        .footer-link {
            margin-top: 15px; text-align: center;
        }
        a { color: #C2912A; text-decoration: none; }
    </style>
</head>
<body>

<div class="container">
    <h2>Purdue Login</h2>
    <form method="POST" action="/login">
        <input name="username" placeholder="Username" required />
        <input name="password" placeholder="Password" required type="password" />
        <button type="submit">Login</button>
    </form>
    <div class="footer-link">
        <a href="/signup">Create an account</a>
    </div>
</div>

</body>
</html>
"""
    return HTMLResponse(html)


# =================================================================
# 5. LOGIN SUBMIT (POST)
# =================================================================

@app.post("/login")
async def login_post(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    client_ip = get_client_ip(request)

    acc = read_account(username)
    if not acc:
        return HTMLResponse("Invalid username. <a href='/login'>Try again</a>")

    stored_pw, stored_ip, last_ts = acc

    if password != stored_pw:
        return HTMLResponse("Incorrect password. <a href='/login'>Try again</a>")

    update_account_login(username, client_ip)

    response = RedirectResponse("/chat", status_code=302)
    set_session(response, username)
    return response


# =================================================================
# 6. SIGNUP
# =================================================================

@app.get("/signup", response_class=HTMLResponse)
async def signup_page():
    html = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Create Account</title>
    <style>
        body {
            margin: 0; background: #fafafa;
            font-family: Arial;
            display: flex; align-items: center; justify-content: center;
            height: 100vh;
        }
        .box {
            width: 90%; max-width: 420px;
            padding: 30px;
            border-radius: 12px;
            border: 2px solid #DAA520;
            background: white;
            box-shadow: 0 0 10px rgba(0,0,0,0.15);
        }
        input { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: 1px solid #ccc; }
        button {
            width: 100%; padding: 14px; border-radius: 8px;
            background: #000; color: gold; border: none; cursor: pointer;
        }
        button:hover { opacity: 0.85; }
    </style>
</head>
<body>
<div class="box">
    <h2 style="text-align:center;">Create Account</h2>
    <form method="POST" action="/signup">
        <input name="username" placeholder="Username" required />
        <input name="password" placeholder="Password (no commas)" required type="password" />
        <input name="confirm" placeholder="Confirm Password" required type="password" />
        <button type="submit">Register</button>
    </form>
</div>
</body>
</html>
"""
    return HTMLResponse(html)


@app.post("/signup")
async def signup_post(request: Request):
    form = await request.form()
    username = form.get("username", "")
    password = form.get("password", "")
    confirm = form.get("confirm", "")

    if "," in password:
        return HTMLResponse("Password cannot contain commas.")

    if password != confirm:
        return HTMLResponse("Passwords do not match.")

    acc_path = f"{ACCOUNTS_DIR}/{username}.txt"
    if os.path.exists(acc_path):
        return HTMLResponse("Username already exists.")

    with open(acc_path, "w") as f:
        f.write(f"{password},none,0\n")

    return RedirectResponse("/login", status_code=302)


# =================================================================
# 7. CHAT PAGE
# =================================================================

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(session: Optional[str] = Cookie(default=None)):   # <<< FIXED
    username = get_session_username(session)
    if not username:
        return RedirectResponse("/login")
    if read_account(username) is None:
        return RedirectResponse("/login")

    html = r"""
<!DOCTYPE html>
<html>
<head>
    <title>Purdue GraphRAG Chat</title>
    <link rel="icon" href="/static/favicon.ico" />

    <style>
        body {
            margin: 0;
            background: #f5f5f5;
            font-family: Arial, sans-serif;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }
        #topbar {
            position: fixed;
            top: 10px;
            right: 15px;
            z-index: 1000;
        }
       #upload-btn {
           position: fixed;
           top: 40px;
           right: 15px;
           z-index: 1000;
           padding: 6px 14px;
           background: #000;
           color: gold;
           border-radius: 8px;
           border: 1px solid #DAA520;
          cursor: pointer;
          font-weight: bold;
       }

        #logout-btn {
            padding: 6px 14px;
            background: #000;
            color: gold;
            text-decoration: none;
            border-radius: 8px;
            border: 1px solid #DAA520;
            font-weight: bold;
            font-size: 14px;
        }

        #logout-btn:hover {
            background: #333;
        }
        #chatbox {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: white;
            border-bottom: 2px solid #DAA520;
        }
        .msg-user {
            background: #C8E6C9;
            margin: 10px 0;
            padding: 10px 14px;
            border-radius: 8px;
            width: fit-content;
            max-width: 80%;
        }
        .msg-bot {
            background: #eee;
            margin: 10px 0;
            padding: 10px 14px;
            border-radius: 8px;
            width: fit-content;
            max-width: 80%;
            white-space: pre-wrap;
        }
        #translator-section {
            padding: 10px;
            border-bottom: 2px solid #DAA520;
            background: #fff;
        }
        #input-section {
            padding: 8px;
            background: #fff;
            border-top: 2px solid #DAA520;
        }
        #promptbar {
            width: 100%;
            padding: 12px;
            border-radius: 12px;
            border: 2px solid #DAA520;
            font-size: 16px;
        }
        button.lang-btn {
            padding: 7px 14px;
            background: #f2e1a3;
            border-radius: 6px;
            border: 1px solid #DAA520;
            cursor: pointer;
        }
        button.lang-btn.active {
            background: #000;
            color: gold;
        }
        @media (max-width: 600px) {
            #promptbar { font-size: 15px; }
        }
    </style>
</head>

<body>

<div id="topbar">
    <a href="/logout" id="logout-btn">Logout</a>
    <button id="upload-btn">Upload File</button>
    <input type="file" id="file-input" accept=".txt" hidden />
</div>

<div id="chatbox">
    <div class="msg-bot">Welcome! Select a language below, then ask a question.</div>
</div>

<div id="translator-section">
    <button class="lang-btn active" data-lang="none">Original</button>
    <button class="lang-btn" data-lang="spanish">Spanish</button>
    <button class="lang-btn" data-lang="french">French</button>
    <button class="lang-btn" data-lang="german">German</button>
    <button class="lang-btn" data-lang="japanese">Japanese</button>
    <button class="lang-btn" data-lang="chinese">Chinese</button>
</div>

<div id="input-section">
    <input id="promptbar" placeholder="Not satisfied with results? Contribute and upload files to our database! Study guides, how to guides, anything!" />
</div>

<script>
    const chatbox = document.getElementById("chatbox");
    const bar = document.getElementById("promptbar");

    let currentLanguage = "none";
    let history = [];

    document.querySelectorAll(".lang-btn").forEach(btn=>{
        btn.onclick = ()=>{
            document.querySelectorAll(".lang-btn").forEach(b=>b.classList.remove("active"));
            btn.classList.add("active");
            currentLanguage = btn.dataset.lang;
        };
    });

    function addMessage(msg, sender){
        let div = document.createElement("div");
        div.className = sender === "user" ? "msg-user" : "msg-bot";
        div.innerText = msg;
        chatbox.appendChild(div);
        chatbox.scrollTop = chatbox.scrollHeight;
        history.push({role: sender === "user" ? "user" : "model", content: msg});
    }

    function addThinking(){
        let d = document.createElement("div");
        d.className = "msg-bot";
        d.innerText = "Thinking...";
        chatbox.appendChild(d);
        chatbox.scrollTop = chatbox.scrollHeight;
        return d;
    }

    function buildPayload(question){
        return history.map(h => `${h.role}: ${h.content}`).join("\n\n") +
               "\n\n==============================\ncurrent question: " + question;
    }

    bar.addEventListener("keydown", async e=>{
        if(e.key=="Enter"){
            let text = bar.value.trim();
            if(!text) return;
            addMessage(text, "user");  // ← This adds to history
            bar.value = "";
            let thinking = addThinking();
            let payload = buildPayload(text);

            let res = await fetch("/prompt", {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({query: payload, lang: currentLanguage})
            });

            let answer = await res.text();
            thinking.innerText = answer;
            history.push({role:"model", content:answer});
        }
    });

    bar.focus();

    // File upload handling
    const uploadBtn = document.getElementById("upload-btn");
    const fileInput = document.getElementById("file-input");

    uploadBtn.onclick = () => {
        fileInput.click(); // open file explorer
    };

    fileInput.onchange = async () => {
        const file = fileInput.files[0];
        if (!file) return;

        if (!(file.name.endsWith(".txt") || file.name.endsWith(".pdf"))) {
            alert("Only .txt and .pdf files are allowed.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        const res = await fetch("/upload", {
            method: "POST",
            body: formData
        });

        const msg = await res.text();
        alert(msg);

        fileInput.value = ""; // reset input
    };
    
</script>

</body>
</html>
"""
    return HTMLResponse(html)


# =================================================================
# 8. MODEL INTERACTION ENDPOINT
# =================================================================

class PromptInput(BaseModel):
    query: str
    lang: str = "none"


@app.post("/prompt", response_class=PlainTextResponse)
async def prompt(
    request: Request,
    request_data: PromptInput,
    session: Optional[str] = Cookie(default=None)
):
    username = get_session_username(session)
    if not username:
        return "Not logged in."

    decoded_query = request_data.query
    target_lang = (request_data.lang or "none").lower()

    print("\n======== RECEIVED QUERY ========")
    print(decoded_query[:500], "...")
    print("Language:", target_lang)
    print("================================\n")

    # Extract just the current question (remove history and separator)
    if "\n\n==============================\ncurrent question: " in decoded_query:
        current_question = "user: " + decoded_query.split("\n\n==============================\ncurrent question: ")[-1]
    else:
        current_question = decoded_query  # Fallback if format doesn't match

    try:
        answer = graph_rag.query(current_question)  # Use current_question instead

        if target_lang == "none":
            append_conversation(username, current_question + "\n\nmodel: " + answer)
            return answer

        translated = translate_text_multilingual(
            answer, target_language=target_lang.capitalize()
        )
        append_conversation(
            username,
            current_question + f"\n\n---\n\n[Translated to {target_lang}]:\n\n" + translated
        )
        return translated

    except Exception as e:
        return f"Server error: TRY AGAIN LATER"


# =================================================================
# 9. HEALTH CHECK
# =================================================================

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "GraphRAG Chat Server"}


# =================================================================
# 9. FILE UPLOAD ENDPOINT
@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    session: Optional[str] = Cookie(default=None),
):
    # -----------------------------
    # Auth
    # -----------------------------
    username = get_session_username(session)
    if not username:
        raise HTTPException(status_code=401, detail="Not logged in")

    # -----------------------------
    # Internal helpers
    # -----------------------------
    MAX_CHARS = 8000

    def clean_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def chunk_text(text: str):
        return [text[i:i + MAX_CHARS] for i in range(0, len(text), MAX_CHARS)]

    def pdf_to_text(path: str) -> str:
        reader = PdfReader(path)
        pages = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
        return "\n".join(pages)

    # -----------------------------
    # File validation
    # -----------------------------
    filename = os.path.basename(file.filename)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in {".txt", ".pdf"}:
        raise HTTPException(status_code=400, detail="Only .txt or .pdf allowed")

    save_dir = "./user_uploads"
    os.makedirs(save_dir, exist_ok=True)

    timestamp = int(time.time())

    # -----------------------------
    # Save temp upload
    # -----------------------------
    temp_path = os.path.join(
        save_dir, f"_tmp_{username}_{timestamp}{ext}"
    )

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # -----------------------------
    # Extract text
    # -----------------------------
    if ext == ".txt":
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
    else:  # PDF
        raw_text = pdf_to_text(temp_path)

    os.remove(temp_path)

    raw_text = clean_text(raw_text)
    if not raw_text:
        raise HTTPException(status_code=400, detail="No readable text found")

    # -----------------------------
    # Chunk + save
    # -----------------------------
    chunks = chunk_text(raw_text)
    saved_files = []

    for i, chunk in enumerate(chunks):
        if len(chunks) == 1:
            out_name = f"{username}_{timestamp}_{name}.txt"
        else:
            out_name = f"{username}_{timestamp}_{name}_chunk{i+1}.txt"

        out_path = os.path.join(save_dir, out_name)
        with open(out_path, "w", encoding="utf-8") as f:
            chunk = transform_raw_text(chunk)
            f.write(chunk)

        saved_files.append(out_name)

    # -----------------------------
    # Response
    # -----------------------------
    return {
        "File uploaded successfully."
    }

# =================================================================
# 10. START SERVER
# =================================================================

if __name__ == "__main__":
    print("🚀 Starting GraphRAG Chat Server at http://localhost:8000/")
    uvicorn.run(app, host="0.0.0.0", port=8000)
