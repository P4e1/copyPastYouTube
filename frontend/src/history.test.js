import assert from "node:assert/strict";
import test from "node:test";

import { historyView } from "./history.js";

test("history sends a guest to login and lists watched videos for a signed-in viewer", () => {
  assert.deepEqual(historyView({ signedIn: false, items: [{ id: "a" }] }), {
    redirect: "/login",
    empty: false,
    items: [],
  });
  assert.deepEqual(historyView({ signedIn: true, items: [] }), {
    redirect: null,
    empty: true,
    items: [],
  });
  const items = [{ id: "new" }, { id: "old" }];
  assert.deepEqual(historyView({ signedIn: true, items }), {
    redirect: null,
    empty: false,
    items,
  });
});
