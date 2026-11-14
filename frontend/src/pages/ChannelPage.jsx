import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { formatSubscribers } from "../format";

export function ChannelPage() {
  const { channelId } = useParams();
  const [channel, setChannel] = useState(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    let active = true;
    api(`/channels/${channelId}`)
      .then((data) => {
        if (active) {
          setChannel(data);
        }
      })
      .catch(() => {
        if (active) {
          setMissing(true);
        }
      });
    return () => {
      active = false;
    };
  }, [channelId]);

  if (missing) {
    return (
      <section className="empty">
        <h1>Канал не найден</h1>
      </section>
    );
  }
  if (!channel) {
    return null;
  }
  return (
    <section className="channel-plain">
      <h1>{channel.name}</h1>
      <p>{formatSubscribers(channel.subscriber_count)}</p>
      <ul className="sub-list">
        {channel.videos.map((video) => (
          <li key={video.id}>
            <Link to={`/watch/${video.id}`}>{video.title}</Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
