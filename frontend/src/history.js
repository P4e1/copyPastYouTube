export const HISTORY_EMPTY = "В истории просмотра ничего нет";

export function historyView({ signedIn, items }) {
  if (!signedIn) {
    return { redirect: "/login", empty: false, items: [] };
  }
  const list = items || [];
  return { redirect: null, empty: list.length === 0, items: list };
}
