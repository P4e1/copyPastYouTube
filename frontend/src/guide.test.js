import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import { guideItemActive, guideMode, guideYouLinks, visibleSubscriptions } from "./guide.js";
import { VIDEO_SORTS, channelTab } from "./channel.js";

test("channel videos sort uses the YouTube chips", () => {
  assert.deepEqual(
    VIDEO_SORTS.map((item) => item.label),
    ["Новые", "Популярные", "Старые"],
  );
  assert.deepEqual(
    VIDEO_SORTS.map((item) => item.id),
    ["latest", "popular", "oldest"],
  );
});

test("channel tab query stays on a known tab", () => {
  assert.equal(channelTab("videos"), "videos");
  assert.equal(channelTab("playlists"), "playlists");
  assert.equal(channelTab("nope"), "home");
  assert.equal(channelTab(null), "home");
});

test("closed wide guide stays a narrow icon rail", () => {
  assert.equal(guideMode({ open: true, narrow: false }), "full");
  assert.equal(guideMode({ open: false, narrow: false }), "mini");
  assert.equal(guideMode({ open: true, narrow: true }), "overlay");
  assert.equal(guideMode({ open: false, narrow: true }), "hidden");
  const css = readFileSync(new URL("./styles.css", import.meta.url), "utf8");
  const blocks = [...css.matchAll(/\.shell:not\(\.shell--nav-open\) \.sidebar\s*\{[^}]*\}/g)].map((match) => match[0]);
  assert.ok(blocks.some((block) => /width:\s*72px/.test(block) && !/display:\s*none/.test(block)));
});

test("guide shows the first subscriptions until it is expanded", () => {
  const items = ["a", "b", "c", "d"].map((id) => ({ id }));
  assert.deepEqual(
    visibleSubscriptions(items, false, 3).map((item) => item.id),
    ["a", "b", "c"],
  );
  assert.equal(visibleSubscriptions(items, true, 3).length, 4);
  assert.equal(visibleSubscriptions(items.slice(0, 2), false, 3).length, 2);
});

test("only the matching Вы item is current on a channel tab", () => {
  const links = guideYouLinks({ channel_id: "channel-1" });
  const videos = { pathname: "/channel/channel-1", search: "?tab=videos" };
  assert.equal(guideItemActive(links[3], videos), true);
  assert.equal(guideItemActive(links[0], videos), false);
  assert.equal(guideItemActive(links[2], videos), false);
  assert.equal(guideItemActive(links[1], { pathname: "/history", search: "" }), true);
});

test("signed-in guide points Вы at the channel, history, playlists and videos", () => {
  const links = guideYouLinks({ channel_id: "channel-1" });
  assert.deepEqual(
    links.map((item) => item.label),
    ["Мой канал", "История", "Плейлисты", "Ваши видео"],
  );
  assert.equal(links[0].to, "/channel/channel-1");
  assert.equal(links[1].to, "/history");
  assert.equal(links[2].to, "/channel/channel-1?tab=playlists");
  assert.equal(links[3].to, "/channel/channel-1?tab=videos");
  assert.equal(guideYouLinks(null)[0].to, "/you");
});
