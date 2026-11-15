import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");

function block(selector) {
  const start = css.indexOf(selector);
  assert.notEqual(start, -1, selector);
  const open = css.indexOf("{", start);
  const close = css.indexOf("}", open);
  return css.slice(open + 1, close);
}

function tokens(body) {
  const found = {};
  for (const match of body.matchAll(/(--[a-z0-9-]+):\s*([^;]+);/g)) {
    found[match[1]] = match[2].trim();
  }
  return found;
}

test("light and dark themes define the same color tokens", () => {
  const light = tokens(block(":root"));
  const dark = tokens(block('html[data-theme="dark"]'));
  assert.deepEqual(Object.keys(light).sort(), Object.keys(dark).sort());
  assert.equal(light["--bg"], "#fff");
  assert.equal(dark["--bg"], "#0f0f0f");
  assert.equal(light["--text"], "#0f0f0f");
  assert.equal(dark["--text"], "#f1f1f1");
  assert.equal(light["--subscribe"], "#0f0f0f");
  assert.equal(dark["--subscribe"], "#f1f1f1");
  assert.equal(light["--chip-on"], "#0f0f0f");
  assert.equal(dark["--chip-on"], "#f1f1f1");
  assert.notEqual(light["--chip"], dark["--chip"]);
});

test("shell, guide and subscribe follow the active theme", () => {
  assert.match(block(".icon-button {"), /color:\s*var\(--text\)/);
  assert.match(block(".sidebar a {"), /color:\s*var\(--text\)/);
  assert.match(block(".logo__svg {"), /fill:\s*var\(--logo\)/);
  assert.match(block("\n.subscribe {"), /background:\s*var\(--subscribe\)/);
  assert.match(block("\n.subscribe {"), /color:\s*var\(--subscribe-text\)/);
  assert.match(block(".action,"), /background:\s*var\(--chip\)/);
  assert.match(block(".filter-chip--on {"), /background:\s*var\(--chip-on\)/);
  assert.doesNotMatch(block('html[data-theme="dark"]'), /icon-button|sidebar a/);
});
