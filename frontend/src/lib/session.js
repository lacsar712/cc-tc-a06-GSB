import { writable } from "svelte/store";

const KEY = "tunnel_session";

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY));
  } catch {
    return null;
  }
}

export const session = writable(load());

session.subscribe((value) => {
  if (value) localStorage.setItem(KEY, JSON.stringify(value));
  else localStorage.removeItem(KEY);
});

export const ROLE_NAMES = { writer: "测量员", reader: "巡检员", monitor: "监理" };

export function roleName(s) {
  return s?.role_name || ROLE_NAMES[s?.role] || s?.role || "";
}
