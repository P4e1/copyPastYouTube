import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { api } from "../api/client";
import { VideoCard } from "../components/VideoCard";
import { useSession } from "../session";
import { subscriptionFeed } from "../subscriptions";

export function SubscriptionsPage() {
  const { token } = useSession();
  const [channels, setChannels] = useState(null);
  const [videos, setVideos] = useState(null);

  useEffect(() => {
    if (!token) {
      return undefined;
    }
    let active = true;
    Promise.all([api("/subscriptions"), api("/subscriptions/feed")])
      .then(([followed, feed]) => {
        if (active) {
          setChannels(followed.items || []);
          setVideos(feed.items || []);
        }
      })
      .catch(() => {
        if (active) {
          setChannels([]);
          setVideos([]);
        }
      });
    return () => {
      active = false;
    };
  }, [token]);

  const view = subscriptionFeed({
    signedIn: Boolean(token),
    channels: channels || [],
    videos: videos || [],
  });
  if (view.redirect) {
    return <Navigate to={view.redirect} replace />;
  }
  if (channels === null || videos === null) {
    return null;
  }
  if (view.empty) {
    return (
      <section className="empty">
        <h1>{view.empty}</h1>
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
