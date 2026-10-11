import sys; sys.stdout.reconfigure(encoding="utf-8")
import time, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cdp import Browser
URL = "https://s95722462-cell.github.io/homework/"
B = Browser("live"); ok = []
def check(n, c, i=""): ok.append(bool(c)); print(("PASS " if c else "FAIL ") + n, i)
try:
    for w, h, nm in ((1280, 900, "pc"), (390, 844, "phone")):
        p = B.page(nm, w, h, "window.confirm=()=>true;", URL); time.sleep(2)
        p.wait('window.HW && !document.getElementById("welSheet").hidden && 1', 15)
        check(f"{nm}: 질문 150개 불러옴", p.ev('document.getElementById("welBundle").textContent.includes("150문제")'))
        check(f"{nm}: 시작 안내 보임", p.ev('!document.getElementById("welSheet").hidden'))
        p.ev('document.getElementById("wGo").click(), 1'); time.sleep(0.5)
        check(f"{nm}: 지금 숙제하기 → Q001", p.ev('document.getElementById("bNow").click(), HW.O && HW.O.qid') == "Q001")
        check(f"{nm}: 서비스 워커 등록", p.wait('navigator.serviceWorker.getRegistration().then(r => !!(r && (r.active || r.waiting || r.installing)))', 10))
        z = p.ev('new Promise(r => { const s = document.createElement("script"); s.src = "https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"; s.integrity = "sha512-XMVd28F1oH/O71fzwBnV7HucLxVwtxf26XV8P4wPk26EDxuGZ91N8bsOttmnomcCD3CS5ZMRL50H0GgOHvegtg=="; s.crossOrigin = "anonymous"; s.onload = () => r(typeof JSZip); s.onerror = () => r("err"); document.head.append(s); })')
        check(f"{nm}: JSZip (cdnjs, SRI) 불러옴", z == "function", z)
        check(f"{nm}: 넘침 없음", p.ev('document.documentElement.scrollWidth <= innerWidth'))
        p.shot(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "shots", f"live_{nm}.png"))
        check(f"{nm}: JS 오류 없음", not p.errs, p.errs)
finally:
    B.quit()
print(f"{sum(ok)}/{len(ok)} 통과")
