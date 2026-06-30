"""
app.py — Government Scheme Assistant (single-file Flask web app)

A polished, demo-ready chatbot UI over two pre-built engines:
  - knowledge.get_answer(question)            -> str
  - eligibility.check_eligibility(scheme, ans) -> {"eligible": bool, "reason": str}

Run:
    python app.py
Then open http://127.0.0.1:5000

Everything (HTML/CSS/JS) lives in this one file. No external assets.
"""

import os
from flask import Flask, request, jsonify, render_template_string

# ── Pre-built engines (imported, never rewritten) ────────────────────────────
from knowledge import get_answer
from eligibility import check_eligibility

app = Flask(__name__)

# ── Scheme + form-field metadata ─────────────────────────────────────────────
# `type` drives both the dynamically-built form AND server-side coercion.
SCHEMES = {
    "pmkisan": {
        "name": "PM-KISAN",
        "full": "Pradhan Mantri Kisan Samman Nidhi",
        "tag": "₹6,000/year income support for small & marginal farmers",
        "emoji": "🌾",
        "fields": [
            {"key": "owns_land",        "label": "Do you own cultivable land?",          "type": "bool"},
            {"key": "land_hectares",    "label": "How much land do you own (hectares)?",  "type": "number", "step": "0.1", "min": "0", "placeholder": "e.g. 1.5"},
            {"key": "is_govt_employee", "label": "Are you a government employee?",         "type": "bool"},
            {"key": "is_taxpayer",      "label": "Are you an income-tax payer?",           "type": "bool"},
            {"key": "is_professional",  "label": "Are you a professional (doctor/CA/etc.)?", "type": "bool"},
        ],
    },
    "pmss": {
        "name": "PM Scholarship",
        "full": "PM Scholarship Scheme (PMSS)",
        "tag": "Scholarships for wards of ex-servicemen pursuing professional degrees",
        "emoji": "🎓",
        "fields": [
            {"key": "is_ward_of_exserviceman", "label": "Are you a ward of an ex-serviceman / ex-coast guard?", "type": "bool"},
            {"key": "class12_percentage",      "label": "Your Class 12 percentage (%)",                          "type": "number", "step": "0.1", "min": "0", "max": "100", "placeholder": "e.g. 75"},
            {"key": "annual_family_income",    "label": "Annual family income (₹)",                              "type": "number", "step": "1000", "min": "0", "placeholder": "e.g. 450000"},
            {"key": "is_pursuing_professional","label": "Pursuing a professional degree (Engg/Medical/MBA/MCA)?","type": "bool"},
        ],
    },
    "pmjay": {
        "name": "Ayushman Bharat",
        "full": "Ayushman Bharat PM-JAY",
        "tag": "Free health cover up to ₹5 lakh/year for eligible families",
        "emoji": "🏥",
        "fields": [
            {"key": "annual_family_income",     "label": "Annual family income (₹)",                 "type": "number", "step": "1000", "min": "0", "placeholder": "e.g. 250000"},
            {"key": "has_govt_health_insurance","label": "Already covered by a govt health scheme?",  "type": "bool"},
            {"key": "is_govt_employee",         "label": "Are you a government employee?",            "type": "bool"},
            {"key": "family_size",              "label": "How many people in your family?",           "type": "number", "step": "1", "min": "1", "placeholder": "e.g. 4"},
        ],
    },
}

_TRUE = {"true", "yes", "1", "on", True, 1}


def coerce_answers(scheme: str, raw: dict) -> dict:
    """Turn the JSON form payload into the real bool/float types the engine expects."""
    answers = {}
    for f in SCHEMES.get(scheme, {}).get("fields", []):
        key, ftype = f["key"], f["type"]
        val = raw.get(key)
        if ftype == "bool":
            answers[key] = (str(val).strip().lower() in {"true", "yes", "1", "on"}) if not isinstance(val, bool) else val
        else:  # number — keep whole numbers as int so verdicts read "4" not "4.0"
            try:
                num = float(val)
                answers[key] = int(num) if num.is_integer() else num
            except (TypeError, ValueError):
                answers[key] = 0
    return answers


# ── Routes ───────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template_string(PAGE, schemes=SCHEMES)


@app.route("/emblem.png")
def emblem():
    from flask import send_file
    return send_file("emblem.png")


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json(force=True, silent=True) or {}
    question = (data.get("question") or "").strip()
    if not question:
        return jsonify({"answer": "Please type a question so I can help. 🙂"})
    try:
        answer = get_answer(question)
    except Exception as exc:  # keep the demo alive even if the LLM/key is unavailable
        answer = ("⚠️ The knowledge engine is unavailable right now. "
                  "Make sure your GROQ_API_KEY is set and dependencies are installed.\n\n"
                  f"(Technical detail: {exc})")
    return jsonify({"answer": answer})


@app.route("/eligibility", methods=["POST"])
def eligibility():
    data = request.get_json(force=True, silent=True) or {}
    scheme = (data.get("scheme") or "").strip().lower()
    answers = coerce_answers(scheme, data.get("answers") or {})
    try:
        result = check_eligibility(scheme, answers)
    except Exception as exc:
        result = {"eligible": False, "reason": f"Could not evaluate eligibility: {exc}"}
    return jsonify(result)


# ── Single-page template (HTML + CSS + JS, all inline) ───────────────────────
PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Government Scheme Assistant</title>
<style>
  :root{
    --saffron:#ff8a1f; --saffron-soft:#ffd9b0;
    --green:#0f9d58; --green-soft:#c9f2dd;
    --navy:#0b1f5e; --chakra:#1a3fb8;
    --ink:#1b2240; --muted:#6b7392;
    --card:#ffffff; --line:#eceef6;
    --bot-bg:#f4f6fc; --user-bg:linear-gradient(135deg,#1a3fb8,#3a63e8);
    --ok:#0f9d58; --no:#e2433a;
    --shadow:0 20px 60px rgba(20,28,70,.18);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  html,body{height:100%}
  body{
    font-family:"Segoe UI",Roboto,system-ui,-apple-system,sans-serif;
    color:var(--ink);
    min-height:100vh;
    background:
      radial-gradient(1100px 540px at 8% -10%, #ffe9d2 0%, transparent 55%),
      radial-gradient(1100px 540px at 105% 8%, #d6f4e4 0%, transparent 52%),
      linear-gradient(160deg,#f3f5fc 0%, #eef1fb 50%, #f6f3ff 100%);
    display:flex; align-items:center; justify-content:center;
    padding:26px 16px;
  }

  .app{
    width:100%; max-width:780px;
    background:var(--card);
    border-radius:26px;
    box-shadow:var(--shadow);
    overflow:hidden;
    display:flex; flex-direction:column;
    height:min(92vh,920px);
    border:1px solid rgba(255,255,255,.6);
  }

  /* ── Header ── */
  header{position:relative; padding:20px 24px 16px; color:#fff;
    background:linear-gradient(120deg,#0b1f5e 0%, #1a3fb8 60%, #2b54d6 100%);}
  header .tricolor{position:absolute;left:0;right:0;top:0;height:5px;
    background:linear-gradient(90deg,var(--saffron) 0 33.3%, #ffffff 33.3% 66.6%, var(--green) 66.6% 100%);}
  .brand{display:flex; align-items:center; gap:14px}
  .emblem{width:46px;height:46px;border-radius:14px;display:flex;align-items:center;justify-content:center;
    background:rgba(255,255,255,.14);
    border:1px solid rgba(255,255,255,.25); backdrop-filter:blur(6px); overflow:hidden}
  .emblem img{max-width:28px;max-height:38px;object-fit:contain;opacity:0.95}
  .brand h1{font-size:20px;font-weight:700;letter-spacing:.2px}
  .brand p{font-size:12.5px;opacity:.82;margin-top:2px}

  /* ── Scheme pills ── */
  .pills{display:flex;gap:10px;margin-top:16px;flex-wrap:wrap}
  .pill{
    flex:1 1 0; min-width:150px; cursor:pointer;
    border:1px solid rgba(255,255,255,.28);
    background:rgba(255,255,255,.10);
    color:#eaf0ff; border-radius:14px; padding:10px 12px;
    display:flex;align-items:center;gap:10px;
    transition:.22s ease; text-align:left;
  }
  .pill:hover{background:rgba(255,255,255,.2); transform:translateY(-1px)}
  .pill .pe{font-size:19px}
  .pill .pt{line-height:1.15}
  .pill .pt b{font-size:13.5px;font-weight:700;display:block}
  .pill .pt span{font-size:11px;opacity:.8}
  .pill.active{background:#fff;color:var(--navy);border-color:#fff;
    box-shadow:0 8px 22px rgba(0,0,0,.22)}
  .pill.active .pt span{color:var(--muted);opacity:1}

  /* ── Chat area ── */
  .chat{flex:1; overflow-y:auto; padding:22px 22px 8px;
    background:linear-gradient(180deg,#fbfcff,#f6f8ff); scroll-behavior:smooth}
  .chat::-webkit-scrollbar{width:9px}
  .chat::-webkit-scrollbar-thumb{background:#d8ddf0;border-radius:20px}

  .row{display:flex;margin:12px 0;gap:10px;align-items:flex-end}
  .row.user{justify-content:flex-end}
  .avatar{width:34px;height:34px;border-radius:50%;flex:0 0 34px;
    display:grid;place-items:center;font-size:17px;box-shadow:0 4px 12px rgba(20,28,70,.12);
    animation:scaleIn 0.3s cubic-bezier(.2,.8,.2,1) both}
  .avatar.bot{background:linear-gradient(135deg,#ffedd9,#ffd9b0)}
  .avatar.usr{background:linear-gradient(135deg,#dbe4ff,#b9c8ff)}
  @keyframes scaleIn {
    from { opacity: 0; transform: scale(0.6); }
    to { opacity: 1; transform: scale(1); }
  }

  .bubble{
    max-width:74%; padding:12px 15px; border-radius:18px; font-size:14.5px;
    line-height:1.55; white-space:pre-wrap; word-wrap:break-word;
    animation:pop .32s cubic-bezier(.2,.8,.2,1) both;
  }
  .bubble.bot{background:var(--bot-bg);border:1px solid var(--line);
    border-bottom-left-radius:6px;color:var(--ink);white-space:normal;
    transform-origin: left bottom}
  /* formatted bot content: preserve line breaks + render lists cleanly */
  .bubble.bot .ln{margin:0;min-height:.2em}
  .bubble.bot .ln.blank{height:.55em}
  .bubble.bot .li{display:flex;gap:8px;margin:3px 0}
  .bubble.bot .li .mk{flex:0 0 auto;font-weight:700;color:var(--chakra);min-width:14px}
  .bubble.bot .li .tx{flex:1}
  .bubble.user{background:var(--user-bg);color:#fff;
    border-bottom-right-radius:6px;box-shadow:0 8px 20px rgba(26,63,184,.28);
    transform-origin: right bottom}
  @keyframes pop{from{opacity:0;transform:translateY(10px) scale(.95)}
                 to{opacity:1;transform:translateY(0) scale(1)}}

  /* fade-out and shrink-out animations for smooth exits */
  .fade-out {
    animation: fadeOut 0.15s cubic-bezier(0.4, 0, 1, 1) forwards !important;
  }
  @keyframes fadeOut {
    from { opacity: 1; transform: scale(1); }
    to { opacity: 0; transform: scale(0.95); }
  }

  .shrink-out {
    animation: shrinkOut 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards !important;
  }
  @keyframes shrinkOut {
    from { opacity: 1; transform: scale(1); max-height: 500px; margin-top: 12px; margin-bottom: 12px; }
    to { opacity: 0; transform: scale(0.92); max-height: 0; margin-top: 0; margin-bottom: 0; padding-top: 0; padding-bottom: 0; border-width: 0; overflow: hidden; }
  }

  /* typing indicator — three bouncing dots */
  .typing{display:flex;gap:6px;padding:15px 16px;align-items:center}
  .typing i{width:9px;height:9px;border-radius:50%;background:#aab2d4;display:inline-block;
    animation:bounce 1.2s infinite ease-in-out both}
  .typing i:nth-child(1){animation-delay:-.24s}
  .typing i:nth-child(2){animation-delay:-.12s}
  @keyframes bounce{0%,80%,100%{transform:translateY(0) scale(.85);opacity:.45}
                    40%{transform:translateY(-6px) scale(1);opacity:1}}

  /* verdict card */
  .verdict{max-width:80%;border-radius:18px;padding:14px 16px;border-left:6px solid;
    background:#fff;border:1px solid var(--line);box-shadow:0 10px 26px rgba(20,28,70,.1);
    animation:pop .35s cubic-bezier(.2,.8,.2,1) both; transform-origin: left bottom}
  .verdict.ok{border-left-color:var(--ok);background:linear-gradient(180deg,#f3fcf7,#fff)}
  .verdict.no{border-left-color:var(--no);background:linear-gradient(180deg,#fdf4f3,#fff)}
  .verdict .vhead{display:flex;align-items:center;gap:9px;font-weight:800;font-size:15px;margin-bottom:5px}
  .verdict.ok .vhead{color:var(--ok)} .verdict.no .vhead{color:var(--no)}
  .verdict .vbody{font-size:14px;line-height:1.55;color:var(--ink)}

  /* eligibility form card */
  .formcard{max-width:88%;width:480px;background:#fff;border:1px solid var(--line);
    border-radius:18px;padding:16px 18px;box-shadow:0 12px 30px rgba(20,28,70,.12);
    animation:pop .35s cubic-bezier(.2,.8,.2,1) both; transform-origin: left bottom}
  .formcard h3{font-size:15px;display:flex;align-items:center;gap:8px;margin-bottom:3px}
  .formcard .sub{font-size:12px;color:var(--muted);margin-bottom:12px}
  .field{margin-bottom:11px}
  .field label{display:block;font-size:13px;font-weight:600;margin-bottom:5px;color:#33406b}
  .field input,.field select{
    width:100%;padding:10px 12px;border:1.5px solid #e3e7f4;border-radius:11px;
    font-size:14px;font-family:inherit;background:#fbfcff;transition:.18s;color:var(--ink)}
  .field input:focus,.field select:focus{outline:none;border-color:var(--chakra);
    background:#fff;box-shadow:0 0 0 4px rgba(26,63,184,.12)}
  .formbtns{display:flex;gap:10px;margin-top:14px}
  .btn{border:none;cursor:pointer;font-family:inherit;font-weight:700;border-radius:11px;
    padding:11px 16px;font-size:14px;transition:.2s}
  .btn-primary{flex:1;color:#fff;background:linear-gradient(135deg,#0f9d58,#13b765);
    box-shadow:0 8px 20px rgba(15,157,88,.32)}
  .btn-primary:hover{transform:translateY(-1px);filter:brightness(1.04)}
  .btn-primary:active{transform:translateY(0)}
  .btn-ghost{background:#f0f2fa;color:var(--muted)}
  .btn-ghost:hover{background:#e7eaf6}
  .btn-ghost:active{background:#dfe2f0}

  /* ── Composer ── */
  .composer{padding:14px 16px 16px;border-top:1px solid var(--line);background:#fff}
  .elig-btn{display:inline-flex;align-items:center;gap:7px;cursor:pointer;
    border:1.5px solid var(--saffron-soft);background:linear-gradient(135deg,#fff6ed,#ffeede);
    color:#b8540a;font-weight:700;font-size:12.5px;border-radius:999px;padding:7px 13px;margin-bottom:11px;
    transition: all .25s cubic-bezier(0.4, 0, 0.2, 1)}
  .elig-btn:hover{transform:translateY(-2px);box-shadow:0 6px 16px rgba(255,138,31,.25)}
  .elig-btn:active{transform:translateY(0)}
  .inputbar{display:flex;gap:10px;align-items:flex-end}
  .inputbar textarea{
    flex:1;resize:none;max-height:120px;min-height:48px;font-family:inherit;font-size:14.5px;
    padding:13px 15px;border:1.5px solid #e3e7f4;border-radius:15px;background:#fbfcff;
    line-height:1.4;transition: border-color .2s, box-shadow .2s, background-color .2s;color:var(--ink)}
  .inputbar textarea:focus{outline:none;border-color:var(--chakra);background:#fff;
    box-shadow:0 0 0 4px rgba(26,63,184,.10)}
  .inputbar textarea:disabled{opacity:0.7;cursor:not-allowed;background:#f1f3f9}
  .send{width:50px;height:50px;flex:0 0 50px;border-radius:15px;border:none;cursor:pointer;
    background:linear-gradient(135deg,#1a3fb8,#3a63e8);color:#fff;font-size:20px;
    display:grid;place-items:center;box-shadow:0 8px 20px rgba(26,63,184,.3);
    transition: all .2s cubic-bezier(0.4, 0, 0.2, 1)}
  .send:hover{transform:translatey(-2px) scale(1.05);box-shadow:0 10px 22px rgba(26,63,184,.4)}
  .send:active{transform:translatey(0) scale(0.98)}
  .send:disabled{opacity:.5;cursor:not-allowed;transform:none;box-shadow:none}
  .hint{font-size:11px;color:var(--muted);text-align:center;margin-top:9px}

  /* suggested question chips */
  .chips{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px 44px}
  .chip{cursor:pointer;border:1.5px solid #dfe4f5;background:#fff;color:var(--chakra);
    font-size:12.5px;font-weight:600;border-radius:999px;padding:8px 14px;
    transition: all .2s cubic-bezier(0.4, 0, 0.2, 1);
    animation:pop .3s cubic-bezier(.2,.8,.2,1) both}
  .chip:nth-child(1){animation-delay:0.05s}
  .chip:nth-child(2){animation-delay:0.12s}
  .chip:nth-child(3){animation-delay:0.19s}
  .chip:nth-child(4){animation-delay:0.26s}
  .chip:hover{background:#eef2ff;border-color:var(--chakra);transform:translateY(-2px);
    box-shadow:0 6px 16px rgba(26,63,184,.16)}
  .chip:active{transform:translateY(0)}
  .chip:disabled{opacity:.5;cursor:not-allowed;transform:none;box-shadow:none}

  /* attention pulse on the eligibility button */
  .elig-btn.pulse{animation:elig-pulse 1.1s ease-in-out infinite}
  @keyframes elig-pulse{
    0%,100%{box-shadow:0 0 0 0 rgba(255,138,31,.5); transform: scale(1);}
    50%{box-shadow:0 0 0 10px rgba(255,138,31,0); transform: scale(1.03);}
  }

  /* ── Dark Mode overrides ── */
  body.dark {
    --ink: #e2e5f3;
    --muted: #9fa7c7;
    --card: #151a30;
    --line: #262c4b;
    --bot-bg: #1d233d;
    --shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
    --saffron-soft: #4d2e12;
    --green-soft: #0e3d24;
    background:
      radial-gradient(1100px 540px at 8% -10%, #3a220f 0%, transparent 55%),
      radial-gradient(1100px 540px at 105% 8%, #0b301c 0%, transparent 52%),
      linear-gradient(160deg,#0a0d1a 0%, #0e1226 50%, #0c081d 100%);
  }
  body.dark .app {
    border: 1px solid rgba(255,255,255,.08);
  }
  body.dark .chat {
    background: linear-gradient(180deg,#121628,#151a30);
  }
  body.dark .chat::-webkit-scrollbar-thumb {
    background: #2d355a;
  }
  body.dark .formcard, body.dark .verdict {
    background: #1b213b;
    border-color: #2d355a;
  }
  body.dark .verdict.ok {
    background: linear-gradient(180deg,#0b2d1c,#151a30);
  }
  body.dark .verdict.no {
    background: linear-gradient(180deg,#3b1a18,#151a30);
  }
  body.dark .field label {
    color: #a9beff;
  }
  body.dark .field input, body.dark .field select {
    background: #121628;
    border-color: #2d355a;
    color: var(--ink);
  }
  body.dark .field input:focus, body.dark .field select:focus {
    background: #151a30;
    border-color: var(--chakra);
  }
  body.dark .btn-ghost {
    background: #1c223c;
    color: var(--muted);
  }
  body.dark .btn-ghost:hover {
    background: #252b4e;
  }
  body.dark .btn-ghost:active {
    background: #1c223c;
  }
  body.dark .composer {
    background: #151a30;
    border-top-color: #262c4b;
  }
  body.dark .elig-btn {
    background: linear-gradient(135deg,#2e1e12,#3a2818);
    border-color: #613e1c;
    color: #ffa352;
  }
  body.dark .inputbar textarea {
    background: #1c223c;
    border-color: #2d355a;
  }
  body.dark .inputbar textarea:focus {
    background: #151a30;
  }
  body.dark .inputbar textarea:disabled {
    background: #121628;
  }
  body.dark .chip {
    background: #1c223c;
    border-color: #2d355a;
    color: #8fa7ff;
  }
  body.dark .chip:hover {
    background: #252b4e;
    border-color: var(--chakra);
    color: #b0c2ff;
  }
  .theme-toggle{
    position:absolute; top:20px; right:24px;
    width:38px; height:38px; border-radius:12px;
    border:1px solid rgba(255,255,255,.25);
    background:rgba(255,255,255,.10);
    color:#fff; font-size:18px; cursor:pointer;
    display:grid; place-items:center; backdrop-filter:blur(6px);
    transition: all .25s cubic-bezier(0.4, 0, 0.2, 1);
    z-index: 10;
  }
  .theme-toggle:hover{
    background:rgba(255,255,255,.2);
    transform:translateY(-2px) scale(1.05);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  }
  .theme-toggle:active{
    transform:translateY(0) scale(0.98);
  }

  @media (max-width:560px){
    .app{height:94vh;border-radius:20px}
    .bubble,.verdict{max-width:86%}
    .pill{min-width:0;flex:1 1 30%}
    .pill .pt span{display:none}
    .formcard{width:100%}
    .chips{margin-left:0}
    .theme-toggle{top:15px; right:15px; width:34px; height:34px; font-size:16px}
  }
</style>
</head>
<body>
  <script>
    (function(){
      const savedTheme = localStorage.getItem("theme");
      const systemPrefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      if (savedTheme === "dark" || (!savedTheme && systemPrefersDark)) {
        document.body.classList.add("dark");
      }
    })();
  </script>
  <div class="app">
    <header>
      <div class="tricolor"></div>
      <button class="theme-toggle" id="themeBtn" onclick="toggleTheme()" title="Switch Theme">🌙</button>
      <div class="brand">
        <div class="emblem"><img src="/emblem.png" alt="State Emblem of India" /></div>
        <div>
          <h1>Government Scheme Assistant</h1>
          <p>Ask about benefits &amp; instantly check if you qualify</p>
        </div>
      </div>
      <div class="pills" id="pills">
        {% for key, s in schemes.items() %}
        <button class="pill" data-scheme="{{ key }}" onclick="selectScheme('{{ key }}')">
          <span class="pe">{{ s.emoji }}</span>
          <span class="pt"><b>{{ s.name }}</b><span>{{ s.full }}</span></span>
        </button>
        {% endfor %}
      </div>
    </header>

    <div class="chat" id="chat"></div>

    <div class="composer">
      <button class="elig-btn" onclick="openEligibility()">📋 Check my eligibility</button>
      <div class="inputbar">
        <textarea id="q" rows="1" placeholder="Ask anything… e.g. “What documents do I need for PM-KISAN?”"
          onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();sendQuestion();}"
          oninput="autoGrow(this)"></textarea>
        <button class="send" id="sendBtn" onclick="sendQuestion()" title="Send">➤</button>
      </div>
      <div class="hint">Press <b>Enter</b> to send • <b>Shift+Enter</b> for a new line</div>
    </div>
  </div>

<script>
  const SCHEMES = {{ schemes|tojson }};
  let current = "pmkisan";
  let busy = false;                       // guards against double-sends / overlapping requests
  const chat = document.getElementById("chat");
  const ELIG_INTENT = ["eligible","qualify","should i apply","do i qualify","am i able"];

  // ── theme management ───────────────────────────────────────
  function toggleTheme(){
    const body = document.body;
    const isDark = body.classList.toggle("dark");
    localStorage.setItem("theme", isDark ? "dark" : "light");
    updateThemeUI(isDark);
  }

  function updateThemeUI(isDark){
    const btn = document.getElementById("themeBtn");
    if(btn){
      btn.innerHTML = isDark ? "☀️" : "🌙";
      btn.title = isDark ? "Switch to Light Mode" : "Switch to Dark Mode";
    }
  }

  // ── helpers ────────────────────────────────────────────────
  function autoGrow(el){ el.style.height="auto"; el.style.height=Math.min(el.scrollHeight,120)+"px"; }
  function scrollDown(){ chat.scrollTop = chat.scrollHeight; }
  function esc(s){ const d=document.createElement("div"); d.textContent=s; return d.innerHTML; }

  // Escape, then preserve newlines and render numbered/bulleted lists readably.
  function formatBot(text){
    const lines = String(text==null ? "" : text).split(/\r?\n/);
    return lines.map(raw=>{
      const line = raw.replace(/\s+$/,"");
      if(line.trim()==="") return `<div class="ln blank"></div>`;
      const m = line.match(/^\s*(\d+[.)]|[-*•·])\s+(.*)$/);
      if(m){
        const mk = /^\d/.test(m[1]) ? m[1] : "•";
        return `<div class="li"><span class="mk">${esc(mk)}</span><span class="tx">${esc(m[2])}</span></div>`;
      }
      return `<div class="ln">${esc(line)}</div>`;
    }).join("");
  }

  // Lock/unlock the composer while a request is in flight.
  function setBusy(b){
    busy = b;
    const box = document.getElementById("q");
    const btn = document.getElementById("sendBtn");
    btn.disabled = b; box.disabled = b;
    document.querySelectorAll(".chip").forEach(c => c.disabled = b);
    if(!b){ box.focus(); }
  }

  function matchesEligIntent(text){
    const t = text.toLowerCase();
    return ELIG_INTENT.some(k => t.includes(k));
  }

  function pulseEligBtn(){
    const b = document.querySelector(".elig-btn");
    if(!b) return;
    b.classList.add("pulse");
    clearTimeout(b._pulseTimer);
    b._pulseTimer = setTimeout(()=>b.classList.remove("pulse"), 6000);
  }

  function addUser(text){
    const row=document.createElement("div"); row.className="row user";
    row.innerHTML=`<div class="bubble user">${esc(text)}</div><div class="avatar usr">🧑</div>`;
    chat.appendChild(row); scrollDown();
  }
  function addBot(text){
    const row=document.createElement("div"); row.className="row";
    row.innerHTML=`<div class="avatar bot">🤖</div><div class="bubble bot">${formatBot(text)}</div>`;
    chat.appendChild(row); scrollDown(); return row;
  }

  // smooth removal and exit animations
  function removeElementSmoothly(el, callback) {
    el.classList.add("fade-out");
    let called = false;
    const done = () => {
      if (called) return;
      called = true;
      el.remove();
      if (callback) callback();
    };
    el.addEventListener("animationend", done);
    setTimeout(done, 200);
  }

  function shrinkElementSmoothly(el, callback) {
    el.classList.add("shrink-out");
    let called = false;
    const done = () => {
      if (called) return;
      called = true;
      el.remove();
      if (callback) callback();
    };
    el.addEventListener("animationend", done);
    setTimeout(done, 350);
  }

  function removeChips(){
    const tray = chat.querySelector(".chips");
    if(tray){
      removeElementSmoothly(tray);
    }
  }

  // suggested-question chips shown under the welcome message
  function addChips(){
    const tray=document.createElement("div"); tray.className="chips";
    [["What is this scheme?","ask"],
     ["Documents needed","ask"],
     ["How to apply","ask"],
     ["Am I eligible?","elig"]].forEach(([label,kind])=>{
      const b=document.createElement("button"); b.className="chip"; b.type="button"; b.textContent=label;
      b.onclick=()=>{
        if(busy) return;
        removeChips();
        if(kind==="elig"){ addUser(label); openEligibility(); }
        else { sendQuestion(label); }
      };
      tray.appendChild(b);
    });
    chat.appendChild(tray); scrollDown();
  }
  function addTyping(){
    const row=document.createElement("div"); row.className="row";
    row.innerHTML=`<div class="avatar bot">🤖</div><div class="bubble bot typing"><i></i><i></i><i></i></div>`;
    chat.appendChild(row); scrollDown(); return row;
  }

  // ── scheme selector ────────────────────────────────────────
  function selectScheme(key){
    current=key;
    document.querySelectorAll(".pill").forEach(p=>
      p.classList.toggle("active", p.dataset.scheme===key));
    const s=SCHEMES[key];
    addBot(`${s.emoji} You're now exploring ${s.full}.\n${s.tag}\n\nAsk me a question, or tap “Check my eligibility”.`);
  }

  // ── ask the knowledge engine ───────────────────────────────
  async function sendQuestion(presetText){
    if(busy) return;                                  // prevent double-sends
    const box=document.getElementById("q");
    const typed = presetText!==undefined ? presetText : box.value;
    const text=(typed||"").trim();
    if(!text) return;                                 // prevent empty sends
    removeChips();
    addUser(text);
    if(presetText===undefined){ box.value=""; autoGrow(box); }
    setBusy(true);
    const t=addTyping();
    let ok=false;
    try{
      const r=await fetch("/ask",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({question:text})});
      if(!r.ok) throw new Error("HTTP "+r.status);
      const data=await r.json();
      removeElementSmoothly(t, () => {
        addBot(data.answer || "Sorry, I didn't get a response.");
        // Auto-open the eligibility form when the message signals eligibility intent.
        // Open first, then pulse — openEligibility() clears any existing pulse on entry.
        if(ok && matchesEligIntent(text)){
          openEligibility();
          pulseEligBtn();
        }
      });
      ok=true;
    }catch(e){
      removeElementSmoothly(t, () => {
        addBot("⚠️ Something went wrong. Please try again.");
      });
    }finally{ setBusy(false); }
  }

  // ── eligibility form (built dynamically from selected scheme) ──
  function openEligibility(){
    const eb=document.querySelector(".elig-btn"); if(eb) eb.classList.remove("pulse");
    // If a form is already open, just bring it into view instead of stacking another.
    const existing=chat.querySelector(".formcard");
    if(existing){
      const row = existing.closest(".row");
      if(row){
        chat.scrollTo({
          top: row.offsetTop - chat.offsetTop,
          behavior: "smooth"
        });
      }
      return;
    }
    const s=SCHEMES[current];
    const row=document.createElement("div"); row.className="row";
    const fields=s.fields.map(f=>{
      if(f.type==="bool"){
        return `<div class="field"><label>${esc(f.label)}</label>
          <select data-key="${f.key}">
            <option value="false">No</option>
            <option value="true">Yes</option>
          </select></div>`;
      }
      const attrs=[`type="number"`,`data-key="${f.key}"`];
      if(f.step) attrs.push(`step="${f.step}"`);
      if(f.min!==undefined) attrs.push(`min="${f.min}"`);
      if(f.max!==undefined) attrs.push(`max="${f.max}"`);
      attrs.push(`placeholder="${f.placeholder||''}"`);
      return `<div class="field"><label>${esc(f.label)}</label><input ${attrs.join(" ")} /></div>`;
    }).join("");

    row.innerHTML=`<div class="avatar bot">📋</div>
      <div class="formcard">
        <h3>${s.emoji} ${esc(s.full)}</h3>
        <div class="sub">Fill this in and I'll check your eligibility instantly.</div>
        <div class="fields">${fields}</div>
        <div class="formbtns">
          <button class="btn btn-primary">Check eligibility</button>
          <button class="btn btn-ghost">Cancel</button>
        </div>
      </div>`;
    chat.appendChild(row); scrollDown();

    const schemeAtOpen=current;
    row.querySelector(".btn-primary").onclick=()=>submitEligibility(row,schemeAtOpen);
    row.querySelector(".btn-ghost").onclick=()=>shrinkElementSmoothly(row);
  }

  async function submitEligibility(row,scheme){
    if(busy) return;
    const answers={};
    row.querySelectorAll("[data-key]").forEach(el=>answers[el.dataset.key]=el.value);
    const btn=row.querySelector(".btn-primary");
    btn.disabled=true; btn.textContent="Checking…";
    setBusy(true);

    const t=addTyping();
    try{
      const r=await fetch("/eligibility",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({scheme,answers})});
      if(!r.ok) throw new Error("HTTP "+r.status);
      const data=await r.json();
      removeElementSmoothly(t, () => {
        addVerdict(data.eligible, data.reason);
      });
      shrinkElementSmoothly(row);
    }catch(e){
      removeElementSmoothly(t, () => {
        addBot("⚠️ Something went wrong. Please try again.");
      });
      btn.disabled=false; btn.textContent="Check eligibility";
    }finally{ setBusy(false); }
  }

  function addVerdict(ok, reason){
    const row=document.createElement("div"); row.className="row";
    const cls=ok?"ok":"no";
    const head=ok?"✅ You are Eligible":"❌ Not Eligible";
    row.innerHTML=`<div class="avatar bot">${ok?'🎉':'📄'}</div>
      <div class="verdict ${cls}">
        <div class="vhead">${head}</div>
        <div class="vbody">${esc(reason||"")}</div>
      </div>`;
    chat.appendChild(row); scrollDown();
  }

  // ── boot ───────────────────────────────────────────────────
  window.addEventListener("DOMContentLoaded",()=>{
    updateThemeUI(document.body.classList.contains("dark"));
    document.querySelector('.pill[data-scheme="pmkisan"]').classList.add("active");
    addBot("🙏 Namaste! I'm your Government Scheme Assistant.\n\nI can explain three schemes — PM-KISAN 🌾, PM Scholarship 🎓 and Ayushman Bharat PM-JAY 🏥 — and check whether you qualify.\n\nPick a scheme above, ask a question, or tap “Check my eligibility”.");
    addChips();
  });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    # Honour the PORT env var (used by the preview launcher); default to 5000.
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
