import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

MEMBERS = data['MEMBERS']
ACT = data['ACT']
RAW = data['RAW']
PROD = data['PROD']

def js_obj(d):
    return '{' + ','.join(f'{json.dumps(k,ensure_ascii=False)}:{json.dumps(v,ensure_ascii=False)}' for k,v in d.items()) + '}'

with open('rototobebe_dashboard_v4.html', 'r', encoding='utf-8') as f:
    html = f.read()

# ── 1. 92명 → 91명
html = html.replace('2026 SUMMER — 총 92명', '2026 SUMMER — 총 91명')
html = html.replace('<div class="kval">92명</div>', '<div class="kval">91명</div>')

# ── 2. KPI 소통계 레이블
html = html.replace('<div class="smk">IG 게시물</div>', '<div class="smk">게시물</div>')
html = html.replace('<div class="smk">IG 스토리</div>', '<div class="smk">댓글</div>')
html = html.replace('<div class="smk">IG 댓글</div>', '<div class="smk">화력 지원</div>')
html = html.replace('<div class="smk">바이럴 게시물</div>', '<div class="smk">—</div>')
html = html.replace('<div class="smk">바이럴 댓글</div>', '<div class="smk">—</div>')
html = html.replace('<div class="kdelta up">게시물+댓글+스토리</div>', '<div class="kdelta up">게시물+댓글+화력</div>')

# ── 3. max-width 확장 (PC 전체폭)
html = html.replace('.main{max-width:1200px;margin:0 auto;padding:1.4rem 1.2rem;}',
                    '.main{max-width:1600px;margin:0 auto;padding:1.4rem 2rem;}')

# ── 4. 테이블 헤더 교체
old_thead = ('      <thead><tr>\n'
             '        <th style="width:24px">#</th>\n'
             '        <th>이름 / 인스타</th>\n'
             '        <th>팔로워</th>\n'
             '        <th>채널</th>\n'
             '        <th style="text-align:center">IG<br>게시물</th>\n'
             '        <th style="text-align:center">IG<br>스토리</th>\n'
             '        <th style="text-align:center">IG<br>댓글</th>\n'
             '        <th style="text-align:center">바이럴<br>게시물</th>\n'
             '        <th style="text-align:center">바이럴<br>댓글</th>\n'
             '        <th style="text-align:right">이번주<br>적립금</th>\n'
             '        <th style="text-align:right">누적<br>적립금</th>\n'
             '      </tr></thead>')
new_thead = ('      <thead><tr>\n'
             '        <th style="width:28px">#</th>\n'
             '        <th style="min-width:140px">이름 / 인스타</th>\n'
             '        <th style="min-width:120px">팔로워 / 제품</th>\n'
             '        <th style="text-align:center;min-width:70px">게시물</th>\n'
             '        <th style="text-align:center;min-width:70px">댓글</th>\n'
             '        <th style="text-align:center;min-width:70px">화력<br>지원</th>\n'
             '        <th style="text-align:right;min-width:90px">이번주<br>적립금</th>\n'
             '        <th style="text-align:right;min-width:90px">누적<br>적립금</th>\n'
             '      </tr></thead>')
html = html.replace(old_thead, new_thead)

# ── 5. JS 데이터 교체
html = re.sub(r'const MEMBERS=\[.*?\];', 'const MEMBERS=' + json.dumps(MEMBERS, ensure_ascii=False) + ';', html, flags=re.DOTALL)
html = re.sub(r'const ACT=\{.*?\};', 'const ACT=' + js_obj(ACT) + ';', html, flags=re.DOTALL)
html = re.sub(r'const RAW=\{.*?\};', 'const RAW=' + js_obj(RAW) + ';', html, flags=re.DOTALL)

# PROD 추가
if 'const PROD=' not in html:
    html = html.replace('let rFilter=', 'const PROD=' + js_obj(PROD) + ';\nlet rFilter=')
else:
    html = re.sub(r'const PROD=\{.*?\};', 'const PROD=' + js_obj(PROD) + ';', html, flags=re.DOTALL)

# ── 6. renderRodem 함수 교체
new_render = r"""function renderRodem(){
  const actPhones=Object.keys(RAW);
  let totalActs=0,totalPts=0;
  Object.values(RAW).forEach(r=>{totalActs+=r.post+r.comment+r.cheer;});
  Object.values(ACT).forEach(a=>{totalPts+=a.w1+a.w2;});
  document.getElementById('r-active').textContent=actPhones.length+'명';
  document.getElementById('r-acts').textContent=totalActs+'건';
  document.getElementById('r-pts').textContent=(totalPts/10000).toFixed(1)+'만원';
  let s_p=0,s_c=0,s_ch=0;
  Object.values(RAW).forEach(r=>{s_p+=r.post;s_c+=r.comment;s_ch+=r.cheer;});
  document.getElementById('s-igp').textContent=s_p;
  document.getElementById('s-igs').textContent=s_c;
  document.getElementById('s-igc').textContent=s_ch;
  document.getElementById('s-vp').textContent='—';
  document.getElementById('s-vc').textContent='—';

  const filtered=MEMBERS.filter(m=>{
    const sr=rSearch.toLowerCase();
    const ok=!sr||m.name.includes(sr)||m.ig.toLowerCase().includes(sr);
    const r=RAW[m.phone]||{post:0,comment:0,cheer:0};
    const hasAct=(r.post+r.comment+r.cheer)>0;
    const ft=rFilter==='all'||(rFilter==='active'&&hasAct)||(rFilter==='none'&&!hasAct);
    return ok&&ft;
  });

  document.getElementById('rodemBody').innerHTML=filtered.map(m=>{
    const r=RAW[m.phone]||{post:0,comment:0,cheer:0};
    const a=ACT[m.phone]||{total:0,w1:0,w2:0};
    const wpt=a.w1+a.w2;
    const hasAct=(r.post+r.comment+r.cheer)>0;
    const an=v=>v>0?'<div class="anum">'+v+'</div>':'<div class="azero">—</div>';
    const prods=PROD[m.phone]||[];
    const prodBtn=prods.length>0
      ?'<button class="fbtn" style="font-size:10px;padding:2px 7px;margin-top:3px" onclick="showProd(\''+m.phone+'\')">제품 '+prods.length+'개</button>'
      :'<span style="font-size:10px;color:var(--bd)">—</span>';
    const igLink=m.ig?'https://www.instagram.com/'+m.ig+'/':'#';
    const ptStr=wpt>0?'<div class="pt">+'+wpt.toLocaleString()+'원</div>':'<div class="pt0">—</div>';
    const totStr=a.total>0?'<div style="text-align:right;font-size:11px;color:var(--tm)">'+a.total.toLocaleString()+'원</div>':'—';
    return '<tr style="'+(hasAct?'':'opacity:.5')+'">'
      +'<td style="color:var(--ts);font-size:10px">'+m.num+'</td>'
      +'<td><a href="'+igLink+'" target="_blank" style="text-decoration:none"><div class="tname" style="color:var(--coral)">'+m.name+'</div></a><div class="tig">@'+m.ig+'</div></td>'
      +'<td style="font-size:11px">'+( m.follower||'—')+'<br>'+prodBtn+'</td>'
      +'<td>'+an(r.post)+'</td>'
      +'<td>'+an(r.comment)+'</td>'
      +'<td>'+an(r.cheer)+'</td>'
      +'<td>'+ptStr+'</td>'
      +'<td>'+totStr+'</td>'
      +'</tr>';
  }).join('');
}"""

old_render_pattern = re.compile(r'function renderRodem\(\)\{.*?\}(?=\s*\nfunction srchRodem)', re.DOTALL)
if old_render_pattern.search(html):
    html = old_render_pattern.sub(new_render, html)
    print('renderRodem 교체 완료')
else:
    print('renderRodem 패턴 못 찾음!')

# ── 7. 제품 모달 CSS 추가 (중복 방지)
if '/* PROD MODAL */' not in html:
    prod_css = '''
/* PROD MODAL */
.prod-modal{background:var(--warm);border-radius:13px;padding:22px;width:600px;max-width:95vw;max-height:80vh;overflow-y:auto;}
.prod-tbl{width:100%;border-collapse:collapse;margin-top:12px;}
.prod-tbl th{font-size:10px;color:var(--ts);font-weight:400;text-align:left;padding:5px 7px;border-bottom:1px solid var(--bd);}
.prod-tbl td{font-size:11px;padding:6px 7px;border-bottom:1px solid var(--bd);vertical-align:top;}
.prod-tbl tr:last-child td{border-bottom:none;}
.dandog-badge{display:inline-flex;padding:2px 5px;border-radius:4px;font-size:9px;font-weight:600;background:var(--coral-l);color:#B03A26;}
'''
    html = html.replace('/* ACT NUM */', prod_css + '\n/* ACT NUM */')

# ── 8. 제품 모달 HTML 추가 (중복 방지)
if 'id="prodModal"' not in html:
    prod_modal_html = '''
<!-- 제품 모달 -->
<div class="mov" id="prodModal">
  <div class="prod-modal">
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:5px">
      <div class="mtitle" id="prodModalTitle" style="margin-bottom:0">제품 목록</div>
      <button onclick="document.getElementById('prodModal').classList.remove('on')" style="background:none;border:none;font-size:20px;cursor:pointer;color:var(--ts)">×</button>
    </div>
    <div id="prodModalBody"></div>
  </div>
</div>'''
    html = html.replace('<div class="toast"', prod_modal_html + '\n<div class="toast"')

# ── 9. showProd JS 함수 추가 (중복 방지)
if 'function showProd(' not in html:
    prod_js = """
function showProd(phone){
  const m=MEMBERS.find(x=>x.phone===phone);
  const prods=PROD[phone]||[];
  document.getElementById('prodModalTitle').textContent=(m?m.name:'')+' 제품 목록 ('+prods.length+'개)';
  var rows=prods.map(function(p){
    var d=p.d&&p.d!=='-'?'<span class="dandog-badge">'+p.d+'</span>':'-';
    return '<tr><td>'+d+'</td><td>'+p.n+'</td><td style="white-space:nowrap">'+p.s+'</td><td>'+p.f+'</td></tr>';
  }).join('');
  document.getElementById('prodModalBody').innerHTML='<table class="prod-tbl"><thead><tr><th>단독</th><th>상품명</th><th>배송</th><th>최종 구매 내역</th></tr></thead><tbody>'+rows+'</tbody></table>';
  document.getElementById('prodModal').classList.add('on');
}
document.getElementById('prodModal').addEventListener('click',function(e){if(e.target===this)this.classList.remove('on');});
"""
    html = html.replace('function srchRodem(', prod_js + '\nfunction srchRodem(')

with open('rototobebe_dashboard_v4.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('HTML 업데이트 완료!')
