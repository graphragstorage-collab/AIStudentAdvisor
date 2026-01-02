import threading
import textwrap
from typing import List
from openai import OpenAI   # <-- switched to OpenAI

# Initialize OpenAI client
openai_client = OpenAI()    # <-- new client


# --------------------------------------------
# 1. LLM Snippet Extraction Function
# --------------------------------------------
def create_snippet(query: str, text: str, llm_client=openai_client,
                   model="gpt-4o-mini", max_tokens=15000):
    """
    Produces a short, query-relevant snippet similar to a search-engine result.
    This does NOT summarize. This extracts the most relevant passage directly
    from the original document text.
    """

    # prompt = f"""
    # You are an expert RAG assistant.

    # TASK:
    # Given a document and a QUERY, extract the most relevant passage EXACTLY as it appears
    # in the text. Do NOT summarize, do NOT paraphrase. Just pull the most relevant
    # sentences or fragments  directly from the document.


    # STRICT RULES:
    # - Do NOT write explanations.
    # - Do NOT give commentary.
    # - Do NOT create summaries.
    # - Only output a DIRECT EXCERPT from the document.

    # ADVICE:
    # - Focus on relevance to the QUERY.
    # - If the answer to the question is explicitly in the text, extract that part. 
    # - If a part does not contribute to the answer straight up answer with nothing "".


    prompt = f"""
    You are an expert RAG assistant.

    TASK:
    Given a document and a QUERY (with the user's chat HISTORY), WITHOUT CHANGING THE TEXT DETERMINE IF IT IS RELEVANT TO THE QUERY.


    STRICT RULES:
    - Do NOT write explanations.
    - Do NOT give commentary.
    - Do NOT create summaries.
    - Only say YES or NO.

    ADVICE:
    - Focus on relevance to the QUERY.
    - If the answer to the question is explicitly in the text, answer YES.
    - If a part does not contribute to the answer straight up answer with nothing "".
    - If the document is not relevant to the query, answer NO.
    - If someone asks about a class and it is not exactly a match (CS 811 vs CS 81100) you should still consider it relevant.
    - CONSIDER THE CHAT HISTORY WHEN MAKING YOUR DECISION.
    

    --- History + QUERY ---
    {query}

    --- DOCUMENT ---
    {text}
    """

    completion = llm_client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=max_tokens
    )
    

    answer = completion.output_text.strip()
    return answer


# --------------------------------------------
# 2. Per-Thread Worker
# --------------------------------------------
def process_single_doc(index, query, text, llm_client, model, output_list):
    """
    Executed inside each thread.
    Writes its snippet result into output_list[index].
    """
    snippet = create_snippet(query, text, llm_client, model=model)

    if snippet.upper() == "NO":
        snippet = "NO"

    else:
        output_list[index] = text


# --------------------------------------------
# 3. Thread Manager — generates snippets in parallel
# --------------------------------------------
def generate_snippets_threaded(query: str,
                               expanded_contexts: List[str],
                               llm_client=openai_client,
                               model="gpt-4o-mini") -> List[str]:
    """
    Creates one thread per document in expanded_contexts and
    returns snippets in the exact same order as the input.
    """

    num_docs = len(expanded_contexts)

    # Pre-allocate output list to preserve ordering
    snippets = [None] * num_docs
    threads = []

    for i, doc_text in enumerate(expanded_contexts):
        t = threading.Thread(
            target=process_single_doc,
            args=(i, query, doc_text, llm_client, model, snippets)
        )
        threads.append(t)
        t.start()

    # Wait for all threads to finish
    for t in threads:
        t.join()

    return snippets
