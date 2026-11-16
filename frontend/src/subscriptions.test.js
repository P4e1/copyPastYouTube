import assert from "node:assert/strict";
import test from "node:test";

import { subscriptionFeed } from "./subscriptions.js";

test("subscription page sends a guest to login and shows videos of followed channels", () => {
  assert.deepEqual(subscriptionFeed({ signedIn: false, channels: [{ id: "c" }], videos: [{ id: "v" }] }), {
    redirect: "/login",
    empty: null,
    items: [],
  });
  assert.deepEqual(subscriptionFeed({ signedIn: true, channels: [], videos: [] }), {
    redirect: null,
    empty: "Подписок пока нет",
    items: [],
  });
  assert.deepEqual(subscriptionFeed({ signedIn: true, channels: [{ id: "c" }], videos: [] }), {
    redirect: null,
    empty: "Новых видео нет",
    items: [],
  });
  const videos = [{ id: "new" }, { id: "old" }];
  assert.deepEqual(subscriptionFeed({ signedIn: true, channels: [{ id: "c" }], videos }), {
    redirect: null,
    empty: null,
    items: videos,
  });
});
