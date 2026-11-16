export const BELL_KEY = "cpy-bells";
export const SEEN_KEY = "cpy-seen-notices";

export function channelBell({ subscribed, ownChannel }) {
  if (!subscribed || ownChannel) {
    return "hidden";
  }
  return "shown";
}

export function bellChoice(level) {
  return level === "none" ? "none" : "all";
}

export function mutedChannelNames(channels, levels) {
  return (channels || [])
    .filter((channel) => bellChoice(levels?.[channel.id]) === "none")
    .map((channel) => channel.name);
}

export function unseenIds(notices, seenIds) {
  const seen = new Set(seenIds || []);
  return (notices || []).filter((item) => !seen.has(item.id)).map((item) => item.id);
}

export function bellBadge(unseen, open) {
  return unseen > 0 && !open;
}

export function settingsBellRows(channels, levels) {
  return (channels || []).map((channel) => ({
    id: channel.id,
    name: channel.name,
    level: bellChoice(levels?.[channel.id]),
  }));
}

export function readBells(storage) {
  try {
    const parsed = JSON.parse(storage.getItem(BELL_KEY) || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

export function writeBell(storage, channelId, level) {
  const next = { ...readBells(storage), [channelId]: bellChoice(level) };
  storage.setItem(BELL_KEY, JSON.stringify(next));
  return next;
}

export function readSeen(storage) {
  try {
    const parsed = JSON.parse(storage.getItem(SEEN_KEY) || "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function rememberSeen(storage, ids) {
  const next = [...new Set([...(readSeen(storage) || []), ...(ids || [])])].slice(-40);
  storage.setItem(SEEN_KEY, JSON.stringify(next));
  return next;
}
