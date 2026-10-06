<script>
  import { onDestroy } from "svelte";
  import { apiGet, apiPut } from "../lib/api.js";
  import { session } from "../lib/session.js";
  import { formatMm, formatTime } from "../lib/verdict.js";

  let band = null;
  let history = [];
  let error = "";
  let saving = false;

  // 编辑表单只对监理渲染；其他角色（含巡检员）只读，后端同样 403 兜底。
  $: isMonitor = $session?.role === "monitor";
  let newInner = "";
  let newOuter = "";
  let note = "";

  async function load() {
    const [b, h] = await Promise.all([apiGet("/api/band"), apiGet("/api/band/history")]);
    if (b.status === 401 || h.status === 401) {
      session.set(null);
      return;
    }
    if (b.ok) band = b.data;
    if (h.ok) history = h.data;
  }

  load();
  const timer = setInterval(load, 5000);
  onDestroy(() => clearInterval(timer));

  async function save() {
    error = "";
    const inner = Number(newInner);
    const outer = Number(newOuter);
    if (!Number.isFinite(inner) || !Number.isFinite(outer)) {
      error = "内缘/外缘必须是数字";
      return;
    }
    if (inner < 0 || outer < 0) {
      error = "内缘/外缘不能为负";
      return;
    }
    if (!(inner < outer)) {
      error = "要求 0 ≤ 内缘 < 外缘";
      return;
    }
    saving = true;
    try {
      const { status, data } = await apiPut("/api/band", {
        inner_mm: inner,
        outer_mm: outer,
        note: note.trim() || null,
      });
      if (status !== 200) {
        error = data?.detail || "改带失败";
        return;
      }
      newInner = "";
      newOuter = "";
      note = "";
      await load();
    } catch {
      error = "改带时网络异常";
    } finally {
      saving = false;
    }
  }

  function oldText(v) {
    return v == null ? "—" : `±${formatMm(v)}`;
  }
</script>

<section>
  <h2>当前判定带</h2>
  {#if band}
    <dl class="info">
      <dt>内缘</dt><dd>±{formatMm(band.inner_mm)} mm（|Δ| ≤ 内缘 为合格）</dd>
      <dt>外缘</dt><dd>±{formatMm(band.outer_mm)} mm（内缘 &lt; |Δ| ≤ 外缘 为近阈，超外缘为超限）</dd>
      <dt>最近更新</dt><dd>{band.updated_by === "system" ? "系统初始化" : band.updated_by} · {formatTime(band.updated_at)}</dd>
    </dl>
  {:else}
    <p class="muted">加载中……</p>
  {/if}
</section>

<section>
  <h2>样例色</h2>
  <span class="swatch tag ok">合格　|Δ| ≤ 内缘</span>
  <span class="swatch tag near">近阈　内缘 &lt; |Δ| ≤ 外缘（可进队）</span>
  <span class="swatch tag bad">超限　|Δ| &gt; 外缘</span>
</section>

{#if isMonitor}
  <section>
    <h2>修改判定带（仅之后新提交的单生效）</h2>
    <p class="muted">已提交/已领走的单据仍按其提交时快照的界判定。</p>
    <label>新内缘（mm）</label>
    <input type="number" step="0.1" bind:value={newInner} placeholder={band ? formatMm(band.inner_mm) : ""} />
    <label>新外缘（mm）</label>
    <input type="number" step="0.1" bind:value={newOuter} placeholder={band ? formatMm(band.outer_mm) : ""} />
    <label>改带备注（可选）</label>
    <input bind:value={note} maxlength="200" placeholder="例如：二期施工收紧" />
    <button disabled={saving} on:click={save}>保存改带</button>
    {#if error}<p class="err">{error}</p>{/if}
  </section>
{:else}
  <section><p class="muted">仅监理可修改判定带；当前账号只读此页。</p></section>
{/if}

<section>
  <h2>改带履历</h2>
  <table>
    <thead>
      <tr><th>时间</th><th>操作人</th><th>原内缘</th><th>新内缘</th><th>原外缘</th><th>新外缘</th><th>备注</th></tr>
    </thead>
    <tbody>
      {#each history as c}
        <tr>
          <td>{formatTime(c.changed_at)}</td>
          <td>{c.changed_by === "system" ? "系统初始化" : c.changed_by}</td>
          <td>{oldText(c.old_inner_mm)}</td>
          <td>±{formatMm(c.new_inner_mm)}</td>
          <td>{oldText(c.old_outer_mm)}</td>
          <td>±{formatMm(c.new_outer_mm)}</td>
          <td>{c.note ?? "—"}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</section>
