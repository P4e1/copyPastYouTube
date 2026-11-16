export function subscribeControl({ ownChannel, signedIn, subscribed }) {
  if (ownChannel) {
    return "hidden";
  }
  if (!signedIn) {
    return "signin";
  }
  if (subscribed) {
    return "subscribed";
  }
  return "subscribe";
}
