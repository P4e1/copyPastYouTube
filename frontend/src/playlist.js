export function playlistAction(items, videoId) {
  return (items || []).some((item) => item.video_id === videoId) ? "remove" : "add";
}

export function nextPlaylistPosition(items) {
  return (items || []).reduce((max, item) => Math.max(max, Number(item.position) || 0), 0) + 1;
}
