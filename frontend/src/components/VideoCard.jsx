import { Link } from "react-router-dom";

import { formatDate, formatDuration, formatViews } from "../format";

export function VideoCard({ video }) {
  const letter = (video.channel_name || "?").slice(0, 1).toUpperCase();
  return (
    <Link className="video-card" to={`/watch/${video.id}`}>
      <div className="thumb">
        {video.thumbnail_url ? <img src={video.thumbnail_url} alt="" /> : <div className="thumb__empty" />}
        {video.status === "hidden" ? <span className="thumb__hidden">Скрыто</span> : null}
        <span className="thumb__time">{formatDuration(video.duration_sec)}</span>
      </div>
      <div className="video-card__body">
        <span className="channel-avatar" aria-hidden="true">
          {letter}
        </span>
        <div className="video-card__text">
          <h2 className="video-card__title">{video.title}</h2>
          <p className="video-card__meta">
            {video.channel_name}
            <br />
            {formatViews(video.view_count)} • {formatDate(video.created_at)}
          </p>
        </div>
      </div>
    </Link>
  );
}
