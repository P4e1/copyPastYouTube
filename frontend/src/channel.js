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
