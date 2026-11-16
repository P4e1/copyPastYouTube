import assert from "node:assert/strict";
import test from "node:test";

import { subscribeControl } from "./subscribe.js";

test("a viewer cannot subscribe to their own channel", () => {
  assert.equal(subscribeControl({ ownChannel: true, signedIn: true, subscribed: false }), "hidden");
  assert.equal(subscribeControl({ ownChannel: true, signedIn: true, subscribed: true }), "hidden");
  assert.equal(subscribeControl({ ownChannel: false, signedIn: false, subscribed: false }), "signin");
  assert.equal(subscribeControl({ ownChannel: false, signedIn: true, subscribed: true }), "subscribed");
  assert.equal(subscribeControl({ ownChannel: false, signedIn: true, subscribed: false }), "subscribe");
});
