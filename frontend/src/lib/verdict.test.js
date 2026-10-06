import { test } from "node:test";
import assert from "node:assert/strict";
import { classify, verdictClass, effectiveBounds, formatMm, DEFAULT_INNER, DEFAULT_OUTER, LABEL } from "./verdict.js";

test("默认 3.0–3.4 边界：合格/近阈/超限", () => {
  const cases = [
    [0.0, LABEL.OK],
    [3.0, LABEL.OK],
    [-3.0, LABEL.OK],
    [3.2, LABEL.NEAR],
    [-3.2, LABEL.NEAR],
    [3.4, LABEL.NEAR],
    [-3.4, LABEL.NEAR],
    [3.4000001, LABEL.OVER],
    [3.8, LABEL.OVER],
    [-3.8, LABEL.OVER],
  ];
  for (const [delta, expected] of cases) {
    assert.equal(classify(delta, DEFAULT_INNER, DEFAULT_OUTER), expected, `${delta} -> ${expected}`);
  }
});

test("自定义带", () => {
  assert.equal(classify(3.7, 3.5, 4.0), LABEL.NEAR);
  assert.equal(classify(3.2, 3.5, 4.0), LABEL.OK);
  assert.equal(classify(4.1, 3.5, 4.0), LABEL.OVER);
});

test("verdictClass 三档映射", () => {
  assert.equal(verdictClass("合格"), "ok");
  assert.equal(verdictClass("近阈"), "near");
  assert.equal(verdictClass("超限"), "bad");
});

test("effectiveBounds：行快照优先，空快照回退当前配置，再回退默认", () => {
  assert.deepEqual(effectiveBounds({ band_inner_mm: 3.0, band_outer_mm: 3.4 }, { inner_mm: 4, outer_mm: 5 }), {
    inner: 3.0,
    outer: 3.4,
    snapshot: true,
  });
  assert.deepEqual(effectiveBounds({ band_inner_mm: null, band_outer_mm: null }, { inner_mm: 4, outer_mm: 5 }), {
    inner: 4,
    outer: 5,
    snapshot: false,
  });
  assert.deepEqual(effectiveBounds({}, null), { inner: 3.0, outer: 3.4, snapshot: false });
});

test("formatMm 去尾零", () => {
  assert.equal(formatMm(3.0), "3");
  assert.equal(formatMm(3.4), "3.4");
  assert.equal(formatMm(3.25), "3.25");
  assert.equal(formatMm(3.39999999999), "3.4");
});
