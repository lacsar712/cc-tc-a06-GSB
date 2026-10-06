<script>
  import { verdictClass } from "../lib/verdict.js";

  // 唯一的结论徽章：颜色只来自 verdictClass，文字即三档结论本身。
  // provisional=true 用于 pending 行按行快照预判（认领后会被存储结论替换）。
  export let label;
  export let provisional = false;
</script>

<span class="tag {verdictClass(label)}">
  {label}{#if provisional}<small>预判</small>{/if}
</span>
