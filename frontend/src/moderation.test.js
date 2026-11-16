import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { moderationEntry } from "./moderation.js";

test("moderation is in the account menu for a moderator", () => {
  assert.equal(moderationEntry("user"), "hidden");
  assert.equal(moderationEntry("moderator"), "shown");
  assert.equal(moderationEntry("admin"), "shown");
  const shell = readFileSync(new URL("./components/AppShell.jsx", import.meta.url), "utf8");
  const page = readFileSync(new URL("./pages/ModerationPage.jsx", import.meta.url), "utf8");
  assert.match(shell, /moderationEntry/);
  assert.match(shell, /to="\/moderation"/);
  assert.match(page, /moderation-card/);
  assert.match(page, /Скрыть/);
});
