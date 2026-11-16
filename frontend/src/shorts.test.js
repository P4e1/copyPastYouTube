import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { shortsFrame } from "./shorts.js";

test("shorts stays an empty vertical stage", () => {
  assert.deepEqual(shortsFrame(), { empty: "Смотреть пока нечего", vertical: true });
  const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
  const stage = css.match(/\.shorts__stage\s*\{[^}]*\}/)[0];
  assert.match(stage, /aspect-ratio:\s*9 \/ 16/);
  const app = readFileSync(new URL("./App.jsx", import.meta.url), "utf8");
  assert.match(app, /path="\/shorts" element={<ShortsPage \/>}/);
});
