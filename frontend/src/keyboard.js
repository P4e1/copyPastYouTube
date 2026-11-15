const RU = [
  ["ё", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "backspace"],
  ["й", "ц", "у", "к", "е", "н", "г", "ш", "щ", "з", "х", "ъ", "\\"],
  ["shift", "ф", "ы", "в", "а", "п", "р", "о", "л", "д", "ж", "э", "shift"],
  ["я", "ч", "с", "м", "и", "т", "ь", "б", "ю", "."],
  ["layout", " ", "layout"],
];

const EN = [
  ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", "backspace"],
  ["q", "w", "e", "r", "t", "y", "u", "i", "o", "p", "[", "]", "\\"],
  ["shift", "a", "s", "d", "f", "g", "h", "j", "k", "l", ";", "'", "shift"],
  ["z", "x", "c", "v", "b", "n", "m", ",", ".", "/"],
  ["layout", " ", "layout"],
];

const SHIFT = {
  "1": "!",
  "2": '"',
  "3": "№",
  "4": ";",
  "5": "%",
  "6": ":",
  "7": "?",
  "8": "*",
  "9": "(",
  "0": ")",
  "-": "_",
  "=": "+",
};

export function keyboardRows(layout) {
  return layout === "en" ? EN : RU;
}

export function toggleLayout(layout) {
  return layout === "ru" ? "en" : "ru";
}

export function applyKey(query, key, shift = false) {
  const text = String(query || "");
  if (key === "backspace") {
    return text.slice(0, -1);
  }
  if (shift && SHIFT[key]) {
    return text + SHIFT[key];
  }
  const char = shift && key.length === 1 ? key.toUpperCase() : key;
  return text + char;
}

export function keyLabel(key, shift = false) {
  if (key === "backspace") {
    return "⌫";
  }
  if (key === "shift") {
    return "⇧";
  }
  if (key === " ") {
    return "";
  }
  if (key === "layout") {
    return "Ctrl + Alt";
  }
  if (shift && SHIFT[key]) {
    return SHIFT[key];
  }
  return shift && key.length === 1 ? key.toUpperCase() : key;
}
