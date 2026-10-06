<script>
  import { classify, effectiveBounds, formatMm, formatTime } from "../lib/verdict.js";
  import VerdictTag from "./VerdictTag.svelte";

  export let logs;
  export let band;
  export let id;

  $: row = logs.find((r) => r.id === id) ?? null;
  $: bounds = row ? effectiveBounds(row, band) : null;
  // 与总表完全同源：done 用存储结论，pending 按行快照预判。
  $: label = row
    ? row.status === "done" && row.verdict
      ? row.verdict
      : classify(row.delta_mm, bounds.inner, bounds.outer)
    : null;
</script>

<section>
  <p><a href="#/">← 返回总表</a></p>
  {#if !row}
    <p class="muted">加载中或单据不存在……</p>
  {:else}
    <h2>单据 #{row.id} 详情</h2>
    <dl class="info">
      <dt>桩号</dt><dd>{row.chainage}</dd>
      <dt>收敛</dt><dd>{row.delta_mm} mm</dd>
      <dt>状态</dt>
      <dd>
        <span class="tag {row.status === 'pending' ? 'pending' : 'ok'}">
          {row.status === "pending" ? "待处理" : "已完成"}
        </span>
      </dd>
      <dt>结论</dt>
      <dd>
        {#if row.status === "done" && row.verdict}
          <VerdictTag label={row.verdict} />
        {:else}
          <VerdictTag label={label} provisional />
        {/if}
      </dd>
      <dt>说明</dt><dd>{row.reason ?? "—"}</dd>
      <dt>提交人</dt><dd>{row.created_by}</dd>
      <dt>提交时间</dt><dd>{formatTime(row.created_at)}</dd>
      <dt>认领时间</dt><dd>{formatTime(row.processed_at)}</dd>
    </dl>

    <!-- 注脚：界、颜色、文字与总表同源（lib/verdict.js + 行快照），不许另写一套。 -->
    {#if bounds.snapshot}
      <p class="footnote">
        注脚：本单提交于 {formatTime(row.created_at)}，按提交时判定带快照
        内缘 ±{formatMm(bounds.inner)} mm、外缘 ±{formatMm(bounds.outer)} mm 判定，
        当前结论：{label}{row.status === "pending" ? "（认领前预判）" : ""}。
        之后改带不影响本单。
      </p>
    {:else}
      <p class="footnote">
        注脚：历史单据无判定带快照，按默认判定带
        内缘 ±{formatMm(bounds.inner)} mm、外缘 ±{formatMm(bounds.outer)} mm 判定，
        当前结论：{label}{row.status === "pending" ? "（认领前预判）" : ""}。
      </p>
    {/if}
  {/if}
</section>
