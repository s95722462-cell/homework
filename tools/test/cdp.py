# 헤드리스 Edge + CDP 도우미 (프로필은 E:, 끝나면 내 Edge 만 끄고 프로필 삭제)
import json, subprocess, time, urllib.request, shutil, os, websocket, base64, socket
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
TEST = r"E:\claude_보관\homework_test"
def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p
class Browser:
    def __init__(self, name):
        self.prof = os.path.join(TEST, "prof_" + name); shutil.rmtree(self.prof, ignore_errors=True)
        self.port = free_port()
        self.p = subprocess.Popen([EDGE, "--headless=new", "--mute-audio", f"--user-data-dir={self.prof}", f"--remote-debugging-port={self.port}", "--remote-allow-origins=*",
            "--no-first-run", "--disable-component-update", "--disable-background-timer-throttling", "--disable-renderer-backgrounding", "about:blank"])
        for _ in range(80):
            try: v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/version")); break
            except Exception: time.sleep(0.25)
        self.ws = websocket.create_connection(v["webSocketDebuggerUrl"], timeout=120, suppress_origin=True); self.n = 0
    def call(self, m, **p):
        self.n += 1; self.ws.send(json.dumps({"id": self.n, "method": m, "params": p}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("id") == self.n: return r.get("result", r)
    def page(self, name, w, h, hook="", url=None, ctx=None, ua=None, dark=False):
        if ctx is None: ctx = self.call("Target.createBrowserContext")["browserContextId"]
        tid = self.call("Target.createTarget", url="about:blank", browserContextId=ctx)["targetId"]
        p = Page(self, tid, name); p.ctx = ctx
        p.call("Runtime.enable"); p.call("Page.enable"); p.call("Emulation.setFocusEmulationEnabled", enabled=True)
        p.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=2 if w < 600 else 1, mobile=w < 600)
        if ua: p.call("Emulation.setUserAgentOverride", userAgent=ua)
        if dark: p.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "dark"}])
        if hook: p.call("Page.addScriptToEvaluateOnNewDocument", source=hook)
        if url: p.go(url); time.sleep(1.5)
        return p
    def quit(self):
        try: self.ws.close()
        except Exception: pass
        try: self.p.terminate()
        except Exception: pass
        time.sleep(0.8)
        prof = self.prof.replace("'", "''")
        subprocess.run(["powershell", "-NoProfile", "-Command", f"Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object {{ $_.CommandLine -like '*{prof}*' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }}"], capture_output=True)
        time.sleep(0.8); shutil.rmtree(self.prof, ignore_errors=True)
class Page:
    def __init__(self, b, tid, name):
        self.b = b; self.name = name; self.tid = tid; self.n = 0; self.errs = []
        self.ws = websocket.create_connection(f"ws://127.0.0.1:{b.port}/devtools/page/{tid}", timeout=120, suppress_origin=True)
    def call(self, m, **p):
        self.n += 1; self.ws.send(json.dumps({"id": self.n, "method": m, "params": p}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get("method") == "Runtime.exceptionThrown": d = r["params"]["exceptionDetails"]; self.errs.append(d.get("exception", {}).get("description", d.get("text", ""))[:300])
            if r.get("method") == "Runtime.consoleAPICalled" and r["params"]["type"] == "error": self.errs.append("console: " + str([a.get("value", a.get("description")) for a in r["params"]["args"]])[:300])
            if r.get("id") == self.n: return r.get("result", r)
    def ev(self, js):
        r = self.call("Runtime.evaluate", expression=js, awaitPromise=True, returnByValue=True, userGesture=True)
        if "exceptionDetails" in r: return "EXC " + json.dumps(r["exceptionDetails"], ensure_ascii=False)[:300]
        return r.get("result", {}).get("value")
    def go(self, url): self.call("Page.navigate", url=url)
    def shot(self, path, full=False):
        p = {"format": "png"}
        if full:
            m = self.call("Page.getLayoutMetrics")["cssContentSize"]; p["clip"] = {"x": 0, "y": 0, "width": m["width"], "height": m["height"], "scale": 1}; p["captureBeyondViewport"] = True
        open(path, "wb").write(base64.b64decode(self.call("Page.captureScreenshot", **p)["data"]))
    def wait(self, js, t=12):
        t0 = time.time()
        while time.time() - t0 < t:
            v = self.ev(js)
            if v and not (isinstance(v, str) and v.startswith("EXC")): return v
            time.sleep(0.25)
        return None
