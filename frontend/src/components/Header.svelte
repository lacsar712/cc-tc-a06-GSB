<script>
  import { roleName, session } from "../lib/session.js";
  import { route } from "../lib/router.js";

  function logout() {
    session.set(null);
    location.hash = "#/";
  }
</script>

<header>
  <h1>隧道收敛测缝台</h1>
  <nav>
    <a href="#/" class={$route.name === "list" || $route.name === "detail" ? "active" : ""}>总表</a>
    <a href="#/band" class={$route.name === "band" ? "active" : ""}>琥珀专页</a>
  </nav>
  <p class="sub">
    已登录：{$session.username}（{roleName($session)}）
    <button class="secondary" on:click={logout} style="margin-left:0.75rem">退出</button>
  </p>
</header>
