# 숙제 웹앱 시험: 헤드리스 Edge + 가짜 시계 + 시험용 폴더(OPFS → E: 로 꺼내 확인)
import sys; sys.stdout.reconfigure(encoding="utf-8")
import json, time, os, shutil, threading, base64, zipfile, functools, glob
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser, free_port, TEST
REPO = r"C:\Users\ds5yr\OneDrive\문서\GitHub\homework"
APP = os.path.join(TEST, "site", "app"); shutil.rmtree(os.path.join(TEST, "site"), ignore_errors=True)
shutil.copytree(REPO, APP, ignore=shutil.ignore_patterns(".git", "tools"))
SH = os.path.join(TEST, "shots"); shutil.rmtree(SH, ignore_errors=True); os.makedirs(SH)
DL = os.path.join(TEST, "downloads"); shutil.rmtree(DL, ignore_errors=True); os.makedirs(DL)
MIRROR = os.path.join(TEST, "book_mirror"); shutil.rmtree(MIRROR, ignore_errors=True)
BUNDLE = json.load(open(os.path.join(REPO, "bundles", "adult-manual.json"), encoding="utf-8"))
QS = BUNDLE["questions"]; QB = {q["id"]: q for q in QS}
def first_of(ch, skip=()): return next(q["id"] for q in QS if q["ch"] == ch and q["id"] not in skip)

class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
PORT = free_port()
ThreadingHTTPServer.handle_error = lambda *a: None
srv = ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Quiet, directory=os.path.join(TEST, "site")))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{PORT}/app/index.html"

res = []
def check(name, cond, info=""):
    res.append((name, bool(cond))); print(("PASS " if cond else "FAIL ") + name, ("— " + str(info)[:240]) if info != "" else "", flush=True)

HOOK = r"""
(() => {
  const K = "__hwT";
  const load = () => { try { return JSON.parse(localStorage.getItem(K)); } catch (e) { return null; } };
  window.__setNow = (iso, fast) => { localStorage.setItem(K, JSON.stringify({ base: new Date(iso).getTime(), r0: Date.now(), fast: fast || 1 })); return 1; };
  window.__hwNow = () => { const t = load(); return t ? t.base + (Date.now() - t.r0) * t.fast : Date.now(); };
  window.__hwTickMs = 250;
  window.__N = []; window.__U = []; window.__focus = false; window.__shared = null;
  document.hasFocus = () => window.__focus;
  window.confirm = () => true;
  class FakeN { constructor(t, o) { window.__N.push({ t, body: o && o.body }); } close() {} }
  FakeN.permission = "default"; FakeN.requestPermission = () => { FakeN.permission = "granted"; return Promise.resolve("granted"); };
  window.Notification = FakeN;
  if (window.ServiceWorkerRegistration) ServiceWorkerRegistration.prototype.showNotification = function (t, o) { window.__N.push({ t, body: o && o.body, sw: 1 }); return Promise.resolve(); };
  if (window.speechSynthesis) { speechSynthesis.speak = u => { window.__U.push(u.text); }; speechSynthesis.cancel = () => {}; }
  if (window.__PHONE__) {
    window.showDirectoryPicker = undefined;
    navigator.canShare = () => true;
    navigator.share = async d => { const f = d.files[0]; const b = new Uint8Array(await f.arrayBuffer()); let s = ""; for (const x of b) s += String.fromCharCode(x); window.__shared = { name: f.name, b64: btoa(s) }; };
  } else {
    window.showDirectoryPicker = async () => (await navigator.storage.getDirectory()).getDirectoryHandle("어른 매뉴얼", { create: true });
  }
})();
"""
SEED = r"""(async () => {
  const root = await navigator.storage.getDirectory(), book = await root.getDirectoryHandle("어른 매뉴얼", { create: true }), qa = await book.getDirectoryHandle("_질문과답", { create: true });
  const put = async (n, t) => { const w = await (await qa.getFileHandle(n, { create: true })).createWritable(); await w.write(t); await w.close(); };
  await put("2026-10-11_Q001_첫현장.md", %s);
  await put("2026-10-11_A000_서론_원문.md", "# 서론 원문\r\n\r\n원문");
  await put("2026-10-09_Q049_첫시운전.md", "# Q049 · 2026-10-09 · (04 기본운전 엔지니어)\r\n\r\n**질문:** …\r\n\r\n**답:** 대화로 이미 답한 질문\r\n");
  return 1; })()"""
DUMP = r"""(async () => {
  const out = {}; const walk = async (d, p) => { for await (const h of d.values()) { const q = p + h.name; if (h.kind === "directory") await walk(h, q + "/"); else out[q] = await (await h.getFile()).text(); } };
  await walk(await navigator.storage.getDirectory(), ""); return JSON.stringify(out); })()"""
ORIG_Q001 = open(r"C:\Users\ds5yr\Desktop\어른 매뉴얼\_질문과답\2026-10-11_Q001_첫현장.md", encoding="utf-8", newline="").read()

def J(p, js): return p.ev(js)
def click(p, id): return p.ev(f'(() => {{ const b = document.getElementById("{id}"); if (!b || b.disabled || b.closest("[hidden]")) return "no " + "{id}"; b.click(); return 1; }})()')
def ov(p): return p.ev('JSON.stringify({ open: !document.getElementById("ov").hidden, mode: HW.O && HW.O.mode, date: HW.O && HW.O.date, qid: HW.O && HW.O.qid, diary: HW.O && HW.O.diary, kick: document.getElementById("oKick").textContent, snooze: document.getElementById("oSnooze").hidden ? null : document.getElementById("oSnooze").textContent, rest: !document.getElementById("oRest").hidden, msg: document.getElementById("oMsg").textContent, streak: document.getElementById("oStreak").textContent, pill: document.getElementById("oPill").textContent, done: document.getElementById("oDoneBig").textContent, doneShown: !document.getElementById("oDone").hidden })')
def O(p): return json.loads(ov(p))
def setnow(p, iso, fast=1): p.ev(f'__setNow("{iso}", {fast})'); time.sleep(0.6)
def type_text(p, text, field="oText"):
    p.ev(f'(() => {{ const t = document.getElementById("{field}"); t.focus(); t.value = ""; return 1; }})()')
    p.call("Input.insertText", text=text); time.sleep(0.2)
def wait_open(p, t=6): return p.wait('!document.getElementById("ov").hidden && HW.O && 1', t)
def wait_closed(p, t=5): return p.wait('document.getElementById("ov").hidden && 1', t)
def toast(p): return p.ev('document.getElementById("toast").hidden ? "" : document.getElementById("toast").textContent')
def no_overflow(p): return p.ev('document.documentElement.scrollWidth <= innerWidth && [...document.querySelectorAll(".ov, .sheet > .pane")].every(e => e.offsetParent === null || e.scrollWidth <= e.clientWidth + 1)')
def dump(p): return json.loads(p.ev(DUMP))
def reload(p): p.call("Page.reload"); time.sleep(1.2); p.wait('HW && HW.S && 1', 8); time.sleep(0.6)

B = Browser("e2e"); pages = []
try:
    # ================= PC (Edge, 폴더 저장) =================
    P = B.page("pc", 1280, 900, HOOK); pages.append(P)
    B.call("Browser.setDownloadBehavior", behavior="allow", downloadPath=DL, browserContextId=P.ctx, eventsEnabled=True)
    P.go(BASE); time.sleep(1.0)
    P.ev('__setNow("2026-10-11T20:59:30", 1)'); P.ev(SEED % json.dumps(ORIG_Q001, ensure_ascii=False)); reload(P)
    check("처음: 시작 안내 보임 + 책 폴더 줄 있음", P.ev('!document.getElementById("welSheet").hidden && !document.getElementById("wFolderRow").hidden'))
    click(P, "wNotify"); time.sleep(0.3)
    check("알림 허용 (가짜) → 허용됨 표시", "허용됨" in (P.ev('document.getElementById("wNState").textContent') or ""))
    click(P, "wFolder"); time.sleep(1.0)
    check("책 폴더 고르기 → 연결", P.ev('HW.dirOk') and "어른 매뉴얼" in P.ev('document.getElementById("wFState").textContent'))
    click(P, "wGo"); time.sleep(0.6)
    check("시작하기 → 안내 닫힘, 아직 20:59 라 숙제 창 없음", P.ev('document.getElementById("welSheet").hidden && document.getElementById("ov").hidden && HW.S.setup'))
    check("폴더 읽기: 대화로 답한 Q049 는 답한 것으로", P.ev('HW.folder.answered.has("Q049") && !HW.folder.answered.has("Q001")'))
    check("A000 원문 파일은 기록 날짜로 안 셈", not P.ev('HW.folder.dates.has("2026-10-11")'))
    st = P.ev('document.getElementById("tStatus").textContent')
    check("홈: '오늘 숙제 검사 21:00'", "21:00" in st, st)
    P.shot(os.path.join(SH, "pc_home_before.png"))
    # --- 21:00 ---
    setnow(P, "2026-10-11T21:00:02")
    check("21:00 → 숙제 창 자동으로 열림", wait_open(P))
    o = O(P)
    check("첫 질문은 Q001 (03 설치)", o["qid"] == "Q001" and "03 설치" in o["pill"], o["pill"])
    check("문구 '오늘의 숙제가 있어요 ✏️'", o["kick"] == "오늘의 숙제가 있어요 ✏️", o["kick"])
    check("미루기 버튼 '10분 뒤에 (3번 남음)'", o["snooze"] == "10분 뒤에 (3번 남음)", o["snooze"])
    check("오늘은 쉼은 아직 안 보임", not o["rest"])
    n = json.loads(P.ev('JSON.stringify(__N)'))
    check("알림 1개 (탭에 초점 없을 때)", len(n) == 1 and n[0]["t"] == "오늘의 숙제가 있어요 ✏️", n)
    u = json.loads(P.ev('JSON.stringify(__U)'))
    check("질문 읽어 주기 (한 번)", len(u) == 1 and "처음 엔지니어로" in u[0], u)
    P.shot(os.path.join(SH, "pc_ov_normal.png"))
    # 빈 저장
    click(P, "oSave"); time.sleep(0.3)
    check("빈 칸 저장 → '한 줄만 써 주세요'", "한 줄만 써 주세요" in O(P)["msg"])
    # 미루기 ×3
    click(P, "oSnooze"); time.sleep(0.3)
    check("미루기 1 → 창 닫힘 + '숙제 검사 10분 전입니다'", wait_closed(P) and "숙제 검사 10분 전입니다" in toast(P), toast(P))
    check("홈 상태: 숙제 검사 21:10 (미룸 1/3)", "21:10" in P.ev('document.getElementById("tStatus").textContent'))
    setnow(P, "2026-10-11T21:09:30")
    check("9분 30초 뒤엔 아직 안 뜸", P.ev('document.getElementById("ov").hidden'))
    reload(P)
    check("새로 고쳐도 미룸 유지 (안 뜸)", P.ev('document.getElementById("ov").hidden && HW.S.day.snoozes === 1'))
    setnow(P, "2026-10-11T21:10:05")
    check("10분 뒤 다시 뜸", wait_open(P))
    o = O(P)
    check("두 번째: '숙제 검사 시간이에요' + 2번 남음", o["kick"] == "숙제 검사 시간이에요 ✏️" and "2번 남음" in o["snooze"], o)
    type_text(P, "임시 초안")
    click(P, "oX"); time.sleep(0.3)
    check("✕ 닫기도 미루기로 셈 (2/3)", wait_closed(P) and P.ev('HW.S.day.snoozes') == 2)
    setnow(P, "2026-10-11T21:20:10"); wait_open(P)
    o = O(P)
    check("세 번째: 1번 남음 + 초안 '임시 초안' 그대로", "1번 남음" in o["snooze"] and P.ev('document.getElementById("oText").value') == "임시 초안", o["snooze"])
    click(P, "oSnooze"); wait_closed(P)
    setnow(P, "2026-10-11T21:30:10"); wait_open(P)
    o = O(P)
    check("3번 미룬 뒤: persist, 미루기 버튼 없음", o["mode"] == "persist" and o["snooze"] is None, o)
    check("문구 '숙제는 한 줄이면 끝!' + 오늘은 쉼 보임", o["kick"] == "숙제는 한 줄이면 끝!" and o["rest"], o)
    P.shot(os.path.join(SH, "pc_ov_persist.png"))
    click(P, "oX"); time.sleep(0.3)
    check("persist 에서 ✕ → 잠깐 닫힘", wait_closed(P) and "1분 뒤에 다시" in toast(P))
    setnow(P, "2026-10-11T21:30:50")
    check("40초 뒤엔 아직", P.ev('document.getElementById("ov").hidden'))
    setnow(P, "2026-10-11T21:31:15")
    check("1분 뒤 다시 뜸 (persist)", wait_open(P) and O(P)["mode"] == "persist")
    # 쉼: 이유 너무 짧음
    click(P, "oRestOpen"); P.ev('document.getElementById("oRestText").value = "아"'); click(P, "oRestSave"); time.sleep(0.3)
    check("쉼 이유 1글자 → 거절", "이유" in O(P)["msg"] and not O(P)["doneShown"])
    # 한국어 입력 (IME 조합 흉내 → 확정)
    P.ev('(() => { const t = document.getElementById("oText"); t.focus(); t.value = ""; return 1; })()')
    for comp in ("ㅊ", "처", "첫"): P.call("Input.imeSetComposition", text=comp, selectionStart=len(comp), selectionEnd=len(comp))
    P.call("Input.insertText", text="첫")
    P.call("Input.insertText", text=" 현장은 울산이었다.\n안전화 끈부터 다시 맸다.")
    val = P.ev('document.getElementById("oText").value')
    check("한국어 입력 (IME 조합 → 확정, 두 줄)", val == "첫 현장은 울산이었다.\n안전화 끈부터 다시 맸다.", val)
    P.call("Input.dispatchKeyEvent", type="keyDown", key="Enter", code="Enter", modifiers=2, windowsVirtualKeyCode=13)
    P.call("Input.dispatchKeyEvent", type="keyUp", key="Enter", code="Enter", modifiers=2, windowsVirtualKeyCode=13)
    time.sleep(0.6)
    o = O(P)
    check("Ctrl+Enter 저장 → '숙제 끝! 🔥 1일째'", o["doneShown"] and o["done"] == "숙제 끝! 🔥 1일째", o["done"])
    P.shot(os.path.join(SH, "pc_ov_done.png"))
    wait_closed(P, 4)
    fs = dump(P)
    qa = {k.split("/")[-1]: v for k, v in fs.items() if "/_질문과답/" in k}
    check("기존 Q001 파일은 그대로 (덮어쓰지 않음)", qa.get("2026-10-11_Q001_첫현장.md") == ORIG_Q001)
    new = qa.get("2026-10-11_Q001_첫현장_2.md", "")
    check("새 파일 2026-10-11_Q001_첫현장_2.md", bool(new), list(qa))
    check("형식: 제목·질문·답 (CRLF)", new.startswith("# Q001 · 2026-10-11 · (03 설치)\r\n\r\n**질문:** 처음 엔지니어로") and "**답:**\r\n\r\n첫 현장은 울산이었다.\r\n안전화 끈부터 다시 맸다." in new, new[:200])
    setnow(P, "2026-10-11T22:30:00")
    check("저장 뒤 다시 안 뜸 + 홈 '오늘 숙제 끝 ✓'", P.ev('document.getElementById("ov").hidden') and "끝" in P.ev('document.getElementById("tStatus").textContent'))
    # ---------- 2일째: 다른 질문 + 자유 일기 ----------
    setnow(P, "2026-10-12T21:00:01"); wait_open(P)
    o = O(P); q2 = first_of("04", {"Q049"})
    check(f"2일째: 장 순환 04 + 답한 Q049 건너뜀 → {q2}", o["qid"] == q2 and o["kick"] == "오늘의 숙제가 있어요 ✏️", o["qid"])
    check("2일째 연속 표시 '🔥 1일째'", o["streak"] == "🔥 1일째", o["streak"])
    click(P, "oOther"); time.sleep(0.3)
    o = O(P); q3 = first_of("05")
    check(f"[다른 질문] → 05 장 {q3}", o["qid"] == q3 and "05 응용운전 영업" in o["pill"], o["pill"])
    check("건너뛴 질문 기록", P.ev(f'HW.S.b["adult-manual"].skipped["{q2}"]') == 1)
    click(P, "oDiary"); time.sleep(0.2)
    check("자유 일기 모드", O(P)["diary"] and O(P)["pill"] == "자유 일기")
    type_text(P, "오늘은 질문 대신 일기. 아들이랑 저녁 먹음.")
    click(P, "oSave"); time.sleep(0.6)
    check("일기 저장 → 🔥 2일째", O(P)["done"] == "숙제 끝! 🔥 2일째", O(P)["done"])
    wait_closed(P, 4)
    qa = {k.split("/")[-1]: v for k, v in dump(P).items() if "/_질문과답/" in k}
    d1 = qa.get("2026-10-12_D001_일기.md", "")
    check("2026-10-12_D001_일기.md", d1.startswith("# D001 · 2026-10-12 · 자유 일기\r\n\r\n오늘은 질문 대신 일기."), list(qa))
    # 하나 더 쓰기 (수동)
    click(P, "bNow"); time.sleep(0.4)
    o = O(P)
    check("'하나 더 쓰기' → 수동 창 (닫기 버튼)", o["mode"] == "manual" and o["snooze"] == "닫기", o)
    click(P, "oSnooze"); wait_closed(P)
    # ---------- 3일째 놓침 → 4일째 아침에 '어제 숙제' ----------
    setnow(P, "2026-10-14T08:00:00"); reload(P)
    check("PC 꺼져 있던 날 → 다음 날 켜면 '어제 숙제'", wait_open(P) and O(P)["mode"] == "catchup")
    o = O(P)
    check("어제 숙제 문구·날짜", o["kick"] == "어제 숙제가 남아 있어요 📒" and "10월 13일" in P.ev('document.getElementById("oDate").textContent') and o["snooze"] == "다음에", o)
    check("어제 숙제 창: '🔥 2일째 · 이어 가기'", o["streak"] == "🔥 2일째 · 이어 가기", o["streak"])
    P.shot(os.path.join(SH, "pc_ov_catchup.png"))
    qid3 = o["qid"]
    type_text(P, "어제는 출장이라 못 썼다.")
    click(P, "oSave"); time.sleep(0.6)
    check("어제 숙제 저장 → 🔥 3일째 (10/11~10/13)", O(P)["done"] == "숙제 끝! 🔥 3일째", O(P)["done"])
    wait_closed(P, 4)
    qa = {k.split("/")[-1]: v for k, v in dump(P).items() if "/_질문과답/" in k}
    f3 = [k for k in qa if k.startswith(f"2026-10-13_{qid3}_")]
    check("어제 날짜 파일 + '다음 날 씀'", f3 and "· 다음 날 씀" in qa[f3[0]].splitlines()[0], f3)
    reload(P)
    check("다시 열어도 어제 숙제는 한 번만", P.ev('document.getElementById("ov").hidden'))
    # ---------- 4일째: 22:30 에 켬 → 바로 뜸 → 3번 미룸 → 쉼 ----------
    setnow(P, "2026-10-14T22:30:00"); reload(P)
    check("21:00 지나서 켬 → 바로 숙제 창", wait_open(P) and O(P)["mode"] == "normal")
    for i, t in enumerate(("22:40:05", "22:50:05", "23:00:05")):
        click(P, "oSnooze"); wait_closed(P); setnow(P, "2026-10-14T" + t); wait_open(P)
    check("3번 미룸 → persist", O(P)["mode"] == "persist")
    click(P, "oRestOpen"); time.sleep(0.3); type_text(P, "감기 몸살로 일찍 잠", "oRestText"); click(P, "oRestSave"); time.sleep(0.6)
    check("오늘은 쉼 저장 → '오늘은 쉼 ✓  🔥 4일째'", O(P)["done"] == "오늘은 쉼 ✓  🔥 4일째", O(P)["done"])
    wait_closed(P, 4)
    qa = {k.split("/")[-1]: v for k, v in dump(P).items() if "/_질문과답/" in k}
    r1 = qa.get("2026-10-14_쉼.md", "")
    check("2026-10-14_쉼.md 에 이유", "**쉰 이유:** 감기 몸살로 일찍 잠" in r1, r1[:120])
    check("쉰 날 질문은 답한 것으로 안 침", not P.ev(f'"{O(P)["qid"] if O(P)["qid"] else "x"}" in HW.S.b["adult-manual"].answered'))
    # ---------- 5일째 놓침 → 6일째 '다음에' → 다시 안 물음, 연속 끊김 ----------
    setnow(P, "2026-10-16T09:00:00"); reload(P)
    check("10/15 놓침 → 어제 숙제", wait_open(P) and O(P)["mode"] == "catchup")
    click(P, "oSnooze"); wait_closed(P); reload(P)
    check("'다음에' 누르면 다시 안 물음", P.ev('document.getElementById("ov").hidden'))
    check("연속 기록 끊김 → '🔥 오늘이 첫날'", P.ev('document.getElementById("tStreak").textContent') == "🔥 오늘이 첫날")
    # ---------- 자정 넘김: 창이 열린 채 날짜가 바뀜 → 어제 숙제로 ----------
    setnow(P, "2026-10-16T23:59:57"); wait_open(P)
    check("10/16 23:59 숙제 창", O(P)["date"] == "2026-10-16" and O(P)["mode"] == "normal")
    setnow(P, "2026-10-17T00:00:03"); time.sleep(0.6)
    o = O(P)
    check("자정 넘으면 같은 창이 '어제 숙제'로 바뀜", o["mode"] == "catchup" and o["date"] == "2026-10-16", o)
    type_text(P, "자정 넘어 쓴 한 줄"); click(P, "oSave"); time.sleep(0.6)
    check("저장 → 10/16 로 기록, 🔥 1일째", O(P)["done"] == "숙제 끝! 🔥 1일째", O(P)["done"]); wait_closed(P, 4)
    # ---------- 설정 저장 ----------
    click(P, "bSettings"); time.sleep(0.3)
    P.ev('(() => { const s = (id, v) => { const e = document.getElementById(id); e.value = v; e.dispatchEvent(new Event("change")); }; s("cTime", "20:30"); s("cSnMin", "5"); s("cSnMax", "2"); s("cTheme", "dark"); const sp = document.getElementById("cSpeak"); sp.checked = false; sp.dispatchEvent(new Event("change")); return 1; })()')
    P.shot(os.path.join(SH, "pc_settings_dark.png"))
    reload(P)
    c = json.loads(P.ev('JSON.stringify(HW.cfg)'))
    check("설정 저장 유지 (20:30·5분·2번·어둡게·읽기 끔)", c["time"] == "20:30" and c["snoozeMin"] == 5 and c["snoozeMax"] == 2 and c["theme"] == "dark" and c["speak"] is False, c)
    check("어둡게 → data-theme=dark", P.ev('document.documentElement.dataset.theme') == "dark")
    setnow(P, "2026-10-17T20:30:05"); wait_open(P)
    check("바꾼 시각 20:30 에 뜸 + '5분 뒤에 (2번 남음)'", O(P)["snooze"] == "5분 뒤에 (2번 남음)", O(P)["snooze"])
    P.shot(os.path.join(SH, "pc_ov_dark.png"))
    click(P, "oSnooze"); wait_closed(P)
    check("미룸 토스트 '숙제 검사 5분 전입니다'", "숙제 검사 5분 전입니다" in toast(P), toast(P))
    P.ev('(() => { const e = document.getElementById("cTheme"); e.value = "auto"; e.dispatchEvent(new Event("change")); return 1; })()')
    # ---------- 내보내기 (PC: 내려받기) ----------
    print("  export:", P.ev('HW.exportAll().then(n => String(n)).catch(e => "ERR " + e.message)'), toast(P))
    for _ in range(40):
        zips = glob.glob(os.path.join(DL, "homework_*.zip"))
        if zips: time.sleep(0.5); break
        time.sleep(0.5)
    check("PC 내보내기 → zip 내려받음", zips, zips)
    if zips:
        with zipfile.ZipFile(zips[0]) as z: names = z.namelist()
        check("zip 안: _질문과답/…md + homework.json (한글 이름)", "homework.json" in names and any(n.endswith("2026-10-11_Q001_첫현장_2.md") for n in names), names)
    check("PC 페이지 JS 오류 없음", not P.errs, P.errs)

    # ================= 휴대폰 (폴더 없음 → 기기 저장 → 공유) =================
    M = B.page("phone", 390, 844, "window.__PHONE__ = 1;" + HOOK); pages.append(M)
    M.go(BASE); time.sleep(1.0); M.ev('__setNow("2026-10-11T21:00:00", 1)'); reload(M)
    check("휴대폰: 폴더 줄 없음", M.ev('document.getElementById("wFolderRow").hidden'))
    M.shot(os.path.join(SH, "phone_welcome.png"))
    click(M, "wGo"); time.sleep(0.4); M.ev('HW.tick()')
    check("휴대폰 21:00 → 숙제 창", wait_open(M) and O(M)["qid"] == "Q001")
    M.shot(os.path.join(SH, "phone_ov.png"))
    type_text(M, "휴대폰에서 쓴 첫 현장 이야기"); click(M, "oSave"); time.sleep(0.6)
    check("휴대폰 저장 → 숙제 끝 + '이 기기에 저장'", "숙제 끝!" in O(M)["done"] and "이 기기" in M.ev('document.getElementById("oDoneSmall").textContent'))
    wait_closed(M, 4)
    check("목록에 '📱 이 기기에만'", "이 기기에만" in M.ev('document.getElementById("list").textContent'))
    check("휴대폰 홈: 기기 카드 보임, 폴더 카드 숨김", M.ev('!document.getElementById("cDevice").hidden && document.getElementById("cFolder").hidden'))
    M.shot(os.path.join(SH, "phone_home.png"), full=True)
    click(M, "bExport"); time.sleep(2.5)
    sh = json.loads(M.ev('JSON.stringify(window.__shared)') or "null")
    check("휴대폰 내보내기 → 공유 (ASCII 파일 이름 zip)", sh and sh["name"].startswith("homework_") and sh["name"].isascii(), sh and sh["name"])
    PZ = os.path.join(DL, "phone_" + (sh["name"] if sh else "x.zip"))
    if sh: open(PZ, "wb").write(base64.b64decode(sh["b64"]))
    # 같은 날 두 번째 (수동) → 질문 바뀜
    click(M, "bNow"); time.sleep(0.4)
    check("휴대폰 '하나 더 쓰기' → 답한 Q001 대신 다른 질문", O(M)["qid"] != "Q001", O(M)["qid"])
    click(M, "oSnooze"); wait_closed(M)
    check("휴대폰 JS 오류 없음", not M.errs, M.errs)

    # ================= PC 로 가져오기 =================
    doc = P.call("DOM.getDocument")["root"]["nodeId"]
    nid = P.call("DOM.querySelector", nodeId=doc, selector="#fImport")["nodeId"]
    P.call("DOM.setFileInputFiles", nodeId=nid, files=[PZ]); time.sleep(2.0)
    t1 = toast(P)
    qa = {k.split("/")[-1]: v for k, v in dump(P).items() if "/_질문과답/" in k}
    check("가져오기 → '가져옴 1개'", "가져옴 1개" in t1, t1)
    check("휴대폰 답 → 2026-10-11_Q001_첫현장_3.md (기존 둘 그대로)", "휴대폰에서 쓴" in qa.get("2026-10-11_Q001_첫현장_3.md", "") and qa.get("2026-10-11_Q001_첫현장.md") == ORIG_Q001, sorted(qa))
    P.call("DOM.setFileInputFiles", nodeId=nid, files=[PZ]); time.sleep(2.0)
    t2 = toast(P)
    check("같은 파일 다시 가져오기 → 이미 있음 (중복 안 생김)", "가져옴 0개" in t2 and "이미 있음 1개" in t2, t2)
    # ================= 화면 넘침 (320~430) =================
    for w in (320, 360, 390, 430):
        P.call("Emulation.setDeviceMetricsOverride", width=w, height=800, deviceScaleFactor=2, mobile=True); time.sleep(0.4)
        a = no_overflow(P)
        click(P, "bNow"); time.sleep(0.4); b2 = no_overflow(P)
        if w == 320: P.shot(os.path.join(SH, "w320_ov.png"))
        click(P, "oX"); wait_closed(P)
        click(P, "bSettings"); time.sleep(0.3); c2 = no_overflow(P)
        if w == 320: P.shot(os.path.join(SH, "w320_settings.png"))
        P.ev('document.querySelector("#setSheet [data-close]").click()')
        check(f"{w}px: 홈·숙제 창·설정 넘침 없음", a and b2 and c2, (a, b2, c2))
    P.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "dark"}]); time.sleep(0.3)
    P.shot(os.path.join(SH, "w430_home_dark.png"), full=True)
    check("모든 페이지 JS 오류 0", not P.errs and not M.errs, P.errs + M.errs)
    # 시험 폴더를 E: 로 꺼내 둠
    for k, v in dump(P).items():
        out = os.path.join(MIRROR, *k.split("/")); os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8", newline="").write(v)
    print("시험 폴더 사본:", MIRROR, sorted(os.listdir(os.path.join(MIRROR, "어른 매뉴얼", "_질문과답"))))
finally:
    B.quit(); srv.shutdown()
ok = sum(1 for _, c in res if c)
print(f"\n{ok}/{len(res)} 통과")
sys.exit(0 if ok == len(res) else 1)
