<script>
  import { apiPost } from "../lib/api.js";

  export let refresh;

  let chainage = "";
  let deltaMm = "";
  let error = "";
  let loading = false;

  async function submit() {
    error = "";
    loading = true;
    try {
      const { status, data } = await apiPost("/api/logs", {
        chainage,
        delta_mm: Number(deltaMm),
      });
      if (status !== 201) {
        error = data?.detail || "提交失败";
        return;
      }
      chainage = "";
      deltaMm = "";
      await refresh();
    } catch {
      error = "提交时网络异常";
    } finally {
      loading = false;
    }
  }
</script>

<section>
  <label>里程桩号</label>
  <input placeholder="例如 K20+050" bind:value={chainage} />
  <label>收敛（毫米，可正可负；落入近阈带仍可进队）</label>
  <input type="number" step="0.1" bind:value={deltaMm} />
  <button disabled={loading} on:click={submit}>提交（进入待认领）</button>
  {#if error}<p class="err">{error}</p>{/if}
</section>
