"""
update_all.py
모든 엑셀 파일을 읽어 index.html 전체를 한 번에 업데이트합니다.

사용법:
  python update_all.py

업데이트 항목:
  1. 버즈 모니터링  ← 03 데일리 버즈 모니터링/00.데일리 버즈 모니터링.xlsx
  2. 로덬메이트     ← 02 로덬메이트/📢 2026 SUMMER 로덬메이트 운영현황_최신.xlsx
  3. Naver API     ← fetch_naver_buzz.py 자동 실행
"""

import sys, os, json, re, glob, subprocess
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
from json import JSONDecoder

BASE = os.path.dirname(os.path.abspath(__file__))
HTML_IN  = os.path.join(BASE, 'rototobebe_dashboard_v4.html')
HTML_OUT = os.path.join(BASE, 'index.html')

# ── JSON 파서 기반 교체 (특수문자 안전)
def replace_json_var(html: str, var_name: str, new_data) -> str:
    marker = f'const {var_name}='
    start = html.find(marker)
    if start < 0:
        print(f'  [SKIP] {var_name} 없음')
        return html
    data_start = start + len(marker)
    decoder = JSONDecoder()
    _, length = decoder.raw_decode(html[data_start:])
    end = data_start + length
    if html[end:end+1] == ';':
        end += 1
    new_str = marker + json.dumps(new_data, ensure_ascii=False) + ';'
    return html[:start] + new_str + html[end:]


# ══════════════════════════════════════════
# 1. 버즈 모니터링 (Excel)
# ══════════════════════════════════════════
def load_buzz():
    xl_path = os.path.join(BASE, '03 데일리 버즈 모니터링', '00.데일리 버즈  모니터링.xlsx')
    if not os.path.exists(xl_path):
        print('  [SKIP] 버즈 Excel 없음')
        return None, None, None

    xl = pd.ExcelFile(xl_path)

    # WEEKLY
    weekly_raw = pd.read_excel(xl, sheet_name='DATE(WEEKLY)', header=None)
    BUZZ_WEEKLY = []
    for i in range(6, 11):
        row = weekly_raw.iloc[i]
        week = str(row[0]).strip() if pd.notna(row[0]) else ''
        if not week or week == 'nan':
            continue
        total = int(row[1]) if pd.notna(row[1]) else 0
        delta_raw = row[2]
        delta = None if (pd.isna(delta_raw) or str(delta_raw).strip() in ['-','nan','']) else int(delta_raw)
        post  = int(row[3])  if pd.notna(row[3])  else 0
        comment = int(row[4]) if pd.notna(row[4]) else 0
        mam   = int(row[5])  if pd.notna(row[5])  else 0
        beibe = int(row[8])  if pd.notna(row[8])  else 0
        haydn = int(row[11]) if pd.notna(row[11]) else 0
        lemon = int(row[14]) if pd.notna(row[14]) else 0
        mam_og   = int(row[6])  if pd.notna(row[6])  else 0
        beibe_og = int(row[9])  if pd.notna(row[9])  else 0
        haydn_og = int(row[12]) if pd.notna(row[12]) else 0
        lemon_og = int(row[15]) if pd.notna(row[15]) else 0
        organic = mam_og + beibe_og + haydn_og + lemon_og
        BUZZ_WEEKLY.append({
            'week': week, 'total': total, 'delta': delta,
            'post': post, 'comment': comment, 'organic': organic,
            'mam': mam, 'beibe': beibe, 'haydn': haydn, 'lemon': lemon
        })

    # DAILY
    daily_raw = pd.read_excel(xl, sheet_name='DATE(DAYLY)', header=None)
    BUZZ_DAILY_CHART = []
    for i in range(6, len(daily_raw)):
        row = daily_raw.iloc[i]
        date_str = str(row[2]).strip() if pd.notna(row[2]) else ''
        if not date_str or date_str == 'nan':
            continue
        total   = int(row[3]) if pd.notna(row[3]) else 0
        organic = int(row[5]) if pd.notna(row[5]) else 0
        ad      = int(row[6]) if pd.notna(row[6]) else 0
        d = date_str.replace('2026.', '').rstrip('.')
        BUZZ_DAILY_CHART.append({'d': d, 'total': total, 'organic': organic, 'ad': ad})

    # POSTS
    db = pd.read_excel(xl, sheet_name='DATEBASE', header=0)
    BUZZ_POSTS = []
    for _, row in db.iterrows():
        cafe  = str(row['카페명']).strip()    if pd.notna(row.get('카페명'))    else ''
        date  = str(row['작성일']).strip()    if pd.notna(row.get('작성일'))    else ''
        title = str(row['게시물']).strip()    if pd.notna(row.get('게시물'))    else ''
        sent  = str(row['긍/부정']).strip()   if pd.notna(row.get('긍/부정'))   else ''
        summ  = str(row['내용 축약']).strip() if pd.notna(row.get('내용 축약')) else ''
        view  = int(row['조회수'])            if pd.notna(row.get('조회수'))    else 0
        cmt   = int(row['댓글'])              if pd.notna(row.get('댓글'))      else 0
        cat   = str(row['구분']).strip()      if pd.notna(row.get('구분'))      else ''
        wtype = str(row['작성형태']).strip()  if pd.notna(row.get('작성형태'))  else ''
        link  = str(row['게시물 링크']).strip() if (pd.notna(row.get('게시물 링크')) and str(row.get('게시물 링크')) != 'nan') else ''
        sort_key = date.replace('.','').ljust(8,'0')
        BUZZ_POSTS.append({
            'date': date, 'cafe': cafe, 'title': title, 'sent': sent,
            'summary': summ, 'view': view, 'cmt': cmt, 'cat': cat,
            'type': wtype, 'link': link, '_sort': sort_key
        })
    BUZZ_POSTS.sort(key=lambda x: x['_sort'], reverse=True)
    for p in BUZZ_POSTS:
        del p['_sort']

    print(f'  버즈 Excel: 위클리 {len(BUZZ_WEEKLY)}주 / 데일리 {len(BUZZ_DAILY_CHART)}일 / 게시물 {len(BUZZ_POSTS)}건')
    return BUZZ_WEEKLY, BUZZ_DAILY_CHART, BUZZ_POSTS


# ══════════════════════════════════════════
# 2. 로덬메이트 (Excel)
# ══════════════════════════════════════════
def load_rodem():
    rodem_dir = os.path.join(BASE, '02 로덬메이트')
    files = sorted(glob.glob(os.path.join(rodem_dir, '*.xlsx')))
    if not files:
        print('  [SKIP] 로덬메이트 Excel 없음')
        return None, None, None, None

    xl_path = files[-1]  # 가장 최신 파일
    xl = pd.ExcelFile(xl_path)
    print(f'  로덬메이트 파일: {os.path.basename(xl_path)}')

    # ── MEMBERS: 26여름로덬메이트 시트 (기본 정보)
    df_base = pd.read_excel(xl, sheet_name='26여름로덬메이트', header=0)
    # 컬럼명 표준화
    cols = df_base.columns.tolist()
    name_col  = next((c for c in cols if '성함' in str(c)), cols[2])
    phone_col = next((c for c in cols if '연락처' in str(c)), cols[3])

    # ── 활동 현황: 여름 활동 현황 시트
    df_act = pd.read_excel(xl, sheet_name='여름 활동 현황', header=5)
    act_cols = df_act.columns.tolist()
    # 주차 컬럼들 찾기 (1주차~12주차)
    week_cols = [c for c in act_cols if re.match(r'\d+주차$', str(c))]

    # ── 댓글 활동: 댓글 활동 시트
    df_cmt = pd.read_excel(xl, sheet_name='댓글 활동', header=0)

    # phone → 행 매핑 (여름 활동 현황)
    phone_map = {}
    for _, row in df_act.iterrows():
        name = str(row.get('이름', '')).strip()
        phone = str(row.get('핸드폰번호', '')).strip()
        total = int(row.get('합계', 0)) if pd.notna(row.get('합계')) else 0
        w_vals = {}
        for wc in week_cols:
            v = row.get(wc)
            w_vals[wc] = int(v) if pd.notna(v) else 0
        phone_map[name] = {'phone': phone, 'total': total, 'weeks': w_vals}

    # ig → 댓글수 매핑
    ig_comment_map = {}
    if 'username' in df_cmt.columns:
        cmt_counts = df_cmt['username'].value_counts().to_dict()
        ig_comment_map = {str(k): int(v) for k, v in cmt_counts.items()}

    # dashboard_data.json 기반으로 MEMBERS 구조 유지
    data_path = os.path.join(BASE, 'dashboard_data.json')
    if os.path.exists(data_path):
        with open(data_path, encoding='utf-8') as f:
            data = json.load(f)
        MEMBERS = data['MEMBERS']
        PROD = data['PROD']
    else:
        MEMBERS = []
        PROD = {}

    # ACT 업데이트
    ACT = {}
    for m in MEMBERS:
        name  = m['name']
        phone = m['phone']
        info  = phone_map.get(name, {})
        total = info.get('total', 0)
        w_vals = info.get('weeks', {})
        # 최신 2주차 값 추출
        wk_list = [w_vals.get(wc, 0) for wc in week_cols] if week_cols else []
        # 현재 주차(마지막 비어있지 않은 주차)
        w_current = next((v for v in reversed(wk_list) if v > 0), 0)
        w_prev = 0
        for i in range(len(wk_list)-2, -1, -1):
            if wk_list[i] > 0:
                w_prev = wk_list[i]
                break
        ACT[phone] = {'total': total, 'w1': w_current, 'w2': w_prev}

    # RAW 업데이트 (댓글 카운트)
    RAW = {}
    for m in MEMBERS:
        ig = m.get('ig', '')
        phone = m['phone']
        cheer = ig_comment_map.get(ig, 0)
        # 기존 RAW 유지하고 cheer만 업데이트
        existing = data.get('RAW', {}).get(phone, {'post': 0, 'comment': 0, 'cheer': 0}) if os.path.exists(data_path) else {'post': 0, 'comment': 0, 'cheer': 0}
        RAW[phone] = {'post': existing['post'], 'comment': existing['comment'], 'cheer': cheer}

    print(f'  로덬메이트: {len(MEMBERS)}명 / ACT {len(ACT)}건 / RAW {len(RAW)}건')
    return MEMBERS, ACT, RAW, PROD


# ══════════════════════════════════════════
# 3. 네이버 API 버즈 수집
# ══════════════════════════════════════════
def fetch_naver():
    script = os.path.join(BASE, 'fetch_naver_buzz.py')
    print('  네이버 API 수집 중...')
    result = subprocess.run([sys.executable, script], capture_output=True, text=True, encoding='utf-8')
    if result.returncode == 0:
        lines = [l for l in result.stdout.strip().split('\n') if l]
        for l in lines:
            print('    ' + l)
    else:
        print('  [경고] 네이버 API 오류:', result.stderr[:200])


# ══════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════
def main():
    print('=== update_all.py 시작 ===\n')

    # 1. 버즈 Excel 로드
    print('[1] 버즈 모니터링 Excel 로드')
    BUZZ_WEEKLY, BUZZ_DAILY_CHART, BUZZ_POSTS_excel = load_buzz()

    # 2. 로덬메이트 Excel 로드
    print('\n[2] 로덬메이트 Excel 로드')
    MEMBERS, ACT, RAW, PROD = load_rodem()

    # 3. 네이버 API 수집
    print('\n[3] 네이버 API 버즈 수집')
    fetch_naver()

    # 4. 네이버 캐시 합산
    cache_path = os.path.join(BASE, 'naver_buzz_cache.json')
    BUZZ_POSTS = BUZZ_POSTS_excel or []
    if os.path.exists(cache_path):
        with open(cache_path, encoding='utf-8') as f:
            naver_posts = json.load(f)
        existing_links = {p.get('link','') for p in BUZZ_POSTS if p.get('link')}
        added = 0
        for p in naver_posts:
            link = p.get('link','')
            if link and link in existing_links:
                continue
            existing_links.add(link)
            p_clean = {k: v for k, v in p.items() if k != '_src'}
            BUZZ_POSTS.append(p_clean)
            added += 1
        BUZZ_POSTS.sort(key=lambda x: x.get('date',''), reverse=True)
        print(f'  네이버 캐시 {len(naver_posts)}건 중 {added}건 추가 → 총 {len(BUZZ_POSTS)}건')

    # 5. dashboard_data.json 업데이트
    if MEMBERS:
        data_out = {'MEMBERS': MEMBERS, 'ACT': ACT, 'RAW': RAW, 'PROD': PROD or {}}
        with open(os.path.join(BASE, 'dashboard_data.json'), 'w', encoding='utf-8') as f:
            json.dump(data_out, f, ensure_ascii=False, indent=2)
        print('\n  dashboard_data.json 저장 완료')

    # 6. rototobebe_dashboard_v4.html 읽기
    print('\n[4] HTML 업데이트')
    with open(HTML_IN, 'r', encoding='utf-8') as f:
        html = f.read()

    # 버즈 데이터 교체
    if BUZZ_WEEKLY:
        html = replace_json_var(html, 'BUZZ_WEEKLY', BUZZ_WEEKLY)
        html = replace_json_var(html, 'BUZZ_DAILY_CHART', BUZZ_DAILY_CHART)
        print('  BUZZ_WEEKLY / BUZZ_DAILY_CHART 교체 완료')

    if BUZZ_POSTS:
        html = replace_json_var(html, 'BUZZ_POSTS', BUZZ_POSTS)
        neg = len([p for p in BUZZ_POSTS if p.get('sent') == '부정'])
        print(f'  BUZZ_POSTS {len(BUZZ_POSTS)}건 교체 완료 (부정 {neg}건)')

    # 로덬메이트 데이터 교체
    if MEMBERS:
        html = replace_json_var(html, 'MEMBERS', MEMBERS)
        html = replace_json_var(html, 'ACT', ACT)
        html = replace_json_var(html, 'RAW', RAW)
        if PROD:
            html = replace_json_var(html, 'PROD', PROD)
        print(f'  MEMBERS({len(MEMBERS)}명) / ACT / RAW / PROD 교체 완료')

    # 7. 저장
    with open(HTML_IN, 'w', encoding='utf-8') as f:
        f.write(html)
    import shutil
    shutil.copy2(HTML_IN, HTML_OUT)
    print(f'\n  {os.path.basename(HTML_IN)} → index.html 저장 완료')
    print('\n=== 완료! ===')


if __name__ == '__main__':
    main()
