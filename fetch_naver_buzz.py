"""
fetch_naver_buzz.py
네이버 카페 검색 API로 로토토베베·로덬메이트 언급 게시물을 자동 수집합니다.
결과를 naver_buzz_cache.json에 저장하고, update_buzz.py 실행 전에 돌려주세요.

사용법:
  1. .env 파일에 NAVER_CLIENT_ID, NAVER_CLIENT_SECRET 입력
  2. python fetch_naver_buzz.py
  3. python update_buzz.py  (Excel + 네이버 API 데이터 합산)
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os, json, re, requests
from datetime import datetime, timezone, timedelta
from html import unescape

# ── .env 파일 로드 (있으면 자동 적용)
_env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(_env_path):
    with open(_env_path, encoding='utf-8') as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith('#') and '=' in _line:
                _k, _v = _line.split('=', 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# ── 환경변수 또는 직접 입력 (.env 파일 권장)
CLIENT_ID     = os.environ.get('NAVER_CLIENT_ID',     'YOUR_CLIENT_ID')
CLIENT_SECRET = os.environ.get('NAVER_CLIENT_SECRET', 'YOUR_CLIENT_SECRET')

# ── 검색 키워드 (브랜드·제품명)
KEYWORDS = ['로토토베베', '로덬메이트', 'rototobebe']

# ── 모니터링 대상 카페 (cafename에 포함되면 매핑)
TARGET_CAFES = {
    '맘스홀릭베이비': '맘스홀릭베이비',
    '맘스홀릭':       '맘스홀릭베이비',
    '맘이베베':       '맘이베베',
    '헤이든':         '헤이든',
    '레몬테라스':     '레몬테라스',
}

# ── 간단 감성 키워드 (자동 분류)
POS_WORDS = ['좋아요','추천','완전조아','최고','만족','강추','효과','좋은','예뻐','귀여워','좋았']
NEG_WORDS = ['별로','실망','환불','불만','최악','나빠','비추','문제','이상','불편','화나','짜증']

KST = timezone(timedelta(hours=9))


def clean_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    return unescape(text).strip()


def parse_pub_date(pub_date_str: str) -> str:
    """'Mon, 10 Apr 2026 10:00:00 +0900' → '2026.04.10.'"""
    try:
        dt = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
        return dt.astimezone(KST).strftime('%Y.%m.%d.')
    except Exception:
        return ''


def detect_cafe(cafe_name: str) -> str:
    for key, mapped in TARGET_CAFES.items():
        if key in cafe_name:
            return mapped
    return ''


def detect_sentiment(title: str, description: str) -> str:
    text = title + ' ' + description
    pos = sum(1 for w in POS_WORDS if w in text)
    neg = sum(1 for w in NEG_WORDS if w in text)
    if neg > pos:
        return '부정'
    if pos > neg:
        return '긍정'
    return '중립'


def search_cafe_articles(query: str, display: int = 100, sort: str = 'date') -> list:
    url = 'https://openapi.naver.com/v1/search/cafearticle.json'
    headers = {
        'X-Naver-Client-Id':     CLIENT_ID,
        'X-Naver-Client-Secret': CLIENT_SECRET,
    }
    params = {'query': query, 'display': display, 'sort': sort}
    res = requests.get(url, headers=headers, params=params, timeout=10)
    res.raise_for_status()
    return res.json().get('items', [])


def fetch_all() -> list:
    posts = []
    seen  = set()

    for keyword in KEYWORDS:
        try:
            items = search_cafe_articles(keyword)
            count = 0
            for item in items:
                link = item.get('link', '')
                if link in seen:
                    continue
                seen.add(link)

                cafe = detect_cafe(item.get('cafename', ''))
                if not cafe:
                    continue  # 타겟 카페 외 제외

                title       = clean_html(item.get('title', ''))
                description = clean_html(item.get('description', ''))
                pub_date    = parse_pub_date(item.get('pubDate', ''))
                sentiment   = detect_sentiment(title, description)

                posts.append({
                    'date':    pub_date,
                    'cafe':    cafe,
                    'title':   title,
                    'sent':    sentiment,
                    'summary': description[:100],
                    'view':    0,   # API에서 조회수 미제공
                    'cmt':     0,   # API에서 댓글수 미제공
                    'cat':     keyword,
                    'type':    '오가닉',  # 자동 수집 = 오가닉으로 분류
                    'link':    link,
                    '_src':    'naver_api',
                })
                count += 1

            print(f'[{keyword}] 타겟 카페 {count}건 수집 (전체 {len(items)}건 중)')

        except requests.HTTPError as e:
            print(f'[{keyword}] HTTP 오류: {e.response.status_code} — {e.response.text[:200]}')
        except Exception as e:
            print(f'[{keyword}] 오류: {e}')

    # 날짜 내림차순 정렬
    posts.sort(key=lambda x: x['date'], reverse=True)
    return posts


def main():
    if CLIENT_ID == 'YOUR_CLIENT_ID':
        print('⚠  API 키가 설정되지 않았습니다.')
        print('   .env 파일에 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET를 입력하거나')
        print('   이 파일 상단의 CLIENT_ID / CLIENT_SECRET 변수를 직접 수정하세요.')
        print()
        print('   네이버 개발자센터 → 애플리케이션 등록:')
        print('   https://developers.naver.com/apps/#/register')
        return

    print('네이버 카페 버즈 수집 시작...')
    posts = fetch_all()

    cache_path = os.path.join(os.path.dirname(__file__), 'naver_buzz_cache.json')
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(posts, f, ensure_ascii=False, indent=2)

    print(f'\n총 {len(posts)}건 수집 → naver_buzz_cache.json 저장 완료')

    # 감성 요약
    neg = [p for p in posts if p['sent'] == '부정']
    pos = [p for p in posts if p['sent'] == '긍정']
    print(f'긍정: {len(pos)}건 / 부정: {len(neg)}건 / 중립: {len(posts)-len(pos)-len(neg)}건')

    if neg:
        print('\n[부정 게시물 목록]')
        for p in neg[:5]:
            print(f'  {p["date"]} [{p["cafe"]}] {p["title"][:40]}')


if __name__ == '__main__':
    main()
