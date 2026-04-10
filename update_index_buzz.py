"""
update_index_buzz.py
GitHub Actions 전용 - Excel 없이 네이버 API 캐시(naver_buzz_cache.json)만으로
index.html의 BUZZ_POSTS를 업데이트합니다.
기존 index.html에 이미 포함된 Excel 데이터는 유지하고, 신규 Naver API 데이터만 추가합니다.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json, re, os

BASE = os.path.dirname(__file__)
HTML_PATH  = os.path.join(BASE, 'index.html')
CACHE_PATH = os.path.join(BASE, 'naver_buzz_cache.json')

# ── index.html 읽기
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 기존 BUZZ_POSTS 추출
m = re.search(r'const BUZZ_POSTS=(\[.*?\]);', html, re.DOTALL)
if not m:
    print('BUZZ_POSTS를 찾을 수 없습니다.')
    sys.exit(1)

existing_posts = json.loads(m.group(1))
existing_links = {p.get('link', '') for p in existing_posts if p.get('link')}
print(f'기존 BUZZ_POSTS: {len(existing_posts)}건')

# ── 네이버 API 캐시 로드 및 신규 추가
if not os.path.exists(CACHE_PATH):
    print('naver_buzz_cache.json 없음 — 업데이트 없이 종료')
    sys.exit(0)

with open(CACHE_PATH, 'r', encoding='utf-8') as f:
    naver_posts = json.load(f)

added = 0
for p in naver_posts:
    link = p.get('link', '')
    if link and link in existing_links:
        continue
    existing_links.add(link)
    p_clean = {k: v for k, v in p.items() if k != '_src'}
    existing_posts.append(p_clean)
    added += 1

# 날짜 내림차순 정렬
existing_posts.sort(key=lambda x: x.get('date', ''), reverse=True)

print(f'신규 추가: {added}건 → 총 {len(existing_posts)}건')

# ── index.html BUZZ_POSTS 교체
new_js = f'const BUZZ_POSTS={json.dumps(existing_posts, ensure_ascii=False)};'
html = re.sub(r'const BUZZ_POSTS=\[.*?\];', new_js, html, flags=re.DOTALL)

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print('index.html 업데이트 완료')
