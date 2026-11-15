import assert from "node:assert/strict";
import test from "node:test";

import { channelHandle, filterByTitle, sortChannelVideos } from "./channel.js";

const videos = [
  { id: "a", title: "Утро на канале", view_count: 1, created_at: "2026-11-15T12:00:00Z" },
  { id: "b", title: "Второй ролик", view_count: 9, created_at: "2026-11-15T13:00:00Z" },
  { id: "c", title: "Ролик соседа", view_count: 3, created_at: "2026-11-14T13:00:00Z" },
];

test("channel handle is the name with @ and without spaces", () => {
  assert.equal(channelHandle("author-one"), "@author-one");
  assert.equal(channelHandle("Author One"), "@authorone");
  assert.equal(channelHandle("  "), "@channel");
});

test("channel search matches the title and ignores case", () => {
  assert.deepEqual(
    filterByTitle(videos, "ролик").map((item) => item.id),
    ["b", "c"],
  );
  assert.deepEqual(filterByTitle(videos, "   "), videos);
});

test("channel video sort follows the YouTube menu", () => {
  assert.deepEqual(
    sortChannelVideos(videos, "latest").map((item) => item.id),
    ["b", "a", "c"],
  );
  assert.deepEqual(
    sortChannelVideos(videos, "popular").map((item) => item.id),
    ["b", "c", "a"],
  );
  assert.deepEqual(
    sortChannelVideos(videos, "oldest").map((item) => item.id),
    ["c", "a", "b"],
  );
});
