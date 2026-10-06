<script>
  import { classify, effectiveBounds } from "../lib/verdict.js";
  import VerdictTag from "./VerdictTag.svelte";

  export let logs;
  export let band;
</script>

<section>
  <table>
    <thead>
      <tr><th>编号</th><th>桩号</th><th>收敛mm</th><th>状态</th><th>结论</th><th>说明</th></tr>
    </thead>
    <tbody>
      {#each logs as row}
        {@const bounds = effectiveBounds(row, band)}
        <tr>
          <td><a href="#/logs/{row.id}">{row.id}</a></td>
          <td>{row.chainage}</td>
          <td>{row.delta_mm}</td>
          <td>
            <span class="tag {row.status === 'pending' ? 'pending' : 'ok'}">
              {row.status === "pending" ? "待处理" : "已完成"}
            </span>
          </td>
          <td>
            {#if row.status === "done" && row.verdict}
              <VerdictTag label={row.verdict} />
            {:else}
              <!-- pending：按本单提交时快照预判，认领后与存储结论必然一致 -->
              <VerdictTag label={classify(row.delta_mm, bounds.inner, bounds.outer)} provisional />
            {/if}
          </td>
          <td>{row.reason ?? "—"}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</section>
