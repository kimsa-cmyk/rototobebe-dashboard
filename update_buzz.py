import json, re, sys, os
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

xl = pd.ExcelFile('03 데일리 버즈 모니터링/00.데일리 버즈  모니터링.xlsx')

# ── 1. WEEKLY 데이터
weekly_raw = pd.read_excel(xl, sheet_name='DATE(WEEKLY)', header=None)
BUZZ_WEEKLY = []
for i in range(6, 11):  # 2월 1주차 ~ 1월 2주차
    row = weekly_raw.iloc[i]
    week = str(row[0]).strip() if pd.notna(row[0]) else ''
    total = int(row[1]) if pd.notna(row[1]) else 0
    delta_raw = row[2]
    if pd.isna(delta_raw) or str(delta_raw).strip() in ['-', 'nan', '']:
        delta = None
    else:
        delta = int(delta_raw)
    post = int(row[3]) if pd.notna(row[3]) else 0
    comment = int(row[4]) if pd.notna(row[4]) else 0
    mam  = int(row[5])  if pd.notna(row[5])  else 0
    beibe= int(row[8])  if pd.notna(row[8])  else 0
    haydn= int(row[11]) if pd.notna(row[11]) else 0
    lemon= int(row[14]) if pd.notna(row[14]) else 0
    mam_og  = int(row[6])  if pd.notna(row[6])  else 0
    beibe_og= int(row[9])  if pd.notna(row[9])  else 0
    haydn_og= int(row[12]) if pd.notna(row[12]) else 0
    lemon_og= int(row[15]) if pd.notna(row[15]) else 0
    organic = mam_og + beibe_og + haydn_og + lemon_og
    BUZZ_WEEKLY.append({
        'week': week, 'total': total, 'delta': delta,
        'post': post, 'comment': comment, 'organic': organic,
        'mam': mam, 'beibe': beibe, 'haydn': haydn, 'lemon': lemon
    })

# ── 2. DAILY 추이 (DATE(DAYLY))
daily_raw = pd.read_excel(xl, sheet_name='DATE(DAYLY)', header=None)
BUZZ_DAILY_CHART = []
for i in range(6, len(daily_raw)):
    row = daily_raw.iloc[i]
    date_str = str(row[2]).strip() if pd.notna(row[2]) else ''
    if not date_str or date_str == 'nan':
        continue
    total = int(row[3]) if pd.notna(row[3]) else 0
    organic = int(row[5]) if pd.notna(row[5]) else 0
    ad = int(row[6]) if pd.notna(row[6]) else 0
    # date format: 2026.01.05. -> 01.05
    d = date_str.replace('2026.', '').rstrip('.')
    BUZZ_DAILY_CHART.append({'d': d, 'total': total, 'organic': organic, 'ad': ad})

# ── 3. DATEBASE 개별 게시물
db = pd.read_excel(xl, sheet_name='DATEBASE', header=0)
BUZZ_POSTS = []
for _, row in db.iterrows():
    cafe  = str(row['카페명']).strip()    if pd.notna(row['카페명'])    else ''
    date  = str(row['작성일']).strip()    if pd.notna(row['작성일'])    else ''
    title = str(row['게시물']).strip()    if pd.notna(row['게시물'])    else ''
    sent  = str(row['긍/부정']).strip()   if pd.notna(row['긍/부정'])   else ''
    summ  = str(row['내용 축약']).strip() if pd.notna(row['내용 축약']) else ''
    view  = int(row['조회수'])            if pd.notna(row['조회수'])    else 0
    cmt   = int(row['댓글'])              if pd.notna(row['댓글'])      else 0
    cat   = str(row['구분']).strip()      if pd.notna(row['구분'])      else ''
    wtype = str(row['작성형태']).strip()  if pd.notna(row['작성형태'])  else ''
    link  = str(row['게시물 링크']).strip() if (pd.notna(row['게시물 링크']) and str(row['게시물 링크']) != 'nan') else ''
    # 날짜 정렬키: 2026.02.09. -> 20260209
    sort_key = date.replace('.', '').ljust(8, '0')
    BUZZ_POSTS.append({
        'date': date, 'cafe': cafe, 'title': title, 'sent': sent,
        'summary': summ, 'view': view, 'cmt': cmt, 'cat': cat,
        'type': wtype, 'link': link, '_sort': sort_key
    })
# 날짜 내림차순 정렬 후 _sort 키 제거
BUZZ_POSTS.sort(key=lambda x: x['_sort'], reverse=True)
for p in BUZZ_POSTS:
    del p['_sort']

# ── 네이버 API 캐시 데이터 합산 (fetch_naver_buzz.py 실행 결과)
CACHE_PATH = os.path.join(os.path.dirname(__file__), 'naver_buzz_cache.json')
if os.path.exists(CACHE_PATH):
    with open(CACHE_PATH, 'r', encoding='utf-8') as f:
        naver_posts = json.load(f)

    # 중복 제거: 링크 기준 (Excel에 이미 있는 게시물 제외)
    existing_links = {p.get('link','') for p in BUZZ_POSTS if p.get('link')}
    added = 0
    for p in naver_posts:
        link = p.get('link', '')
        if link and link in existing_links:
            continue
        existing_links.add(link)
        # _src 키 제거 후 추가
        p_clean = {k: v for k, v in p.items() if k != '_src'}
        BUZZ_POSTS.append(p_clean)
        added += 1

    # 합산 후 다시 날짜 내림차순 정렬
    BUZZ_POSTS.sort(key=lambda x: x.get('date', ''), reverse=True)
    print(f'네이버 API 캐시: {len(naver_posts)}건 중 {added}건 신규 추가')
else:
    print('네이버 API 캐시 없음 (fetch_naver_buzz.py를 먼저 실행하면 자동 수집 가능)')

# ── 최신 주 KPI
w0 = BUZZ_WEEKLY[0]  # 2월 1주차
neg_count = len([p for p in BUZZ_POSTS if p['sent'] == '부정'])
pos_count = len([p for p in BUZZ_POSTS if p['sent'] == '긍정'])

print(f'위클리 데이터: {len(BUZZ_WEEKLY)}주')
print(f'일간 차트 데이터: {len(BUZZ_DAILY_CHART)}일')
print(f'게시물 총: {len(BUZZ_POSTS)}건 | 부정:{neg_count} 긍정:{pos_count}')
print(f'최신주 ({w0["week"]}): 총계 {w0["total"]} / 전주대비 {w0["delta"]}')

# ── HTML 교체
with open('rototobebe_dashboard_v4.html', 'r', encoding='utf-8') as f:
    html = f.read()

# JS 데이터 상수 교체 또는 추가
js_block = f"""const BUZZ_WEEKLY={json.dumps(BUZZ_WEEKLY, ensure_ascii=False)};
const BUZZ_DAILY_CHART={json.dumps(BUZZ_DAILY_CHART, ensure_ascii=False)};
const BUZZ_POSTS={json.dumps(BUZZ_POSTS, ensure_ascii=False)};"""

# 기존 BUZZ 배열 제거하고 새 데이터 삽입
if 'const BUZZ_WEEKLY=' in html:
    html = re.sub(r'const BUZZ_WEEKLY=.*?const BUZZ_POSTS=.*?;', js_block, html, flags=re.DOTALL)
else:
    html = re.sub(r'const BUZZ=\[.*?\];', js_block, html, flags=re.DOTALL)

# ── 버즈 섹션 HTML 교체
delta_str = (f'+{w0["delta"]}건 ↑' if w0["delta"] and w0["delta"] > 0
             else f'{w0["delta"]}건 ↓' if w0["delta"] and w0["delta"] < 0
             else '—')

new_buzz_section = f"""<!-- ===== 버즈 모니터링 ===== -->
<section class="sec" id="sec-buzz">
  <div class="sec-hd">
    <div><div class="sec-title">버즈 모니터링</div><div class="sec-sub">네이버 맘카페 언급 추적 — 맘스홀릭베이비 · 맘이베베 · 헤이든 · 레몬테라스</div></div>
    <div class="frow">
      <button class="fbtn on" id="bztab-weekly" onclick="bzTab('weekly',this)">위클리</button>
      <button class="fbtn" id="bztab-daily" onclick="bzTab('daily',this)">데일리</button>
    </div>
  </div>

  <!-- KPI -->
  <div class="krow">
    <div class="kcard c1"><div class="klbl">이번주 총 언급</div><div class="kval">{w0['total']}건</div><div class="kdelta up">{w0['week']}</div></div>
    <div class="kcard c2"><div class="klbl">전주 대비</div><div class="kval" style="color:var(--sage)">{delta_str}</div><div class="kdelta up">게시물 {w0['post']} / 댓글 {w0['comment']}</div></div>
    <div class="kcard c3"><div class="klbl">오가닉 언급</div><div class="kval">{w0['organic']}건</div><div class="kdelta">자연 유입</div></div>
    <div class="kcard c5"><div class="klbl">부정 감지</div><div class="kval" style="color:var(--coral)">{neg_count}건</div><div class="kdelta">전체 기간 누적</div></div>
  </div>

  <!-- 위클리 탭 -->
  <div id="bz-weekly">
    <div class="g2">
      <div class="card">
        <div class="ctitle">주차별 언급 추이</div>
        <div class="csub">총 언급건수 기준</div>
        <div style="position:relative;height:180px"><canvas id="buzzWeekChart"></canvas></div>
      </div>
      <div class="card">
        <div class="ctitle">카페별 점유율</div>
        <div class="csub">이번주 ({w0['week']}) 기준</div>
        <div style="position:relative;height:180px"><canvas id="buzzCafeChart"></canvas></div>
      </div>
    </div>
    <div class="card" style="margin-top:11px">
      <div class="ctitle" style="margin-bottom:11px">주차별 카페 언급 현황</div>
      <div class="tw"><table class="tbl" style="min-width:600px">
        <thead><tr>
          <th>주차</th>
          <th style="text-align:right">총계</th>
          <th style="text-align:right">증감</th>
          <th style="text-align:right">게시물</th>
          <th style="text-align:right">댓글</th>
          <th style="text-align:right">맘스홀릭</th>
          <th style="text-align:right">헤이든</th>
          <th style="text-align:right">맘이베베</th>
          <th style="text-align:right">레몬테라스</th>
        </tr></thead>
        <tbody id="buzzWeeklyBody"></tbody>
      </table></div>
    </div>
  </div>

  <!-- 데일리 탭 -->
  <div id="bz-daily" style="display:none">
    <div class="frow" style="margin-bottom:10px;flex-wrap:wrap;gap:6px">
      <button class="fbtn on" onclick="bzFlt('all',this)">전체</button>
      <button class="fbtn" onclick="bzFlt('오가닉',this)">오가닉</button>
      <button class="fbtn" onclick="bzFlt('바이럴 확인',this)">바이럴 확인</button>
      <button class="fbtn" onclick="bzFlt('로덬메이트',this)">로덬메이트</button>
      <button class="fbtn" onclick="bzFlt('로토토베베',this)">로토토베베</button>
      <span style="margin-left:8px;color:var(--ts);font-size:11px">카페:</span>
      <button class="fbtn" onclick="bzCafe('all',this)">전체</button>
      <button class="fbtn" onclick="bzCafe('맘스홀릭베이비',this)">맘스홀릭</button>
      <button class="fbtn" onclick="bzCafe('헤이든',this)">헤이든</button>
      <button class="fbtn" onclick="bzCafe('맘이베베',this)">맘이베베</button>
      <button class="fbtn" onclick="bzCafe('레몬테라스',this)">레몬테라스</button>
    </div>
    <div class="card">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:11px">
        <div class="ctitle">게시물 목록</div>
        <span id="bzCount" style="font-size:10px;color:var(--ts)"></span>
      </div>
      <div class="tw"><table class="tbl" style="min-width:800px">
        <thead><tr>
          <th style="min-width:85px">날짜</th>
          <th>카페</th>
          <th style="min-width:240px">게시물 제목</th>
          <th>긍부정</th>
          <th style="min-width:160px">내용</th>
          <th style="text-align:right">조회</th>
          <th style="text-align:right">댓글</th>
          <th>작성형태</th>
          <th style="text-align:center">링크</th>
        </tr></thead>
        <tbody id="buzzDailyBody"></tbody>
      </table></div>
    </div>
  </div>
</section>"""

old_buzz = re.compile(r'<!-- ===== 버즈 모니터링 ===== -->.*?</section>', re.DOTALL)
if old_buzz.search(html):
    html = old_buzz.sub(new_buzz_section, html, count=1)
    print('버즈 섹션 교체 완료')
else:
    print('버즈 섹션 패턴 못 찾음!')

# ── renderBuzz 함수 교체
new_render_buzz = r"""let bzFilter='all';
let bzCafeFilter='all';

function bzTab(tab, btn){
  document.querySelectorAll('#sec-buzz .fbtn[id^="bztab-"]').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  document.getElementById('bz-weekly').style.display = tab==='weekly'?'':'none';
  document.getElementById('bz-daily').style.display = tab==='daily'?'':'none';
}

function renderBuzz(f){
  if(f) bzFilter=f;
  renderBuzzWeekly();
  renderBuzzDaily();
  renderBuzzCharts();
}

function renderBuzzWeekly(){
  const SC={긍정:'bpos',부정:'bneg',중립:'bne',핫딜:'bs',판매:'bne',정보:'bne'};
  document.getElementById('buzzWeeklyBody').innerHTML=BUZZ_WEEKLY.map(w=>{
    const dStr=w.delta===null?'—':(w.delta>0?'<span style="color:var(--sage)">+'+w.delta+'</span>':'<span style="color:var(--coral)">'+w.delta+'</span>');
    return '<tr>'
      +'<td class="tname">'+w.week+'</td>'
      +'<td style="text-align:right;font-weight:600">'+w.total+'</td>'
      +'<td style="text-align:right">'+dStr+'</td>'
      +'<td style="text-align:right">'+w.post+'</td>'
      +'<td style="text-align:right">'+w.comment+'</td>'
      +'<td style="text-align:right">'+w.mam+'</td>'
      +'<td style="text-align:right">'+w.haydn+'</td>'
      +'<td style="text-align:right">'+w.beibe+'</td>'
      +'<td style="text-align:right">'+w.lemon+'</td>'
      +'</tr>';
  }).join('');
}

function bzFlt(f,btn){
  document.querySelectorAll('#bz-daily .frow:first-child .fbtn').forEach(b=>{
    if(['전체','오가닉','바이럴 확인','로덬메이트','로토토베베'].includes(b.textContent)) b.classList.remove('on');
  });
  btn.classList.add('on');
  bzFilter=f;
  renderBuzzDaily();
}

function bzCafe(f,btn){
  document.querySelectorAll('#bz-daily .frow:first-child .fbtn').forEach(b=>{
    if(['전체','맘스홀릭','헤이든','맘이베베','레몬테라스'].includes(b.textContent)) b.classList.remove('on');
  });
  btn.classList.add('on');
  bzCafeFilter=f;
  renderBuzzDaily();
}

function renderBuzzDaily(){
  const SC={긍정:'bpos',부정:'bneg',핫딜:'bs',판매:'bne',정보:'bne'};
  const TC={오가닉:'bok',로덬메이트:'bok','바이럴 확인':'bne',로토토베베:'bi'};
  const fd=BUZZ_POSTS.filter(p=>{
    const okType=bzFilter==='all'||p.type===bzFilter;
    const okCafe=bzCafeFilter==='all'||p.cafe===bzCafeFilter;
    return okType&&okCafe;
  });
  document.getElementById('bzCount').textContent=fd.length+'건';
  document.getElementById('buzzDailyBody').innerHTML=fd.map(p=>{
    const linkBtn=p.link?'<a href="'+p.link+'" target="_blank" style="font-size:11px;color:var(--coral)">↗</a>':'—';
    return '<tr class="'+(p.sent==='부정'?'issue':'')+'">'
      +'<td style="font-size:10px;color:var(--ts);white-space:nowrap">'+p.date+'</td>'
      +'<td style="font-size:11px">'+p.cafe+'</td>'
      +'<td style="font-size:11px">'+p.title+'</td>'
      +'<td><span class="bdg '+(SC[p.sent]||'bne')+'">'+p.sent+'</span></td>'
      +'<td style="font-size:10px;color:var(--ts)">'+p.summary+'</td>'
      +'<td style="text-align:right;font-size:11px">'+p.view.toLocaleString()+'</td>'
      +'<td style="text-align:right;font-size:11px">'+p.cmt+'</td>'
      +'<td><span class="bdg '+(TC[p.type]||'bne')+'">'+p.type+'</span></td>'
      +'<td style="text-align:center">'+linkBtn+'</td>'
      +'</tr>';
  }).join('');
}

function renderBuzzCharts(){
  // 주차별 추이 차트
  const wCtx=document.getElementById('buzzWeekChart');
  if(wCtx){
    if(wCtx._chart) wCtx._chart.destroy();
    const weeks=[...BUZZ_WEEKLY].reverse();
    wCtx._chart=new Chart(wCtx,{type:'bar',data:{
      labels:weeks.map(w=>w.week),
      datasets:[{label:'총 언급',data:weeks.map(w=>w.total),backgroundColor:'rgba(205,120,98,0.7)',borderRadius:4}]
    },options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,grid:{color:'rgba(0,0,0,.05)'}}}}});
  }
  // 카페별 도넛 차트
  const cCtx=document.getElementById('buzzCafeChart');
  if(cCtx){
    if(cCtx._chart) cCtx._chart.destroy();
    const w0=BUZZ_WEEKLY[0];
    cCtx._chart=new Chart(cCtx,{type:'doughnut',data:{
      labels:['맘스홀릭베이비','헤이든','맘이베베','레몬테라스'],
      datasets:[{data:[w0.mam,w0.haydn,w0.beibe,w0.lemon],backgroundColor:['#CD7862','#8DB4A0','#8B9DC3','#F4C897'],borderWidth:0}]
    },options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'right',labels:{font:{size:10},boxWidth:10}}}}});
  }
}"""

# 기존 renderBuzz 관련 함수 교체
old_render_pattern = re.compile(
    r'// ── 버즈\nconst BUZZ=\[.*?function fltBuzz\(f,btn\)\{.*?\}',
    re.DOTALL
)
if old_render_pattern.search(html):
    html = old_render_pattern.sub('// ── 버즈\n' + new_render_buzz, html)
    print('renderBuzz 함수 교체 완료')
else:
    # 기존 버즈 함수들 개별 교체 시도
    old_fn = re.compile(r'let bFilter=.*?function fltBuzz\(f,btn\)\{[^}]+\}', re.DOTALL)
    if old_fn.search(html):
        html = old_fn.sub(new_render_buzz, html)
        print('renderBuzz 함수 교체 완료 (alt)')
    else:
        print('renderBuzz 패턴 못 찾음')

# renderBuzz 호출 교체
html = html.replace("if(id==='buzz') renderBuzz('all');", "if(id==='buzz') renderBuzz('all');")

with open('rototobebe_dashboard_v4.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('완료!')
