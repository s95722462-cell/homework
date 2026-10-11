# 숙제 (Homework)

하루 한 질문, **한 줄이면 끝**나는 숙제. 답은 책 원고 재료로 쌓여요.

- 주소: https://s95722462-cell.github.io/homework/
- 질문 묶음: `bundles/adult-manual.json` — "어른 매뉴얼 숙제" 150문제 (`tools/make_bundle.py` 로 만듦, 번호는 바꾸지 않고 새 질문은 끝에 추가)
- PC Edge/Chrome: 처음 한 번 책 폴더(`어른 매뉴얼`)를 고르면 `_질문과답\YYYY-MM-DD_Q###_주제.md` 새 파일로 바로 저장 (덮어쓰지 않음, 같은 이름이면 `_2`)
- 휴대폰: 기기(IndexedDB)에 저장 → [내보내기] zip 공유 → PC에서 [휴대폰 숙제 가져오기]
- 알림은 이 화면(탭)이 열려 있을 때만 — 탭이 닫혀 있을 때는 휴대폰 알람·아이폰 단축어·Edge 앱 자동 시작으로 열어 주세요
- 시험: `py tools/test/e2e.py` (헤드리스 Edge, 가짜 시계, 시험 폴더는 OPFS → `E:\claude_보관\homework_test\book_mirror`)
- 올릴 때마다 `sw.js` 의 `CACHE` 번호를 올림
