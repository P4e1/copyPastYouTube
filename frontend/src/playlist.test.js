import assert from "node:assert/strict";
import test from "node:test";

import { nextPlaylistPosition, playlistAction } from "./playlist.js";

test("a video already in a playlist is removed instead of added again", () => {
  const items = [
    { video_id: "one", position: 1 },
    { video_id: "two", position: 4 },
  ];
  assert.equal(playlistAction(items, "two"), "remove");
  assert.equal(playlistAction(items, "three"), "add");
  assert.equal(playlistAction([], "three"), "add");
  assert.equal(nextPlaylistPosition(items), 5);
});
