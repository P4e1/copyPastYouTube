export const VIDEO_SORTS = [
  { id: "latest", label: "Новые" },
  { id: "popular", label: "Популярные" },
  { id: "oldest", label: "Старые" },
];

const CHANNEL_TABS = new Set(["home", "videos", "shorts", "playlists"]);

export function channelTab(value) {
  return CHANNEL_TABS.has(value) ? value : "home";
}

export function channelHandle(name) {
  const slug = String(name || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "");
  return `@${slug || "channel"}`;
}

export function filterByTitle(items, query) {
  const needle = String(query || "")
    .trim()
    .toLowerCase();
  if (!needle) {
    return items;
  }
  return items.filter((item) => String(item.title || "").toLowerCase().includes(needle));
}

export function sortChannelVideos(videos, mode) {
  const copy = [...videos];
  if (mode === "popular") {
    return copy.sort((left, right) => (right.view_count || 0) - (left.view_count || 0));
  }
  if (mode === "oldest") {
    return copy.sort((left, right) => String(left.created_at).localeCompare(String(right.created_at)));
  }
  return copy.sort((left, right) => String(right.created_at).localeCompare(String(left.created_at)));
}
