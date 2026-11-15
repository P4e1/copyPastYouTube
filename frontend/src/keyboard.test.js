import assert from "node:assert/strict";
import test from "node:test";

import { applyKey, keyboardRows, toggleLayout } from "./keyboard.js";

test("the on-screen keyboard starts in Russian and switches with Ctrl+Alt", () => {
  assert.equal(keyboardRows("ru")[1][0], "й");
  assert.equal(keyboardRows("en")[1][0], "q");
  assert.equal(toggleLayout("ru"), "en");
  assert.equal(toggleLayout("en"), "ru");
});

test("keys type into the search query the way the YouTube keyboard does", () => {
  assert.equal(applyKey("остров", " "), "остров ");
  assert.equal(applyKey("остров ", "п"), "остров п");
  assert.equal(applyKey("Остров", "backspace"), "Остро");
  assert.equal(applyKey("а", "б", true), "аБ");
  assert.equal(applyKey("", "1", true), "!");
});
