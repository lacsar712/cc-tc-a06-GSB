<script>
  import { apiPost } from "../lib/api.js";
  import { session } from "../lib/session.js";

  let loginUser = "surveyor";
  let loginPass = "surv123456";
  let error = "";
  let loading = false;

  async function login() {
    error = "";
    loading = true;
    try {
      const { status, data } = await apiPost("/api/auth/login", {
        username: loginUser,
        password: loginPass,
      });
      if (status !== 200 || !data?.access_token) {
        error = data?.detail || "登录失败";
        return;
      }
      session.set({
        token: data.access_token,
        username: data.username,
        role: data.role,
        role_name: data.role_name,
      });
    } catch {
      error = "无法连接接口";
    } finally {
      loading = false;
    }
  }
</script>

<p class="sub">
  测量员提交桩号与收敛毫米值，接口进程内线程认领后按判定带出结论；落在近阈琥珀带仍可进队，超外缘才算超限。
  账号：surveyor 测量员 / inspector 巡检员（只读）/ monitor 监理（可改带）。
</p>
<section>
  <label>用户名</label>
  <input bind:value={loginUser} autocomplete="off" />
  <label>密码</label>
  <input type="password" bind:value={loginPass} autocomplete="off" on:keydown={(e) => e.key === "Enter" && login()} />
  <button disabled={loading} on:click={login}>登录</button>
  {#if error}<p class="err">{error}</p>{/if}
</section>
