import { useEffect, useState } from "react";

import { api } from "../api/client";
import { VideoCard } from "../components/VideoCard";

export function HomePage() {
  const [items, setItems] = useState(null);

  useEffect(() => {
    let active = true;
    api("/feed")
      .then((data) => {
        if (active) {
          setItems(data.items);
        }
      })
      .catch(() => {
        if (active) {
          setItems([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  if (items === null) {
    return null;
  }
  if (items.length === 0) {
    return (
      <section className="empty">
        <h1>Смотреть пока нечего</h1>
      </section>
    );
  }
  return (
    <section className="video-grid">
      {items.map((video) => (
        <VideoCard key={video.id} video={video} />
      ))}
    </section>
  );
}
