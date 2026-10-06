<script>
  let session = null;
  let logs = [];
  let band = null;
  let bandHistory = [];
  let view = "logs";
  let detail = null;
  let loginUser = "surveyor";
  let loginPass = "surv123456";
  let chainage = "";
  let deltaMm = "";
  let innerInput = "";
  let outerInput = "";
  let noteInput = "";
  let error = "";
  let bandError = "";
  let bandMsg = "";
  let loading = false;
  let timer;

  $: isWriter = session?.role === "writer";

  function headers() {
    return session ? { Authorization: "Bearer " + session.token } : {};
  }

  function fmt(n) {
    if (n === null || n === undefined) return "—";
    return Number.isInteger(n) ? n.toFixed(1) : String(n);
  }

  // 总表与详情共用同一套结论→配色映射，保证颜色文字一致
  function verdictClass(v) {
    return v === "合格" ? "ok" : v === "近阈" ? "near" : v === "超限" ? "bad" : "";
  }

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      ...opts,
      headers: { ...(opts.headers || {}), ...headers() },
    });
    if (res.status === 401) {
      logout();
      return null;
    }
    return res;
  }

  async function refresh() {
    if (!session) return;
    const res = await api("/api/logs");
    if (res && res.ok) {
      logs = await res.json();
      if (detail) {
        const fresh = logs.find((r) => r.id === detail.id);
        if (fresh) detail = fresh;
      }
    }
    const b = await api("/api/band");
    if (b && b.ok) band = await b.json();
    if (view === "band") await loadBandHistory();
  }

  async function loadBandHistory() {
    const res = await api("/api/band/history");
    if (res && res.ok) bandHistory = await res.json();
  }

  function gotoBand() {
    view = "band";
    bandError = "";
    bandMsg = "";
    loadBandHistory();
  }

  async function login() {
    error = "";
    loading = true;
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: loginUser, password: loginPass }),
      });
      const data = await res.json();
      if (!res.ok) {
        error = data.detail || "登录失败";
        return;
      }
      session = { token: data.access_token, username: data.username, role: data.role };
      localStorage.setItem("tunnel_session", JSON.stringify(session));
      await refresh();
      timer = setInterval(refresh, 2000);
    } catch {
      error = "无法连接接口";
    } finally {
      loading = false;
    }
  }

  function logout() {
    if (timer) clearInterval(timer);
    session = null;
    logs = [];
    band = null;
    bandHistory = [];
    detail = null;
    view = "logs";
    localStorage.removeItem("tunnel_session");
  }

  async function submit() {
    error = "";
    loading = true;
    try {
      const res = await api("/api/logs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chainage, delta_mm: Number(deltaMm) }),
      });
      if (!res) return;
      const data = await res.json();
      if (!res.ok) {
        error = data.detail || "提交失败";
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

  async function changeBand() {
    bandError = "";
    bandMsg = "";
    loading = true;
    try {
      const res = await api("/api/band", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          inner_mm: Number(innerInput),
          outer_mm: Number(outerInput),
          note: noteInput,
        }),
      });
      if (!res) return;
      const data = await res.json();
      if (!res.ok) {
        bandError = data.detail || "改带失败";
        return;
      }
      band = data;
      bandMsg = `已改带：内缘 ±${fmt(data.inner_mm)} mm、外缘 ±${fmt(data.outer_mm)} mm，仅作用于之后新交的单`;
      innerInput = "";
      outerInput = "";
      noteInput = "";
      await loadBandHistory();
      await refresh();
    } catch {
      bandError = "改带时网络异常";
    } finally {
      loading = false;
    }
  }

  const raw = localStorage.getItem("tunnel_session");
  if (raw) {
    try {
      session = JSON.parse(raw);
      refresh();
      timer = setInterval(refresh, 2000);
    } catch {
      localStorage.removeItem("tunnel_session");
    }
  }
</script>

<style>
  :global(body) {
    margin: 0;
    font-family: "Segoe UI", system-ui, sans-serif;
    background: #1c1917;
    color: #f5f5f4;
  }
  main { max-width: 960px; margin: 0 auto; padding: 1.5rem; }
  h1 { color: #fbbf24; margin: 0 0 0.25rem; }
  h2 { font-size: 1.05rem; margin: 0 0 0.6rem; color: #fcd34d; }
  .sub { color: #a8a29e; margin-bottom: 1.25rem; }
  section {
    background: #292524; border: 1px solid #44403c; border-radius: 8px;
    padding: 1rem 1.25rem; margin-bottom: 1rem;
  }
  label { display: block; font-size: 0.85rem; color: #d6d3d1; margin-bottom: 0.25rem; }
  input {
    width: 100%; box-sizing: border-box; padding: 0.5rem 0.65rem; border-radius: 6px;
    border: 1px solid #57534e; background: #0c0a09; color: #fafaf9; margin-bottom: 0.75rem;
  }
  button {
    cursor: pointer; padding: 0.5rem 1rem; border: none; border-radius: 6px;
    background: #d97706; color: #fff; font-weight: 600;
  }
  button.secondary { background: #57534e; }
  button.nav { background: #44403c; }
  button.nav.active { background: #d97706; }
  .topbar { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
  .topbar nav { display: flex; gap: 0.4rem; }
  .topbar .who { margin-left: auto; color: #a8a29e; font-size: 0.85rem; }
  .err { color: #fb7185; }
  .okmsg { color: #86efac; }
  .hint { color: #a8a29e; font-size: 0.8rem; margin-bottom: 0; }
  table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
  th, td { text-align: left; padding: 0.45rem; border-bottom: 1px solid #44403c; }
  tbody tr { cursor: pointer; }
  tbody tr:hover { background: #322e2b; }
  .tag { padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.8rem; white-space: nowrap; }
  .ok { background: #14532d; color: #86efac; }
  .near { background: #78350f; color: #fbbf24; }
  .bad { background: #7f1d1d; color: #fca5a5; }
  .pending { background: #44403c; color: #d6d3d1; }
  .edges { display: flex; gap: 1rem; margin: 0.75rem 0; }
  .edges > div {
    flex: 1; background: #1c1917; border: 1px solid #57534e; border-radius: 8px;
    padding: 0.6rem 0.9rem; display: flex; flex-direction: column; gap: 0.2rem;
  }
  .edges span { font-size: 0.8rem; color: #a8a29e; }
  .edges strong { font-size: 1.2rem; color: #fbbf24; }
  .strip { display: flex; height: 2rem; border-radius: 6px; overflow: hidden; margin-top: 0.75rem; }
  .seg {
    display: flex; align-items: center; justify-content: center;
    font-size: 0.8rem; font-weight: 600; flex: 1;
  }
  .seg.ok { flex: 2; }
  .scale {
    display: flex; justify-content: space-between;
    color: #a8a29e; font-size: 0.75rem; margin-top: 0.25rem;
  }
  .samples { display: flex; gap: 0.6rem; align-items: center; margin-top: 0.75rem; }
  .overlay {
    position: fixed; inset: 0; background: rgba(0, 0, 0, 0.65);
    display: flex; align-items: center; justify-content: center; padding: 1rem; z-index: 10;
  }
  .detail { max-width: 540px; width: 100%; margin-bottom: 0; }
  .detail p { margin: 0.35rem 0; }
  .foot {
    border-top: 1px dashed #57534e; padding-top: 0.55rem;
    color: #fbbf24; font-size: 0.85rem;
  }
  .meta { color: #a8a29e; font-size: 0.8rem; }
</style>

<main>
  <h1>隧道收敛测缝台</h1>
  {#if !session}
    <p class="sub">测量员提交桩号与收敛毫米值，接口进程内线程认领后出结论。登录框已预填可写账号 surveyor / surv123456。</p>
    <section>
      <label>用户名</label>
      <input bind:value={loginUser} autocomplete="off" />
      <label>密码</label>
      <input type="password" bind:value={loginPass} autocomplete="off" />
      <button disabled={loading} on:click={login}>登录</button>
      {#if error}<p class="err">{error}</p>{/if}
    </section>
  {:else}
    <section class="topbar">
      <nav>
        <button class="nav {view === 'logs' ? 'active' : ''}" on:click={() => (view = "logs")}>总表</button>
        <button class="nav {view === 'band' ? 'active' : ''}" on:click={gotoBand}>琥珀专页</button>
      </nav>
      <span class="who">已登录：{session.username}（{isWriter ? "可提交" : "只读"}）</span>
      <button class="secondary" disabled={loading} on:click={refresh}>刷新列表</button>
      <button class="secondary" on:click={logout}>退出</button>
    </section>

    {#if view === "logs"}
      {#if isWriter}
        <section>
          <label>里程桩号</label>
          <input placeholder="例如 K20+050" bind:value={chainage} />
          <label>收敛（毫米，可正可负）</label>
          <input type="number" step="0.1" bind:value={deltaMm} />
          <button disabled={loading} on:click={submit}>提交（进入待认领）</button>
          {#if error}<p class="err">{error}</p>{/if}
          {#if band}
            <p class="hint">
              当前判定界：合格 ±{fmt(band.inner_mm)} mm；琥珀近阈区 {fmt(band.inner_mm)}~{fmt(band.outer_mm)} mm 仍可进队、标近阈；超出外缘 ±{fmt(band.outer_mm)} mm 才算超限。
            </p>
          {/if}
        </section>
      {/if}
      <section>
        <table>
          <thead>
            <tr><th>编号</th><th>桩号</th><th>收敛mm</th><th>状态</th><th>结论</th><th>说明</th></tr>
          </thead>
          <tbody>
            {#each logs as row}
              <tr on:click={() => (detail = row)}>
                <td>{row.id}</td>
                <td>{row.chainage}</td>
                <td>{row.delta_mm}</td>
                <td><span class="tag {row.status === 'pending' ? 'pending' : 'ok'}">{row.status === 'pending' ? '待处理' : '已完成'}</span></td>
                <td>
                  {#if row.verdict}
                    <span class="tag {verdictClass(row.verdict)}">{row.verdict}</span>
                  {:else}—{/if}
                </td>
                <td>{row.reason ?? "—"}</td>
              </tr>
            {/each}
          </tbody>
        </table>
        <p class="hint">点击行查看详情；总表着色与详情注脚使用同一套判定界（领走时快照）。</p>
      </section>
    {:else}
      <section>
        <h2>琥珀近阈带</h2>
        {#if band}
          <p class="sub" style="margin-bottom:0.5rem">
            合格带 ±{fmt(band.inner_mm)} mm 之外再画一条琥珀近阈区，方便监理盯边墙：落入琥珀区仍可进队、标近阈；超出外缘 ±{fmt(band.outer_mm)} mm 才算超限。
          </p>
          <div class="edges">
            <div><span>内缘（合格带边界）</span><strong>±{fmt(band.inner_mm)} mm</strong></div>
            <div><span>外缘（超限起算线）</span><strong>±{fmt(band.outer_mm)} mm</strong></div>
          </div>
          <div class="strip">
            <div class="seg bad">超限</div>
            <div class="seg near">近阈</div>
            <div class="seg ok">合格</div>
            <div class="seg near">近阈</div>
            <div class="seg bad">超限</div>
          </div>
          <div class="scale">
            <span>−{fmt(band.outer_mm)}</span>
            <span>−{fmt(band.inner_mm)}</span>
            <span>0</span>
            <span>+{fmt(band.inner_mm)}</span>
            <span>+{fmt(band.outer_mm)}</span>
          </div>
          <div class="samples">
            <span class="hint" style="margin:0">样例色：</span>
            <span class="tag ok">合格</span>
            <span class="tag near">近阈</span>
            <span class="tag bad">超限</span>
          </div>
        {:else}
          <p class="sub">尚未设置琥珀带。</p>
        {/if}
      </section>

      {#if isWriter}
        <section>
          <h2>改带（仅测量员）</h2>
          <label>内缘（合格带 ±mm）</label>
          <input type="number" step="0.1" bind:value={innerInput} placeholder={band ? String(band.inner_mm) : "3.0"} />
          <label>外缘（琥珀区上限 ±mm）</label>
          <input type="number" step="0.1" bind:value={outerInput} placeholder={band ? String(band.outer_mm) : "3.4"} />
          <label>备注（可选）</label>
          <input bind:value={noteInput} placeholder="例如：二衬浇筑后收紧外缘" />
          <button disabled={loading} on:click={changeBand}>提交改带</button>
          {#if bandError}<p class="err">{bandError}</p>{/if}
          {#if bandMsg}<p class="okmsg">{bandMsg}</p>{/if}
          <p class="hint">改带只作用于之后新交的单；已领走的单据仍按领走时快照的琥珀界判定与展示。</p>
        </section>
      {:else}
        <section>
          <p class="hint" style="margin:0">巡检员只读，不能改带。</p>
        </section>
      {/if}

      <section>
        <h2>改带履历</h2>
        <table>
          <thead>
            <tr><th>时间</th><th>内缘</th><th>外缘</th><th>操作人</th><th>备注</th></tr>
          </thead>
          <tbody>
            {#each bandHistory as b}
              <tr style="cursor:default">
                <td>{b.changed_at ? new Date(b.changed_at).toLocaleString() : "—"}</td>
                <td>±{fmt(b.inner_mm)}</td>
                <td>±{fmt(b.outer_mm)}</td>
                <td>{b.changed_by}</td>
                <td>{b.note ?? "—"}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </section>
    {/if}
  {/if}

  {#if detail}
    <!-- svelte-ignore a11y-click-events-have-key-events a11y-no-static-element-interactions -->
    <div class="overlay" on:click|self={() => (detail = null)}>
      <section class="detail">
        <h2>单据详情 #{detail.id}</h2>
        <p>桩号：{detail.chainage}</p>
        <p>收敛：{detail.delta_mm} mm</p>
        <p>状态：<span class="tag {detail.status === 'pending' ? 'pending' : 'ok'}">{detail.status === 'pending' ? '待处理' : '已完成'}</span></p>
        <p>
          结论：
          {#if detail.verdict}
            <span class="tag {verdictClass(detail.verdict)}">{detail.verdict}</span>
          {:else}—{/if}
        </p>
        <p>说明：{detail.reason ?? "—"}</p>
        <p class="foot">
          {#if detail.band_inner_mm !== null && detail.band_inner_mm !== undefined}
            判定界（领走时快照）：内缘 ±{fmt(detail.band_inner_mm)} mm、外缘 ±{fmt(detail.band_outer_mm)} mm；改带不追溯。
          {:else if detail.status === "pending"}
            判定界：待认领，领走时快照当时的琥珀界。
          {:else}
            判定界：改带功能前的老单据，无快照，以说明文字为准。
          {/if}
        </p>
        <p class="meta">提交人 {detail.created_by} · {detail.created_at ? new Date(detail.created_at).toLocaleString() : "—"}</p>
        <button class="secondary" on:click={() => (detail = null)}>关闭</button>
      </section>
    </div>
  {/if}
</main>
