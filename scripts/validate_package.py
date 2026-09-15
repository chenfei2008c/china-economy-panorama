"""Validate the published metadata, transparent arithmetic and XLSX export.

Uses only the Python standard library. It does not fetch data or author Excel.
"""
from pathlib import Path
from decimal import Decimal, getcontext
from collections import Counter
import ast, json, re, zipfile, xml.etree.ElementTree as ET

getcontext().prec=32
P=Path(__file__).resolve().parent.parent
C=json.loads((P/'data/catalog.json').read_text())
W=json.loads((P/'data/workbook.json').read_text())
CASES=json.loads((P/'data/calculation_cases.json').read_text())
results=[]
def check(name,cond,detail=''):
    results.append(dict(check=name,passed=bool(cond),detail=detail))
def formula(node,env):
    if isinstance(node,ast.Expression):return formula(node.body,env)
    if isinstance(node,ast.Name):return env[node.id]
    if isinstance(node,ast.Constant):return Decimal(str(node.value))
    if isinstance(node,ast.BinOp):
        a,b=formula(node.left,env),formula(node.right,env)
        if isinstance(node.op,ast.Add):return a+b
        if isinstance(node.op,ast.Sub):return a-b
        if isinstance(node.op,ast.Mult):return a*b
        if isinstance(node.op,ast.Div):return a/b
    if isinstance(node,ast.UnaryOp) and isinstance(node.op,ast.USub):return -formula(node.operand,env)
    raise ValueError('Unsupported expression')

M={m['id']:m for m in C['metrics']};S={s['id']:s for s in C['sources']};Q={q['id']:q for q in C['questions']}
check('7体系与28核心问题',len(C['systems'])==7 and len(Q)==28)
check('8张约定工作表',[s['name'] for s in W['sheets']]==['体系问题','指标字典','问题—指标映射','维度覆盖','来源登记','判断规则','全景模板','缺口与边界'])
check('编号唯一',len(M)==len(C['metrics']) and len(S)==len(C['sources']))
required=['name','definition','unit','frequency','population','source_id','source_locator','history','breaks','origin','formula','conditions','interpretation','pitfalls']
check('指标必填字段',all(all(m.get(f) for f in required) for m in M.values()))
check('原文和定义入口',all(s.get('url','').startswith('https://') and s.get('definition_url') and s.get('definition_evidence') and s.get('history_evidence') for s in S.values()))
check('指标和覆盖来源引用',all(m['source_id'] in S and all(s in S for c in m['coverage'] for s in c['source_ids']) for m in M.values()))
check('问题指标双向引用',all(q['metric_ids'] and all(i in M and q['id'] in M[i]['question_ids'] for i in q['metric_ids']) for q in Q.values()))
check('指标全部对应问题',all(m['question_ids'] and all(q in Q for q in m['question_ids']) for m in M.values()))
check('每个问题含反证替代解释边界',all(q['counter'] and q['alternatives'] and q['boundary'] for q in Q.values()))
check('四种覆盖状态',all(c['status'] in ['已覆盖','部分覆盖','无稳定公开数据','不适用'] for c in C['coverage']))
check('每问题指标检查七维',len(C['coverage'])==sum(len(q['metric_ids']) for q in Q.values())*7)
check('31省及20行业目录',sum(r['type']=='省级成员' for r in C['dimension_registry'])==31 and sum(r['type']=='行业门类' for r in C['dimension_registry'])==20)
check('细分键独立于矩阵行数',len(C['series_registry'])==124 and len({(s['metric_id'],s['dimension_id']) for s in C['series_registry']})==124)
check('七体系均有原值执行路径',set('KMFGISD') <= {e['system'] for e in C['examples']} and all(e['inputs'] and e['permitted_conclusion'] and e['forbidden_conclusion'] for e in C['examples']))
derived={m['id'] for m in M.values() if m['origin']=='透明派生'}
check('派生输入已登记',all(M[i]['inputs'] and all(x in M for x in M[i]['inputs']) for i in derived))
def visit(i,stack):
    if i in stack:raise ValueError('cycle: '+i)
    for j in M[i]['inputs']:visit(j,stack|{i})
try:
    for i in M:visit(i,set())
    check('派生依赖无环',True)
except ValueError as e:check('派生依赖无环',False,str(e))
check('全部派生有真实输入复算',derived <= {o['metric_id'] for c in CASES for o in c['outputs']},str(sorted(derived)))
for c in CASES:
    env={f'x{n}':Decimal(str(x['value'])) for n,x in enumerate(c['inputs'])}
    check(c['id']+'输入定位',all(x['metric_id'] in M and x['source'] in S and x['location'] for x in c['inputs']))
    for o in c['outputs']:
        v=formula(ast.parse(o['expression'],mode='eval'),env)
        check(c['id']+' '+o['metric_id'],abs(v-Decimal(str(o['expected'])))<=Decimal(str(o['tolerance'])),f'computed={v}; expected={o["expected"]}')

# Boundary checks target likely analytical errors, not implementation trivia.
def safe_ratio(a,b):return None if a is None or b is None or b<=0 else a/b
def period_difference(current,previous,kind,same_scope=True):
    if current is None or previous is None or kind!='累计金额' or not same_scope:return None
    return current-previous
check('真零与缺失不同',safe_ratio(0,10)==0 and safe_ratio(None,10) is None)
check('零分母不输出结果',safe_ratio(10,0) is None)
check('累计同比不能相减',period_difference(5.0,4.0,'累计增速') is None)
check('累计金额仅同口径可差分',period_difference(100,70,'累计金额')==30 and period_difference(100,70,'累计金额',False) is None)
check('M2与实际GDP比较形式去重','A054' not in M and 'A003' not in M and C['aliases']['A054']=='A043')
check('劳动力调查共享证据',M['A025']['evidence_group']==M['A026']['evidence_group'])
check('无医保收支直接偿债映射',all(i not in Q[q]['metric_ids'] for i in ['C046','C047'] for q in ['F2','F4']))
check('FOF实际消费只含住户政府',all('国外' not in c['members'] and '非金融企业' not in c['members'] for c in M['R007']['coverage'] if c['dimension']=='机构部门'))
check('期末资产负债率',M['B010']['period_basis']=='期末')
check('外债原文与计算差异保留','56.546866' in M['B063']['conditions'] and '56%' in M['B063']['conditions'])
check('长文本无空模板遗漏',not any('<!-- SYSTEM_CHAPTERS -->' in f.read_text() for f in P.glob('*.md')))
check('8份研究模板',len(list((P/'templates').glob('*.md')))==8)
check('CSV与工作簿视图同源',all(len(s['headers'])==len(s['widths']) and all(len(r)==len(s['headers']) for r in s['rows']) for s in W['sheets']))

xlsx=P/'中国经济全景指标字典.xlsx'
if xlsx.exists():
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(xlsx) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            sx=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(t.text or '' for t in si.findall('.//m:t',ns)) for si in sx]
        def cell_value(c):
            t=c.attrib.get('t');v=c.find('m:v',ns)
            if t=='s':return shared[int(v.text)]
            if t=='inlineStr':return ''.join(t.text or '' for t in c.findall('.//m:t',ns))
            return v.text if v is not None else ''
        def column(n):
            s=''
            while n:
                n,r=divmod(n-1,26);s=chr(65+r)+s
            return s
        book=ET.fromstring(z.read('xl/workbook.xml'))
        names=[e.attrib['name'] for e in book.find('m:sheets',ns)]
        check('导出Excel八表可读',names==[s['name'] for s in W['sheets']])
        check('Excel有8个筛选表',len([n for n in z.namelist() if re.fullmatch(r'xl/tables/table\d+\.xml',n)])==8)
        cells={}
        for n in range(1,9):
            xml=ET.fromstring(z.read(f'xl/worksheets/sheet{n}.xml'))
            errors=[c.attrib.get('r') for c in xml.findall('.//m:c',ns) if c.attrib.get('t')=='e']
            check('Excel公式无错误 '+names[n-1],not errors,str(errors))
            check('Excel冻结窗格 '+names[n-1],xml.find('.//m:pane',ns) is not None)
            exported={c.attrib['r']:cell_value(c) for c in xml.findall('.//m:c',ns)}
            spec=W['sheets'][n-1]
            mismatches=[]
            for ri,row in enumerate([spec['headers']]+spec['rows'],5):
                for ci,val in enumerate(row,1):
                    key=column(ci)+str(ri)
                    if str(val)!=exported.get(key,''):mismatches.append(key)
            check('Excel内容与发布元数据一致 '+names[n-1],not mismatches,str(mismatches[:8]))
            for c in xml.findall('.//m:c',ns):
                if c.find('m:f',ns) is not None:
                    v=c.find('m:v',ns);cells[names[n-1]+'!'+c.attrib['r']]=v.text if v is not None else None
        manifest=json.loads((P/'validation/formula_manifest.json').read_text())
        check('公式数与当前样例定义一致',len(manifest)==sum(len(c['outputs']) for c in CASES))
        for f in manifest:
            v=cells.get(f['cell'])
            check('Excel缓存 '+f['cell'],v is not None and abs(Decimal(v)-Decimal(str(f['expected'])))<=Decimal(str(f['tolerance'])),str(v))
        check('所有计算已导出',len(cells)==len(manifest),str(len(cells)))
else:
    results.append(dict(check='Excel导出验收',passed=None,detail='等待生成工作簿后重跑'))

report=dict(as_of='2026-09-15',counts=C['counts'],checks=results,failed=sum(r['passed'] is False for r in results),pending=sum(r['passed'] is None for r in results))
(P/'validation/validation_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':len(results),'failed':report['failed'],'pending':report['pending']},ensure_ascii=False))
for r in results:
    if r['passed'] is False:print('FAIL',r['check'],r['detail'])
raise SystemExit(1 if report['failed'] else 0)
