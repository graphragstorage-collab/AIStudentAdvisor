import os
import json
import gc
import math
import time
import psutil
import threading
from typing import List
from concurrent.futures import ThreadPoolExecutor

import networkx as nx

# Import your custom Document class (no LangChain)
from load import *   # <-- Adjust this to match your file name


#########################################################
# GLOBAL DOCUMENT STORAGE
#########################################################
documents = []
documents_lock = threading.Lock()


#########################################################
# 1. SAFE SUBFOLDER SCAN
#########################################################
def scan_all_subfolders(root):
    """Return a list of subfolders using scandir (fast + safe)."""
    folders = []
    with os.scandir(root) as it:
        for entry in it:
            if entry.is_dir():
                folders.append(entry.name)
    folders.sort()
    return folders


#########################################################
# 2. WORKER FUNCTION — PROCESSES A CHUNK OF FOLDERS
#########################################################
def process_subfolders(subfolder_list, root):
    global documents

    for folder in subfolder_list:
        folder_path = os.path.join(root, folder)

        # --- Scan folder for chunk files ---
        chunk_files = []
        try:
            with os.scandir(folder_path) as it:
                for entry in it:
                    if entry.is_file() and "chunk" in entry.name.lower():
                        chunk_files.append(entry.name)
        except Exception as e:
            print(f"Error scanning {folder_path}: {e}")
            continue

        if not chunk_files:
            continue
        chunk_files.sort()

        # --- Build content ---
        header = f"WEBPAGE: {folder[:-24]}\n\n"
        sep = "\n" + ("_" * 50) + "\n"
        parts = [header]

        for cf in chunk_files:
            vm = psutil.virtual_memory()
            print(f"VM Available: {vm.available/1e9:.2f} GB")

            # Ensure enough RAM
            while vm.available / 1e9 < 0.1:
                print("Waiting for memory...")
                time.sleep(0.5)
                vm = psutil.virtual_memory()

            path = os.path.join(folder_path, cf)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except:
                continue

            # Remove summary if present
            if "Summary" in text:
                idx = text.rfind("Summary")
                text = text[:idx].strip()

            parts.append(text)
            parts.append(sep)

        combined_text = "".join(parts)

        doc = Document(
            page_content=combined_text,
            metadata={
                "source": folder,
                "num_chunks": len(chunk_files),
            }
        )

        # --- Thread-safe append ---
        with documents_lock:
            documents.append(doc)
            print(f"Processed {folder}: {len(chunk_files)} chunks → total docs = {len(documents)}")

        del parts, combined_text, doc
        gc.collect()


#########################################################
# 3. MAIN LOADER (DEFAULT 4 WORKERS)
#########################################################
def load_crawled_website(root="./crawled", num_workers=4):
    print("Scanning folders...")
    all_folders = scan_all_subfolders(root)
    total = len(all_folders)
    print(f"Found {total} folders.")

    if total == 0:
        return []

    # Split into worker batches
    batch_size = math.ceil(total / num_workers)
    chunks = [all_folders[i:i + batch_size] for i in range(0, total, batch_size)]

    print(f"\nLaunching {num_workers} workers, ~{batch_size} folders each.\n")

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(process_subfolders, c, root) for c in chunks]
        for f in futures:
            f.result()

    print(f"\n✓ DONE — Loaded {len(documents)} documents.\n")
    return documents


#########################################################
# 4. SAVE DOCUMENTS
#########################################################
def save_documents(docs, path="documents.jsonl"):
    with open(path, "w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps({
                "page_content": d.page_content,
                "metadata": d.metadata
            }) + "\n")
    print(f"✓ Saved documents → {path}")


#########################################################
# 5. GRAPH-RAG BUILDER (WRAPPER)
#########################################################
def build_graph_rag(documents, graph_rag_class):
    print("\nBuilding Graph-RAG...")

    gr = graph_rag_class()
    gr.process_documents(documents)  # <-- FIXED

    print("✓ Graph built.")
    print("✓ Vector store created.")
    return gr


#########################################################
# 6. SAVE VECTOR STORE + GRAPH AS JSON
#########################################################
def save_vector_store(vector_store, path):
    # Your custom class must implement serialize()
    data = vector_store.serialize()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"✓ Saved vector store → {path}")


def save_graph(graph, path):
    data = nx.readwrite.json_graph.node_link_data(graph)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"✓ Saved graph → {path}")


#########################################################
# 7. FULL PIPELINE EXECUTION
#########################################################
def run_full_pipeline(graph_rag_class, root="./crawled"):
    global documents
    if os.path.exists("documents.jsonl"):
        documents = load_documents_jsonl("documents.jsonl")
    else:       
        documents = []  # reset

        #####################################################
        # Step 1 → Load crawled website
        #####################################################
        documents = load_crawled_website(root=root, num_workers=4)

        #####################################################
        # Step 2 → Save raw documents
        #####################################################
        save_documents(documents, "documents.jsonl")

    #####################################################
    # Step 3 → Build Graph-RAG
    #####################################################
    graph_rag = build_graph_rag(documents, graph_rag_class)

    #####################################################
    # Step 4 → Save vector store + knowledge graph
    #####################################################
    save_vector_store(graph_rag.query_engine.vector_store, "vector_store.json")
    save_graph(graph_rag.knowledge_graph.graph, "knowledge_graph.json")

    print("\n✓ ALL DONE — Graph + vector store saved and ready for reload.\n")



def load_vector_store(path, embedding_model):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return SimpleFAISSVectorStore.deserialize(data, embedding_model)

def load_graph(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return nx.readwrite.json_graph.node_link_graph(data)


run_full_pipeline(GraphRAG, root="./crawled") 
