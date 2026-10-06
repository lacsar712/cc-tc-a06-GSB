/**
 * 全前端唯一的判定界/颜色/文字真源。
 * 总表徽章、详情徽章与注脚、琥珀专页样例色全部只能走这里，
 * 不允许在组件里再写第二处 “=== '合格'” 判定。
 */
export const DEFAULT_INNER = 3.0;
export const DEFAULT_OUTER = 3.4;

export const LABEL = { OK: "合格", NEAR: "近阈", OVER: "超限" };

/** 最多两位小数、去尾零：3.0 -> '3'，3.40 -> '3.4'，与后端 rules._mm 同规则。 */
export function formatMm(x) {
  return Number(Number(x).toFixed(2)).toString();
}

/** 与后端 rules.classify 完全同边界：<= 内缘合格，<= 外缘近阈，否则超限。 */
export function classify(delta, inner = DEFAULT_INNER, outer = DEFAULT_OUTER) {
  const absolute = Math.abs(Number(delta));
  if (absolute <= Number(inner)) return LABEL.OK;
  if (absolute <= Number(outer)) return LABEL.NEAR;
  return LABEL.OVER;
}

/** 结论文字 -> 全局颜色 class（app.css 中唯一定义）。 */
export function verdictClass(label) {
  return { 合格: "ok", 近阈: "near", 超限: "bad" }[label] || "bad";
}

/**
 * 一行单据生效的判定界：行快照优先（提交时冻结），
 * 历史空快照回退当前配置，再回退默认常量。
 */
export function effectiveBounds(row, band) {
  const hasSnapshot = row.band_inner_mm != null && row.band_outer_mm != null;
  return {
    inner: hasSnapshot ? row.band_inner_mm : band?.inner_mm ?? DEFAULT_INNER,
    outer: hasSnapshot ? row.band_outer_mm : band?.outer_mm ?? DEFAULT_OUTER,
    snapshot: hasSnapshot,
  };
}

/** ISO 时间 -> 'YYYY-MM-DD HH:MM'（仅展示）。 */
export function formatTime(iso) {
  if (!iso) return "—";
  return iso.replace("T", " ").slice(0, 16);
}
