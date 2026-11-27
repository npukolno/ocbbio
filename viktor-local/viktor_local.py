#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp[cli]>=1.9,<2", "uvicorn"]
# ///
"""viktor-local: a small MCP server that gives an agent files + shell inside ONE folder.

Run:   uv run viktor_local.py [folder]        (folder defaults to the current one)
It downloads cloudflared on first run, opens a tunnel by itself and prints the one URL
to paste into Viktor (Add Custom Integration -> MCP Server). --no-tunnel for local only.

Safety: every path is resolved inside VIKTOR_ROOT; requests without the token get 404;
commands run with a timeout; everything is logged to viktor_local.log. Stop it with Ctrl+C.
"""
import os, sys, re, secrets, subprocess, shlex, time, uuid, logging, pathlib, platform, threading, urllib.request, tarfile, shutil
from mcp.server.fastmcp import FastMCP

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
ROOT = pathlib.Path(ARGS[0] if ARGS else os.environ.get("VIKTOR_ROOT", os.getcwd())).expanduser().resolve()
PORT = int(os.environ.get("VIKTOR_PORT", "8765"))
TOKEN_FILE = pathlib.Path.home() / ".viktor_local_token"
TOKEN = os.environ.get("VIKTOR_TOKEN") or (TOKEN_FILE.read_text().strip() if TOKEN_FILE.exists() else "")
if not TOKEN:
    TOKEN = secrets.token_urlsafe(32)
    TOKEN_FILE.write_text(TOKEN); TOKEN_FILE.chmod(0o600)
MAX_OUT = 60_000
WIN = os.name == "nt"
SHELL = (lambda c: ["cmd", "/c", c]) if WIN else (lambda c: ["bash", "-lc", c] if shutil.which("bash") else ["sh", "-c", c])
logging.basicConfig(filename=str(ROOT / "viktor_local.log"), level=logging.INFO,
                    format="%(asctime)s %(message)s")
log = logging.getLogger("viktor-local")

try:  # the tunnel sends its own Host header; the secret path is the guard instead
    from mcp.server.transport_security import TransportSecuritySettings
    mcp = FastMCP("viktor-local", stateless_http=True,
                  transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False))
except ImportError:
    mcp = FastMCP("viktor-local", stateless_http=True)
JOBS: dict[str, dict] = {}


def _p(path: str) -> pathlib.Path:
    p = (ROOT / path).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ValueError(f"path outside {ROOT}: {path}")
    return p


def _cut(s: str) -> str:
    return s if len(s) <= MAX_OUT else s[:MAX_OUT // 2] + "\n...[cut]...\n" + s[-MAX_OUT // 2:]


@mcp.tool()
def info() -> dict:
    """Root folder, OS and tool versions on this machine."""
    import platform, shutil
    return {"root": str(ROOT), "os": platform.platform(),
            "tools": {t: bool(shutil.which(t)) for t in ["git", "rg", "godot", "node", "python3", "cargo", "cmake", "make"]}}


@mcp.tool()
def list_dir(path: str = ".", depth: int = 1) -> str:
    """List files under path (relative to root), up to depth levels. Skips .git and node_modules."""
    base = _p(path); out = []
    for p in sorted(base.rglob("*")):
        rel = p.relative_to(base)
        if len(rel.parts) > depth or {".git", "node_modules", ".godot", "Library"} & set(rel.parts):
            continue
        out.append(f"{rel}{'/' if p.is_dir() else ''}\t{p.stat().st_size if p.is_file() else ''}")
    return _cut("\n".join(out) or "(empty)")


@mcp.tool()
def read_file(path: str, start_line: int = 1, end_line: int = 0) -> str:
    """Read a text file; optional 1-based inclusive line range (end_line=0 means to the end)."""
    lines = _p(path).read_text(errors="replace").splitlines()
    sel = lines[start_line - 1:(end_line or len(lines))]
    return _cut("\n".join(f"{i}\t{l}" for i, l in enumerate(sel, start_line)))


@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Create or overwrite a file (parent folders are created)."""
    p = _p(path); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(content)
    log.info("write %s (%d bytes)", p, len(content)); return f"wrote {len(content)} bytes to {path}"


@mcp.tool()
def edit_file(path: str, old: str, new: str, replace_all: bool = False) -> str:
    """Replace exact text in a file. Fails if old is missing, or appears more than once without replace_all."""
    p = _p(path); s = p.read_text(); n = s.count(old)
    if n == 0: raise ValueError("old text not found")
    if n > 1 and not replace_all: raise ValueError(f"old text found {n} times; pass replace_all or more context")
    p.write_text(s.replace(old, new) if replace_all else s.replace(old, new, 1))
    log.info("edit %s (%d replacements)", p, n if replace_all else 1); return f"replaced {n if replace_all else 1}"


@mcp.tool()
def search(pattern: str, path: str = ".", glob: str = "") -> str:
    """Regex search with ripgrep (falls back to grep -rn)."""
    base = _p(path)
    cmd = ["rg", "-n", "--max-columns", "300", pattern, str(base)] + (["-g", glob] if glob else [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except FileNotFoundError:
        r = subprocess.run(["grep", "-rn", pattern, str(base)], capture_output=True, text=True, timeout=60)
    return _cut(r.stdout.replace(str(ROOT) + "/", "") or "(no matches)")


@mcp.tool()
def run(command: str, cwd: str = ".", timeout_seconds: int = 300) -> dict:
    """Run a shell command (bash -lc) in cwd under root and wait for it. For long jobs use start_job."""
    log.info("run [%s] %s", cwd, command)
    try:
        r = subprocess.run(SHELL(command), cwd=_p(cwd), capture_output=True, text=True, timeout=timeout_seconds)
        return {"exit_code": r.returncode, "stdout": _cut(r.stdout), "stderr": _cut(r.stderr)}
    except subprocess.TimeoutExpired as e:
        return {"exit_code": None, "timed_out": True, "stdout": _cut(e.stdout or ""), "stderr": _cut(e.stderr or "")}


@mcp.tool()
def start_job(command: str, cwd: str = ".") -> str:
    """Start a long command in the background (a build, the game itself). Returns a job id for job_output."""
    jid = uuid.uuid4().hex[:8]; logf = ROOT / f".viktor_job_{jid}.log"
    proc = subprocess.Popen(SHELL(command), cwd=_p(cwd), stdout=open(logf, "w"), stderr=subprocess.STDOUT)
    JOBS[jid] = {"proc": proc, "log": logf, "cmd": command, "started": time.time()}
    log.info("job %s [%s] %s", jid, cwd, command); return jid


@mcp.tool()
def job_output(job_id: str, tail_chars: int = 20000) -> dict:
    """Status and the tail of a background job's output."""
    j = JOBS[job_id]; rc = j["proc"].poll()
    return {"running": rc is None, "exit_code": rc, "output": j["log"].read_text(errors="replace")[-tail_chars:]}


@mcp.tool()
def stop_job(job_id: str) -> str:
    """Stop a background job."""
    JOBS[job_id]["proc"].terminate(); return "stopped"


CACHE = pathlib.Path.home() / ".cache" / "viktor-local"
CF_BASE = "https://github.com/cloudflare/cloudflared/releases/latest/download/"


def cloudflared_path() -> str:
    """cloudflared from PATH, else download the official binary for this OS once."""
    found = shutil.which("cloudflared")
    if found:
        return found
    arch = {"x86_64": "amd64", "amd64": "amd64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine().lower(), "amd64")
    sysname = platform.system()
    CACHE.mkdir(parents=True, exist_ok=True)
    exe = CACHE / ("cloudflared.exe" if WIN else "cloudflared")
    if exe.exists():
        return str(exe)
    print("  downloading cloudflared (one time)...")
    if sysname == "Darwin":
        tgz = CACHE / "cf.tgz"; urllib.request.urlretrieve(CF_BASE + f"cloudflared-darwin-{arch}.tgz", tgz)
        with tarfile.open(tgz) as t: t.extract("cloudflared", CACHE)
        tgz.unlink()
    elif sysname == "Windows":
        urllib.request.urlretrieve(CF_BASE + f"cloudflared-windows-{arch}.exe", exe)
    else:
        urllib.request.urlretrieve(CF_BASE + f"cloudflared-linux-{arch}", exe)
    exe.chmod(0o755)
    return str(exe)


def _drain_and_watch(proc, tail: list[str], started_evt: threading.Event, state: dict, pattern: str, fail_marker: str | None = None):
    for line in proc.stdout:
        s = line.rstrip()
        tail.append(s); del tail[:-15]
        if fail_marker and fail_marker in line and "url" not in state:
            state["api_fail"] = True
        m = re.search(pattern, line)
        if m and "url" not in state:
            state["url"] = m.group(0)
            started_evt.set()
    if started_evt.is_set() and not state.get("stopping"):
        print("\n  [tunnel disconnected — restart viktor-local]", flush=True)


def _wait_tunnel(cmd: list[str], pattern: str, wait_s: int, fail_marker: str | None = None):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    state, tail, started_evt = {}, [], threading.Event()
    threading.Thread(
        target=_drain_and_watch, args=(proc, tail, started_evt, state, pattern, fail_marker), daemon=True
    ).start()
    for i in range(wait_s * 2):
        if "url" in state:
            print(); return state["url"], (proc, state), tail, False
        if state.get("api_fail") or proc.poll() is not None:
            break
        if i % 4 == 0:
            print(".", end="", flush=True)
        time.sleep(0.5)
    state["stopping"] = True
    proc.terminate(); print()
    return None, None, tail, bool(state.get("api_fail"))


def _try_tunnel(port: int, protocol: str, wait_s: int):
    # An empty config: a ~/.cloudflared/config.yml with its own ingress rules (e.g. a catch-all
    # http_status:404) would otherwise hijack the quick tunnel and never reach this server.
    CACHE.mkdir(parents=True, exist_ok=True)
    empty = CACHE / "empty-config.yml"; empty.write_text("{}\n")
    cmd = [cloudflared_path(), "tunnel", "--config", str(empty), "--no-autoupdate", "--protocol", protocol,
           "--url", f"http://127.0.0.1:{port}"]
    # Exclude api.trycloudflare.com which appears in cloudflared error logs on failure.
    return _wait_tunnel(
        cmd,
        r"https://(?!api\.)[a-z0-9-]+\.trycloudflare\.com",
        wait_s,
        fail_marker="failed to request quick Tunnel",
    )


def _try_localhost_run(port: int, wait_s: int = 20):
    ssh = shutil.which("ssh")
    if not ssh and WIN:
        win_ssh = pathlib.Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "OpenSSH" / "ssh.exe"
        if win_ssh.exists():
            ssh = str(win_ssh)
    if not ssh:
        return None, None, ["ssh not found in PATH"]
    CACHE.mkdir(parents=True, exist_ok=True)
    known = CACHE / "known_hosts"
    cmd = [
        ssh, "-T",
        "-o", "StrictHostKeyChecking=no",
        "-o", f"UserKnownHostsFile={known}",
        "-o", "ConnectTimeout=10",
        "-o", "BatchMode=yes",
        "-o", "ServerAliveInterval=30",
        "-o", "ServerAliveCountMax=3",
        "-o", "ExitOnForwardFailure=yes",
        "-R", f"80:127.0.0.1:{port}",
        "nokey@localhost.run",
    ]
    url, proc, tail, _ = _wait_tunnel(cmd, r"https://[a-z0-9-]+\.(?:app\.)?lhr\.life", wait_s)
    return url, proc, tail


def start_tunnel(port: int):
    """Open a public HTTPS tunnel (Cloudflare quick tunnel, falling back to localhost.run over SSH)."""
    tail = []
    if "--ssh" not in sys.argv:
        for protocol in ("auto", "http2"):
            print(f"  opening https tunnel (cloudflare {protocol})", end="", flush=True)
            url, proc, tail, api_fail = _try_tunnel(port, protocol, 20)
            if url:
                return url, proc
            if api_fail:
                print("  cloudflare quick-tunnel API unreachable, falling back to ssh...", flush=True)
                break
    print("  opening https tunnel (localhost.run ssh)", end="", flush=True)
    url, proc, lr_tail = _try_localhost_run(port, 25)
    if url:
        return url, proc
    print("\n  could not open a public tunnel. Last output:\n")
    print("\n".join("    " + l for l in (lr_tail or tail)))
    print("\n  Check internet/VPN, or run with --no-tunnel and expose port", port, "yourself (Tailscale Funnel, ngrok).\n")
    sys.exit(1)


def free_port(start: int) -> int:
    """First port from start that nothing listens on (an old copy may still hold 8765)."""
    import socket
    for port in range(start, start + 50):
        with socket.socket() as sk:
            try:
                sk.bind(("127.0.0.1", port)); return port
            except OSError:
                continue
    raise RuntimeError("no free port")


def main():
    global PORT
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if PORT == 8765 and "VIKTOR_PORT" not in os.environ:
        p = free_port(8765)
        if p != 8765:
            print(f"\n  port 8765 is busy (used by another process or old viktor-local), using port {p} instead")
        PORT = p
    import uvicorn
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from contextlib import asynccontextmanager
    streamable = mcp.streamable_http_app()          # POST /mcp
    sse = mcp.sse_app()                             # GET /sse + POST /messages/
    inner = Starlette(routes=list(streamable.routes) + list(sse.routes))

    @asynccontextmanager
    async def lifespan(_):
        async with mcp.session_manager.run():
            yield
    app = Starlette(routes=[Mount(f"/{TOKEN}", app=inner)], lifespan=lifespan)

    async def show_requests(scope, receive, send):
        """Print every request so you can see whether Viktor reaches this computer."""
        if scope["type"] != "http":
            return await app(scope, receive, send)
        path = scope["path"]
        shown = path.replace(TOKEN, "<token>") if TOKEN in path else path + "  (no token: refused)"
        status = {}
        async def send_wrap(msg):
            if msg["type"] == "http.response.start":
                status["code"] = msg["status"]
                print(f"  {time.strftime('%H:%M:%S')}  {scope['method']} {shown} -> {msg['status']}", flush=True)
            await send(msg)
        try:
            return await app(scope, receive, send_wrap)
        except RuntimeError as e:  # SSE stream closed by the client: harmless
            if "after response already completed" not in str(e):
                raise

    print(f"\n  viktor-local: folder = {ROOT}")
    tunnel = None
    if "--no-tunnel" in sys.argv:
        print(f"  local only: http://127.0.0.1:{PORT}/{TOKEN}/mcp  (Viktor cannot use this one)")
    else:
        url, tunnel = start_tunnel(PORT)
        print("\n  Paste this into Viktor -> Add Custom Integration -> MCP Server:")
        print(f"\n      {url}/{TOKEN}/mcp\n")
        print(f"  (if Viktor asks for an SSE URL instead: {url}/{TOKEN}/sse)")
        print("  Keep it secret: it gives shell access to this computer. Ctrl+C to stop.")
        print("  Requests from Viktor will show up below:\n")
    try:
        uvicorn.run(show_requests, host="127.0.0.1", port=PORT, log_level="warning")
    finally:
        if tunnel is not None:
            proc, state = tunnel
            state["stopping"] = True
            if proc.poll() is None:
                proc.terminate()


if __name__ == "__main__":
    main()
