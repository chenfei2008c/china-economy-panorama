"""Build dashboard evidence only from the reviewed research package."""
from pathlib import Path
import json

P=Path(__file__).resolve().parent.parent
catalog=json.loads((P/'data/catalog.json').read_text())
sources={s['id']:s for s in catalog['sources']}
def source(label,ids,definition):
    return {'label':label,'files':['data/catalog.json','data/examples.json','data/calculation_cases.json'],
      'links':[{'label':sources[s]['title'],'url':sources[s]['url']} for s in dict.fromkeys(ids)],
      'filters':['研究元数据核验日：2026-09-15；每条经济观测保留原报告期；不是实时数据。'],
      'metricDefinitions':[{'label':label,'definition':definition}],
      'evidenceFlow':[{'title':'原始公开统计','detail':'沿所列发布机构原文及表/脚注位置核验。'},
                      {'title':'研究包记录','detail':'读取同一仓库的catalog、examples及calculation_cases；仅作本地展示变换。'}]}
def query(rows,label,ids,definition):return {'rows':rows,'source':source(label,ids,definition),'methods':[{'language':'text','code':'按脚本 scripts/prepare_dashboard_data.py 从已核验研究包选取观测；不插值、不生成新时期数据。'}]}

examples=catalog['examples']
def find(system,token):
    return next(x for e in examples if e['system']==system for x in e['inputs'] if token==x['name'])
def value(system,token):return find(system,token)['value']
gdp25=value('M','2025 GDP现价额（初步）');gdp24=value('M','2024 GDP现价额（最终核实）')
nominal=(gdp25/gdp24-1)*100
real=value('M','GDP实际增速')
deflator=((gdp25/gdp24)/(1+real/100)-1)*100
growth=[{'driver':n,'contribution':value('K',name),'unit':'百分点','period':'2025全年','sourceId':'A_S03'} for n,name in [('最终消费','最终消费拉动'),('资本形成','资本形成拉动'),('净出口','净出口拉动')]]
money=[{'measure':'M2同比','value':value('M','M2同比增长'),'period':'2025年12月末','unit':'%','sourceId':'A_S17'}, {'measure':'名义GDP增长','value':nominal,'period':'2025全年','unit':'%','sourceId':'A_S01 / A_S02'}]
income=value('K','居民人均可支配收入');spend=value('K','居民人均消费支出')
household=[{'measure':'人均可支配收入','value':income,'unit':'元','period':'2025全年','sourceId':'A_S04'},{'measure':'人均消费支出','value':spend,'unit':'元','period':'2025全年','sourceId':'A_S04'}]
industry=[{'measure':'工业增加值实际增长','value':value('K','规上工业增加值实际增长'),'unit':'%','period':'2025全年','sourceId':'E_S01'}, {'measure':'工业产能利用率','value':value('K','工业产能利用率'),'unit':'%','change':value('K','利用率同比变化'),'changeUnit':'百分点','period':'2025全年','sourceId':'E_S02'}, {'measure':'工业利润增长','value':value('K','规上工业利润同比增长'),'unit':'%','period':'2025全年','sourceId':'B_S01'}]
nominal_rows=[{'measure':'实际GDP增长','value':real,'unit':'%','period':'2025全年'},{'measure':'名义GDP增长','value':nominal,'unit':'%','period':'2025全年'},{'measure':'GDP平减指数变化','value':deflator,'unit':'%','period':'2025全年'}]
coverage=[]
for m in catalog['metrics']:
    for c in m['coverage']:
        coverage.append({'metricId':m['id'],'name':m['name'],'systems':m['systems'],'dimension':c['dimension'],'status':c['status'],'members':c['members'],'evidence':c['evidence'],'limitation':c['limitation']})
metrics=[]
for m in catalog['metrics']:
    row={k:m[k] for k in ['id','name','module','definition','unit','frequency','time_type','stock_flow','price_basis','period_basis','population','source_id','source_locator','history','breaks','origin','formula','inputs','conditions','systems','question_ids','interpretation','companions','pitfalls','coverage','evidence_group']}
    row['sourceUrl']=sources[m['source_id']]['url'];row['publisher']=sources[m['source_id']]['publisher'];row['sourceTitle']=sources[m['source_id']]['title'];metrics.append(row)

snapshot={'surface':'dashboard','title':'中国经济全景','generatedAt':'2026-09-15T02:00:00Z','status':'reviewed','buildStatus':'creating','filters':[],
 'queries':{
 'growth':query(growth,'三大需求对实际GDP增长的拉动',['A_S03'],'按国家统计局2025年公报原值：2.6+0.8+1.6=5.0个百分点；贡献不是因果政策效果。'),
 'money':query(money,'货币与名义产出',['A_S01','A_S02','A_S17'],'M2为2025年12月末存量同比，名义GDP增长按同版2025/2024年度金额复算；不是货币超发或空转率。'),
 'nominal':query(nominal_rows,'GDP量价对照',['A_S01','A_S02'],'实际增长为官方可比价格同比；名义增长=(1401879/1348066−1)×100；平减变化=((1401879/1348066)/1.05−1)×100。'),
 'household':query(household,'居民收入与消费',['A_S04'],'人均可支配收入43377元、人均消费29476元；消费/收入比67.95%，其补数不是国民核算储蓄率。'),
 'industry':query(industry,'工业活动与利用率',['E_S01','E_S02','B_S01'],'2025全国规上工业；工业产能调查和财务调查不是配对面板，不能归因或外推全体企业。'),
 'frameworks':query([{k:s[k] for k in ['code','name','school','output','horizon','chain','boundary','links']} for s in catalog['systems']],'七套研究体系',[],'研究分类与机制，不是经济状态评分；各体系独立作答。'),
 'questions':query(catalog['questions'],'核心研究问题',[],'28个问题的机制、反证、替代解释及指标映射，来源于研究方法手册。'),
 'metrics':query(metrics,'公开指标字典',[],'207个独立定义，其中195个公开指标、12个透明派生；共享指标与派生指标不增加独立证据权重。'),
 'coverage':query(coverage,'公开证据覆盖',[],'每个独立指标×七种维度只计一次，已覆盖与部分覆盖分别保留；无稳定公开数据仅表示本轮未核得。'),
 'examples':query(examples,'方法执行样例',list(dict.fromkeys(s for e in examples for s in e['source_ids'])),'10个已核验公开数据样例，报告期不同。保留允许判断、禁止判断及反向证据，不能拼成当期宏观报告。'),
 'gaps':query(catalog['gaps'],'研究缺口与边界',[],'23项缺口是已核验研究范围内的未解决问题，不表示相关活动不存在。')
 }}
dest=P/'dashboard/src/data.json'
if dest.exists():
    old=json.loads(dest.read_text());snapshot['id']=old['id'];snapshot['buildStatus']='updating'
    dest.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
else:
    dest=P/'data/dashboard_snapshot.json';dest.write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
(P/'data/dashboard_snapshot.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
print(dest)
