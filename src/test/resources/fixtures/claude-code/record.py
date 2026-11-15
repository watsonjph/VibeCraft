"""Re-records the Claude Code fixtures in this folder from the installed CLI.

Usage: python record.py            (run from anywhere; needs `claude` logged in, git, a few cents of usage)

Writes oneshot.jsonl and session.jsonl next to this file, with machine paths, the user
name and account details replaced so the files are safe to commit.
"""
import json, os, queue, re, subprocess, sys, tempfile, threading, time

HERE = os.path.dirname(os.path.abspath(__file__))
WIN = os.name == "nt"
FAKE_REPO = "C:\\fixture\\repo" if WIN else "/fixture/repo"
FAKE_HOME = "C:\\Users\\fixture" if WIN else "/home/fixture"
COMMON = [
    "--output-format", "stream-json", "--verbose", "--include-partial-messages",
    "--disallowedTools", "Bash(git push:*)",
    "--setting-sources", "", "--strict-mcp-config",
    "--model", "haiku", "--max-budget-usd", "0.50",
]
# The daemon will not run inside another Claude Code session, so neither does the recording.
ENV = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}


def make_repo():
    repo = os.path.join(tempfile.mkdtemp(prefix="vcfix"), "repo")
    os.makedirs(repo)
    with open(os.path.join(repo, "greeting.py"), "w", newline="\n") as f:
        f.write('def greeting():\n    return "Hello, world"\n\n\nif __name__ == "__main__":\n    print(greeting())\n')
    git = ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid"]
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(git + ["commit", "-q", "-m", "initial"], cwd=repo, check=True)
    return repo


def scrub_values(o):
    if isinstance(o, dict):
        for k, v in list(o.items()):
            if k == "utilization":
                o[k] = 0.25
            elif k == "credential_expires_at":
                o[k] = 0
            elif k == "messaging_socket_path":
                o[k] = "fixture-socket"
            elif k == "overageDisabledReason":
                o[k] = "fixture"
            else:
                scrub_values(v)
    elif isinstance(o, list):
        for v in o:
            scrub_values(v)


def scrub_text(text, repo):
    home = os.path.expanduser("~")
    user = os.path.basename(home)

    def variants(path):
        yield json.dumps(path)[1:-1]
        yield path.replace("\\", "/")
        yield re.sub(r"[\\/:.]", "-", path)

    for real, fake in ((os.path.realpath(repo), FAKE_REPO), (repo, FAKE_REPO), (home, FAKE_HOME)):
        for real_v, fake_v in zip(variants(real), variants(fake)):
            text = re.sub(re.escape(real_v), lambda m: fake_v, text, flags=re.I)
    text = re.sub(re.escape(user), "fixture", text, flags=re.I)
    assert user.lower() not in text.lower(), "user name survived scrubbing"
    return text


def dump(objs, name, repo):
    for o in objs:
        scrub_values(o)
    text = "".join(json.dumps(o, separators=(",", ":"), ensure_ascii=False) + "\n" for o in objs)
    with open(os.path.join(HERE, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(scrub_text(text, repo))
    print(f"wrote {name}: {len(objs)} lines")


def record_oneshot():
    repo = make_repo()
    prompt = ("Read greeting.py. Change the greeting text to 'Hello, VibeCraft'. "
              "Run 'python greeting.py' to check it. Then tell me in one sentence what you did.")
    cmd = ["claude", "-p", prompt, "--permission-mode", "acceptEdits",
           "--allowedTools", "Read", "Edit", "Bash(python:*)", "--no-session-persistence"] + COMMON
    out = subprocess.run(cmd, cwd=repo, env=ENV, capture_output=True, text=True, encoding="utf-8", shell=WIN)
    assert out.returncode == 0, out.stderr
    assert "VibeCraft" in open(os.path.join(repo, "greeting.py")).read(), "the agent did not edit the file"
    dump([json.loads(l) for l in out.stdout.splitlines() if l.strip()], "oneshot.jsonl", repo)


def record_session():
    repo = make_repo()
    cmd = ["claude", "-p", "--input-format", "stream-json", "--permission-prompt-tool", "stdio",
           "--allowedTools", "Read"] + COMMON
    p = subprocess.Popen(cmd, cwd=repo, env=ENV, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1, shell=WIN)
    lines, log, t0 = queue.Queue(), [], time.time()

    def reader():
        for line in p.stdout:
            lines.put(line)
        lines.put(None)

    threading.Thread(target=reader, daemon=True).start()

    def send(msg):
        log.append({"dir": "in", "t": round(time.time() - t0, 2), "msg": msg})
        p.stdin.write(json.dumps(msg) + "\n")
        p.stdin.flush()

    def user(text):
        send({"type": "user", "message": {"role": "user", "content": text}})

    def pump(until, what, timeout=90):
        end = time.time() + timeout
        while time.time() < end:
            try:
                line = lines.get(timeout=1)
            except queue.Empty:
                continue
            assert line is not None, f"CLI exited while waiting for {what}"
            o = json.loads(line)
            log.append({"dir": "out", "t": round(time.time() - t0, 2), "msg": o})
            if o.get("type") == "control_request" and o["request"].get("subtype") == "can_use_tool":
                send({"type": "control_response", "response": {
                    "subtype": "success", "request_id": o["request_id"],
                    "response": {"behavior": "allow", "updatedInput": o["request"].get("input", {})}}})
            if until(o):
                return o
        raise AssertionError(f"timed out waiting for {what}")

    is_result = lambda o: o.get("type") == "result"
    is_text = lambda o: o.get("type") == "stream_event" and o["event"].get("delta", {}).get("type") == "text_delta"

    user("Change the greeting text in greeting.py to 'Hello again'. Reply with one short sentence.")
    assert pump(is_result, "turn 1 result")["subtype"] == "success"
    assert "Hello again" in open(os.path.join(repo, "greeting.py")).read(), "permission answer did not allow the edit"

    user("Count from 1 to 300, one number per line, nothing else.")
    pump(is_text, "turn 2 first text")
    send({"type": "control_request", "request_id": "int-1", "request": {"subtype": "interrupt"}})
    assert pump(is_result, "turn 2 result")["terminal_reason"] == "aborted_streaming"

    user("Reply with exactly: still here")
    assert "still here" in pump(is_result, "turn 3 result")["result"]

    p.stdin.close()
    assert p.wait(timeout=30) == 0, "CLI did not exit cleanly when stdin closed"
    for e in log:
        scrub_values(e["msg"])
    dump(log, "session.jsonl", repo)


if __name__ == "__main__":
    version = subprocess.run(["claude", "--version"], capture_output=True, text=True, shell=WIN).stdout.strip()
    print("recording with", version)
    record_oneshot()
    record_session()
