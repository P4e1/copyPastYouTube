export const END_COUNTDOWN_SECONDS = 8;

export function endScreen({ ended, autoplay, hasNext }) {
  if (!ended) {
    return "hidden";
  }
  if (autoplay && hasNext) {
    return "countdown";
  }
  return "replay";
}

export function countdownLeft(total, elapsed) {
  const left = Math.ceil(Number(total) - Number(elapsed));
  return left > 0 ? left : 0;
}
