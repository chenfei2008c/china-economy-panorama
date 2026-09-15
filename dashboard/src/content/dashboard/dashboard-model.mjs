// Display transformations only. No observations or economic scores are estimated here.
export const DIMENSIONS = ['全国', '省级', '地级', '行业', '企业类型', '居民群体', '机构部门'];
export const STATUSES = ['已覆盖', '部分覆盖', '无稳定公开数据', '不适用'];

export function filterMetrics(metrics, {system = 'all', dimension = '全国', status = 'all', search = ''}) {
  const term = search.trim().toLowerCase()
    .replaceAll('社融', '社会融资').replaceAll('社零', '社会消费品零售');
  return metrics.filter(m =>
    (system === 'all' || m.systems.includes(system)) &&
    (!term || `${m.id} ${m.name} ${m.module} ${m.definition}`.toLowerCase().includes(term)) &&
    (status === 'all' || m.coverage.find(c => c.dimension === dimension)?.status === status));
}

export function coverageCells(frameworks, coverage) {
  return frameworks.flatMap(f => DIMENSIONS.map(d => {
    const rows = coverage.filter(c => c.systems.includes(f.code) && c.dimension === d);
    const counts = Object.fromEntries(STATUSES.map(s => [s, rows.filter(c => c.status === s).length]));
    return {
      system: f.code, dimension: d, ...counts,
      covered: counts['已覆盖'] + counts['部分覆盖'],
      applicable: rows.length - counts['不适用'],
    };
  }));
}

export function dictionaryCsv(rows, dimension) {
  const headers = ['编号', '指标名称', '性质', '单位', '频率', `${dimension}覆盖状态`, '对应体系', '原始来源'];
  const quote = value => `"${String(value ?? '').replaceAll('"', '""')}"`;
  const records = rows.map(m => [m.id, m.name, m.origin, m.unit, m.frequency, m.coverageStatus, m.systemsText, m.sourceUrl]);
  return '\uFEFF' + [headers, ...records].map(r => r.map(quote).join(',')).join('\r\n');
}
