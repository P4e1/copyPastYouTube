export function formatDuration(seconds) {
  const total = Math.max(0, Number(seconds) || 0);
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const rest = total % 60;
  const pad = (value) => String(value).padStart(2, "0");
  if (hours > 0) {
    return `${hours}:${pad(minutes)}:${pad(rest)}`;
  }
  return `${minutes}:${pad(rest)}`;
}

function whole(count) {
  return Math.max(0, Math.trunc(Number(count) || 0));
}

function plural(value, one, few, many) {
  const mod10 = value % 10;
  const mod100 = value % 100;
  if (mod10 === 1 && mod100 !== 11) {
    return one;
  }
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) {
    return few;
  }
  return many;
}

export function formatGrouped(count) {
  return String(whole(count)).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00a0");
}

function compactNumber(raw) {
  const rounded = raw >= 10 ? Math.round(raw) : Math.round(raw * 10) / 10;
  return String(rounded).replace(".", ",").replace(",0", "");
}

export function formatCompact(count) {
  const value = whole(count);
  if (value < 1000) {
    return formatGrouped(value);
  }
  if (value < 1_000_000) {
    return `${compactNumber(value / 1000)} тыс.`;
  }
  if (value < 1_000_000_000) {
    return `${compactNumber(value / 1_000_000)} млн`;
  }
  return `${compactNumber(value / 1_000_000_000)} млрд`;
}

export function formatViews(count) {
  const value = whole(count);
  return `${formatGrouped(value)} ${plural(value, "просмотр", "просмотра", "просмотров")}`;
}

export function formatViewLine(count) {
  const value = whole(count);
  if (value < 1000) {
    return formatViews(value);
  }
  return `${formatCompact(value)} просмотров`;
}

export function formatVideoCount(count) {
  const value = whole(count);
  if (value >= 1000) {
    return `${formatCompact(value)} видео`;
  }
  return `${formatGrouped(value)} видео`;
}

export function formatSubscribers(count) {
  const value = whole(count);
  if (value >= 1000) {
    return `${formatCompact(value)} подписчиков`;
  }
  return `${formatGrouped(value)} ${plural(value, "подписчик", "подписчика", "подписчиков")}`;
}

export function formatAgo(iso, now = Date.now()) {
  if (!iso) {
    return "";
  }
  const time = new Date(iso).getTime();
  if (Number.isNaN(time)) {
    return "";
  }
  const seconds = Math.max(0, Math.round((now - time) / 1000));
  if (seconds < 60) {
    return "только что";
  }
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) {
    return `${minutes} мин. назад`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours} ч назад`;
  }
  const days = Math.floor(hours / 24);
  if (days < 30) {
    return `${days} дн. назад`;
  }
  const months = Math.floor(days / 30);
  if (months < 12) {
    return `${months} мес. назад`;
  }
  return `${Math.max(1, Math.floor(days / 365))} г. назад`;
}

export function formatDate(iso) {
  if (!iso) {
    return "";
  }
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return "";
  }
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "short", year: "numeric" });
}
