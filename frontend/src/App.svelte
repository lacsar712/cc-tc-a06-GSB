<script>
  import { onDestroy } from "svelte";
  import { apiGet } from "./lib/api.js";
  import { route } from "./lib/router.js";
  import { session } from "./lib/session.js";
  import Header from "./components/Header.svelte";
  import Login from "./components/Login.svelte";
  import SubmitForm from "./components/SubmitForm.svelte";
  import LogTable from "./components/LogTable.svelte";
  import LogDetail from "./components/LogDetail.svelte";
  import BandPage from "./components/BandPage.svelte";

  let logs = [];
  let band = null;
  let timer = null;

  $: isWriter = $session?.role === "writer";
  $: loggedIn = !!$session;

  async function refresh() {
    if (!$session) return;
    const res = await apiGet("/api/logs");
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) logs = res.data;
  }

  async function refreshBand() {
    if (!$session) return;
    const res = await apiGet("/api/band");
    if (res.status === 401) {
      logout();
      return;
    }
    if (res.ok) band = res.data;
  }

  function logout() {
    if (timer) clearInterval(timer);
    timer = null;
    logs = [];
    band = null;
    session.set(null);
  }

  // 登录态变化时启动/停止轮询；日志 2s（pending 预判依赖），判定带 10s。
  $: if (loggedIn && timer === null) {
    refresh();
    refreshBand();
    timer = setInterval(() => {
      refresh();
      refreshBand();
    }, 2000);
  }
  $: if (!loggedIn && timer !== null) {
    clearInterval(timer);
    timer = null;
  }

  onDestroy(() => timer && clearInterval(timer));
</script>

<main>
  {#if !loggedIn}
    <h1>隧道收敛测缝台</h1>
    <Login />
  {:else}
    <Header />
    {#if $route.name === "band"}
      <BandPage />
    {:else if $route.name === "detail"}
      <LogDetail {logs} {band} id={$route.params.id} />
    {:else}
      {#if isWriter}
        <SubmitForm refresh={refresh} />
      {/if}
      <LogTable {logs} {band} />
    {/if}
  {/if}
</main>
