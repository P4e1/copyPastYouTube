export function visibleSubscriptions(items, expanded, limit = 7) {
  if (expanded || items.length <= limit) {
    return items;
  }
  return items.slice(0, limit);
}

export function guideItemActive(item, location) {
  const pathname = location?.pathname || "";
  const tab = new URLSearchParams(location?.search || "").get("tab");
  if (item.id === "videos") {
    return pathname.startsWith("/channel/") && tab === "videos";
  }
  if (item.id === "playlists") {
    return pathname.startsWith("/channel/") && tab === "playlists";
  }
  if (item.id === "channel") {
    return pathname.startsWith("/channel/") && tab !== "videos" && tab !== "playlists";
  }
  if (item.id === "history") {
    return pathname === "/history";
  }
  return false;
}

export function guideYouLinks(account) {
  const channelId = account?.channel_id;
  const channel = channelId ? `/channel/${channelId}` : "/you";
  return [
    { id: "channel", label: "Мой канал", to: channel },
    { id: "history", label: "История", to: "/history" },
    { id: "playlists", label: "Плейлисты", to: channelId ? `${channel}?tab=playlists` : "/you" },
    { id: "videos", label: "Ваши видео", to: channelId ? `${channel}?tab=videos` : "/you" },
  ];
}
