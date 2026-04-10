"""
update_index_buzz.py
GitHub Actions 전용 - Excel 없이 네이버 API 캐시(naver_buzz_cache.json)만으로
index.html의 BUZZ_POSTS를 업데이트합니다.
기존 index.html에 이미 포함된 Excel 데이터는 유지하고, 신규 Naver API 데이터만 추가합니다.
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import json, os
from json import JSONDecoder

BASE = os.path.dirname(__file__)
HTML_PATH  = os.path.join(BASE, 'index.html')
CACHE_PATH = os.path.join(BASE, 'naver_buzz_cache.json')


def replace_json_var(html: str, var_name: str, new_data) -> str:
    """HTML 내 'const VAR_NAME=[...]' 를 JSON 파서로 정확히 찾아 교체."""
    marker = f'const {var_name}='
    start = html.find(marker)
    if start < 0:
        return html
    data_start = start + len(marker)
    decoder = JSONDecoder()
    _, length = decoder.raw_decode(html[data_start:])
    # 세미콜론까지 포함해서 교체
    end = data_start + length
    if html[end:end+1] == ';':
        end += 1
    new_str = marker + json.dumps(new_data, ensure_ascii=False) + ';'
    return html[:start] + new_str + html[end:]


def extract_json_var(html: str, var_name: str):
    """HTML 내 'const VAR_NAME=[...]' 를 JSON 파서로 정확히 추출."""
    marker = f'const {var_name}='
    start = html.find(marker)
    if start < 0:
        return None
    data_start = start + len(marker)
    decoder = JSONDecoder()
    obj, _ = decoder.raw_decode(html[data_start:])
    return obj


# ── index.html 읽기
with open(HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# ── 기존 BUZZ_POSTS 추출
existing_posts = extract_json_var(html, 'BUZZ_POSTS')
if existing_posts is None:
    print('BUZZ_POSTS를 찾을 수 없습니다.')
    sys.exit(1)

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

# ── index.html BUZZ_POSTS 교체 (JSON 파서 기반 - 특수문자 안전)
html = replace_json_var(html, 'BUZZ_POSTS', existing_posts)

with open(HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print('index.html 업데이트 완료')
