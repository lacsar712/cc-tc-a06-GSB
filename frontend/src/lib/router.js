import { writable } from "svelte/store";

/** 极简 hash 路由：#/ 总表，#/band 琥珀专页，#/logs/<id> 详情。 */
function parseHash() {
  const parts = (location.hash.replace(/^#/, "") || "/").split("/").filter(Boolean);
  if (parts[0] === "band") return { name: "band", params: {} };
  if (parts[0] === "logs" && parts[1]) {
    return { name: "detail", params: { id: Number(parts[1]) } };
  }
  return { name: "list", params: {} };
}

export const route = writable(parseHash());

window.addEventListener("hashchange", () => route.set(parseHash()));
