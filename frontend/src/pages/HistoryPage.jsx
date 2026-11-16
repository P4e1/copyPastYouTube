import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { api } from "../api/client";
import { VideoCard } from "../components/VideoCard";
import { HISTORY_EMPTY, historyView } from "../history";
import { useSession } from "../session";

export function HistoryPage() {
  const { token } = useSession();
  const [items, setItems] = useState(null);

  useEffect(() => {
    if (!token) {
      return undefined;
    }
    let active = true;
    api("/history")
      .then((data) => {
        if (active) {
          setItems(data.items || []);
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
  }, [token]);

  const view = historyView({ signedIn: Boolean(token), items: items || [] });
  if (view.redirect) {
    return <Navigate to={view.redirect} replace />;
  }
  if (items === null) {
    return null;
  }
  if (view.empty) {
    return (
      <section className="empty">
        <h1>{HISTORY_EMPTY}</h1>
      </section>
    );
  }
  return (
    <section className="video-grid">
      {view.items.map((video) => (
        <VideoCard key={video.id} video={video} />
      ))}
    </section>
  );
}
