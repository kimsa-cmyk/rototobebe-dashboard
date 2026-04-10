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

# ── 1. MEMBERS 데이터 교체 (h, w, s 포함)
html = re.sub(
    r'const MEMBERS=\[.*?\];',
    'const MEMBERS=' + json.dumps(MEMBERS, ensure_ascii=False) + ';',
    html, flags=re.DOTALL
)

# ── 2. 테이블 헤더: 팔로워/제품 → 팔로워 | 제품·스펙 분리
old_thead = ('        <th style="min-width:120px">팔로워 / 제품</th>\n'
             '        <th style="text-align:center;min-width:70px">게시물</th>')
new_thead = ('        <th style="min-width:80px">팔로워</th>\n'
             '        <th style="min-width:160px">제품 · 스펙</th>\n'
             '        <th style="text-align:center;min-width:70px">게시물</th>')
html = html.replace(old_thead, new_thead)

# ── 3. renderRodem 함수 내 row 렌더링 교체
old_row = (
    "    const r=RAW[m.phone]||{post:0,comment:0,cheer:0};\n"
    "    const a=ACT[m.phone]||{total:0,w1:0,w2:0};\n"
    "    const wpt=a.w1+a.w2;\n"
    "    const hasAct=(r.post+r.comment+r.cheer)>0;\n"
    "    const an=v=>v>0?'<div class=\"anum\">'+v+'</div>':'<div class=\"azero\">—</div>';\n"
    "    const prods=PROD[m.phone]||[];\n"
    "    const prodBtn=prods.length>0\n"
    "      ?'<button class=\"fbtn\" style=\"font-size:10px;padding:2px 7px;margin-top:3px\" onclick=\"showProd(\\''+m.phone+'\\')\">"
    "제품 '+prods.length+'개</button>'\n"
    "      :'<span style=\"font-size:10px;color:var(--bd)\">—</span>';\n"
    "    const igLink=m.ig?'https://www.instagram.com/'+m.ig+'/':'#';\n"
    "    const ptStr=wpt>0?'<div class=\"pt\">+'+wpt.toLocaleString()+'원</div>':'<div class=\"pt0\">—</div>';\n"
    "    const totStr=a.total>0?'<div style=\"text-align:right;font-size:11px;color:var(--tm)\">'+a.total.toLocaleString()+'원</div>':'—';\n"
    "    return '<tr style=\"'+(hasAct?'':'opacity:.5')+'\">'"\
    "+'<td style=\"color:var(--ts);font-size:10px\">'+m.num+'</td>'"\
    "+\"'<td><a href=\"'+igLink+'\" target=\"_blank\" style=\"text-decoration:none\"><div class=\"tname\" style=\"color:var(--coral)\">'+m.name+'</div></a><div class=\"tig\">@'+m.ig+'</div></td>'\""\
    "+\"'<td style=\"font-size:11px\">'+(m.follower||'—')+'<br>'+prodBtn+'</td>'\""
)

# Find and replace the row rendering block more reliably
new_render_body = r"""    const r=RAW[m.phone]||{post:0,comment:0,cheer:0};
    const a=ACT[m.phone]||{total:0,w1:0,w2:0};
    const wpt=a.w1+a.w2;
    const hasAct=(r.post+r.comment+r.cheer)>0;
    const an=v=>v>0?'<div class="anum">'+v+'</div>':'<div class="azero">—</div>';
    const prods=PROD[m.phone]||[];
    const prodBtn=prods.length>0
      ?'<button class="fbtn" style="font-size:10px;padding:2px 7px" onclick="showProd(\''+m.phone+'\')">제품 '+prods.length+'개</button>'
      :'<span style="font-size:10px;color:var(--bd)">—</span>';
    const specStr=(m.h||m.w||m.s)
      ?'<div style="font-size:10px;color:var(--ts);margin-top:3px;line-height:1.6">'
        +(m.h?m.h:'—')+' | '+(m.w?m.w:'—')+' | '+(m.s?m.s+'size':'—')
        +'</div>'
      :'';
    const igLink=m.ig?'https://www.instagram.com/'+m.ig+'/':'#';
    const ptStr=wpt>0?'<div class="pt">+'+wpt.toLocaleString()+'원</div>':'<div class="pt0">—</div>';
    const totStr=a.total>0?'<div style="text-align:right;font-size:11px;color:var(--tm)">'+a.total.toLocaleString()+'원</div>':'—';
    return '<tr style="'+(hasAct?'':'opacity:.5')+'">'
      +'<td style="color:var(--ts);font-size:10px">'+m.num+'</td>'
      +'<td><a href="'+igLink+'" target="_blank" style="text-decoration:none"><div class="tname" style="color:var(--coral)">'+m.name+'</div></a><div class="tig">@'+m.ig+'</div></td>'
      +'<td style="font-size:11px">'+(m.follower||'—')+'</td>'
      +'<td>'+prodBtn+specStr+'</td>'
      +'<td>'+an(r.post)+'</td>'
      +'<td>'+an(r.comment)+'</td>'
      +'<td>'+an(r.cheer)+'</td>'
      +'<td>'+ptStr+'</td>'
      +'<td>'+totStr+'</td>'
      +'</tr>';"""

# Replace entire renderRodem row section
old_row_pattern = re.compile(
    r"(  document\.getElementById\('rodemBody'\)\.innerHTML=filtered\.map\(m=>\{).*?(  \}\.join\(''\);)",
    re.DOTALL
)

def replace_row(match):
    return match.group(1) + '\n' + new_render_body + '\n' + match.group(2)

if old_row_pattern.search(html):
    html = old_row_pattern.sub(replace_row, html)
    print('renderRodem row 교체 완료')
else:
    print('패턴 못찾음')

with open('rototobebe_dashboard_v4.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('완료!')
