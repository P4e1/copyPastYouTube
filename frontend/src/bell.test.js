import assert from "node:assert/strict";
import test from "node:test";

import { bellBadge, bellChoice, channelBell, mutedChannelNames, unseenIds } from "./bell.js";
import { subscriptionNotices } from "./settings.js";

test("a subscribed channel can mute its own bell", () => {
  assert.equal(channelBell({ subscribed: false, ownChannel: false }), "hidden");
  assert.equal(channelBell({ subscribed: true, ownChannel: true }), "hidden");
  assert.equal(channelBell({ subscribed: true, ownChannel: false }), "shown");
  assert.equal(bellChoice("none"), "none");
  assert.equal(bellChoice("all"), "all");
  assert.equal(bellChoice(undefined), "all");
  const channels = [
    { id: "a", name: "author-one" },
    { id: "b", name: "author-two" },
  ];
  assert.deepEqual(mutedChannelNames(channels, { a: "none" }), ["author-one"]);
  const feed = [
    { id: "1", title: "Утро", channel_name: "author-one" },
    { id: "2", title: "Сосед", channel_name: "author-two" },
  ];
  assert.deepEqual(subscriptionNotices(feed, ["author-one", "author-two"], true, ["author-one"]), [feed[1]]);
  assert.deepEqual(unseenIds(feed, ["1"]), ["2"]);
  assert.equal(bellBadge(1, false), true);
  assert.equal(bellBadge(1, true), false);
  assert.equal(bellBadge(0, false), false);
});
