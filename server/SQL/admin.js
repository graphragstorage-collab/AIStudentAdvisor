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
        body { margin:0; font-family:Arial,sans-serif; background:#eef3f8; color:#111827; overflow: hidden; height: 100vh; display: flex; flex-direction: column; }
        .topbar { height:58px; background:linear-gradient(90deg,#2563eb,#7c3aed); color:#fff; display:flex; align-items:center; justify-content:space-between; padding:0 14px; box-shadow:0 1px 6px rgba(0,0,0,.18); flex-shrink: 0; z-index: 10; }
        .title { font-size:20px; font-weight:700; }
        .row { display:flex; gap:8px; align-items:center; flex-wrap:wrap; }
        .rowBetween { display:flex; justify-content:space-between; align-items:center; gap:8px; }
        .layout { display:flex; flex: 1; min-height:0; position:relative; overflow: hidden; }
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
        .docList { padding:10px; overflow:auto; flex:1; }
        .docViewer { padding:15px; white-space:pre-wrap; line-height:1.6; font-size:14px; overflow:auto; flex:1; background:#fff; color:#1e293b; }
        .docSnippet { font-size:13px; color:#374151; white-space:pre-wrap; line-height:1.35; margin-top:6px; max-height:72px; overflow:hidden; }
        .menuOverlay { position:absolute; top:0; right:0; width:420px; max-width:min(92vw,420px); height:100%; background:#fff; border-left:1px solid #d1d5db; box-shadow:-8px 0 24px rgba(0,0,0,.12); z-index:40; display:flex; flex-direction:column; }
        .menuHeader { padding:14px; border-bottom:1px solid #e5e7eb; font-weight:700; font-size:18px; background:#f8fafc; }
        .menuBody { padding:14px; overflow:auto; flex:1; }
        .sticky { position:sticky; top:0; z-index:5; background:#eef3f8; padding-bottom:10px; }
        .terminal-container { background: #0f172a; color: #e2e8f0; display: flex; flex-direction: column; border-top: 2px solid #334155; transition: height 0.2s ease-in-out; flex-shrink: 0; }
        .terminal-header { padding: 8px 14px; background: #1e293b; display: flex; justify-content: space-between; align-items: center; cursor: pointer; user-select: none; }
        .terminal-body { flex: 1; overflow-y: auto; padding: 12px; font-family: 'Courier New', monospace; font-size: 13px; }
        .terminal-input-area { display: flex; background: #1e293b; border-top: 1px solid #334155; padding: 4px; }
        .terminal-input-area input { flex: 1; background: transparent; color: #38bdf8; border: none; padding: 8px 12px; outline: none; font-family: monospace; }
    </style>
</head>
<body>
<div id="root" style="display:contents;"></div>

<script>
const h = React.createElement;

function App() {
    const [terminalInput, setTerminalInput] = React.useState("");
    const [terminalOutput, setTerminalOutput] = React.useState([]);
    const [terminalLoading, setTerminalLoading] = React.useState(false);
    const [terminalOpen, setTerminalOpen] = React.useState(true);

    const [convs, setConvs] = React.useState([]);
    const [selectedConv, setSelectedConv] = React.useState(null);
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
    const [turnForm, setTurnForm] = React.useState({ turn_id:"", question:"", answer:"", rating:0 });
    const [conversationForm, setConversationForm] = React.useState({ conversation_id:"", user_id:"", username:"" });
    const [statusMsg, setStatusMsg] = React.useState("");
    
    const [convRatings, setConvRatings] = React.useState({});

    const getClientSideAvg = (convId) => {
        const ratings = convRatings[convId] || [];
        if (ratings.length === 0) return "0.0";
        const sum = ratings.reduce((a, b) => a + Number(b), 0);
        return (sum / ratings.length).toFixed(1);
    };

    async function getJSON(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(await res.text());
        return await res.json();
    }

    async function postJSON(url, body) {
        const res = await fetch(url, {
            method: "POST",
            headers: { "Content-Type":"application/json" },
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error(await res.text());
        try { return await res.json(); } catch { return null; }
    }

    async function refreshConversations() {
        const url = `/reporting/conversations?order_time=${orderTime}&order_rating=${orderRating}`;
        const data = await getJSON(url);
        
        const ratingsMap = {};
        await Promise.all(data.map(async (c) => {
            try {
                const ratingsData = await getJSON(`/reporting/conversation_ratings/${c.Conversation_id}`);
                ratingsMap[c.Conversation_id] = ratingsData.map(r => r.rating || 0);
            } catch (e) {
                ratingsMap[c.Conversation_id] = [];
            }
        }));
        
        setConvRatings(ratingsMap);
        const f = appliedUserFilter.toLowerCase();
        setConvs(f ? data.filter(c => String(c.Username || "").toLowerCase().includes(f)) : data);
    }

    async function loadConversation(id) {
        setSelectedConv(id);
        const [turnData, ratingData] = await Promise.all([
            getJSON("/reporting/conversation/" + id),
            getJSON(`/reporting/conversation_ratings/${id}`)
        ]);

        const mergedTurns = turnData.map(t => {
            const match = ratingData.find(r => r.Turn_id === t.Turn_id);
            return { ...t, rating: match ? match.rating : 0 };
        });

        setTurns(mergedTurns);
    }

    async function toggleTurnDocs(turnId) {
        const isOpen = expandedDocsByTurn[turnId];
        setExpandedDocsByTurn(prev => ({...prev, [turnId]: !isOpen}));
        setSelectedTurn(turnId); 
        // Reset selected doc so viewer doesn't stay open on old doc
        setSelectedDoc(null);
        // Force right mode to messages to show context for the turn
        setRightMode("messages");
        
        if (!isOpen && selectedConv) {
            const docs = await getJSON(`/reporting/documents/${selectedConv}/${turnId}`);
            setDocsByTurn(prev => ({...prev, [turnId]: docs}));
        }
    }

    // FIXED SEARCH FUNCTION
    async function handleDocSearch() {
        const docs = await getJSON("/reporting/all_documents?keyword=" + docKeywordInput);
        setAllDocuments(docs);
        setRightMode("documents"); // Switch to global mode to see results
        setSelectedDoc(null);      // Close detail view if open
    }

    async function runTerminalQuery() {
        if (!terminalInput.trim()) return;
        setTerminalLoading(true);
        const inputStr = terminalInput;
        setTerminalInput("");
        try {
            const isSelect = inputStr.trim().toUpperCase().startsWith("SELECT");
            const res = await postJSON("/reporting/run_sql", { query: inputStr, params: [], fetch: isSelect });
            setTerminalOutput(p => [...p, { type: "in", text: inputStr }, { type: "out", text: JSON.stringify(res, null, 2) }]);
        } catch (err) {
            setTerminalOutput(p => [...p, { type: "in", text: inputStr }, { type: "err", text: String(err) }]);
        }
        setTerminalLoading(false);
    }

    React.useEffect(() => { 
        refreshConversations(); 
    }, [orderTime, orderRating, appliedUserFilter]);

    // Initial doc load
    React.useEffect(() => {
        getJSON("/reporting/all_documents?keyword=").then(setAllDocuments);
    }, []);

    const Btn = (cls, text, onClick, disabled) => h("button", { className:"btn "+(cls||""), onClick, disabled }, text);

    // Determine which list to show based on rightMode
    const currentDocList = rightMode === "documents" ? allDocuments : (docsByTurn[selectedTurn] || []);

    return h(React.Fragment, null,
        h("div", { className: "topbar" },
            h("div", { className: "title" }, "Admin Panel"),
            h("div", { className: "row" },
                statusMsg && h("div", { className: "pill" }, statusMsg),
                Btn("btn-purple", "Add Conv", () => setMenuOpen("new_conv")),
                Btn("btn-danger", "Delete Conv", () => {
                    if(selectedConv && confirm("Delete?")) postJSON("/reporting/delete_conversation", { conversation_id: Number(selectedConv) }).then(() => { setSelectedConv(null); refreshConversations(); });
                })
            )
        ),

        h("div", { className: "layout" },
            h("div", { className: "left" },
                h("div", { className: "sticky" },
                    h("div", { className: "sectionTitle" }, "Conversations"),
                    h("div", { className: "row", style:{marginBottom: "8px"} },
                        h("label", { className: "tiny" }, h("input", { type: "checkbox", checked: orderTime, onChange: e => setOrderTime(e.target.checked), style:{width:"auto"} }), " Time"),
                        h("label", { className: "tiny" }, h("input", { type: "checkbox", checked: orderRating, onChange: e => setOrderRating(e.target.checked), style:{width:"auto"} }), " Rating")
                    ),
                    h("div", { className: "row" },
                        h("input", { placeholder: "User...", value: userFilterInput, onChange: e => setUserFilterInput(e.target.value) }),
                        Btn("btn-light", "Go", () => setAppliedUserFilter(userFilterInput))
                    )
                ),
                convs.map(c => h("div", { key: c.Conversation_id, className: "card clickable "+(Number(selectedConv)===Number(c.Conversation_id)?"selected":""), onClick:()=>loadConversation(c.Conversation_id) },
                    h("div", { className:"convTitle" }, "Conv "+c.Conversation_id), 
                    h("div", { className:"muted" }, (c.Username||"N/A") + " (" + getClientSideAvg(c.Conversation_id) + "★)")
                ))
            ),

            h("div", { className: "middle" },
                h("div", { className: "rowBetween", style:{marginBottom: "12px"} }, h("div", { className:"sectionTitle" }, "Turns"), Btn("btn-green", "+ Turn", () => { setTurnForm({turn_id:"", question:"", answer:"", rating:0}); setMenuOpen("edit_turn"); })),
                turns.map(t => h("div", { key: t.Turn_id, className: "card" },
                    h("div", { className: "turnHeader", style: {display:'flex', justifyContent:'space-between'} },
                        h("div", null, h("div", { style:{fontWeight:"700"} }, "Turn "+t.Turn_id), h("div", { className:"turnMeta" }, "Rating: "+t.rating)),
                        h("div", { className: "row" }, Btn("btn-light", "Docs", () => toggleTurnDocs(t.Turn_id)), Btn("btn-green", "Edit", () => { setTurnForm(t); setMenuOpen("edit_turn"); }))
                    ),
                    h("div", { className: "bubbleLabel" }, "Q"), h("div", { className: "bubble" }, t.question),
                    h("div", { className: "bubbleLabel" }, "A"), h("div", { className: "bubble" }, t.answer),
                    expandedDocsByTurn[t.Turn_id] && h("div", { style: { marginTop: "10px", borderTop: "1px solid #eee", paddingTop: "10px" } },
                        (docsByTurn[t.Turn_id] || []).map(d => h("div", { key: d.Document_id, className: "card", style: { background: "#f8fafc" } },
                            h("div", { className: "rowBetween" }, h("div", { className: "tiny" }, "ID: "+d.Document_id), Btn("btn-light", "View", () => { setSelectedDoc(d); setSelectedTurn(t.Turn_id); setRightMode("messages"); })),
                            h("div", { className: "docSnippet" }, d.text)
                        ))
                    )
                ))
            ),

            h("div", { className: "right" },
                h("div", { className: "docPanelHeader" },
                    h("div", { className: "rowBetween", style:{marginBottom:"8px"} },
                        h("div", { className: "toggleGroup" },
                            h("button", { className: "toggleBtn "+(rightMode==="messages"?"active":""), onClick:()=>setRightMode("messages") }, "Selected"),
                            h("button", { className: "toggleBtn "+(rightMode==="documents"?"active":""), onClick:()=>setRightMode("documents") }, "Global")
                        ),
                        Btn("btn-light", "Reset", () => { setSelectedDoc(null); setDocKeywordInput(""); getJSON("/reporting/all_documents?keyword=").then(setAllDocuments); })
                    ),
                    h("div", { className: "row" },
                        h("input", { 
                            placeholder: "Search docs...", 
                            value: docKeywordInput, 
                            onChange: e => setDocKeywordInput(e.target.value),
                            onKeyDown: e => e.key === "Enter" && handleDocSearch()
                        }),
                        Btn("btn-light", "Search", handleDocSearch)
                    )
                ),
                selectedDoc ? h("div", { className: "docViewer" }, selectedDoc.text) :
                h("div", { className: "docList" },
                    currentDocList.length > 0 
                        ? currentDocList.map(d => h("div", { key: d.Document_id, className: "card clickable "+(selectedDoc?.Document_id===d.Document_id?"selected":""), onClick: () => setSelectedDoc(d) },
                            h("div", { style:{fontWeight:"700"} }, "Doc "+d.Document_id), h("div", { className: "docSnippet" }, d.text)))
                        : h("div", { className: "emptyState", style: {padding: "20px", color: "#64748b"} }, 
                            rightMode === "documents" ? "No global documents found." : "No documents linked to this turn. Click 'Docs' on a turn to view context.")
                )
            )
        ),

        h("div", { className: "terminal-container", style: { height: terminalOpen ? "300px" : "36px" } },
            h("div", { className: "terminal-header", onClick: () => setTerminalOpen(!terminalOpen) },
                h("div", { style: { fontWeight: "bold", fontSize: "12px", letterSpacing: "1px" } }, "SQL TERMINAL"),
                h("div", { className: "row" },
                    Btn("btn-light", "Clear", (e) => { e.stopPropagation(); setTerminalOutput([]); }),
                    h("span", null, terminalOpen ? "▼" : "▲")
                )
            ),
            terminalOpen && h("div", { className: "terminal-body" },
                terminalOutput.map((o, i) => h("div", { key: i, style: { marginBottom: "10px" } },
                    o.type === "in" ? h("div", { style: { color: "#38bdf8" } }, "> " + o.text) : 
                    o.type === "err" ? h("div", { style: { color: "#fb7185" } }, o.text) : 
                    h("pre", { style: { color: "#94a3b8", margin: "4px 0 0 14px", whiteSpace: "pre-wrap", background: "#1e293b", padding: "8px", borderRadius: "4px" } }, o.text)
                ))
            ),
            terminalOpen && h("div", { className: "terminal-input-area" },
                h("input", { 
                    placeholder: "Enter SQL query...", 
                    value: terminalInput, 
                    onChange: e => setTerminalInput(e.target.value), 
                    onKeyDown: e => e.key === "Enter" && runTerminalQuery() 
                }),
                Btn("btn-purple", terminalLoading ? "..." : "RUN", runTerminalQuery)
            )
        ),

        menuOpen && h("div", { className: "menuOverlay" },
            h("div", { className: "menuHeader" }, h("div", { className: "rowBetween" }, menuOpen.toUpperCase(), Btn("btn-light", "X", () => setMenuOpen(false)))),
            h("div", { className: "menuBody" },
                menuOpen === "new_conv" && h("div", null,
                    h("label", { className: "tiny" }, "Conv ID"), h("input", { value: conversationForm.conversation_id, onChange: e => setConversationForm({...conversationForm, conversation_id: e.target.value}) }),
                    h("label", { className: "tiny" }, "User ID"), h("input", { value: conversationForm.user_id, onChange: e => setConversationForm({...conversationForm, user_id: e.target.value}) }),
                    h("label", { className: "tiny" }, "Username"), h("input", { value: conversationForm.username, onChange: e => setConversationForm({...conversationForm, username: e.target.value}) }),
                    h("div", { style: { marginTop: "12px" } }, Btn("btn-green", "Create", () => {
                        const payload = { conversation_id: Number(conversationForm.conversation_id), user_id: Number(conversationForm.user_id), username: conversationForm.username || "" };
                        postJSON("/reporting/add_conversation_full", payload).then(() => { setMenuOpen(false); refreshConversations(); });
                    }))
                ),
                menuOpen === "edit_turn" && h("div", null,
                    h("label", { className: "tiny" }, "Rating (0-5)"), h("input", { type:"number", value: turnForm.rating, onChange: e => setTurnForm({...turnForm, rating: e.target.value}) }),
                    h("label", { className: "tiny" }, "Question"), h("textarea", { value: turnForm.question, onChange: e => setTurnForm({...turnForm, question: e.target.value}) }),
                    h("label", { className: "tiny" }, "Answer"), h("textarea", { value: turnForm.answer, onChange: e => setTurnForm({...turnForm, answer: e.target.value}) }),
                    h("div", { style: { marginTop: "12px" } }, Btn("btn-green", "Save", () => postJSON(turnForm.turn_id ? "/reporting/update_turn" : "/reporting/add_turn", { ...turnForm, turn_id: turnForm.turn_id ? Number(turnForm.turn_id) : undefined, conversation_id: Number(selectedConv), rating: Number(turnForm.rating) }).then(() => { setMenuOpen(false); loadConversation(selectedConv); refreshConversations(); })))
                )
            )
        )
    );
}

ReactDOM.createRoot(document.getElementById('root')).render(h(App));
</script>
</body>
</html>