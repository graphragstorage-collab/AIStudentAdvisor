
import os
import re
import textwrap
import threading
from typing import List, Tuple

import numpy as np
from pypdf import PdfReader
from openai import OpenAI
from utils.header_maker import create_header
from load import add_document_to_graphrag


# Initialize OpenAI client for relevance checking
openai_client = OpenAI()


# Approximate token controls (char/token ~= 4 for English text)
HEADER_SAMPLE_TOKENS = 9000
CHUNK_TARGET_TOKENS = 3200
CHUNK_OVERLAP_TOKENS = 250
MAX_LLM_COMPARE_CHARS = 1200
EMBEDDING_MAX_CHARS = 15000


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
    """Normalize noisy whitespace while preserving line/paragraph breaks."""
    if not text:
        return ""

    # Normalize newlines first.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove null bytes and trim only trailing spaces per line.
    text = text.replace("\x00", "")
    lines = [re.sub(r"[ \t]+$", "", line) for line in text.split("\n")]
    text = "\n".join(lines)

    # Keep paragraph structure but avoid huge blank runs.
    text = re.sub(r"\n{3,}", "\n\n", text)
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


def _approx_chars_for_tokens(tokens: int) -> int:
    return max(1, tokens * 4)


def _chunk_text_by_token_target(
    text: str,
    target_tokens: int = CHUNK_TARGET_TOKENS,
    overlap_tokens: int = CHUNK_OVERLAP_TOKENS,
) -> List[str]:
    """
    Chunk text to stay safely under embedding limits using a token estimate.
    Uses character windows with overlap to keep it fast and deterministic.
    """
    if not text:
        return []

    target_chars = _approx_chars_for_tokens(target_tokens)
    overlap_chars = min(_approx_chars_for_tokens(overlap_tokens), target_chars // 3)

    chunks: List[str] = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + target_chars, n)

        # Prefer ending at natural boundaries when possible.
        if end < n:
            last_newline = text.rfind("\n", start, end)
            last_space = text.rfind(" ", start, end)
            split_idx = max(last_newline, last_space)
            if split_idx > start + (target_chars // 2):
                end = split_idx

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break
        start = max(end - overlap_chars, start + 1)

    return chunks


def _split_chunk_to_fit_embedding_limit(chunk: str, header: str, max_chars: int = EMBEDDING_MAX_CHARS) -> List[str]:
    """
    Split an accepted chunk into one or more final documents where each
    header+chunk payload is guaranteed to be <= max_chars.
    """
    header = (header or "").strip()
    separator = "\n\n" if header else ""
    room_for_body = max_chars - len(header) - len(separator)

    if room_for_body <= 0:
        # Extremely defensive fallback.
        return [(header[:max_chars]).strip()]

    parts: List[str] = []
    start = 0
    n = len(chunk)
    while start < n:
        end = min(start + room_for_body, n)

        if end < n:
            last_newline = chunk.rfind("\n", start, end)
            last_space = chunk.rfind(" ", start, end)
            split_idx = max(last_newline, last_space)
            if split_idx > start + (room_for_body // 2):
                end = split_idx

        body = chunk[start:end].rstrip()
        if body:
            if header:
                parts.append(f"{header}{separator}{body}".rstrip())
            else:
                parts.append(body)

        if end >= n:
            break
        start = max(end, start + 1)

    return parts


def _choose_top_k(existing_doc_count: int) -> int:
    """Adaptive top-k for redundancy checks: enough context without token waste."""
    if existing_doc_count <= 0:
        return 0
    return min(8, max(3, int(np.sqrt(existing_doc_count))))


def _is_redundant_with_llm(chunk_text: str, candidate_docs: List[str]) -> Tuple[bool, str]:
    """
    Compare chunk with nearest existing docs and decide if it adds new information.
    """
    if not candidate_docs:
        return False, "No similar documents found"

    references = "\n\n".join(
        f"Doc {i+1}:\n{doc[:MAX_LLM_COMPARE_CHARS]}"
        for i, doc in enumerate(candidate_docs)
    )

    prompt = textwrap.dedent(
        f"""
        You are checking whether a new academic text chunk is redundant versus existing indexed chunks.

        Mark as REDUNDANT only if the new chunk is mostly the same information already covered by the references.
        If it adds meaningful new details (new policies, dates, constraints, examples, requirements, procedures, or context), mark as NOVEL.

        New chunk:
        ---
        {chunk_text[:2200]}
        ---

        Reference chunks:
        ---
        {references}
        ---

        Respond with exactly one line:
        REDUNDANT: <brief reason>
        or
        NOVEL: <brief reason>
        """
    )

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.0,
        )
        verdict = (completion.choices[0].message.content or "").strip()
        if verdict.startswith("REDUNDANT"):
            return True, verdict.split(":", 1)[1].strip() if ":" in verdict else "Redundant"
        return False, verdict.split(":", 1)[1].strip() if ":" in verdict else "Novel"
    except Exception as e:
        # If LLM check fails, avoid dropping potentially useful data.
        return False, f"LLM redundancy check failed: {e}"


def _process_in_background(raw_text: str, username: str, filename: str, graph_rag_instance, timestamp: int):
    """
    Background task: chunk, create headers, save, and add documents to GraphRAG.
    Runs in a separate thread to avoid blocking the upload response.
    """
    try:
        print(f"🔄 Background processing started for {username}/{filename}")
        
        save_dir = "./user_uploads"
        name = os.path.splitext(filename)[0]
        
        header_seed_chars = _approx_chars_for_tokens(HEADER_SAMPLE_TOKENS)
        header = create_header(raw_text[:header_seed_chars]).strip()

        chunks = _chunk_text_by_token_target(raw_text)
        if not chunks:
            print(f"⚠️  No chunks generated for {username}/{filename}")
            return

        vs = graph_rag_instance.vector_store
        existing_count = len(vs.documents)
        top_k = _choose_top_k(existing_count)

        # Batch-embed candidate chunks once for speed.
        chunk_embeddings = graph_rag_instance.embedding_model.embed_documents(chunks)
        if chunk_embeddings.shape[0] == 0:
            print(f"⚠️  Could not embed chunks for {username}/{filename}")
            return

        # Vector-level quick dedupe thresholds.
        near_duplicate_threshold = 0.92
        candidate_llm_threshold = 0.72

        accepted_chunks: List[str] = []
        accepted_embeddings: List[np.ndarray] = []

        use_existing_index = vs.index is not None and existing_count > 0 and top_k > 0

        for i, (chunk, emb) in enumerate(zip(chunks, chunk_embeddings), start=1):
            should_skip = False

            # In-upload duplicate protection (cheap cosine with accepted embeddings).
            if accepted_embeddings:
                intra_scores = [float(np.dot(emb, prev_emb)) for prev_emb in accepted_embeddings]
                if max(intra_scores) >= near_duplicate_threshold:
                    should_skip = True

            if should_skip:
                continue

            # Compare against existing corpus using FAISS top-k.
            top_docs_for_llm: List[str] = []
            if use_existing_index:
                q = np.array([emb], dtype="float32")
                scores, idxs = vs.index.search(q, top_k)
                neighbor_scores = [float(s) for s in scores[0] if s > -1]
                neighbor_idxs = [int(j) for j in idxs[0] if j >= 0]

                if neighbor_scores and max(neighbor_scores) >= near_duplicate_threshold:
                    continue

                if neighbor_scores and max(neighbor_scores) >= candidate_llm_threshold:
                    for doc_idx in neighbor_idxs:
                        doc = vs.documents[doc_idx]
                        top_docs_for_llm.append(doc.page_content)

            # LLM redundancy check only when semantic neighbors are somewhat close.
            if top_docs_for_llm:
                redundant, reason = _is_redundant_with_llm(chunk, top_docs_for_llm)
                if redundant:
                    print(f"⏭️  Skipping redundant chunk {i}: {reason}")
                    continue

            accepted_chunks.append(chunk)
            accepted_embeddings.append(emb)

        final_docs: List[str] = []
        for chunk in accepted_chunks:
            final_docs.extend(_split_chunk_to_fit_embedding_limit(chunk, header, EMBEDDING_MAX_CHARS))

        added = 0
        for i, final_text in enumerate(final_docs):
            if len(final_docs) == 1:
                out_name = f"{username}_{timestamp}_{name}.txt"
            else:
                out_name = f"{username}_{timestamp}_{name}_chunk{i+1}.txt"

            out_path = os.path.join(save_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(final_text)

            add_document_to_graphrag(graph_rag_instance, out_path)
            added += 1

        print(
            f"✅ Background processing complete for {username}/{filename} "
            f"(total_chunks={len(chunks)}, added={added}, skipped={len(chunks) - added})"
        )
        
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
