"""
Upload handler - processes and validates uploaded files
"""
import os
import re
import textwrap
import threading
from typing import Tuple
from pypdf import PdfReader
from openai import OpenAI
from utils.transform import transform_raw_text
from utils.header_maker import create_header
from load import add_document_to_graphrag


# Initialize OpenAI client for relevance checking
openai_client = OpenAI()


def check_document_relevance(text: str, max_sample_chars: int = 2000) -> Tuple[bool, str]:
    """
    Uses GPT to check if a document is relevant/appropriate for an academic advice system.
    Permissive mode: accepts any academic or educational content.
    
    Args:
        text: The document text to check
        max_sample_chars: Max characters to send to GPT for efficiency
        
    Returns:
        (is_relevant: bool, reason: str)
    """
    # Take a sample if text is too long
    sample = text[:max_sample_chars]
    
    prompt = textwrap.dedent(f"""
    You are a document relevance checker for an academic advising system.
    
    Determine if the following document is ACADEMIC/EDUCATIONAL in nature.
    
    ACCEPT documents that are: course syllabi, schedules, degree requirements, academic policies,
    department info, academic planning guides, course descriptions, grading policies, graduation requirements,
    study guides, lecture notes, practice problems, homework assignments, exam materials, textbook excerpts,
    research papers, academic proposals, learning materials, course readings, or ANY other educational content
    related to student learning and academic planning.
    
    REJECT ONLY if the document is: spam, advertising, promotional material, completely unrelated to academics,
    or clearly malicious.
    
    When in doubt, ACCEPT academic-related content.
    
    Document sample:
    ---
    {sample}
    ---
    
    RESPOND WITH EXACTLY ONE LINE in this format:
    RELEVANT or NOT_RELEVANT: [brief reason max 50 words]
    """)
    
    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.3
        )
        
        response = completion.choices[0].message.content.strip()
        
        # Parse the response
        if response.startswith("RELEVANT"):
            return True, response.split(":", 1)[1].strip() if ":" in response else "Document is relevant"
        else:
            return False, response.split(":", 1)[1].strip() if ":" in response else "Document is not relevant"
            
    except Exception as e:
        print(f"⚠️  Error checking relevance with GPT: {e}")
        # If GPT fails, default to allowing upload (don't block users)
        return True, "Relevance check failed, but upload allowed"


def clean_text(text: str) -> str:
    """Remove extra whitespace from text."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def pdf_to_text(path: str) -> str:
    """Extract text from PDF file."""
    reader = PdfReader(path)
    pages = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages.append(page_text)
    return "\n".join(pages)


def chunk_text(text: str, max_chars: int = 8000) -> list:
    """Split text into chunks and add headers."""
    header = create_header(text[0:max_chars]) + "\n"
    return [header + text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def _process_in_background(raw_text: str, username: str, filename: str, graph_rag_instance, timestamp: int):
    """
    Background task: chunk, create headers, save, and add documents to GraphRAG.
    Runs in a separate thread to avoid blocking the upload response.
    """
    try:
        print(f"🔄 Background processing started for {username}/{filename}")
        
        save_dir = "./user_uploads"
        name = os.path.splitext(filename)[0]
        
        chunks = chunk_text(raw_text)
        
        for i, chunk in enumerate(chunks):
            if len(chunks) == 1:
                out_name = f"{username}_{timestamp}_{name}.txt"
            else:
                out_name = f"{username}_{timestamp}_{name}_chunk{i+1}.txt"

            out_path = os.path.join(save_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                chunk = transform_raw_text(chunk)
                f.write(chunk)
            
            add_document_to_graphrag(graph_rag_instance, out_path)
        
        print(f"✅ Background processing complete for {username}/{filename} ({len(chunks)} chunks)")
        
    except Exception as e:
        print(f"❌ Error in background processing: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()


async def process_upload(
    file,
    username: str,
    graph_rag_instance
) -> Tuple[bool, str]:
    """
    Process an uploaded file: validate, check relevance, then return immediately.
    Heavy processing (GraphRAG, header creation) happens in background thread.
    
    Args:
        file: FastAPI UploadFile object
        username: Username of uploader
        graph_rag_instance: GraphRAG instance to add documents to
        
    Returns:
        (success: bool, message: str)
    """
    
    # File validation
    filename = os.path.basename(file.filename)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    if ext not in {".txt", ".pdf"}:
        return False, "❌ Only .txt or .pdf files are allowed"

    save_dir = "./user_uploads"
    os.makedirs(save_dir, exist_ok=True)

    timestamp = int(__import__("time").time())

    # Save temp upload
    temp_path = os.path.join(save_dir, f"_tmp_{username}_{timestamp}{ext}")

    with open(temp_path, "wb") as f:
        f.write(await file.read())

    # Extract text
    try:
        if ext == ".txt":
            with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read()
        else:  # PDF
            raw_text = pdf_to_text(temp_path)
    except Exception as e:
        os.remove(temp_path)
        return False, f"❌ Error reading file: {str(e)}"

    os.remove(temp_path)

    raw_text = clean_text(raw_text)
    if not raw_text:
        return False, "❌ No readable text found in file"

    # Check document relevance with GPT (synchronous - must complete before accepting)
    is_relevant, relevance_reason = check_document_relevance(raw_text)
    
    if not is_relevant:
        return False, f"❌ Document not suitable for academic planning system:\n{relevance_reason}"

    # ✅ RETURN IMMEDIATELY - start heavy processing in background
    # Launch background thread for chunking, header creation, and GraphRAG processing
    background_thread = threading.Thread(
        target=_process_in_background,
        args=(raw_text, username, filename, graph_rag_instance, timestamp),
        daemon=True
    )
    background_thread.start()
    
    return True, f"✅ File uploaded successfully! Processing in background..."
