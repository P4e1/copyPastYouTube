import { Link } from "react-router-dom";

import { formatAgo, formatDuration, formatViewLine } from "../format";

export function VideoCard({ video, dense = false }) {
  const letter = (video.channel_name || "?").slice(0, 1).toUpperCase();
  return (
    <Link className={dense ? "video-card video-card--dense" : "video-card"} to={`/watch/${video.id}`}>
      <div className="thumb">
        {video.thumbnail_url ? <img src={video.thumbnail_url} alt="" /> : <div className="thumb__empty" />}
        {video.status === "hidden" ? <span className="thumb__hidden">Скрыто</span> : null}
        <span className="thumb__time">{formatDuration(video.duration_sec)}</span>
      </div>
      <div className="video-card__body">
        {dense ? null : (
          <span className="channel-avatar" aria-hidden="true">
            {letter}
          </span>
        )}
        <div className="video-card__text">
          <h2 className="video-card__title">{video.title}</h2>
          <p className="video-card__meta">
            {dense ? null : (
              <>
                {video.channel_name}
                <br />
              </>
            )}
            {formatViewLine(video.view_count)} • {formatAgo(video.created_at)}
          </p>
        </div>
      </div>
    </Link>
  );
}
