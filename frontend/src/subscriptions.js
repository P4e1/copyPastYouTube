export function subscriptionFeed({ signedIn, channels, videos }) {
  if (!signedIn) {
    return { redirect: "/login", empty: null, items: [] };
  }
  const followed = channels || [];
  const list = videos || [];
  if (followed.length === 0) {
    return { redirect: null, empty: "Подписок пока нет", items: [] };
  }
  if (list.length === 0) {
    return { redirect: null, empty: "Новых видео нет", items: [] };
  }
  return { redirect: null, empty: null, items: list };
}
