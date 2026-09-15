import React, { useState } from 'react';
import { barChartSpec, ChartRenderer, DataComponent, DataTable, Dialog, Dropdown, EvidenceChart, SectionHeader, SortableItem, SortableRegion, useDataApp, useDashboardTabs } from '../../data-app-public.jsx';
import './panorama.css';
import {DIMENSIONS, STATUSES, filterMetrics, coverageCells, dictionaryCsv} from './dashboard-model.mjs';

const TABS = [
  { id: 'panorama', label: '全景', filterIds: [], focusFields: [] },
  { id: 'frameworks', label: '七套体系', filterIds: [], focusFields: ['system'] },
  { id: 'dictionary', label: '指标与覆盖', filterIds: [], focusFields: ['system', 'dimension', 'metric'] },
];
const SHORT = { K: '需求与周期', M: '货币与支出', F: '资产负债表', G: '要素与效率', I: '创新与替代', S: '产业与条件', D: '积累与分配' };
const NUM = { K: '01', M: '02', F: '03', G: '04', I: '05', S: '06', D: '07' };
const REPO = 'https://github.com/chenfei2008c/china-economy-panorama';
const fmt = (n, d = 0) => Number(n).toLocaleString('zh-CN', { minimumFractionDigits: d, maximumFractionDigits: d });
const joined = x => Array.isArray(x) ? (x.join('；') || '—') : x || '—';
const bar = (x, y, color = '#e3120b', type = 'horizontalBar') => type === 'horizontalBar' ? { ...barChartSpec({ presentation: 'groupedList', category: x, value: y, series: [{key: y, label: y === 'contribution' ? '拉动（百分点）' : '全国居民人均值（元）', color}], style: {thickness: 18, gap: 20, radius: 0}, format: {maximumFractionDigits: y === 'contribution' ? 1 : 0} }), stackable: false } : { type, x, y, colors: { [y]: color }, showLegend: false, showXAxisLabel: false, showYAxisLabel: false, valueDecimals: 2, stackable: false };

function Kicker({ children }) { return <p className="pan-kicker">{children}</p>; }
function LinkButton({ onClick, children }) { return <button className="pan-link" onClick={onClick}>{children} <span aria-hidden="true">↗</span></button>; }
function SourceNote({ children }) { return <p className="pan-source-note">{children}</p>; }

export function DashboardContent() {
  const shell = useDataApp();
  const { activeTabId } = useDashboardTabs(TABS);
  const rows = id => shell.queries[id]?.rows || [];
  const go = (tab, focus = {}) => shell.exploreDashboard(tab, { focus });
  return <article className="panorama-page">
    {activeTabId === 'frameworks' ? <FrameworkView shell={shell} rows={rows} go={go} /> : activeTabId === 'dictionary' ? <DictionaryView shell={shell} rows={rows} /> : <Overview shell={shell} rows={rows} go={go} />}
    <footer className="pan-footer"><span className="pan-wordmark">CHINA<br />ECONOMY</span><p>中国经济全景研究<br /><span>稳定公开原值 · 透明计算 · 七套独立判断</span></p><p className="pan-footer-right">图表为已核验公开数据样例，保留实际报告期。<br />研究框架与样例不构成当期经济评级。 <a href={REPO} target="_blank" rel="noreferrer">研究仓库 ↗</a></p></footer>
  </article>;
}

function Overview({ shell, rows, go }) {
  const growth = rows('growth');
  const total = growth.reduce((n, r) => n + r.contribution, 0);
  const consumptionShare = growth[0].contribution / total * 100;
  const household = rows('household');
  const ratio = household[1].value / household[0].value * 100;
  const nominal = rows('nominal');
  const growthSpec = shell.chartOverrides['growth-drivers'] ?? bar('driver', 'contribution');
  return <>
    <header className="pan-masthead"><div><Kicker>CHINA / ECONOMIC OBSERVATORY</Kicker><h1>增长，正在由谁推动？</h1><p className="pan-deck">从总量到结构，从需求到分配，用七种视角读懂中国经济。</p></div><div className="pan-issue"><strong>2025</strong><span>年度观察 · 公开数据样例</span><small>研究框架核验于 2026.09.15</small></div></header>
    <div className="pan-edition"><span><i /> 全景观察</span><span>全国口径 · 各图保留实际报告期</span><a href={`${REPO}/blob/main/研究方法手册.md`} target="_blank" rel="noreferrer">阅读研究手册 ↗</a></div>
    <SortableRegion id="panorama:lead" variant="freeform" authoredRevision={1} className="pan-lead-grid">
      <SortableItem id="growth-drivers" label="增长的支出构成" kind="chart">
        <DataComponent id="growth-drivers" queryId="growth" kind="chart" title="增长的支出构成" chart={growthSpec} sourceRows={growth} displayRows={growth} variant="plain" className="pan-evidence pan-lead-chart">
          <p className="pan-unit">三大需求对 GDP 实际增长的拉动，百分点</p>
          <div className="pan-lead-summary" data-reviewed-rows><p>消费贡献了<br /><strong>{fmt(consumptionShare)}<span>%</span></strong> 的增长拉动</p><div><b>{fmt(total, 1)}<small>%</small></b><span>2025 年实际 GDP 增长</span></div></div>
          <ChartRenderer rows={growth} spec={growthSpec} height={208} {...shell.chartProps('growth-drivers')} />
          <SourceNote>国家统计局 · 2025 年统计公报。贡献占比由舍入后的拉动值计算，不表示政策因果效果。</SourceNote>
        </DataComponent>
      </SortableItem>
      <SortableItem id="money-comparison" label="货币与名义增长" kind="chart" className="pan-lead-rail">
        <EvidenceChart id="money-comparison" queryId="money" title="货币与名义增长（%）" rows={rows('money')} sourceRows={rows('money')} spec={bar('measure', 'value', '#1b3d52', 'bar')} height={195} variant="plain" className="pan-evidence">
          <div className="pan-pair-stats" data-reviewed-rows>{rows('money').map(r => <div key={r.measure}><strong>{fmt(r.value, r.measure.includes('M2') ? 1 : 2)}<small>%</small></strong><span>{r.measure} · {r.period}</span></div>)}</div>
          <p className="pan-reading">货币存量增长快于名义产出，传导判断仍需结合融资结构与资金使用行为。</p>
          <LinkButton onClick={() => go('frameworks', { system: 'M' })}>进入货币体系</LinkButton>
        </EvidenceChart>
      </SortableItem>
    </SortableRegion>
    <SectionHeader id="panorama:sides" title="同一年的不同侧面" />
    <SortableRegion id="panorama:signals" variant="freeform" authoredRevision={1} className="pan-signals-grid">
      <SortableItem id="gdp-prices" label="实际与名义的温差" kind="chart"><EvidenceChart id="gdp-prices" queryId="nominal" title="实际与名义的温差（%）" rows={nominal} sourceRows={nominal} spec={bar('measure', 'value', '#e3120b', 'bar')} height={188} variant="plain" className="pan-evidence"><p className="pan-insight"><strong>{fmt(nominal[2].value, 2)}<small>%</small></strong><span>隐含 GDP 平减指数变动</span></p><SourceNote>2025 全年；用同版本现价 GDP 与实际增速计算。它与 CPI、PPI 的统计范围不同。</SourceNote></EvidenceChart></SortableItem>
      <SortableItem id="household-budget" label="居民收入如何转为消费" kind="chart"><EvidenceChart id="household-budget" queryId="household" title="居民收入如何转为消费" rows={household} sourceRows={household} spec={bar('measure', 'value', '#17676a')} height={188} variant="plain" className="pan-evidence"><p className="pan-insight"><strong>{fmt(ratio, 2)}<small>%</small></strong><span>消费支出 / 可支配收入</span></p><SourceNote>2025 全年，全国居民人均值，元。住户调查口径；不能据此推算国民账户居民储蓄率。</SourceNote></EvidenceChart></SortableItem>
      <SortableItem id="industrial-signals" label="生产扩张与经营表现" kind="custom" className="pan-industrial-block"><DataComponent id="industrial-signals" queryId="industry" title="生产扩张与经营表现" sourceRows={rows('industry')} displayRows={rows('industry')} variant="plain" className="pan-evidence"><div className="pan-industrial" data-reviewed-rows>{rows('industry').map(r => <div key={r.measure}><span>{r.measure}</span><strong>{fmt(r.value, 1)}<small>%</small></strong>{r.change != null && <small>比上年 {r.change > 0 ? '+' : ''}{fmt(r.change, 1)} 个百分点</small>}</div>)}</div><SourceNote>2025 全年。增加值与利润的统计对象不同；产能利用率反映利用程度，不能单独证明投资过度。</SourceNote></DataComponent></SortableItem>
    </SortableRegion>
    <div className="pan-section-heading"><Kicker>SEVEN PERSPECTIVES</Kicker><h2>七套体系，各自回答关键问题。</h2><p>保留独立结论，通过共同证据和传导机制拼合全景。</p></div>
    <DataComponent id="framework-index" queryId="frameworks" title="研究视角" sourceRows={rows('frameworks')} displayRows={rows('frameworks')} variant="plain" className="pan-evidence">
      <div className="pan-framework-index" data-reviewed-rows>{rows('frameworks').map(f => <button key={f.code} onClick={() => go('frameworks', { system: f.code })}><span className="pan-number">{NUM[f.code]}</span><small>{f.school}</small><h3>{f.name}</h3><p>{f.output}</p><span className="pan-tile-arrow" aria-hidden="true">↗</span></button>)}</div>
    </DataComponent>
    <div className="pan-dictionary-teaser"><div><strong>{rows('metrics').length}</strong><span>指标定义</span></div><div><strong>{rows('questions').length}</strong><span>研究问题</span></div><p>同一指标可以解释不同问题。<br />同一底层证据不重复增加判断权重。</p><LinkButton onClick={() => go('dictionary')}>探索指标与覆盖</LinkButton></div>
  </>;
}

function FrameworkView({ shell, rows, go }) {
  const code = SHORT[shell.viewFocus?.system] ? shell.viewFocus.system : 'K';
  const f = rows('frameworks').find(r => r.code === code);
  const questions = rows('questions').filter(q => q.system === code);
  const examples = rows('examples').filter(e => e.system === code);
  const metrics = rows('metrics').filter(m => m.systems.includes(code));
  const [openId, setOpenId] = useState(null);
  return <>
    <header className="pan-page-header"><Kicker>THE RESEARCH LENSES</Kicker><h1>七套答案，一幅全景。</h1><p>每套体系沿自己的证据链作判断，并交代反向证据与解释边界。</p></header>
    <div className="pan-school-layout"><aside className="pan-school-aside"><nav aria-label="选择分析体系">{rows('frameworks').map(s => <button key={s.code} aria-pressed={code === s.code} className={code === s.code ? 'is-active' : ''} onClick={() => { shell.setDashboardFocus({ system: s.code }); setOpenId(null); }}><span>{NUM[s.code]}</span><div>{s.name}<small>{s.school}</small></div></button>)}</nav><div className="pan-cadence"><Kicker>研究节奏</Kicker><p>季度 · 完整全景<br />月度 · 更新可更新部分<br />年度 · 复核结构变化</p></div></aside>
      <div className="pan-school-main">
        <DataComponent id={`school-${code}`} queryId="frameworks" title={f.school} sourceRows={[f]} displayRows={[f]} variant="plain" className="pan-evidence pan-school-intro"><span className="pan-watermark" aria-hidden="true">{NUM[code]}</span><h2>{f.name}</h2><p className="pan-school-output">{f.output}</p><div className="pan-tags" data-reviewed-rows><span>{questions.length} 个研究问题</span><span>{metrics.length} 项关联指标</span><span>{examples.length} 条验证样例</span></div><div className="pan-chain" aria-label="理论证据链">{f.chain.split('→').map((s, i) => <div key={s}><small>0{i + 1}</small><span>{s}</span></div>)}</div><SourceNote>观察尺度：{f.horizon}。{f.boundary}</SourceNote></DataComponent>
        <DataComponent id={`questions-${code}`} queryId="questions" title="从问题到判断" sourceRows={questions} displayRows={questions} variant="plain" className="pan-evidence pan-question-list">{questions.map((q, i) => { const isOpen = openId === q.id || (openId === null && i === 0); return <section key={q.id} className="pan-question"><button className="pan-question-toggle" aria-expanded={isOpen} onClick={() => setOpenId(isOpen ? '' : q.id)}><span>{q.id}</span><h3>{q.title}</h3><b aria-hidden="true">{isOpen ? '−' : '+'}</b></button>{isOpen && <div className="pan-question-body"><p className="pan-hypothesis">{q.hypothesis}</p><div className="pan-evidence-pair"><div><h4>支持证据</h4><p>{q.support}</p></div><div><h4>反向证据</h4><p>{q.counter}</p></div></div><p><b>替代解释</b> {q.alternatives}</p><p className="pan-boundary"><b>判断边界</b> {q.boundary}</p><div className="pan-metric-links">{q.metric_ids.slice(0, 7).map(id => <button key={id} onClick={() => go('dictionary', { system: code, metric: id })}>{rows('metrics').find(m => m.id === id)?.name || id} ↗</button>)}</div><LinkButton onClick={() => go('dictionary', { system: code })}>查看本体系全部指标</LinkButton></div>}</section>; })}</DataComponent>
        <div className="pan-section-heading pan-section-heading--small"><Kicker>WORKED EVIDENCE</Kicker><h2>用公开数据，走通证据链。</h2><p>以下为方法验证样例，保留各项数据的实际年份与口径。</p></div>
        {examples.map(e => <DataComponent key={e.id} id={`example-${e.id}`} queryId="examples" title={`${e.id} · ${e.question}`} sourceRows={[e]} displayRows={[e]} variant="plain" className="pan-evidence pan-example"><div className="pan-example-values" data-reviewed-rows>{e.inputs.slice(0, 6).map((r, i) => <div key={i}><span>{r.name}</span><strong>{fmt(r.value, Number.isInteger(r.value) ? 0 : 2)}<small>{r.unit}</small></strong><small>{r.period}</small></div>)}</div><details><summary>完整输入与复算公式</summary><DataTable rows={e.inputs} columns={[{field:'name',label:'输入指标'}, {field:'value',label:'原值'}, {field:'unit',label:'单位'}, {field:'period',label:'报告期'}, {field:'location',label:'发布位置'}]} searchable={false} label="样例原始输入" /><p className="pan-formula">{e.calculation}</p></details><div className="pan-evidence-pair"><div><h4>当前可作出的判断</h4><p>{e.permitted_conclusion}</p></div><div><h4>尚不能作出的判断</h4><p>{e.forbidden_conclusion}</p></div></div><SourceNote>后续观察：{joined(e.counterevidence_needed)}</SourceNote></DataComponent>)}
      </div>
    </div>
  </>;
}

function DictionaryView({ shell, rows }) {
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('all');
  const [selected, setSelected] = useState(null);
  const system = shell.viewFocus?.system || 'all';
  const dimension = shell.viewFocus?.dimension || '全国';
  const focusMetric = shell.viewFocus?.metric;
  const metric = selected === false ? null : rows('metrics').find(m => m.id === (selected || focusMetric));
  const setScope = (s, d) => { shell.setDashboardFocus({system: s, dimension: d}); setSelected(false); };
  const filtered = filterMetrics(rows('metrics'), {system, dimension, status, search});
  const tableRows = filtered.map(m => ({...m, coverageStatus: m.coverage.find(c => c.dimension === dimension)?.status, systemsText: m.systems.map(s => SHORT[s]).join(' / ')}));
  const cells = coverageCells(rows('frameworks'), rows('coverage'));
  const gaps = rows('gaps').filter(g => system === 'all' || g.system === system);
  const reset = () => { setSearch(''); setStatus('all'); setScope('all','全国'); };
  function download() {
    const csv = dictionaryCsv(tableRows, dimension);
    const url = URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8;'}));
    const a = document.createElement('a'); a.href=url; a.download=`中国经济指标_${system}_${dimension}.csv`; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  return <>
    <header className="pan-page-header"><Kicker>THE EVIDENCE ATLAS</Kicker><h1>知道什么，也看清不知道什么。</h1><p>检索指标、核对公开来源，沿地域与群体维度查看研究覆盖。</p></header>
    <DataComponent id="coverage-matrix" queryId="coverage" title="七套体系 × 七类观察维度" sourceRows={rows('coverage')} displayRows={cells} variant="plain" className="pan-evidence">
      <p className="pan-unit">每格为有覆盖的指标数 / 适用指标数。点击一个格子，筛选下方指标。</p>
      <p className="pan-mobile-hint">左右滑动表格，查看全部维度 →</p><div className="pan-matrix-scroll"><table className="pan-matrix" data-reviewed-rows><caption>研究覆盖矩阵：已覆盖与部分覆盖合计；同一体系内指标去重</caption><thead><tr><th scope="col">研究体系</th>{DIMENSIONS.map(d => <th scope="col" key={d}>{d}</th>)}</tr></thead><tbody>{rows('frameworks').map(f => <tr key={f.code}><th scope="row"><span>{NUM[f.code]}</span> {f.name}</th>{DIMENSIONS.map(d => {const c=cells.find(c => c.system===f.code && c.dimension===d); return <td key={d}><button aria-label={`${f.name}，${d}：${c.applicable ? `${c.covered} / ${c.applicable}` : "不适用"}`} aria-pressed={system===f.code && dimension===d} onClick={() => {setScope(f.code,d);setStatus('all');setSearch('');}} style={{background:`color-mix(in srgb, #17676a ${c.applicable ? c.covered/c.applicable*35 : 0}%, #f7f5ef)`}} title={`已覆盖 ${c['已覆盖']}；部分覆盖 ${c['部分覆盖']}；无稳定公开数据 ${c['无稳定公开数据']}；不适用 ${c['不适用']}`}>{c.applicable ? <><strong>{c.covered}</strong><span> / {c.applicable}</span></> : <span>不适用</span>}</button></td>;})}</tr>)}</tbody></table></div>
      <SourceNote>覆盖反映本轮核验的公开资料范围，不代表完整细分序列已经采集。未建立稳定来源是研究缺口，不断言其他官方资料不存在。</SourceNote>
    </DataComponent>
    <div className="pan-dictionary-controls"><label className="pan-search"><span>搜索指标</span><input type="search" placeholder="指标名称、编号或经济含义…" value={search} onChange={e=>setSearch(e.target.value)} /></label><Dropdown label="体系" allLabel="全部体系" showLabel value={system} choices={['all',...Object.keys(SHORT)]} choiceLabels={{all:'全部体系',...SHORT}} onChange={s=>setScope(s,dimension)} /><Dropdown label="维度" showLabel value={dimension} choices={DIMENSIONS} onChange={d=>setScope(system,d)} /><Dropdown label="覆盖状态" allLabel="全部状态" showLabel value={status} choices={['all',...STATUSES]} choiceLabels={{all:'全部状态'}} onChange={setStatus} /><button className="pan-reset" onClick={reset}>重置筛选</button></div>
    <div className="pan-results-summary"><p aria-live="polite"><strong>{filtered.length}</strong> 项指标 <span> / 共 {rows('metrics').length} 项 · {dimension}维度</span></p><button className="pan-link" onClick={download}>下载当前结果 CSV ↓</button></div>
    <DataComponent id="indicator-records" queryId="metrics" title="指标字典" sourceRows={filtered} displayRows={tableRows} kind="table" variant="plain" className="pan-evidence pan-record-table"><DataTable rows={tableRows} columns={[{field:'id',label:'编号'},{field:'name',label:'指标名称'},{field:'origin',label:'性质'},{field:'unit',label:'单位'},{field:'frequency',label:'频率'},{field:'coverageStatus',label:`${dimension}覆盖`,renderCell:v=><span className="pan-status" data-status={v}>{v}</span>},{field:'systemsText',label:'对应体系'}]} searchable={false} rowKey="id" onRowSelect={m=>setSelected(m.id)} selectedRowKey={metric?.id} rowActionLabel={m=>`查看${m.name}的定义与来源`} label="指标字典，点击一行查看完整定义及来源" />{!filtered.length && <p className="pan-empty">没有符合筛选条件的指标。请修改关键词或重置筛选。</p>}</DataComponent>
    <div className="pan-section-heading pan-section-heading--small"><Kicker>LIMITS OF OBSERVATION</Kicker><h2>把缺口留在视野里。</h2></div>
    <DataComponent id="coverage-gaps" queryId="gaps" title={`当前体系的研究缺口 · ${gaps.length} 项`} sourceRows={gaps} displayRows={gaps} variant="plain" className="pan-evidence"><div className="pan-gaps" data-reviewed-rows>{gaps.map(g=><details key={g.id}><summary><span>{g.id}</span>{g.missing_item}</summary><p>{g.reason}</p><p><b>可用替代：</b>{g.allowed_alternative}</p><p className="pan-boundary">{g.boundary}</p></details>)}</div></DataComponent>
    <MetricDialog metric={metric} onClose={()=>{setSelected(false); shell.setDashboardFocus({system,dimension});}} />
  </>;
}

function MetricDialog({metric:m,onClose}) {
  return <Dialog open={Boolean(m)} onClose={onClose} title={m?.name || '指标详情'} expanded>{m && <div className="pan-metric-detail"><div className="pan-tags"><span>{m.id}</span><span>{m.origin}</span><span>{m.frequency}</span><span>{m.unit}</span></div><p className="pan-definition">{m.definition}</p><dl>{[['统计对象',m.population],['时间与性质',`${m.time_type} · ${m.stock_flow} · ${m.price_basis} · ${m.period_basis}`],['公式',m.formula],['输入指标',joined(m.inputs)],['适用条件',m.conditions],['口径断点',m.breaks],['历史覆盖',m.history],['经济含义',m.interpretation],['配套证据',joined(m.companions)],['误读风险',m.pitfalls]].map(([k,v])=><div key={k}><dt>{k}</dt><dd>{v}</dd></div>)}</dl><h3>维度覆盖</h3><div className="pan-detail-coverage">{m.coverage.map(c=><details key={c.dimension}><summary>{c.dimension}<span className="pan-status" data-status={c.status}>{c.status}</span></summary><p>{c.members || '本轮未建立稳定公开细分来源。'}</p><p>{c.evidence}</p><p>{c.limitation}</p></details>)}</div><div className="pan-source-box"><small>{m.publisher} · {m.source_id}</small><h3><a href={m.sourceUrl} target="_blank" rel="noreferrer">{m.sourceTitle} ↗</a></h3><p>发布位置：{m.source_locator}</p></div></div>}</Dialog>;
}
