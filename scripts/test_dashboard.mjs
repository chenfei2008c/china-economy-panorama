import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {filterMetrics, coverageCells, dictionaryCsv, DIMENSIONS} from '../dashboard/src/content/dashboard/dashboard-model.mjs';

const snapshot = JSON.parse(readFileSync(new URL('../dashboard/src/data.json', import.meta.url)));
const catalog = JSON.parse(readFileSync(new URL('../data/catalog.json', import.meta.url)));
const rows = id => snapshot.queries[id].rows;
const close = (a,b) => assert.ok(Math.abs(a-b)<1e-9, `${a} != ${b}`);
const input = (system, name) => rows('examples').filter(e=>e.system===system)
  .flatMap(e=>e.inputs).find(r=>r.name===name).value;

test('all reviewed definitions, questions and examples retain their identity', () => {
  assert.match(snapshot.id, /^dashboard:/);
  for (const id of ['metrics','questions','examples']) {
    assert.deepEqual(rows(id).map(r=>r.id), catalog[id].map(r=>r.id));
  }
  assert.equal(rows('metrics').filter(m=>m.origin==='透明派生').length, 12);
  assert.equal(rows('coverage').length, rows('metrics').length * DIMENSIONS.length);
  assert.equal(new Set(rows('coverage').map(c=>`${c.metricId}:${c.dimension}`)).size, rows('coverage').length);
});

test('headline figures reconcile to the reviewed original inputs', () => {
  const real = input('M','GDP实际增速');
  close(rows('growth').reduce((s,r)=>s+r.contribution,0), real);
  const ratio = input('M','2025 GDP现价额（初步）') / input('M','2024 GDP现价额（最终核实）');
  close(rows('money')[1].value, (ratio-1)*100);
  close(rows('nominal')[2].value, (ratio/(1+real/100)-1)*100);
  close(rows('household')[1].value/rows('household')[0].value, 29476/43377);
  assert.equal(rows('industry')[1].change, -0.6);
  for (const id of ['growth','money','nominal','household','industry']) {
    assert.ok(rows(id).every(r=>r.period.startsWith('2025')));
    assert.ok(snapshot.queries[id].source.links.length>0);
  }
});

test('coverage denominator excludes inapplicable dimensions and does not multiply shared questions', () => {
  const cells=coverageCells(rows('frameworks'),rows('coverage'));
  assert.equal(cells.length,49);
  for(const cell of cells) {
    assert.ok(cell.covered <= cell.applicable);
    const metrics=rows('metrics').filter(m=>m.systems.includes(cell.system));
    assert.equal(cell.applicable+cell['不适用'], metrics.length);
  }
  const na=cells.find(c=>c.system==='F' && c.dimension==='居民群体');
  assert.equal(na.applicable,0);
  assert.equal(na.covered,0);
});

test('search aliases, dimension filters, reset and empty results stay consistent', () => {
  assert.deepEqual(filterMetrics(rows('metrics'),{search:'社融'}).map(m=>m.id),['A048','A049']);
  assert.ok(filterMetrics(rows('metrics'),{search:'社零'}).length>0);
  assert.equal(filterMetrics(rows('metrics'),{search:'不存在的指标xyz'}).length,0);
  assert.equal(filterMetrics(rows('metrics'),{}).length,207);
  const selected=filterMetrics(rows('metrics'),{system:'K',dimension:'省级',status:'已覆盖'});
  assert.ok(selected.length>0);
  assert.ok(selected.every(m=>m.systems.includes('K') && m.coverage.find(c=>c.dimension==='省级').status==='已覆盖'));
});

test('CSV contains only filtered records, preserves Chinese and escapes quotes', () => {
  const selected=filterMetrics(rows('metrics'),{search:'社融'}).map(m=>({...m,coverageStatus:'已覆盖',systemsText:m.systems.join('/')}));
  const csv=dictionaryCsv(selected,'全国');
  assert.ok(csv.startsWith('\uFEFF"编号"'));
  assert.equal(csv.split('\r\n').length,3);
  assert.ok(csv.includes('A048') && csv.includes('A049') && !csv.includes('A001'));
  assert.ok(dictionaryCsv([{name:'含"引号"的指标'}],'全国').includes('"含""引号""的指标"'));
});

test('source lineage and all system paths remain usable', () => {
  const sourceIds = new Set(catalog.sources.map(s=>s.id));
  for(const m of rows('metrics')) {
    assert.ok(sourceIds.has(m.source_id));
    assert.match(m.sourceUrl, /^https?:\/\//);
    assert.ok(m.definition && m.source_locator && m.pitfalls);
  }
  for(const f of rows('frameworks')) {
    assert.equal(rows('questions').filter(q=>q.system===f.code).length,4);
    assert.ok(rows('examples').some(e=>e.system===f.code));
  }
});
