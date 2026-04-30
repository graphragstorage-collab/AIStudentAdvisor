import threading
import textwrap
from typing import List
from openai import OpenAI   # <-- switched to OpenAI
from cerebras.cloud.sdk import Cerebras
import json
# Initialize OpenAI client
api_keys = [
    "csk-tn98d46prf8mvhwvyy8d5y48ncck2w2xc6336y9dxvcd4eyt",
    "csk-f43h2hjymmty4489n22n5966ty6336fvw59m4m4d8rr499xt",
    "csk-d8wcjrn639wftfcp8858yr9wtvrw8y5dm4mkfcp52xh6rnem",
    "csk-twcjfk4mwmtm3hnkd6pn6n282whrvte88c9pcrct69tw38m6",
    "csk-mppyvph8kxx9n6dxxcmhrnxjwkveyxjfrrm23eyyyxfjmfy4",
    "csk-n9r5k3h62pcjwn5393k4wct8y65enw6pkypmwwrj4cm8j23n",
    "csk-2j548nk43nw2ftr6368yxekdtp6rfw355c45832etttc8522",
    "csk-tpwdj98pewtepj4c5v3d8eejnx8t3rrdj8yh54f2vd8vprk6",
    "csk-mknjvx8xxpm2v4nryhe6v963cwxekdmm3dd8ftydtvjhnyn8",
    "csk-5ht9eh59wd289pycrk9vvfdcffxxrpmyjx9e29hyk3jfjjcx",
    "csk-fvj93vywv283cmt69mvyhmywyymrpd2fndhm9x3djmh8mc2h",
    "csk-m49vrdt4mfc5n3mxk4496wddevdrrx39erxyf3d3cv58jytm",
    "csk-839ek535y939jcjm6fynj8nd3cj369xpcet2rfdtrv9xpxw6",
    "csk-ccevmrkdpdhjn23c3crmmye8tejj6vpy5jf8dcrvthe53y8r",
    "csk-xyv3j8wej9mxtnf32mvrxtxrwt3wt3nj8jm68h5r8cvkxn63",

]


openai_client = OpenAI()    # <-- new client

llm_clients = []
for key in api_keys:
    llm_client = Cerebras(api_key=key)
    llm_clients.append(llm_client)

# --------------------------------------------
# 1. LLM Snippet Extraction Function
# --------------------------------------------
def create_snippet(query: str, text: str, llm_client=llm_client,
                   model="gpt-5.4", max_tokens=15000):
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


    # prompt = f"""
    # You are an expert RAG recall-oriented relevance classifier.

    # TASK:
    # Given a DOCUMENT and a QUERY (considering the user's CHAT HISTORY),
    # decide whether REMOVING this document would make it harder
    # to answer the query well.

    # PRIMARY GOAL:
    # Maximize recall, but only keep documents that meaningfully help
    # with the user's specific task or intent.

    # STRICT OUTPUT FORMAT:
    # - Respond with YES or NO
    # - Give a brief justification (1 sentence preferred, max 2)
    # - End with #YES or #NO

    # DECISION RULES:
    # Answer YES if the document:
    # - Directly or partially answers the query
    # - Provides background, definitions, or constraints needed to act
    # - Helps with comparison, planning, pacing, or preparation
    # - Covers one of multiple topics/classes mentioned in the query
    # - Is supportive context a human expert would actually use

    # Answer NO only if:
    # - The document is clearly unrelated
    # - It does not help accomplish the user's task
    # - A knowledgeable human would confidently discard it

    # TASK FIT CONSTRAINT:
    # If the query is procedural, temporal, or recovery-oriented
    # (e.g., missing a week, catching up, what to study next),
    # answer YES only if the document provides:
    # - Week-by-week structure
    # - Specific topics, lectures, or assignments
    # - Actionable or concrete guidance

    # Purely high-level or static documents (e.g., course catalogs,
    # degree requirements, program overviews) should be NO for such
    # queries unless they include task-level or week-level detail.

    # CRITICAL CONSTRAINTS:
    # - Do NOT reject a document solely because it does not directly answer the query.
    # - Do NOT justify NO using absence-of-information arguments alone.
    # - Do NOT keep documents that are only tangentially academic
    # but do not help with the user's stated task.

    # UNCERTAINTY RULE:
    # - When uncertain, choose YES only if the document could reasonably
    # help the user take action.
    # - Otherwise, choose NO.

    # CONSIDER:
    # - The full chat history
    # - The user's underlying intent
    # - Whether the document helps the user do something, not just understand something

    # --- QUERY ---
    # {query}

    # --- DOCUMENT ---
    # {text}
    # """

    prompt = f"""
    You are a relevance filter for a RAG system.

    TASK:
    Given a QUERY and a DOCUMENT, decide if the document contains
    information that would help answer the query — even partially.

    OUTPUT FORMAT:
    Line 1: One sentence explaining your reasoning.
    Line 2: #YES or #NO

    KEEP the document (#YES) if it:
    - Directly answers any part of the query
    - Provides definitions, context, or constraints relevant to the query
    - Covers any topic, class, or concept mentioned in the query
    - Would help a knowledgeable human construct a better answer

    DISCARD the document (#NO) only if:
    - It is clearly about a different subject
    - Nothing in it relates to the query, even indirectly

    When in doubt, choose #YES.

    --- QUERY ---
    {query}

    --- DOCUMENT ---
    {text}
    """


    global openai_client
    completion = openai_client.responses.create(
         model=model,
         input=prompt,
         max_output_tokens=max_tokens
    )
    


    answer = completion.output_text.strip()
    # with open("justify.txt", "a") as f:
    #     f.write(answer + "\n\n\n\n\n")
    answer = answer.split("#")[-1]
    #answer = completion.choices[0].message.content.strip()
 
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
                               llm_client=llm_client,
                               model="gpt-5.4") -> List[str]:
    """
    Creates one thread per document in expanded_contexts and
    returns snippets in the exact same order as the input.
    """
    global llm_clients

    num_docs = len(expanded_contexts)

    # Pre-allocate output list to preserve ordering
    snippets = [None] * num_docs
    threads = []
    
    for i, doc_text in enumerate(expanded_contexts):
        llm_client = llm_clients[i % len(llm_clients)]
        t = threading.Thread(
            target=process_single_doc,
            args=(i, query, doc_text, llm_client, model, snippets)
        )
        threads.append(t)
        t.start()

    counter = 0
    for t in threads:

        print(f"DONE {counter}")
        counter += 1
        t.join()

    return snippets


def preview_snippet(query: str,
                    expanded_contexts: List[str],
                    model="gpt-5.4") -> List[str]:
    """
    First pass: feeds 200-char previews of all docs to a single LLM call.
    Model returns a JSON object scoring each doc as PASS/FAIL with justification.
    Returns full docs for all passing indices.
    """

    previews = {i: doc[:200] for i, doc in enumerate(expanded_contexts)}
    previews_json = json.dumps(previews, indent=2)

    prompt = f"""
You are a relevance filter for a RAG system.

You will be given a QUERY and a JSON object mapping document indices to short previews.
Evaluate each document's relevance to the query relative to the other documents.

Return ONLY a JSON object. No explanation, no markdown, no backticks.

Each key is a document index (as a string).
Each value is a list of two items:
  - Item 0: "PASS" or "FAIL"
  - Item 1: One sentence justifying your decision

Example output format:
{{
  "0": ["PASS", "Directly discusses the query topic."],
  "1": ["FAIL", "Covers an unrelated subject."],
  "2": ["PASS", "Provides relevant background context."]
}}

When in doubt, PASS the document.

--- QUERY ---
{query}

--- DOCUMENT PREVIEWS ---
{previews_json}
"""

    response = openai_client.responses.create(
        model=model,
        input=prompt,
        max_output_tokens=1000
    )

    raw = response.output_text.strip()
    print("Model grading response:", raw)

    try:
        grades = json.loads(raw)
    except json.JSONDecodeError:
        print("Failed to parse grading response — keeping all docs.")
        return expanded_contexts[:]

    snippets = []
    for i, doc in enumerate(expanded_contexts):
        entry = grades.get(str(i))

        if entry is None:
            # Index missing from response — keep it to be safe
            snippets.append(doc)
            continue

        verdict, justification = entry[0].upper(), entry[1]
        print(f"  [{i}] {verdict} — {justification}")

        if verdict == "PASS":
            snippets.append(doc)

    return snippets