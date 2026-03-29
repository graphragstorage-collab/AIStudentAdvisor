<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8" />
    <title>Admin Panel</title>
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <script src="https://unpkg.com/react@18/umd/react.development.js"></script>
    <script src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
    <style>
        * { box-sizing: border-box; }
        body { margin:0; font-family:Arial,sans-serif; background:#eef3f8; color:#111827; }
        .topbar { height:58px; background:linear-gradient(90deg,#2563eb,#7c3aed); color:#fff; display:flex; align-items:center; justify-content:space-between; padding:0 14px; box-shadow:0 1px 6px rgba(0,0,0,.18); }
        .title { font-size:20px; font-weight:700; }
        .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
        .rowBetween { display:flex; justify-content:space-between; align-items:center; gap:8px; }
        .layout { display:flex; height:calc(100vh - 58px); min-height:0; position:relative; }
        .left { width:320px; min-width:260px; max-width:420px; overflow:auto; background:#f8fafc; border-right:1px solid #d1d5db; padding:10px; }
        .middle { flex:1; min-width:0; overflow:auto; padding:12px; background:#eef3f8; }
        .right { width:40%; min-width:320px; max-width:70vw; resize:horizontal; overflow:auto; border-left:1px solid #d1d5db; background:#fff; display:flex; flex-direction:column; }
        .card, .panel { background:#fff; border:1px solid #dbe4ee; border-radius:12px; padding:10px; margin-bottom:10px; box-shadow:0 1px 2px rgba(0,0,0,.04); }
        .card.clickable { cursor:pointer; }
        .card.clickable:hover { background:#eff6ff; }
        .selected { border:2px solid #2563eb; background:#eff6ff; }
        .sectionTitle { font-size:15px; font-weight:700; margin:0 0 8px 0; }
        .muted, .tiny { color:#6b7280; font-size:12px; }
        .tiny { font-size:11px; }
        .convTitle { font-size:14px; font-weight:700; margin-bottom:6px; }
        .turnMeta { font-size:12px; color:#6b7280; margin-bottom:6px; }
        .bubbleLabel { font-weight:700; margin-top:8px; margin-bottom:4px; font-size:13px; }
        .bubble { white-space:pre-wrap; background:#f8fafc; border:1px solid #e5e7eb; border-radius:10px; padding:10px; font-size:14px; line-height:1.4; max-height:220px; overflow:auto; }
        input, textarea, select { width:100%; border:1px solid #cbd5e1; border-radius:8px; padding:8px 10px; font-size:14px; background:#fff; }
        textarea { min-height:90px; resize:vertical; font-family:Arial,sans-serif; }
        .btn { padding:7px 11px; border:none; border-radius:8px; cursor:pointer; background:#2563eb; color:#fff; font-weight:600; font-size:13px; }
        .btn:hover { filter:brightness(.97); }
        .btn:disabled { opacity:.55; cursor:not-allowed; }
        .btn-light { background:#e5e7eb; color:#111827; }
        .btn-green { background:#059669; }
        .btn-purple { background:#7c3aed; }
        .btn-danger { background:#dc2626; }
        .btn-orange { background:#ea580c; }
        .pill { display:inline-block; padding:3px 8px; border-radius:999px; background:#e0e7ff; color:#3730a3; font-size:12px; font-weight:700; }
        .toggleGroup { display:inline-flex; background:#e5e7eb; border-radius:10px; padding:3px; gap:3px; }
        .toggleBtn { border:none; border-radius:8px; padding:7px 12px; cursor:pointer; font-weight:700; background:transparent; color:#374151; }
        .toggleBtn.active { background:#fff; color:#111827; box-shadow:0 1px 2px rgba(0,0,0,.08); }
        .docPanelHeader { padding:12px; border-bottom:1px solid #e5e7eb; background:#f8fafc; }
        .docList, .docViewer { padding:10px; overflow:auto; flex:1; min-height:0; }
        .docViewer { white-space:pre-wrap; line-height:1.45; font-size:14px; }
        .docSnippet { font-size:13px; color:#374151; white-space:pre-wrap; line-height:1.35; margin-top:6px; max-height:72px; overflow:hidden; }
        .menuOverlay { position:absolute; top:0; right:0; width:420px; max-width:min(92vw,420px); height:100%; background:#fff; border-left:1px solid #d1d5db; box-shadow:-8px 0 24px rgba(0,0,0,.12); z-index:40; display:flex; flex-direction:column; }
        .menuHeader { padding:14px; border-bottom:1px solid #e5e7eb; font-weight:700; font-size:18px; background:#f8fafc; }
        .menuBody { padding:14px; overflow:auto; flex:1; }
        .menuSection { margin-bottom:16px; padding-bottom:14px; border-bottom:1px solid #eef2f7; }
        .menuSection:last-child { border-bottom:none; padding-bottom:0; }
        .smallScroll { max-height:180px; overflow:auto; border:1px solid #e5e7eb; border-radius:8px; padding:6px; background:#fafafa; }
        .emptyState { padding:18px; color:#6b7280; }
        .turnHeader { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; margin-bottom:8px; }
        .sticky { position:sticky; top:0; z-index:5; background:#eef3f8; padding-bottom:10px; }
    </style>
</head>
<body>
<div id="root"></div>

<script>
const h = React.createElement;

function App() {
    const [allConvs, setAllConvs] = React.useState([]);
    const [convs, setConvs] = React.useState([]);
    const [selectedConv, setSelectedConv] = React.useState(null);
    const [selectedConvObj, setSelectedConvObj] = React.useState(null);

    const [turns, setTurns] = React.useState([]);
    const [expandedDocsByTurn, setExpandedDocsByTurn] = React.useState({});
    const [docsByTurn, setDocsByTurn] = React.useState({});

    const [allDocuments, setAllDocuments] = React.useState([]);
    const [selectedTurn, setSelectedTurn] = React.useState(null);
    const [selectedDoc, setSelectedDoc] = React.useState(null);

    const [rightMode, setRightMode] = React.useState("messages");
    const [menuOpen, setMenuOpen] = React.useState(false);

    const [orderTime, setOrderTime] = React.useState(true);
    const [orderRating, setOrderRating] = React.useState(false);

    const [userFilterInput, setUserFilterInput] = React.useState("");
    const [appliedUserFilter, setAppliedUserFilter] = React.useState("");
    const [docKeywordInput, setDocKeywordInput] = React.useState("");
    const [appliedDocKeyword, setAppliedDocKeyword] = React.useState("");

    const [turnForm, setTurnForm] = React.useState({ turn_id:"", question:"", answer:"", rating:0, time:"" });
    const [newDocText, setNewDocText] = React.useState("");
    const [selectedExistingDocId, setSelectedExistingDocId] = React.useState("");
    const [selectedUploadFile, setSelectedUploadFile] = React.useState(null);
    const [statusMsg, setStatusMsg] = React.useState("");

    const [conversationForm, setConversationForm] = React.useState({ conversation_id:"", user_id:"", username:"" });

    function setStatus(text) {
        setStatusMsg(text || "");
        if (text) {
            setTimeout(() => setStatusMsg(cur => cur === text ? "" : cur), 3000);
        }
    }

    function docsForTurn(turnId) {
        return docsByTurn[turnId] || [];
    }

    function resetTurnForm() {
        setTurnForm({ turn_id:"", question:"", answer:"", rating:0, time:"" });
    }

    async function getJSON(url, opts) {
        const res = await fetch(url, opts);
        if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt || ("Request failed: " + url));
        }
        return await res.json();
    }

    async function deleteConversation() {
        if (!selectedConv) {
            setStatus("Select a conversation first.");
            return;
        }
        if (!confirm("Are you sure you want to delete this conversation?")) return;

        try {
            await postJSON("/reporting/delete_conversation", {
                conversation_id: Number(selectedConv)
            });

            setStatus("Conversation deleted.");
            setSelectedConv(null);
            setSelectedConvObj(null);
            setTurns([]);
            setSelectedTurn(null);
            setSelectedDoc(null);

            await refreshConversations(false);
        } catch (err) {
            console.error(err);
            setStatus("Failed to delete conversation.");
        }
    }

    async function postJSON(url, body) {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type":"application/json" },
            body: JSON.stringify(body)
        });
        if (!res.ok) {
            const txt = await res.text();
            throw new Error(txt || ("Request failed: " + url));
        }
        try { return await res.json(); } catch { return null; }
    }

    function applyConversationFilter(data, filterValue) {
        const f = String(filterValue || "").trim().toLowerCase();
        if (!f) return data;
        return data.filter(c => String(c.Username || "").toLowerCase().includes(f));
    }

    async function refreshConversations(keepSelection=true) {
        const url = "/reporting/conversations?order_time=" + orderTime + "&order_rating=" + orderRating;
        const data = await getJSON(url);
        setAllConvs(data);
        setConvs(applyConversationFilter(data, appliedUserFilter));
        if (keepSelection && selectedConv != null) {
            const found = data.find(c => Number(c.Conversation_id) === Number(selectedConv)) || null;
            setSelectedConvObj(found);
        }
    }

    async function refreshAllDocuments(keywordOverride=null) {
        const keyword = keywordOverride !== null ? keywordOverride : appliedDocKeyword;
        const url = "/reporting/all_documents?keyword=" + encodeURIComponent(keyword || "") + "&order_by_rating=" + orderRating;
        const data = await getJSON(url);
        setAllDocuments(data);
    }

    async function loadConversation(conversationId, resetSelection = false) {
        setSelectedConv(conversationId);
        if (resetSelection) {
            setSelectedDoc(null);
            setSelectedTurn(null);
        }

        const found = allConvs.find(c => Number(c.Conversation_id) === Number(conversationId)) || null;
        setSelectedConvObj(found);

        const data = await getJSON("/reporting/conversation/" + conversationId);
        setTurns(data);
        if (selectedTurn != null) {
            const exists = data.some(t => Number(t.Turn_id) === Number(selectedTurn));
            if (!exists) {
                setSelectedTurn(null);
                setSelectedDoc(null);
            }
        }

        const updated = {};
        for (const t of data) {
            if (expandedDocsByTurn[Number(t.Turn_id)]) {
                updated[t.Turn_id] = await getJSON("/reporting/documents/" + conversationId + "/" + t.Turn_id);
            }
        }
        if (Object.keys(updated).length) {
            setDocsByTurn(prev => Object.assign({}, prev, updated));
        }
    }

    async function refreshSelectedConversation() {
        if (selectedConv == null) return;
        await loadConversation(selectedConv, false);
        await refreshConversations(true);
    }

    async function toggleTurnDocs(turnId) {
        const open = !!expandedDocsByTurn[turnId];
        setExpandedDocsByTurn(prev => Object.assign({}, prev, { [Number(turnId)]: !open }));
        if (!open && selectedConv != null) {
            const docs = await getJSON("/reporting/documents/" + selectedConv + "/" + turnId);
            setDocsByTurn(prev => Object.assign({}, prev, { [Number(turnId)]: docs }));
        }
    }

    function openTurnEditor(turnObj) {
        setSelectedTurn(turnObj.Turn_id);
        setTurnForm({
            turn_id: turnObj.Turn_id ?? "",
            question: turnObj.question ?? "",
            answer: turnObj.answer ?? "",
            rating: turnObj.rating ?? 0,
            time: turnObj.time ?? ""
        });
        setMenuOpen(true);
    }

    function newTurnForCurrentConversation() {
        if (!selectedConv) { setStatus("Select a conversation first."); return; }
        setSelectedTurn(null);
        resetTurnForm();
        setMenuOpen(true);
    }

    async function saveTurn() {
        if (!selectedConv) { setStatus("Select a conversation first."); return; }
        try {
            const isNew = !turnForm.turn_id;
            const endpoint = isNew ? "/reporting/add_turn" : "/reporting/update_turn";
            const payload = isNew
                ? {
                    conversation_id: selectedConv,
                    question: turnForm.question,
                    answer: turnForm.answer,
                    rating: Number(turnForm.rating || 0)
                }
                : {
                    turn_id: Number(turnForm.turn_id),
                    conversation_id: selectedConv,
                    question: turnForm.question,
                    answer: turnForm.answer,
                    rating: Number(turnForm.rating || 0),
                    time: turnForm.time
                };
            await postJSON(endpoint, payload);
            setStatus(isNew ? "Turn added." : "Turn updated.");
            await refreshSelectedConversation();
            if (isNew) resetTurnForm();
        } catch (err) {
            console.error(err);
            setStatus("Failed to save turn.");
        }
    }

    async function deleteAttachment(turnId, docId) {
        if (!selectedConv) return;
        try {
            await postJSON("/reporting/run_sql", {
                query: "DELETE FROM Retrieval WHERE Turn_id = %s AND Conversation_id = %s AND Document_id = %s",
                params: [turnId, selectedConv, docId],
                fetch: false
            });
            const docs = await getJSON("/reporting/documents/" + selectedConv + "/" + turnId);
            setDocsByTurn(prev => Object.assign({}, prev, { [Number(turnId)]: docs }));
            if (selectedDoc && Number(selectedDoc.Document_id) === Number(docId)) setSelectedDoc(null);
            setStatus("Attachment deleted.");
            await refreshAllDocuments();
        } catch (err) {
            console.error(err);
            setStatus("Failed to delete attachment.");
        }
    }

    async function attachExistingDocumentToTurn() {
        if (!selectedConv || !selectedTurn || !selectedExistingDocId) {
            setStatus("Select a turn and a document.");
            return;
        }
        try {
            await postJSON("/reporting/attach_existing_document", {
                conversation_id: selectedConv,
                turn_id: selectedTurn,
                document_id: Number(selectedExistingDocId)
            });
            const docs = await getJSON("/reporting/documents/" + selectedConv + "/" + selectedTurn);
            setDocsByTurn(prev => Object.assign({}, prev, { [selectedTurn]: docs }));
            setExpandedDocsByTurn(prev => Object.assign({}, prev, { [selectedTurn]: true }));
            setStatus("Existing document attached.");
        } catch (err) {
            console.error(err);
            setStatus("Failed to attach existing document.");
        }
    }

    async function addInlineTextDocumentToTurn() {
        if (!selectedConv || !selectedTurn) { setStatus("Select a turn first."); return; }
        if (!String(newDocText || "").trim()) { setStatus("Document text cannot be blank."); return; }
        try {
            await postJSON("/reporting/add_document_to_turn", {
                conversation_id: selectedConv,
                turn_id: selectedTurn,
                text: newDocText
            });
            setNewDocText("");
            const docs = await getJSON("/reporting/documents/" + selectedConv + "/" + selectedTurn);
            setDocsByTurn(prev => Object.assign({}, prev, { [selectedTurn]: docs }));
            setExpandedDocsByTurn(prev => Object.assign({}, prev, { [selectedTurn]: true }));
            setStatus("New document attached to turn.");
            await refreshAllDocuments();
        } catch (err) {
            console.error(err);
            setStatus("Failed to add new text document.");
        }
    }

    async function uploadDocumentToSelectedTurn() {
        if (!selectedConv || !selectedTurn || !selectedUploadFile) {
            setStatus("Select a turn and choose a .txt file.");
            return;
        }
        try {
            const fd = new FormData();
            fd.append("file", selectedUploadFile);
            const res = await fetch(
                "/reporting/upload_document_to_turn?conversation_id=" + encodeURIComponent(selectedConv) + "&turn_id=" + encodeURIComponent(selectedTurn),
                { method:"POST", body:fd }
            );
            if (!res.ok) throw new Error(await res.text());
            setSelectedUploadFile(null);
            const input = document.getElementById("turnUploadFileInput");
            if (input) input.value = "";
            const docs = await getJSON("/reporting/documents/" + selectedConv + "/" + selectedTurn);
            setDocsByTurn(prev => Object.assign({}, prev, { [selectedTurn]: docs }));
            setExpandedDocsByTurn(prev => Object.assign({}, prev, { [selectedTurn]: true }));
            setStatus("Uploaded and attached document.");
            await refreshAllDocuments();
        } catch (err) {
            console.error(err);
            setStatus("Failed to upload document to turn.");
        }
    }

    async function uploadStandaloneDocument() {
        if (!selectedUploadFile) { setStatus("Choose a .txt file first."); return; }
        try {
            const fd = new FormData();
            fd.append("file", selectedUploadFile);
            const res = await fetch("/reporting/upload_document", { method:"POST", body:fd });
            if (!res.ok) throw new Error(await res.text());
            setSelectedUploadFile(null);
            const input = document.getElementById("turnUploadFileInput");
            if (input) input.value = "";
            setStatus("Standalone document uploaded.");
            await refreshAllDocuments();
        } catch (err) {
            console.error(err);
            setStatus("Failed to upload standalone document.");
        }
    }

    async function addConversation() {
        const payload = {
            conversation_id: Number(conversationForm.conversation_id),
            user_id: Number(conversationForm.user_id),
            username: conversationForm.username || ""
        };
        if (!payload.conversation_id || !payload.user_id) {
            setStatus("conversation_id and user_id are required.");
            return;
        }
        try {
            await postJSON("/reporting/add_conversation_full", payload);
            setConversationForm({ conversation_id:"", user_id:"", username:"" });
            setStatus("Conversation added.");
            await refreshConversations(false);
        } catch (err) {
            console.error(err);
            setStatus("Failed to add conversation.");
        }
    }

    async function updateConversationUser() {
        if (!selectedConv || !selectedConvObj) { setStatus("Select a conversation first."); return; }
        try {
            await postJSON("/reporting/update_conversation", {
                conversation_id: Number(selectedConv),
                user_id: Number(selectedConvObj.User_id || 0),
                username: String(selectedConvObj.Username || "")
            });
            setStatus("Conversation updated.");
            await refreshConversations(true);
        } catch (err) {
            console.error(err);
            setStatus("Failed to update conversation.");
        }
    }

    function runUserSearch() {
        const value = userFilterInput.trim();
        setAppliedUserFilter(value);
        setConvs(applyConversationFilter(allConvs, value));
    }

    function resetUserSearch() {
        setUserFilterInput("");
        setAppliedUserFilter("");
        setConvs(allConvs);
    }

    async function runDocumentKeywordSearch() {
        const value = docKeywordInput.trim();
        setAppliedDocKeyword(value);
        await refreshAllDocuments(value);
        setRightMode("documents");
        setSelectedDoc(null);
    }

    async function resetDocumentKeywordSearch() {
        setDocKeywordInput("");
        setAppliedDocKeyword("");
        await refreshAllDocuments("");
    }

    React.useEffect(() => {
        refreshConversations(false);
        refreshAllDocuments("");
    }, [orderTime, orderRating]);

    React.useEffect(() => {
        const interval = setInterval(() => {
            refreshConversations(true);
            if (selectedConv != null) loadConversation(selectedConv, false);
        }, 5000);
        return () => clearInterval(interval);
    }, [selectedConv, orderTime, orderRating, appliedUserFilter]);

    function Btn(cls, text, onClick, disabled) {
        return h("button", { className:"btn " + (cls || ""), onClick:onClick, disabled:!!disabled }, text);
    }

    function LabeledInput(label, value, onChange, placeholder, extra) {
        return h("div", { style:{ marginTop:"8px" } },
            h("label", { className:"tiny" }, label),
            h("input", Object.assign({
                value:value,
                onChange:onChange,
                placeholder:placeholder || ""
            }, extra || {}))
        );
    }

    function LabeledTextarea(label, value, onChange, placeholder) {
        return h("div", { style:{ marginTop:"8px" } },
            h("label", { className:"tiny" }, label),
            h("textarea", { value:value, onChange:onChange, placeholder:placeholder || "" })
        );
    }

    const rightPanelDocuments = rightMode === "documents"
        ? allDocuments
        : (selectedTurn ? docsForTurn(selectedTurn) : []);

    function renderConversationCard(c) {
        const selected = Number(selectedConv) === Number(c.Conversation_id);
        return h("div", {
            key:c.Conversation_id,
            className:"card clickable " + (selected ? "selected" : ""),
            onClick:() => loadConversation(c.Conversation_id, true)
        },
            h("div", { className:"convTitle" }, "Conversation " + c.Conversation_id),
            h("div", { className:"muted" }, "User: " + (c.Username ?? "N/A")),
            h("div", { className:"muted" }, "User ID: " + (c.User_id ?? "N/A")),
            h("div", { className:"muted" }, "Avg Rating: " + (c.avg_rating ?? "N/A")),
            h("div", { className:"muted" }, "Latest Time: " + (c.latest_time ?? "N/A"))
        );
    }

    function renderAttachedDoc(turnId, d, compact) {
        return h("div", { key:d.Document_id, className:"card", style: compact ? { marginBottom:"6px", padding:"8px" } : { marginBottom:"8px" } },
            h("div", { className:"rowBetween" },
                h("div", { style:{ fontWeight:"700" } }, "Document " + d.Document_id),
                h("div", { className:"row" },
                    Btn("btn-light", "Open", () => {
                        setSelectedTurn(turnId);
                        setSelectedDoc(d);
                        setRightMode("messages");
                    }),
                    Btn("btn-danger", "Delete", () => deleteAttachment(turnId, d.Document_id))
                )
            ),
            h("div", { className:"docSnippet" }, String(d.text || "").slice(0, compact ? 240 : 400))
        );
    }

    function renderTurn(t) {
        const docsOpen = !!expandedDocsByTurn[t.Turn_id];
        const turnDocs = docsForTurn(t.Turn_id);
        return h("div", { key:t.Turn_id, className:"card" },
            h("div", { className:"turnHeader" },
                h("div", null,
                    h("div", { style:{ fontWeight:"700", fontSize:"15px" } }, "Turn " + t.Turn_id),
                    h("div", { className:"turnMeta" }, "Time: " + (t.time ?? "N/A") + " | Rating: " + (t.rating ?? "N/A"))
                ),
                h("div", { className:"row" },
                    Btn("btn-light", "Select", () => {
                        setSelectedTurn(t.Turn_id);
                        setRightMode("messages");
                        setSelectedDoc(null);
                    }),
                    Btn("", docsOpen ? "Hide Docs" : "Show Docs", () => toggleTurnDocs(t.Turn_id)),
                    Btn("btn-green", "Edit", () => openTurnEditor(t))
                )
            ),
            h("div", { className:"bubbleLabel" }, "Question"),
            h("div", { className:"bubble" }, t.question ?? ""),
            h("div", { className:"bubbleLabel" }, "Answer"),
            h("div", { className:"bubble" }, t.answer ?? ""),
            docsOpen ? h("div", { style:{ marginTop:"10px" } },
                h("div", { className:"rowBetween", style:{ marginBottom:"8px" } },
                    h("div", { className:"sectionTitle" }, "Attached Documents"),
                    Btn("btn-orange", "Manage Attachments", () => {
                        setSelectedTurn(t.Turn_id);
                        setMenuOpen(true);
                    })
                ),
                turnDocs.length === 0
                    ? h("div", { className:"emptyState", style:{ padding:"8px 0" } }, "No attached documents.")
                    : turnDocs.map(d => renderAttachedDoc(t.Turn_id, d, false))
            ) : null
        );
    }

    function renderRightPanel() {
        return h("div", { className:"right" },
            h("div", { className:"docPanelHeader" },
                h("div", { className:"rowBetween" },
                    h("div", null,
                        h("div", { className:"sectionTitle", style:{ marginBottom:"4px" } },
                            rightMode === "documents" ? "Documents" : "Turn Document Viewer"
                        ),
                        h("div", { className:"tiny" },
                            rightMode === "documents"
                                ? "Keyword: " + (appliedDocKeyword || "none")
                                : (selectedTurn ? "Selected Turn: " + selectedTurn : "Select a turn and open its docs.")
                        )
                    ),
                    h("div", { className:"row" },
                        Btn("btn-light", "Clear Viewer", () => setSelectedDoc(null))
                    )
                )
            ),
            selectedDoc
                ? h("div", { className:"docViewer" }, selectedDoc.text ?? "")
                : h("div", { className:"docList" },
                    rightMode === "documents"
                        ? (
                            rightPanelDocuments.length === 0
                                ? h("div", { className:"emptyState" }, "No documents found.")
                                : rightPanelDocuments.map(d =>
                                    h("div", { key:d.Document_id, className:"card" },
                                        h("div", { className:"rowBetween" },
                                            h("div", { style:{ fontWeight:"700" } }, "Document " + d.Document_id),
                                            Btn("btn-light", "Open", () => setSelectedDoc(d))
                                        ),
                                        h("div", { className:"docSnippet" }, String(d.text || "").slice(0, 500))
                                    )
                                )
                        )
                        : (
                            !selectedTurn
                                ? h("div", { className:"emptyState" }, "No turn selected.")
                                : rightPanelDocuments.length === 0
                                    ? h("div", { className:"emptyState" }, "This turn has no loaded documents. Use Show Docs or Manage Attachments.")
                                    : rightPanelDocuments.map(d =>
                                        h("div", { key:d.Document_id, className:"card" },
                                            h("div", { className:"rowBetween" },
                                                h("div", { style:{ fontWeight:"700" } }, "Document " + d.Document_id),
                                                h("div", { className:"row" },
                                                    Btn("btn-light", "Open", () => setSelectedDoc(d)),
                                                    Btn("btn-danger", "Delete", () => deleteAttachment(selectedTurn, d.Document_id))
                                                )
                                            ),
                                            h("div", { className:"docSnippet" }, String(d.text || "").slice(0, 500))
                                        )
                                    )
                        )
                )
        );
    }

    function renderMenu() {
        if (!menuOpen) return null;
        return h("div", { className:"menuOverlay" },
            h("div", { className:"menuHeader" }, "Admin Controls"),
            h("div", { className:"menuBody" },

                h("div", { className:"menuSection" },
                    h("div", { className:"sectionTitle" }, "Turn Editor"),
                    h("div", { className:"tiny" },
                        selectedConv
                            ? ("Editing within conversation " + selectedConv + (selectedTurn ? (" | turn " + selectedTurn) : ""))
                            : "Select a conversation first."
                    ),
                    LabeledInput("Turn ID", turnForm.turn_id, () => {}, "Auto for new turn", { readOnly:true }),
                    LabeledTextarea("Question", turnForm.question, ev => setTurnForm(Object.assign({}, turnForm, { question:ev.target.value })), "Question"),
                    LabeledTextarea("Answer", turnForm.answer, ev => setTurnForm(Object.assign({}, turnForm, { answer:ev.target.value })), "Answer"),
                    h("div", { className:"row", style:{ marginTop:"8px" } },
                        h("div", { style:{ flex:1 } },
                            LabeledInput("Rating", turnForm.rating, ev => setTurnForm(Object.assign({}, turnForm, { rating:ev.target.value })), "", { type:"number" })
                        ),
                        h("div", { style:{ flex:1 } },
                            LabeledInput("Time", turnForm.time, ev => setTurnForm(Object.assign({}, turnForm, { time:ev.target.value })), "Time value")
                        )
                    ),
                    h("div", { className:"row", style:{ marginTop:"10px" } },
                        Btn("btn-green", turnForm.turn_id ? "Save Turn" : "Add Turn", saveTurn, !selectedConv),
                        Btn("btn-light", "Clear", resetTurnForm),
                        Btn("btn-light", "New Blank Turn", newTurnForCurrentConversation, !selectedConv)
                    )
                ),

                h("div", { className:"menuSection" },
                    h("div", { className:"sectionTitle" }, "Review Attached Documents"),
                    h("div", { className:"tiny" }, "Choose a turn, then review documents attached to it."),
                    h("div", { style:{ marginTop:"8px" } },
                        h("select", {
                            value:selectedTurn || "",
                            onChange: async (ev) => {
                                const turnId = ev.target.value ? Number(ev.target.value) : null;
                                setSelectedTurn(turnId);
                                setSelectedDoc(null);
                                if (turnId && selectedConv != null) {
                                    const docs = await getJSON("/reporting/documents/" + selectedConv + "/" + turnId);
                                    setDocsByTurn(prev => Object.assign({}, prev, { [Number(turnId)]: docs }));
                                    setExpandedDocsByTurn(prev => Object.assign({}, prev, { [Number(turnId)]: true }));
                                }
                            }
                        },
                            h("option", { value:"" }, "Select turn"),
                            turns.map(t => h("option", { key:t.Turn_id, value:t.Turn_id }, "Turn " + t.Turn_id))
                        )
                    ),
                    h("div", { className:"smallScroll", style:{ marginTop:"8px" } },
                        !selectedTurn
                            ? h("div", { className:"tiny" }, "No turn selected.")
                            : docsForTurn(selectedTurn).length === 0
                                ? h("div", { className:"tiny" }, "No attached documents loaded.")
                                : docsForTurn(selectedTurn).map(d => renderAttachedDoc(selectedTurn, d, true))
                    )
                ),

                h("div", { className:"menuSection" },
                    h("div", { className:"sectionTitle" }, "Attach Existing Document To Turn"),
                    h("div", { className:"tiny" }, "Uses /reporting/attach_existing_document."),
                    h("div", { style:{ marginTop:"8px" } },
                        h("select", {
                            value:selectedExistingDocId,
                            onChange:(ev) => setSelectedExistingDocId(ev.target.value)
                        },
                            h("option", { value:"" }, "Select existing document"),
                            allDocuments.map(d =>
                                h("option", { key:d.Document_id, value:d.Document_id },
                                    "Document " + d.Document_id + " - " + String(d.text || "").slice(0, 60).split("\\n").join(" ")
                                )
                            )
                        )
                    ),
                    h("div", { className:"row", style:{ marginTop:"8px" } },
                        Btn("", "Attach Existing", attachExistingDocumentToTurn, !selectedTurn || !selectedConv)
                    )
                ),

                h("div", { className:"menuSection" },
                    h("div", { className:"sectionTitle" }, "Add New Text Document To Turn"),
                    h("div", { className:"tiny" }, "Creates a new document and attaches it directly to the selected turn."),
                    LabeledTextarea("", newDocText, ev => setNewDocText(ev.target.value), "Paste text for the new document"),
                    h("div", { className:"row", style:{ marginTop:"8px" } },
                        Btn("btn-green", "Add Text Document", addInlineTextDocumentToTurn, !selectedTurn || !selectedConv)
                    )
                ),

                h("div", { className:"menuSection" },
                    h("div", { className:"sectionTitle" }, "Upload Document"),
                    h("div", { className:"tiny" }, "Choose a .txt file and either upload it standalone or upload-and-attach it to the selected turn."),
                    h("div", { style:{ marginTop:"8px" } },
                        h("input", {
                            id:"turnUploadFileInput",
                            type:"file",
                            accept:".txt,text/plain",
                            onChange:(ev) => setSelectedUploadFile(ev.target.files && ev.target.files[0] ? ev.target.files[0] : null)
                        })
                    ),
                    h("div", { className:"row", style:{ marginTop:"8px" } },
                        Btn("btn-purple", "Upload Standalone", uploadStandaloneDocument, !selectedUploadFile),
                        Btn("btn-green", "Upload To Turn", uploadDocumentToSelectedTurn, !selectedUploadFile || !selectedTurn || !selectedConv)
                    )
                ),

                h("div", { className:"menuSection" },
                    h("div", { className:"sectionTitle" }, "Conversation Controls"),
                    h("div", { className:"tiny" }, "Keeps add/update conversation support available."),
                    LabeledInput("Conversation ID", conversationForm.conversation_id, ev => setConversationForm(Object.assign({}, conversationForm, { conversation_id:ev.target.value })), "Conversation ID"),
                    LabeledInput("User ID", conversationForm.user_id, ev => setConversationForm(Object.assign({}, conversationForm, { user_id:ev.target.value })), "User ID"),
                    LabeledInput("Username", conversationForm.username, ev => setConversationForm(Object.assign({}, conversationForm, { username:ev.target.value })), "Username"),
                    h("div", { className:"row", style:{ marginTop:"8px" } },
                        Btn("", "Add Conversation", addConversation),
                        Btn("btn-light", "Update Selected Conversation", updateConversationUser, !selectedConv)
                    )
                ),

                h("div", { className:"menuSection" },
                    h("div", { className:"sectionTitle" }, "Quick Search Copy"),
                    h("div", { className:"tiny" }, "Both searches remain present here too."),
                    LabeledInput("User search", userFilterInput, ev => setUserFilterInput(ev.target.value), "Search username"),
                    h("div", { className:"row", style:{ marginTop:"6px" } },
                        Btn("", "Run User Search", runUserSearch),
                        Btn("btn-light", "Reset", resetUserSearch)
                    ),
                    LabeledInput("Document keyword search", docKeywordInput, ev => setDocKeywordInput(ev.target.value), "Keyword"),
                    h("div", { className:"row", style:{ marginTop:"6px" } },
                        Btn("", "Run Doc Search", runDocumentKeywordSearch),
                        Btn("btn-light", "Reset", resetDocumentKeywordSearch)
                    )
                )
            )
        );
    }

    return h("div", null,
        h("div", { className:"topbar" },
            h("div", { className:"title" }, "Admin Panel"),
            h("div", { className:"row" },
                statusMsg ? h("span", { className:"pill" }, statusMsg) : null,
                h("div", { className:"toggleGroup" },
                    h("button", {
                        className:"toggleBtn " + (rightMode === "messages" ? "active" : ""),
                        onClick:() => setRightMode("messages")
                    }, "View Messages"),
                    h("button", {
                        className:"toggleBtn " + (rightMode === "documents" ? "active" : ""),
                        onClick:() => setRightMode("documents")
                    }, "View Documents")
                ),
                Btn("btn-purple", menuOpen ? "Close Menu" : "Open Menu", () => setMenuOpen(v => !v))
            )
        ),

        h("div", { className:"layout" },

            h("div", { className:"left" },
                h("div", { className:"panel" },
                    h("div", { className:"sectionTitle" }, "Conversation Search"),
                    h("div", { className:"tiny" }, "User search stays available."),
                    h("div", { style:{ marginTop:"8px" } },
                        h("input", {
                            placeholder:"Search username",
                            value:userFilterInput,
                            onChange:(ev) => {
                                const v = ev.target.value;
                                setUserFilterInput(v);
                                if (v.trim() === "") {
                                    setAppliedUserFilter("");
                                    setConvs(allConvs);
                                }
                            }
                        })
                    ),
                    h("div", { className:"row", style:{ marginTop:"8px" } },
                        Btn("", "Search", runUserSearch),
                        Btn("btn-light", "Reset", resetUserSearch),
                        Btn("btn-green", "New Turn", newTurnForCurrentConversation, !selectedConv)
                    )
                ),

                h("div", { className:"panel" },
                    h("div", { className:"sectionTitle" }, "Document Keyword Search"),
                    h("div", { className:"tiny" }, "Searches all documents through /reporting/all_documents."),
                    h("div", { style:{ marginTop:"8px" } },
                        h("input", {
                            placeholder:"Keyword in documents",
                            value:docKeywordInput,
                            onChange:(ev) => setDocKeywordInput(ev.target.value)
                        })
                    ),
                    h("div", { className:"row", style:{ marginTop:"8px" } },
                        Btn("", "Search Docs", runDocumentKeywordSearch),
                        Btn("btn-light", "Reset", resetDocumentKeywordSearch)
                    )
                ),

                h("div", { className:"row", style:{ marginBottom:"10px" } },
                    h("label", { className:"tiny" },
                        h("input", {
                            type:"checkbox",
                            checked:orderTime,
                            style:{ width:"auto", marginRight:"6px" },
                            onChange:() => setOrderTime(v => !v)
                        }),
                        "Order by time"
                    ),
                    h("label", { className:"tiny" },
                        h("input", {
                            type:"checkbox",
                            checked:orderRating,
                            style:{ width:"auto", marginRight:"6px" },
                            onChange:() => setOrderRating(v => !v)
                        }),
                        "Order by rating"
                    )
                ),

                convs.length === 0
                    ? h("div", { className:"emptyState" }, "No conversations found.")
                    : convs.map(renderConversationCard)
            ),

            h("div", { className:"middle" },
                h("div", { className:"sticky" },
                    h("div", { className:"rowBetween" },
                        h("div", null,
                            selectedConv
                                ? h("div", { className:"card", style:{ marginBottom:"10px" } },
                                    h("div", { className:"sectionTitle" }, "Selected Conversation"),
                                    h("div", { className:"muted" }, "Conversation ID: " + selectedConv),
                                    h("div", { className:"muted" }, "Username: " + ((selectedConvObj && selectedConvObj.Username) || "N/A")),
                                    h("div", { className:"muted" }, "User ID: " + ((selectedConvObj && selectedConvObj.User_id) || "N/A"))
                                )
                                : h("div", { className:"emptyState" }, "Select a conversation.")
                        ),
                        h("div", { className:"row" },
                            Btn("btn-light", "Refresh Conversation", refreshSelectedConversation, !selectedConv),
                            Btn("btn-purple", "Open Admin Menu", () => setMenuOpen(true)),
                            Btn("btn-danger", "Delete Conversation", deleteConversation, !selectedConv)
                        )
                    )
                ),

                !selectedConv
                    ? h("div", { className:"emptyState" }, "Choose a conversation from the left.")
                    : turns.length === 0
                        ? h("div", { className:"emptyState" }, "No turns for this conversation.")
                        : turns.map(renderTurn)
            ),

            renderRightPanel(),
            renderMenu()
        )
    );
}

ReactDOM.createRoot(document.getElementById("root")).render(h(App));
</script>
</body>
</html>

