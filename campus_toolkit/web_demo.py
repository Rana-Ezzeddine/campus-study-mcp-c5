"""Optional loopback-only chat window for demonstrating the existing MCP agent."""
from __future__ import annotations

import asyncio
from concurrent.futures import Future
from contextlib import redirect_stdout
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import os
from pathlib import Path
from queue import Queue
import secrets
import threading
from urllib.parse import urlsplit

from agents import set_tracing_disabled
from .agent import ROOT, build_agent, connection, run_turn

HOST, PORT = "127.0.0.1", int(os.getenv("CAMPUS_DEMO_PORT", "8767"))
TOKEN = secrets.token_urlsafe(32)
REQUESTS = Queue()
READY = threading.Event()
START_ERROR = []

PAGE = r'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Campus Study Assistant</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f5f4;color:#182d27;font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:980px;margin:auto;padding:36px 24px}small,.muted{color:#64736d}h1{font-size:34px;letter-spacing:-1px;margin:8px 0}header{margin-bottom:24px}.tags{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}.tag{background:#e3ebe6;padding:6px 12px;border-radius:20px;font-size:13px}.prompts{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}button{font:inherit;cursor:pointer;border:1px solid #cdd7d1;background:white;border-radius:12px;padding:14px;text-align:left;color:inherit}button:hover{background:#e9f0ec}button:disabled{opacity:.5;cursor:wait}.prompts b{display:block;font-size:14px}.prompts span{display:block;font-size:13px;margin-top:5px;color:#64736d}#chat{margin:24px 0;display:grid;gap:16px}.message{padding:18px 22px;border-radius:16px;background:white;border:1px solid #e1e7e3;white-space:pre-wrap}.user{background:#dcebe3;margin-left:12%}.label{font-size:11px;font-weight:700;letter-spacing:1px;margin-bottom:7px;color:#587366}details{white-space:normal;margin-top:14px;border-top:1px solid #e1e7e3;padding-top:12px;font-size:13px}summary{cursor:pointer;font-weight:600}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f4;padding:12px;border-radius:8px;font-size:12px}form{display:flex;gap:10px;position:sticky;bottom:0;background:#f3f5f4;padding:12px 0}input{font:inherit;flex:1;min-width:0;padding:16px;border:1px solid #cdd7d1;border-radius:12px}form button{background:#214f3d;color:white;min-width:86px;text-align:center}#status{font-size:13px;margin-top:12px;min-height:22px}@media(max-width:650px){.prompts{grid-template-columns:1fr}main{padding:22px 16px}h1{font-size:28px}}</style>
<main><header><small>MCP TOOLKIT · LIVE DEMONSTRATION</small><h1>Campus Study Assistant</h1><div class="muted">Find and reserve fictional campus study rooms. Free model running on your Mac.</div><div class="tags"><span class="tag">FastMCP</span><span class="tag">OpenAI Agents SDK</span><span class="tag">Local Ollama</span><span class="tag">Exactly 3 tools</span></div></header>
<div class="prompts"><button data-prompt="Which quiet rooms are available for 2 people on __DAY__ at 10:00 Beirut time? Only look up availability."><b>1 · Data tool</b><span>Find quiet rooms for two people.</span></button><button data-prompt="Book fictional room CEDAR-2 for Rana, 2 people, on __DAY__ at 10:00 Beirut time."><b>2 · Action tool</b><span>Reserve the room I selected.</span></button><button data-prompt="Find and book a quiet fictional room for Rana, 3 people, on __DAY__ at 10:00 Beirut time."><b>3 · Orchestration tool</b><span>Find a suitable room and reserve it.</span></button></div>
<div id="status">Connecting to your local agent…</div><div id="chat"></div><form><input id="prompt" aria-label="Your request" placeholder="Ask about a room or make a reservation…" autocomplete="off" required maxlength="4000"><button id="send">Send</button></form><small>Include all booking details in each request. Reservations last one hour, use Beirut time, and are saved in this demo session. Expand a reply to see the real MCP calls and results.</small></main>
<script>
const token='__TOKEN__',chat=document.querySelector('#chat'),status=document.querySelector('#status'),input=document.querySelector('#prompt');let busy=false,ready=false;
function controls(){document.querySelectorAll('button').forEach(b=>b.disabled=busy||!ready);input.disabled=busy||!ready}
function message(label,text,kind){const d=document.createElement('div');d.className='message '+kind;const l=document.createElement('div');l.className='label';l.textContent=label;d.append(l,document.createTextNode(text));chat.append(d);return d}
async function send(prompt){if(busy||!ready||!prompt.trim())return;busy=true;controls();input.value='';message('YOU',prompt,'user');status.textContent='The local model is choosing a tool and processing your request…';try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json','X-Demo-Token':token},body:JSON.stringify({prompt})}),data=await r.json();if(!r.ok)throw Error(data.error||'Request failed');const d=message('ASSISTANT',data.answer,'assistant');const detail=document.createElement('details'),sum=document.createElement('summary'),pre=document.createElement('pre');sum.textContent='Actual MCP calls and results';pre.textContent=data.trace;detail.append(sum,pre);d.append(detail);status.textContent='Ready for your next request.'}catch(e){message('ERROR',e.message,'assistant');status.textContent='Request failed. Review the error above.'}finally{busy=false;controls();input.focus()}}
document.querySelector('form').onsubmit=e=>{e.preventDefault();send(input.value)};document.querySelectorAll('[data-prompt]').forEach(b=>b.onclick=()=>send(b.dataset.prompt));async function health(){try{const r=await fetch('/status'),d=await r.json();ready=d.ready;status.textContent=d.error|| (ready?'Ready · real local model and all three MCP tools connected.':'Starting your agent…');controls();if(!ready&&!d.error)setTimeout(health,1500)}catch(e){status.textContent='Waiting for the local server…';setTimeout(health,1500)}}controls();health();
</script></html>'''


async def agent_worker():
    set_tracing_disabled(True)
    db_path = ROOT / "runtime" / "web_demo.sqlite3"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    async with connection(str(db_path)) as server:
        tools = await server.list_tools()
        if {t.name for t in tools} != {"search_rooms", "reserve_room", "find_and_reserve"}:
            raise RuntimeError("The expected three MCP tools were not discovered.")
        agent = build_agent(server)
        READY.set()
        while True:
            prompt, future = await asyncio.to_thread(REQUESTS.get)
            try:
                trace = io.StringIO()
                with redirect_stdout(trace):
                    result = await run_turn(agent, prompt)
                future.set_result({"answer": result.final_output, "trace": trace.getvalue()})
            except Exception as exc:
                future.set_exception(exc)

def start_worker():
    try:
        asyncio.run(agent_worker())
    except Exception as exc:
        START_ERROR.append(str(exc))
        READY.clear()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def respond(self, status, data, content_type="application/json"):
        body = data.encode() if isinstance(data, str) else json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            self.respond(200, PAGE.replace("__TOKEN__", TOKEN).replace("__DAY__", (datetime.now(ZoneInfo("Asia/Beirut")) + timedelta(days=1)).date().isoformat()), "text/html")
        elif self.path == "/status":
            self.respond(200, {"ready": READY.is_set(), "error": START_ERROR[0] if START_ERROR else None})
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/chat":
            return self.respond(404, {"error": "Not found"})
        if self.headers.get("X-Demo-Token") != TOKEN:
            return self.respond(403, {"error": "Open the demo page to send a request."})
        origin = self.headers.get("Origin")
        if origin and urlsplit(origin).netloc != f"{HOST}:{PORT}":
            return self.respond(403, {"error": "Use the local demo page."})
        if not READY.is_set():
            return self.respond(503, {"error": "The agent is still starting."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 16000:
                raise ValueError("Request is too large or empty.")
            prompt = json.loads(self.rfile.read(length)).get("prompt")
            if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 4000:
                raise ValueError("Enter a request of up to 4,000 characters.")
            future = Future()
            REQUESTS.put((prompt, future))
            self.respond(200, future.result(timeout=600))
        except ValueError as exc:
            self.respond(400, {"error": str(exc)})
        except Exception as exc:
            self.respond(500, {"error": str(exc)})


def main():
    import signal
    signal.signal(signal.SIGHUP, signal.SIG_IGN)
    os.environ.update(MODEL_PROVIDER="ollama", OLLAMA_MODEL="qwen2.5:3b",
        OLLAMA_BASE_URL="http://127.0.0.1:11434/v1", FASTMCP_CHECK_FOR_UPDATES="off",
        NO_PROXY="localhost,127.0.0.1,::1", no_proxy="localhost,127.0.0.1,::1")
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    threading.Thread(target=start_worker, daemon=True).start()
    print(f"Campus Study Assistant: http://{HOST}:{PORT}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
