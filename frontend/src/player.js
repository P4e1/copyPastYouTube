import { formatDuration } from "./format.js";

export const PLAYBACK_RATES = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2];

export function formatPlayerClock(seconds) {
  return formatDuration(Math.floor(Math.max(0, Number(seconds) || 0)));
}

function spoken(seconds) {
  const total = Math.max(0, Math.floor(Number(seconds) || 0));
  const hours = Math.floor(total / 3600);
  const minutes = Math.floor((total % 3600) / 60);
  const rest = total % 60;
  const parts = [];
  if (hours > 0) {
    parts.push(`${hours} ч.`);
    parts.push(`${minutes} мин.`);
  } else if (minutes > 0) {
    parts.push(`${minutes} мин.`);
  }
  parts.push(`${rest} сек.`);
  return parts.join(" ");
}

export function formatPlayerTimeLabel(current, duration) {
  return `${spoken(current)} (общая длительность ${spoken(duration)})`;
}

export function seekToRatio(ratio, duration) {
  const length = Math.max(0, Number(duration) || 0);
  const clamped = Math.min(1, Math.max(0, Number(ratio) || 0));
  return clamped * length;
}

export function bufferedFraction(ranges, current, duration) {
  const length = Number(duration) || 0;
  if (length <= 0) {
    return 0;
  }
  const time = Number(current) || 0;
  let end = 0;
  for (const [start, stop] of ranges) {
    if (time >= start && time <= stop) {
      end = Math.max(end, stop);
    }
  }
  return Math.min(1, Math.max(0, end / length));
}

export function rateLabel(rate) {
  if (rate === 1) {
    return "Обычная";
  }
  return String(rate).replace(".", ",");
}
