"""Compile reviewed research metadata. No collection or economic estimation."""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
import json, csv, re, shutil
from frameworks import SYSTEMS, GLOBAL_RULES

OUT=Path(__file__).resolve().parent.parent
W=OUT/"data/design_inputs"
for d in ['data','templates','validation','scripts']:
    (OUT/d).mkdir(exist_ok=True)
def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def txt(v):
    if v is None:return ''
    if isinstance(v,list):return '；'.join(txt(x) for x in v)
    if isinstance(v,dict):return '；'.join(str(k)+'：'+txt(x) for k,x in v.items())
    return str(v)
def ids(prefix,a,b):return [f'{prefix}{n:03d}' for n in range(a,b+1)]

groups=[json.loads((W/f'group_{g}.json').read_text()) for g in ['a','b','c','r','e']]
sources={s['id']:s for g in groups for s in g['sources']}
for source in sources.values():source.pop('evidence_file',None)
metrics={m['id']:m for g in groups for m in g['metrics']}
examples=[e for g in groups for e in g.get('examples',[])]
gaps=[g for group in groups for g in group.get('gaps',[])]
dimensions=json.loads((W/'dimensions.json').read_text())
sources['R_POP_TIME']=dict(id='R_POP_TIME',publisher='国家统计局',title='关于开展2024年人口变动情况抽样调查的公告（2024年第4号）',url='https://www.stats.gov.cn/xw/tjxw/tzgg/202410/t20241010_1956861.html',definition_url='https://www.stats.gov.cn/xw/tjxw/tzgg/202410/t20241010_1956861.html',publication_date='2024-10-10',access_date='2026-09-15',reporting_period='2024-11-01零时',frequency='年度人口变动抽样调查',location='第四项 调查时间',definition_evidence='调查标准时点为2024年11月1日零时；不是年末时点。',history_evidence='年度人口变动调查实施公告，2024年标准时点已读。',coverage_evidence='人口变动情况抽样调查；年度汇总表样本不等于全国总人口。',limitations='与年末人口、公报分年龄人口口径分别记录。')
for mid in ['C025','C026']:
    metrics[mid]['period_basis']='不适用（人口调查标准时点）'
    metrics[mid]['time_type']='时点（2024样例：11月1日零时）'
    metrics[mid]['conditions']+='；2024年调查标准时点为11月1日零时，见R_POP_TIME第四项，不标作年末。'
    metrics[mid]['additional_sources']=['R_POP_TIME']
for c in metrics['C016']['coverage']:
    if c['dimension']=='企业类型':c['evidence']='2025专利调查印刷页27 / PDF第34页图27：大型1084.8、中型1081.1、小型724.2、微型337.2万元/件；累计收益定义见印刷页164。'
for c in metrics['C015']['coverage']:
    if c['dimension']=='省级':c.update(status='无稳定公开数据',members=[],evidence='调查覆盖27省与四大区域聚合，不证明逐省产业化率已公开',limitation='本轮未核验逐省结果；不由区域结果分摊。')
for e in examples:
    if e['system']=='G':
        e['source_ids'].append('R_POP_TIME')
        for x in e['inputs']:
            if '报告期' in x:x['报告期']='2024-11-01零时（调查标准时点）'
        e['question']='劳动供给数量、教育程度与劳动生产率如何共同观察？'
        e['inputs'] += [dict(name='16—59岁人口平均受教育年限',value=11.3,unit='年',period='2025年',location='C_S02第十部分教育段末句；比上年提高0.1年'),dict(name='16—59岁人口',value=85136,unit='万人',period='2025年末',location='C_S02第一部分表1'),dict(name='全国就业人员',value=72504,unit='万人',period='2025年末',location='C_S02第一部分就业段'),dict(name='全员劳动生产率',value=184413,unit='元/人（2020年价格）',period='2025全年',location='C_S02第一部分首段、注4；比上年提高6.1%')]
        e['result']+=' 2025年另外观察到教育年限提高0.1年、劳动年龄人口及就业规模，以及实际劳动生产率提高6.1%；它们构成劳动数量、教育程度和单位就业者产出三个环节。'
        e['permitted_conclusion']+=' 2025年三环节可分别登记并联合提出研究问题；不把2024年抽样年龄表当2025年同期总体。'
        e['forbidden_conclusion']+=' 教育人群与就业人群不匹配，不能将教育变化解释为生产率增长贡献；不能以72504/85136计算劳动参与率，也不将年末就业直接代入官方生产率分母。'
    if e['system']=='I':
        e['inputs'] += [dict(name='企业发明专利产业化平均收益',value=872.0,unit='万元/件（累计收益）',period='2025调查；专利运用日至调查日',location='C_S06印刷页27/PDF34正文与图27；定义印刷164/PDF171'),dict(name='企业发明专利产业化平均收益',value=869.5,unit='万元/件（累计收益）',period='2024调查；专利运用日至调查日',location='C_S06印刷页27/PDF34正文与图27')]
        e['calculation']+=' 872.0−869.5=2.5万元/件；(872.0/869.5−1)×100≈0.2875%。'
        e['result']+=' 两次调查的产业化平均累计收益分别为869.5和872.0万元/件，为成果运用补充经营收益观察。'
        e['forbidden_conclusion']+=' 该收益为各项专利运用以来累计，样本和专利年龄不同；不是两年年度利润，不计算研发ROI或年化回报。'
    if e['system']=='D' and isinstance(e.get('result'),str):e['result']=e['result'].replace('两端家庭组人均收入均值相差约10.22倍','高收入家庭组人均收入均值约为低收入组的10.22倍')
aliases={'C020':'A011','A054':'A043','A003':'A002'}
metrics['A002']['name']='国内生产总值实际增长（同比/季调环比）'
metrics['A002']['definition']+='；季调环比采用发布方季节调整结果，与同比作为同一实际GDP变动的不同比较形式。'
metrics['A002']['conditions']+='；同比与季调环比分开记录，后者随新增数据追溯修订。'
metrics.pop('A003')
metrics['A043']['name']='广义货币M2余额及同比增长'
metrics['A043']['definition']+='；同比为同口径期末余额较上年同月的增长率，作为同一底层序列的展示字段。'
metrics['A043']['unit']='亿元（余额）；%（同比）'
metrics['A043']['additional_sources']=[metrics['A054']['source_id']]
metrics.pop('A054')
metrics['A055']['inputs']=['A043','A012']
metrics['A055']['formula']='A043[同年12月末同比,%] − A012[该年名义GDP同比,%]，单位百分点'
if 'C020' in metrics:
    cm=metrics.pop('C020'); am=metrics['A011']
    am['systems']=sorted(set(am['systems']+cm['systems']))
    am['additional_sources']=[cm['source_id']]
    am['history']+='；'+cm['history']
    am['breaks']+='；'+cm['breaks']
    am['source_locator']+='；'+cm['source_locator']
    am['conditions']+='；官方全员劳动生产率口径，不自行以名义GDP除年末就业替代。'
metrics['C038']['inputs']=['A014']
metrics['C038']['formula']='A014[城镇,同年] / A014[农村,同年]'

# Region rows are supported by the actual 2025 yearbook tables, not imputed.
province_names=[p['name'] for p in dimensions['provinces']]
for mid,sid,evidence in [('A001','R_REGION_GDP','表3-9地区GDP金额，2024年'),('A004','R_REGION_GDP','表3-9三次产业与主要行业增加值，2024年'),('A005','R_REGION_GDP','表3-9三次产业等指数，按实际非空列'),('A010','R_REGION_GDP','表3-9人均GDP，2024年'),('A014','R_REGION_INCOME','表6-18各省全体居民，2018—2024年')]:
    m=metrics[mid]
    m['coverage']=[c for c in m['coverage'] if c['dimension']!='省级']
    m['coverage'].append(dict(dimension='省级',status='已覆盖' if mid!='A005' else '部分覆盖',members=province_names,source_ids=[sid],evidence=evidence,limitation='年度口径；不表示省级季度及各居民群体交叉全覆盖。空白以原表为准。'))
metrics['B015']['coverage'].append(dict(dimension='省级',status='部分覆盖',members=province_names,source_ids=['R_REGION_INVESTMENT'],evidence='表10-18，2024年31省目录×所列行业投资增速',limitation='部分单元空白；未提供全部行业投资金额，不反推金额。'))
for c in metrics['B015']['coverage']:
    if c['dimension']=='省级' and 'R_REGION_INVESTMENT' not in c.get('source_ids',[]):
        c['limitation']='B_S02月报仅四大区域；R_REGION_INVESTMENT另核得2024年31省×行业增速，部分单元缺失。'

# An institutional unit count adds information on the stock of operating entities,
# but cannot identify entries, exits, or active firms.
metrics['R017']=dict(id='R017',name='按地区和主要行业分法人单位数',family='法人单位',module='经济主体结构',definition='按法人单位统计口径登记的单位数量，包含企业及非企业法人；按主要行业和地区列示。',unit='个',frequency='年度',time_type='时点',stock_flow='存量',price_basis='不适用',period_basis='年末',population='基本单位统计范围内法人单位；非等同企业或活跃经营单位',source_id='R_REGION_UNITS',source_locator='2025年鉴表1-5及表下注',history='全国2005—2024年度列；31省2024年行已核验',breaks='2008/2013/2018/2023经济普查数据及历史修订；2013部分行业数据缺失见表注，2018/2023不含无法分组部分。',origin='公开发布',formula='原文发布',inputs=[],conditions='年度与行业版本一致；缺失保留。',systems=['I','S'],interpretation='观察经济主体存量在地区和行业的分布。',companions='就业、行业产出、经营收入、连续企业追踪',pitfalls='不能用单位数差额认定新设企业数、净退出或创造性破坏。',coverage=[dict(dimension='全国',status='已覆盖',members=['全国'],source_ids=['R_REGION_UNITS'],evidence='表1-5全国年度行',limitation='表注修订'),dict(dimension='省级',status='已覆盖',members=province_names,source_ids=['R_REGION_UNITS'],evidence='31省逐行',limitation='2024年'),dict(dimension='行业',status='部分覆盖',members=[i['name'] for i in dimensions['industries'][:19]],source_ids=['R_REGION_UNITS'],evidence='A—S门类表列',limitation='不含T国际组织；历史缺失见表注')])
for mid in ['R013','R014','R016']:
    metrics[mid]['coverage']=[dict(dimension='全国',status='已覆盖',members=['全国住户部门'],source_ids=['R_FOF'],evidence='同表住户及国内合计相应列计算',limitation='2023年；不能分配给其他部门'),dict(dimension='机构部门',status='部分覆盖',members=['住户'],source_ids=['R_FOF'],evidence='公式指定住户部门',limitation='不是完整五部门比率')]
metrics['R015']['coverage']=[dict(dimension='全国',status='已覆盖',members=['国内合计'],source_ids=['R_FOF'],evidence='国内劳动报酬运用/增加值来源',limitation='2023年；不自行分拆混合收入')]
for mid in ids('R',1,12):
    sec=['非金融企业','金融机构','广义政府','住户']
    if mid in ['R002','R008','R010','R011','R012']:sec+=['国外']
    if mid in ['R005','R007']:sec=['广义政府','住户']
    metrics[mid]['coverage']=[c for c in metrics[mid]['coverage'] if c['dimension']!='机构部门']+[dict(dimension='机构部门',status='部分覆盖',members=sec,source_ids=['R_FOF'],evidence='表3-15本交易行的实际非空部门列；来源/运用分别选取',limitation='不承诺各部门双侧都有数值；实物转移仅政府运用/住户来源；实际最终消费仅政府/住户。')]
metrics['B010']['period_basis']='期末'
metrics['B027']['coverage']=[c for c in metrics['B027']['coverage'] if c['dimension']!='机构部门']
metrics['B027']['coverage'].append(dict(dimension='机构部门',status='部分覆盖',members=['全国一般公共预算非税收入'],source_ids=[metrics['B027']['source_id']],evidence='正文只核验全国非税收入',limitation='未核得中央/地方非税分项，不继承一般公共预算总收入分项。'))
metrics['B063']['coverage']=[c for c in metrics['B063']['coverage'] if c['dimension']!='机构部门']
metrics['B063']['coverage'].append(dict(dimension='机构部门',status='部分覆盖',members=['全口径外债合计'],source_ids=[metrics['B063']['source_id']],evidence='签约短期外债合计/外债合计；同币种',limitation='无逐部门匹配的短期分子，不向公司间贷款等分组复制。'))
metrics['B063']['conditions']+='；2025年末人民币展示金额复算56.546866%，原文整数份额写56%；不宣称二者精确复现，不自行归因于普通舍入。'
gaps.append(dict(system='F',question='F1/F2',dimension='全国',missing_item='2025年末外债原文短期份额56%与人民币展示余额复算56.546866%的差异说明',reason='B_S17原文整数份额与余额之比并非通常四舍五入一致，尚无进一步官方解释',allowed_alternative='保留原文56%与透明派生56.546866%并注明各自位置、币种和版本',boundary='不覆盖原值，不称误差已经解释，不混用美元舍入数'))
for mid,label in [('C036','全国五等份高低组之间的均值对比'),('C038','全国城镇与农村之间的均值对比')]:
    metrics[mid]['coverage']=[c for c in metrics[mid]['coverage'] if c['dimension']!='居民群体']+[dict(dimension='居民群体',status='部分覆盖',members=[label],source_ids=[metrics[mid]['source_id']],evidence='按公式指定两个组的均值进行一次对比',limitation='输入组不是该比率输出的独立分组；不能为高/低组或城/乡各造一个比率。')]
metrics['C058']['coverage'].append(dict(dimension='居民群体',status='部分覆盖',members=['中层及以上管理人员','专业技术人员','办事人员和有关人员','社会生产服务和生活服务人员','生产制造及有关人员'],source_ids=[metrics['C058']['source_id']],evidence='2025年规上企业分岗位工资原文表5—8',limitation='规上企业就业人员岗位分类，不代表全体劳动者；各岗位按原表名称。'))
for c in metrics['B052']['coverage']:
    if c['dimension']=='行业' and isinstance(c['members'],list):c['members']=[v for v in c['members'] if '手机' not in v]
    if c['dimension']=='企业类型':
        c.update(status='无稳定公开数据',members=[],evidence='已读表仅给民营进出口合计与出口，进口分项未直接核得',limitation='不将二者差额伪记为已公开进口原值；待登记兼容输入的独立派生。')

QMAP={
'K1':ids('A',31,40)+['A016','A020','A024','A026','B001','B003','B008','B012']+ids('E',1,6),
'K2':['A001','A002','A003']+ids('A',6,8)+['A014','A015','A016','A017','A018','A019']+ids('A',20,24)+['A056','A057','A058','B015','B017','B051','B052','B054','B055'],
'K3':ids('A',14,19)+ids('A',25,30)+['A035','A039']+ids('C',34,34)+ids('C',39,42),
'K4':['A016','B015','B016','B023']+ids('B',25,38)+['C010','C042'],
'M1':['A001','A002','A009','A012','A013']+ids('A',41,43)+['A054','A055'],
'M2':['A016','A041','A042','A043','A046','A047','R008','R014'],
'M3':ids('A',44,45)+ids('A',48,53)+['A016','B015','B035','B036'],
'M4':['A014','A016']+ids('A',44,49)+['B001','B003','B015','B026','B030'],
'F1':ids('A',44,45)+ids('A',48,49)+['B005']+ids('B',32,36)+ids('B',53,63)+['R010'],
'F2':ids('B',1,7)+ids('B',9,11)+ids('B',23,38),
'F3':ids('B',17,24)+['B028','A044','A045']+ids('E',7,8),
'F4':ids('B',39,50)+['B023','B026','B028','B038'],
'G1':ids('A',25,30)+ids('C',21,33),
'G2':['A004','A005','A007','B015','B016','B013','B014','C007','C050','R009']+ids('E',1,6),
'G3':['A002','A004','A005','A011','A027','A028','R001'],
'G4':['A004','A005','A010','A011','A014','B013','B014','B015','C027','C033','R001'],
'I1':ids('C',1,14),
'I2':ids('C',15,19)+['B016','E004'],
'I3':['C009','C015','C016','C018','B001','B003','B009','E001','E004','E005'],
'I4':['A011','A028','C027','C030','C031','R017','E001'],
'S1':['A004','A005','A010','B015','C001','C006','C027','C030','C033','C049','C051','C052','R017'],
'S2':['B026','C010']+ids('C',27,33)+['C043','C044']+ids('C',49,55),
'S3':['A004','A005','B051','B052']+ids('C',8,9)+ids('C',13,19)+['C052','R017','E003','E004'],
'S4':['B001','B003','B009','B012','B013','B015','B016','B017','C049','C050','E001','E005'],
'D1':['A007','B001','B002','B003','B006','B007','B008','B009','B012','B015','R008','R009','E001','E002'],
'D2':['A011','A014','A015','A027','A028','C034','C037','C039','R002','R015'],
'D3':['A014','A015','A016','A017','A018','A019','A056']+ids('C',21,24)+ids('C',34,48)+['R004','R005','R006','R007','R013','R016'],
'D4':ids('R',1,16)+['B053','B054','B055','B056']
}
# Newly verified price and wage metrics are attached by actual names, never by
# numerical positions assigned during asynchronous source research.
for mid,m in metrics.items():
    n=m['name']
    if mid.startswith('A') and any(x in n for x in ['CPI','PPI','居民消费价格','工业生产者','核心消费']):
        for q in ['K1','K3','M1','S4']:QMAP[q].append(mid)
    if mid.startswith('C') and '工资' in n and '工资性' not in n:
        for q in ['G1','G3','G4','I4','D2','D3']:QMAP[q].append(mid)
    if '技术合同' in n:
        for q in ['I2','I3','S3']:QMAP[q].append(mid)
    if '高等教育毛' in n:QMAP['G1'].append(mid)
for q in QMAP:QMAP[q]=sorted(set(aliases.get(m,m) for m in QMAP[q] if aliases.get(m,m) in metrics))

qobjs={}
for sy in SYSTEMS:
    for q in sy['questions']:
        qobjs[q[0]]=dict(id=q[0],system=sy['code'],title=q[1],hypothesis=q[2],support=q[3],counter=q[4],alternatives=q[5],boundary=q[7],metric_ids=QMAP[q[0]])
unmapped=set(metrics)-{m for a in QMAP.values() for m in a}
assert not unmapped, f'Unmapped indicators: {unmapped}'

def group_for(m):
    sid=m['source_id']; mid=m['id']; n=m['name']
    if mid.startswith('R') and mid!='R017':return 'EG-资金流量'
    if mid in ids('A',1,13):return 'EG-国民核算'
    if mid in ids('A',14,19)+['A056'] or mid in ids('C',34,42):return 'EG-住户调查'
    if mid in ids('B',1,14):return 'EG-规上工业财务'
    if mid in ids('B',39,50):return 'EG-银行监管'
    if mid in ids('A',41,49)+['A054']:return 'EG-金融统计'
    if mid in ids('C',1,10):return 'EG-科技经费'
    if mid in ['A025','A026','A027']:return 'EG-劳动力调查'
    if mid in ['C056','C057','C058']:return 'EG-城镇单位工资'
    return 'EG-'+sid
for mid,m in metrics.items():
    m['inputs']=[aliases.get(i,i) for i in m['inputs']]
    m['question_ids']=[q for q,arr in QMAP.items() if mid in arr]
    m['systems']=sorted(set(q[0] for q in m['question_ids']))
    m['evidence_group']=group_for(m)
for mid,m in metrics.items():
    if m['origin']=='透明派生':m['evidence_group']=' + '.join(sorted(set(metrics[i]['evidence_group'] for i in m['inputs'])))

DIM={'全国':'DIM-NAT','省级':'DIM-PROV','地级':'DIM-PREF','行业':'DIM-IND','企业类型':'DIM-FIRM','居民群体':'DIM-HH','机构部门':'DIM-SEC'}
registry=[dict(id=v,type=k,name=k,definition={'全国':'内地统计范围；来源若另有范围从其规定','省级':'31省级地区，直辖市单列；省全域','地级':'地级市/地区/自治州/盟；市辖区、市全域和市本级财政分开','行业':'国民经济行业分类及专题映射；仅来源支持组合','企业类型':'所有制、登记类型、规模、统计门槛分别记，不默认互斥','居民群体':'城乡、收入五等份、年龄、就业身份；分类不可机械交叉','机构部门':'住户、非金融企业、金融机构、广义政府、国外；不等同登记所有制'}[k],version='来源统计年度',source_id='R_INDUSTRY' if k=='行业' else 'R_GEO_RULE' if k in ['省级','地级'] else '') for k,v in DIM.items()]
for p in dimensions['provinces']:
    registry.append(dict(id='PROV-'+p['code'],type='省级成员',name=p['name'],definition=('直辖市；单列比较，不计入地级行政区划' if p['municipality'] else f"2024年末下辖地级单位{p['prefecture_count_2024']}个"),version='2024-12-31',source_id='R_REGION_ADMIN'))
for i in dimensions['industries']:
    registry.append(dict(id='IND-'+i['code'],type='行业门类',name=i['name'],definition='分类目录成员；不是该门类全部指标已公开的声明',version='GB/T4754—2017及第1号修改单',source_id='R_INDUSTRY'))
for typ,vals,sid in [('居民群体',['城镇','农村','低收入组','中间偏下收入组','中间收入组','中间偏上收入组','高收入组','16—24岁（不含在校生）','25—29岁（不含在校生）','30—59岁（不含在校生）','农民工'], 'A_S04'),('企业类型',['国有控股','股份制','外商及港澳台投资','私营','规上工业','城镇非私营单位','城镇私营单位'], 'B_S01'),('机构部门',['住户','非金融企业','金融机构','广义政府','国外'],'R_FOF')]:
    for j,v in enumerate(vals):registry.append(dict(id=DIM[typ]+f'-{j+1:02d}',type=typ+'成员',name=v,definition='仅用于对应来源，交叉与重叠按指标覆盖栏',version='指标来源版本',source_id=sid if not ('岁' in v or v=='农民工' or '单位' in v) else ''))

# Four allowed status labels are retained; evidence provenance states whether a
# cell is directly read, an interpretation boundary, or still lacks verification.
coverage=[]
for mid,m in metrics.items():
    bydim=defaultdict(list)
    for c in m['coverage']:bydim[c['dimension']].append(c)
    normalized=[]
    for dim,did in DIM.items():
        cs=bydim.get(dim,[])
        if cs:
            statuses=[c['status'] for c in cs]
            status='已覆盖' if '已覆盖' in statuses else '部分覆盖' if '部分覆盖' in statuses else statuses[0]
            c=dict(dimension=dim,status=status,members='；'.join(dict.fromkeys(txt(x['members']) for x in cs if txt(x['members']))),source_ids=sorted(set(s for x in cs for s in x.get('source_ids',[]))),evidence='；'.join(dict.fromkeys(txt(x['evidence']) for x in cs)),limitation='；'.join(dict.fromkeys(txt(x.get('limitation','')) for x in cs if x.get('limitation'))),verification='已读原表/定义；仅所列范围')
            if mid in ['C011','C012','C014']:c['verification']='已读发布指引/定义/目录；未逐表核验数值'
        else:
            # Splitting a nationwide rate or an enterprise balance sheet into
            # resident age groups is generally a category mismatch.
            na=(dim=='居民群体' and (mid.startswith('B') or mid.startswith('E') or mid.startswith('R') or mid in ids('A',31,55) or mid in ids('C',1,19)+ids('C',49,55)))
            na=na or (dim=='企业类型' and (mid in ids('A',14,19)+['A025','A026','A028','A029','A030'] or mid in ids('C',21,48)))
            na=na or (dim in ['省级','地级'] and mid in ['A041','A042','A043','A050','A053','A054','A055'])
            c=dict(dimension=dim,status='不适用' if na else '无稳定公开数据',members='',source_ids=[m['source_id']],evidence='本指标定义不直接接受该维度拆分' if na else '已读来源未提供该维度的稳定全覆盖表；本轮未建立额外逐单元来源',limitation='不得借用同名但不同范围指标填补' if na else '这是本轮证据缺口，不断言其他官方资料不存在；后续需逐表核验',verification='适用性判断' if na else '原来源已查；扩展来源待核验')
        c['dimension_id']=did
        normalized.append(c)
        for q in m['question_ids']:
            coverage.append(dict(id=f'CV{len(coverage)+1:05d}',question_id=q,metric_id=mid,**c))
    m['coverage']=normalized

for n,e in enumerate(examples,1):
    e['id']=f'EX{n:02d}'
    e['inputs']=[dict(name=x.get('name',x.get('名称','')),value=x.get('value',x.get('值')),unit=x.get('unit',x.get('单位','')),period=x.get('period',x.get('报告期','')),location=x.get('location',x.get('定位',''))) for x in e['inputs']]
for n,g in enumerate(gaps,1):g['id']=f'GAP{n:03d}'
for q in qobjs.values():
    q['gap_ids']=[g['id'] for g in gaps if g.get('system') in [q['system'],'全部']]

# Count only fully specified, directly evidenced series keys; no Cartesian
# product of all seven dimensions, and no claim that a full panel is collected.
series=[]
for p in dimensions['provinces']:
    for mid,sid,period in [('A001','R_REGION_GDP','2024'),('A010','R_REGION_GDP','2024'),('A014','R_REGION_INCOME','2018—2024'),('C001','C_S01','2024')]:
        series.append(dict(id=f'SER{len(series)+1:04d}',metric_id=mid,dimension_id='PROV-'+p['code'],member=p['name'],scope='省级全域；总量/全体居民按指标定义',frequency='年度',verified_period=period,source_id=sid,status='已核验表中成员与口径；未采集完整历史数值'))

counts=dict(systems=7,questions=len(qobjs),metrics=len(metrics),published=sum(m['origin']=='公开发布' for m in metrics.values()),derived=sum(m['origin']=='透明派生' for m in metrics.values()),sources=len(sources),mappings=sum(map(len,QMAP.values())),coverage_rows=len(coverage),registered_series=len(series),full_history_series_collected=0,examples=len(examples),gaps=len(gaps))
catalog=dict(version='1.0.0',as_of='2026-09-15',scope='方法与元数据设计；非当期经济判断或全历史数据平台',counts=counts,systems=SYSTEMS,questions=list(qobjs.values()),metrics=list(metrics.values()),sources=list(sources.values()),dimension_registry=registry,coverage=coverage,series_registry=series,examples=examples,gaps=gaps,aliases=aliases,global_rules=GLOBAL_RULES)
dump(OUT/'data/catalog.json',catalog)
dump(OUT/'data/series_registry.json',series)
dump(OUT/'data/examples.json',examples)

def source_link(sid):
    s=sources[sid];return f"[{sid} · {s['title']}]({s['url']})"
def metlist(q):return '；'.join(f"{mid} {metrics[mid]['name']}" for mid in QMAP[q])

chapters=[]
for n,sy in enumerate(SYSTEMS,1):
    chapter=f"### 6.{n} {sy['school']}：{sy['name']}\n\n**独立答案**：{sy['output']}。\n\n**观察时间**：{sy['horizon']}。\n\n**主要机制链**：{sy['chain']}。\n\n**与其他体系连接**：{sy['links']}。\n\n**解释边界**：{sy['boundary']}\n"
    template=f"# {sy['code']} · {sy['name']}分析模板\n\n> 理论视角：{sy['school']}。本文件是待填模板，未包含当期经济结论。\n\n- 研究报告期：待填\n- 信息截止日与版本：待填\n- 地域/行业/群体/部门：待填\n- 作者与复核人：待填\n\n## 独立答案摘要\n\n| 回答对象 | 状态 | 变化方向 | 证据充分程度 | 最重要的分化/缺口 |\n|---|---|---|---|---|\n| {sy['output']} | 待填 | 待填 | 待填 | 待填 |\n\n证据链：{sy['chain']}。\n\n解释边界：{sy['boundary']}\n"
    for q0 in sy['questions']:
        q=qobjs[q0[0]];midtext=metlist(q['id'])
        chapter+=f"\n#### {q['id']} {q['title']}\n\n- 机制假说：{q['hypothesis']}\n- 观察指标：{midtext}。\n- 支持证据：{q['support']}\n- 反向证据：{q['counter']}\n- 替代解释：{q['alternatives']}\n- 允许的判断方式：写明哪些证据与上述机制一致、覆盖哪些范围；不足时只报告环节事实。\n- 尚不能回答：{q['boundary']}\n"
        template+=f"\n## {q['id']} {q['title']}\n\n**机制假说**：{q['hypothesis']}\n\n**候选指标**：{midtext}。先读工作簿对应覆盖与样本，按本期问题选取，不要求全部机械使用。\n\n| 证据ID | 指标ID与细分键 | 原值/单位 | 报告期/版本 | 原文位置 | 事实与机制角色 | 共享证据组 |\n|---|---|---|---|---|---|---|\n| 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |\n\n- 支持证据（检查：{q['support']}）：待填\n- 反向证据（检查：{q['counter']}）：待填\n- 替代解释（至少检视：{q['alternatives']}）：待填\n- 排除/保留替代解释的理由：待填\n- 当前可作出的判断与适用范围：待填\n- 尚不能回答：{q['boundary']}；本期另补待填\n- 证据充分程度与理由：待填\n- 下一项可增强判断的数据：待填\n- 下一项可推翻判断的数据：待填\n- 等待的发布日期/修订：待填\n"
    template+=f"\n## 跨体系交接\n\n{sy['links']}。\n\n| 向哪套体系提供什么事实 | 共用底层证据 | 该体系新增的独立证据 | 仍有分歧 |\n|---|---|---|---|\n| 待填 | 待填 | 待填 | 待填 |\n\n## 有条件的政策含义\n\n若【待填事实】且【待填机制条件】成立，则更支持【待填推论】；可能代价为【待填】；若【待填反向变化】，应撤回或调整这一推论。\n"
    (OUT/'templates'/f'{sy["code"]}_{sy["name"]}.md').write_text(template)
    chapters.append(chapter)
manual=(W/'manual_base.md').read_text().replace('<!-- SYSTEM_CHAPTERS -->','\n'.join(chapters))
manual+='\n## 10. 版本1.0交付规模与来源导航\n\n'+f"本版登记{counts['published']}项独立公开指标定义、{counts['derived']}项透明派生定义（合计{counts['metrics']}项），{counts['mappings']}条问题—指标关系，{counts['coverage_rows']}条维度检查，{len(sources)}个来源登记项。同文转载和派生项不增加独立证据权重。\n\n已单列{len(series)}条省级细分序列键（GDP、人均GDP、居民收入、R&D经费各31省）；这是已核验表列成员的登记数。其余公开分组按指标覆盖栏保存，尚未逐一展开成序列键，因此不计入这个数。本阶段完整历史数值面板采集数为0，不能把覆盖行数当时间序列数。\n\n"
manual+='### 主要核验入口\n\n'+'\n'.join('- '+source_link(sid) for sid in dict.fromkeys(['A_S01','A_S04','B_S01','B_S09','C_S01','C_S06','R_FOF','R_REGION_GDP','R_REGION_ADMIN','R_INDUSTRY']) if sid in sources)+'\n'
(OUT/'研究方法手册.md').write_text(manual)

pan='''# 中国经济全景模板

> 模板没有预设当前经济状态。先完成七份独立答案，再做跨体系综合。

- 报告季度与信息截止日：待填
- 月度补充覆盖到：待填
- 年度结构指标实际报告期：待填
- 本次新增/修订的数据及受影响判断：待填

## 一、七维状态摘要

| 体系 | 核心答案（对应问题ID） | 状态 | 方向 | 证据充分程度与理由 | 适用期间 | 地域/行业/群体差异 | 未覆盖部分 |
|---|---|---|---|---|---|---|---|
'''
for sy in SYSTEMS:pan+=f"| {sy['code']} {sy['name']} | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |\n"
pan+='''
## 二、跨体系关系图

下图是待检验机制目录。每条连线应在下表标注观察性质，不能直接当作已识别的因果关系。

```mermaid
flowchart LR
  D[就业与分配] --> Y[居民收入]
  Y --> C[消费]
  C --> P[销售与生产]
  P --> I[利润与投资]
  I --> D
  M[货币条件] --> F[融资取得]
  F --> I
  I --> CF[收入与回款]
  CF --> DS[偿债]
  DS --> B[金融机构]
  B --> F
  H[住房成交与资产价格] --> CF
  H --> T[土地收入与财政]
  T --> I
  S[教育与基础设施] --> N[研发与技术应用]
  N --> I
```

| 关系ID | 起点→终点 | 相关问题ID | 匹配证据与报告期 | 观察性质 | 时滞假说 | 替代解释/反馈 | 尚缺数据 |
|---|---|---|---|---|---|---|---|
| L1 | 就业/分配→收入→消费 | D2/D3/K3/K2 | 待填 | 待填 | 待填 | 待填 | 待填 |
| L2 | 融资→支出→回款→偿债 | M3/M4/F2 | 待填 | 待填 | 待填 | 待填 | 待填 |
| L3 | 住房→开发回款/土地→财政 | F3/K4/F4 | 待填 | 待填 | 待填 | 待填 | 待填 |
| L4 | 要素/创新→产业回报→就业 | G1/I2/I3/S4/I4 | 待填 | 待填 | 待填 | 待填 | 待填 |

观察性质仅填：已观察联系、待检验机制、证据不足。反馈另写，不能用图的箭头代替证据。

## 三、分歧解释表

| 分歧ID | 两项结论与问题ID | 共用证据 | 各自新增证据 | 口径/版本排查 | 时间尺度与时滞 | 群体/地区/行业解释 | 竞争性机制 | 下一项判别数据 |
|---|---|---|---|---|---|---|---|---|
| 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |

允许短期需求弱、部分产业升级、部分部门偿债压力升高同时成立。不投票、不加权生成总分。

## 四、条件与后续观察

| 判断ID | 若什么变化出现则增强 | 若什么变化出现则推翻 | 等待什么数据/报告期 | 发布节奏 | 责任人 | 条件政策推论与代价 |
|---|---|---|---|---|---|---|
| 待填 | 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |

## 五、证据账本与覆盖声明

| 证据组ID | 底层原值/调查 | 被哪些体系使用 | 派生关系 | 是否同一报告版本 | 不能覆盖的范围 |
|---|---|---|---|---|---|
| 待填 | 待填 | 待填 | 待填 | 待填 | 待填 |

全国、省级、地级、行业、企业、居民群体及机构部门覆盖分别声明；低频资料保留原报告期。更新前对照指标字典的口径断点及缺口表。
'''
(OUT/'templates/全景模板.md').write_text(pan)

gapmd='# 覆盖缺口与解释边界\n\n“无稳定公开数据”表示本轮已读来源未形成所需的稳定公开组合，不是对所有资料绝对不存在的断言。已覆盖也只指所列成员、期间和口径；没有展开采集全历史值。\n\n## 覆盖状态\n\n| 层级 | 已覆盖 | 部分覆盖 | 无稳定公开数据 | 不适用 |\n|---|---:|---:|---:|---:|\n'
for dim in DIM:
    c=Counter(x['status'] for m in metrics.values() for x in m['coverage'] if x['dimension']==dim)
    gapmd+='| '+dim+' | '+' | '.join(str(c[s]) for s in ['已覆盖','部分覆盖','无稳定公开数据','不适用'])+' |\n'
gapmd+='\n以上按独立指标定义×维度统计；Excel矩阵按问题×指标×维度展开，不能把两种计数混用。31省已逐一列名；2024年底333个地级行政单元只核验数量，不冒充2026地级名单。70城房价仅代表其市辖区的相应住房交易范围。\n\n## 缺口处理清单\n'
for g in gaps:
    gapmd+=f"\n### {g['id']} {g['missing_item']}\n\n- 对应：{g['system']} / {g['question']} / {g['dimension']}\n- 缺口原因：{g['reason']}\n- 可用的有限替代：{g['allowed_alternative']}\n- 判断边界：{g['boundary']}\n- 后续动作：按上述缺失对象查找新的官方原表；取得定义、连续性及范围证据后才变更覆盖状态。\n"
gapmd+='\n## 后续优先核验\n\n1. 建立按统计年度的完整地级实体名录，并逐地登记统计年鉴/预算决算原表；不把城市调查制度等同公开数据覆盖。\n2. 省市行业×企业类型及居民分组交叉表逐单元核验；缺少分组消费时保留D3的边界。\n3. 企业现金流、居民债务偿付及行业创新回报无法由总量余额推断，保留为研究缺口。\n4. 投入产出表可用于产业联系，但本版尚未核验具体表及统一映射，S3暂用行业和贸易结构等有限证据；不构造城市投入产出。\n'
(OUT/'覆盖缺口.md').write_text(gapmd)

exmd='# 公开数据样例与验收\n\n样例用于检验方法是否可执行，覆盖不同报告期与有限统计总体。算术复核通过不等于因果机制已被证明，亦不是2026年当期经济报告。每个体系至少有一条从原值、计算/比较到有限判断和反证需求的路径；缺失环节仍明确留空。\n'
for e in examples:
    exmd+=f"\n## {e['id']} · {e['system']} · {e['question']}\n\n"+'；'.join(source_link(s) for s in e['source_ids'] if s in sources)+'\n\n| 公开输入 | 值 | 单位 | 报告期 | 原文位置 |\n|---|---:|---|---|---|\n'
    for i in e['inputs']:exmd+='| '+' | '.join(txt(i[k]).replace('|','/') for k in ['name','value','unit','period','location'])+' |\n'
    exmd+=f"\n**计算/核对**：{txt(e['calculation'])}\n\n**结果**：{txt(e['result'])}\n\n**允许的结论**：{txt(e['permitted_conclusion'])}\n\n**不能得出的结论**：{txt(e['forbidden_conclusion'])}\n\n**反向证据与待补环节**：{txt(e['counterevidence_needed'])}\n"
exmd+='''
## 统计问题的执行检查

| 情形 | 已核验触发点 | 本版处理 | 不能采取的做法 |
|---|---|---|---|
| 定义断点 | 2025年M1扩围，2024官方回溯；分年龄失业率新口径 | 新旧序列分版，回溯只到已核验起点 | 把新旧同比或年龄率直接拼接 |
| 统计修订 | GDP经济普查修订；地方债年报/预算报告/决算显示精度与时点不同 | 记录发布时间与版本，比较用同版数据 | 用旧GDP分母配新分子后称真实变化 |
| 缺失与有效零 | 年鉴地区行业表部分单元空白 | 缺失值保留空值及原因，真零不删 | 空白填零，累计增长率作差 |
| 样本范围 | 规上工业2000万元门槛；70城市辖区；年龄人口为抽样表样本人数 | 结论限定到调查总体和空间范围 | 推为全部企业、全部城市或总体人口 |
| 派生输入不匹配 | 城镇单位工资与全国劳动生产率总体不同 | 并列观察并说明人群差异 | 计算并解释为全社会劳动收入份额 |
| 跨体系分歧 | 同期行业产出扩张可伴随利用率下降、私人需求弱 | 保留不同范围与机制的答案 | 通过投票、加权总分或删指标“消除”分歧 |
| 同源重复 | 住户收入在K/M/D共用，收入消费比由同一调查派生 | 同一证据组，不额外增加独立证据 | 以重复次数表示证据可信度 |
| 低频滞后 | FOF样例是2023年；研发样例2024年，专利调查2025年 | 每条证据保留原报告期 | 统一改标2026年或做伪月度变化 |

自动结构/算术检查结果见[验收结果](validation_results.json)。Excel“判断规则”表底部有同一公开输入的可编辑计算样例；这些样例不输入任何经济总分。
'''
(OUT/'validation/样例与验收.md').write_text(exmd)

# Eight sheet payloads. Literal formula definitions stay text; runnable formulas
# live in a dedicated calculation example block in 判断规则.
sheets=[]
def sheet(name,headers,rows,widths,subtitle):
    sheets.append(dict(name=name,headers=headers,rows=[[txt(x) for x in r] for r in rows],widths=widths,subtitle=subtitle))
sheet('体系问题',['问题编号','体系','核心问题','机制假说','主要证据链','支持证据','反向证据','替代解释','独立答案','判断边界','指标编号','相关缺口'],[[q['id'],next(s['school'] for s in SYSTEMS if s['code']==q['system']),q['title'],q['hypothesis'],next(s['chain'] for s in SYSTEMS if s['code']==q['system']),q['support'],q['counter'],q['alternatives'],next(s['output'] for s in SYSTEMS if s['code']==q['system']),q['boundary'],q['metric_ids'],q['gap_ids']] for q in qobjs.values()],[95,155,260,350,310,350,320,280,280,350,280,160],'7套体系 · 28个问题｜从问题进入指标，结论须分别保留')
mh=['指标编号','指标名称','模块','性质','经济含义/定义','单位','统计对象/范围','频率','时点/期间','存量/流量','价格口径','当期/累计','来源编号','原文定位','历史覆盖证据','更新规律','口径断点/修订','公式（文字定义）','输入指标','适用条件','对应体系','问题编号','可能解释','配套证据','误读风险','共享证据组','维度范围','原文链接']
mr=[]
for m in metrics.values():
    mr.append([m['id'],m['name'],m['module'],m['origin'],m['definition'],m['unit'],m['population'],m['frequency'],m['time_type'],m['stock_flow'],m['price_basis'],m['period_basis'],m['source_id'],m['source_locator'],m['history'],sources[m['source_id']]['frequency'],m['breaks'],m['formula'],m['inputs'],m['conditions'],m['systems'],m['question_ids'],m['interpretation'],m['companions'],m['pitfalls'],m['evidence_group'],[c['dimension']+'：'+c['status']+'（'+txt(c['members'])+'）' for c in m['coverage']],sources[m['source_id']]['url']])
sheet('指标字典',mh,mr,[95,270,160,105,360,95,320,135,100,100,100,110,115,350,380,135,400,350,150,360,120,160,310,300,350,185,400,300],f"{counts['published']}项公开定义 + {counts['derived']}项透明派生｜金额、指数和调查样本按原文口径")
maprows=[]
for q in qobjs.values():
    for mid in q['metric_ids']:
        m=metrics[mid]
        maprows.append([f'MAP{len(maprows)+1:04d}',q['id'],mid,m['name'],m['interpretation'],q['hypothesis'],q['support'],q['counter'],q['alternatives'],q['boundary'],m['evidence_group'],m['source_id']])
sheet('问题—指标映射',['映射编号','问题编号','指标编号','指标名称','本指标观察含义','本问题机制','支持证据组合','反向证据组合','替代解释','本问题边界','共享证据组','来源编号'],maprows,[100,95,95,270,330,350,350,350,300,350,200,125],'同一指标在不同问题中采用不同机制解释；组合支持不是因果识别')
cvrows=[]
for r in registry:cvrows.append(['维度目录',r['id'],'','',r['id'],r['type'],'目录成员',r['name'],r['source_id'],r['definition'],r['version'],'目录不是数据覆盖声明'])
for c in coverage:cvrows.append(['覆盖检查',c['id'],c['question_id'],c['metric_id'],c['dimension_id'],c['dimension'],c['status'],c['members'],c['source_ids'],c['evidence'],c['limitation'],c['verification']])
sheet('维度覆盖',['记录类型','记录编号','问题编号','指标编号','维度编号','维度/层级','覆盖状态','已核验成员/分类','来源编号','覆盖依据','限制/版本','核验性质'],cvrows,[115,110,95,95,125,145,160,480,150,440,390,210],f"{len(coverage)}条问题×指标×维度检查｜目录成员与覆盖记录分开筛选")
sh=['来源编号','发布主体','标题','公开原文链接','定义入口','发布日','读取日','报告期','发布节奏','表/节/脚注位置','已读定义依据','历史/制度证据','范围依据','限制']
sheet('来源登记',sh,[[s.get(k,'') for k in ['id','publisher','title','url','definition_url','publication_date','access_date','reporting_period','frequency','location','definition_evidence','history_evidence','coverage_evidence','limitations']] for s in sources.values()],[115,210,380,330,330,115,115,160,180,350,430,390,390,430],'公开原文与统计定义｜转载与原发布者区分；未宣称核验全部历史数值')
rule_rows=[[r[0],'全局',r[1],r[2],'',r[3],'',''] for r in GLOBAL_RULES]
for q in qobjs.values():rule_rows.append(['J-'+q['id'],q['id'],q['title'],q['support'],q['counter'],q['boundary'],q['alternatives'],'若后续结果环节与机制环节背离，应下调支持程度并重查替代解释。'])
sheet('判断规则',['规则编号','适用问题','规则/判断对象','支持条件/执行方法','反向证据','不可推断的边界','替代解释','后续判别'],rule_rows,[110,110,265,430,390,420,350,350],'证据状态：多环节支持 / 部分支持 / 相互矛盾 / 证据不足｜底部附可复算公开样例')
prows=[]
for s in SYSTEMS:prows.append(['七维摘要',s['code'],s['name'],'待填','待填','待填','待填',s['output'],'实际报告期另填；按模板完成四个核心问题'])
for code,name,questions in [('L1','收入→消费→生产','D2/D3/K3/K2'),('L2','融资→支出→回款→偿债','M3/M4/F2'),('L3','住房→土地/财政→项目','F3/K4/F4'),('L4','要素/创新→回报→就业','G1/I2/I3/S4/I4')]:prows.append(['跨体系关系',code,name,'待填','待填','待填','待填',questions,'标记已观察联系、待检验机制或证据不足；注明时滞及共享证据'])
prows.extend([['分歧解释','DIFF','口径/时间/群体/竞争机制','待填','待填','待填','待填','涉及问题ID、共同证据、各自新增证据','不投票；不加权总分'],['条件观察','COND','增强/推翻当前判断的条件','待填','待填','待填','待填','等待的报告期、数据、发布节奏','政策含义写条件和代价'],['证据账本','EG','同源与派生关系','待填','待填','待填','待填','底层调查、来源、版本、使用体系','共享原值重复不增加证据权重']])
sheet('全景模板',['板块','编号','回答主题','当前状态','方向','证据充分程度','报告期/版本','应填证据','综合规则'],prows,[150,100,300,130,110,190,170,420,450],'填写区｜先独立回答七套问题，再解释关系、分歧和条件')
sheet('缺口与边界',['缺口编号','体系','对应问题','维度','缺少什么','原因','有限替代','判断边界','后续核验动作'],[[g['id'],g['system'],g['question'],g['dimension'],g['missing_item'],g['reason'],g['allowed_alternative'],g['boundary'],'寻找同对象官方原表并核验定义、连续性和样本；得到证据后才更改覆盖'] for g in gaps],[110,100,220,190,390,420,390,390,360],'覆盖状态保留真实边界｜无公开证据不等于经济活动不存在')
dump(OUT/'data/workbook.json',dict(counts=counts,sheets=sheets))
for sh in sheets:
    with (OUT/'data'/f"{sh['name']}.csv").open('w',newline='',encoding='utf-8-sig') as f:
        wr=csv.writer(f,lineterminator='\n');wr.writerow(sh['headers']);wr.writerows(sh['rows'])

readme=f'''# 中国经济全景研究框架

七套独立分析体系、共享指标字典和可追溯的研究模板。版本 **1.0.0**，方法与来源核验日 **2026-09-15**。

## 直接使用

- [研究方法手册](研究方法手册.md)：机制、问题树、判断与全景综合规则。
- [Excel指标字典](中国经济全景指标字典.xlsx)：严格八张表，带筛选、冻结列与公开计算样例。
- [七份独立模板与全景模板](templates/)：保留反证、替代解释和待补证据。
- [覆盖缺口](覆盖缺口.md)：各维度实际公开边界与后续动作。
- [公开数据样例与验收](validation/样例与验收.md)：七体系的实值执行路径。

## 本版规模

| 项目 | 数量 | 计数含义 |
|---|---:|---|
| 分析体系 / 核心问题 | 7 / 28 | 分别作答，不投票、不加权总分 |
| 独立公开指标定义 | {counts['published']} | 官方发布的金额、指数或比率；不按每个地区膨胀 |
| 透明派生指标 | {counts['derived']} | 保存公式、输入编号及使用条件 |
| 问题—指标关系 | {counts['mappings']} | 共享不等于独立证据增加 |
| 维度覆盖检查 | {counts['coverage_rows']} | 问题×指标×维度，非实际观测数 |
| 来源登记项 | {counts['sources']} | 同文转载不重复计证据权重 |
| 明确登记的省级序列键 | {counts['registered_series']} | 四类指标各31省，限定已核验表列期间；其余分类未计入 |
| 已采集完整历史面板序列 | 0 | 本阶段是方法与元数据设计 |
| 实值方法样例 | {counts['examples']} | 各自保留实际报告期 |

## 如何开始一次研究

1. 固定季度、信息截止日和研究范围，选择问题编号。
2. 由映射表查指标，再检查定义、覆盖、统计版本和原文位置。
3. 在七份模板分别填写支持证据、反向证据、竞争解释与有限判断。
4. 用全景模板连接部门与产业，保留分歧，列出下一项能推翻判断的数据。

## 数据与重现

`data/catalog.json` 是发布版研究元数据；`data/workbook.json` 是八表视图，CSV可直接筛选或导入。`data/series_registry.json` 只登记确已明确的细分键。原始数据归原发布机构，本仓库提供链接、定义转述和少量核验输入，不镜像完整官方文件。

核验：`python3 scripts/validate_package.py`。编辑 `data/design_inputs/` 后运行 `python3 scripts/compile_metadata.py` 重新编译方法、字典和模板；运行 `python3 scripts/build_calculation_cases.py` 生成公开计算样例。编译器保留别名、去重及复核修正，避免直接修改生成文件后丢失变更。

Excel由 `scripts/build_workbook.mjs` 使用 `@oai/artifact-tool` 生成，需要具备该库的运行环境；此依赖不是本仓库附带的公共npm安装承诺。执行 `node scripts/build_workbook.mjs` 后产生工作簿与预览，再执行验收脚本。结构化元数据与CSV无此依赖。

## 真实边界

本版不包含自动采集、完整城市面板或当前中国经济分析报告。31省和A—T行业目录已设计，但目录成员不等于每项指标均有数据。地级单位目录数量以2024年末官方表为准，尚未逐名核验2026全体地级实体。无稳定公开组合处明确标缺口。

劳动生产率不解释为TFP，专利不解释为投资回报，债务余额不解释为偿债能力。只使用稳定公开原值与透明计算，不自估资本存量、产出缺口、隐性债务或危机概率。
'''
(OUT/'README.md').write_text(readme)
print(json.dumps(counts,ensure_ascii=False))
