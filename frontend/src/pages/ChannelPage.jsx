import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { VideoCard } from "../components/VideoCard";
import { formatSubscribers, formatVideoCount } from "../format";
import { useSession } from "../session";

export function ChannelPage() {
  const { channelId } = useParams();
  const { token, account } = useSession();
  const [channel, setChannel] = useState(null);
  const [videos, setVideos] = useState([]);
  const [playlists, setPlaylists] = useState([]);
  const [titles, setTitles] = useState({});
  const [tab, setTab] = useState("home");
  const [missing, setMissing] = useState(false);
  const [playlistTitle, setPlaylistTitle] = useState("");
  const [pickedVideo, setPickedVideo] = useState("");

  useEffect(() => {
    let active = true;
    setMissing(false);
    setChannel(null);
    api(`/channels/${channelId}`)
      .then(async (card) => {
        const [loadedVideos, loadedPlaylists] = await Promise.all([
          loadVideos(card),
          api(`/playlists?channel_id=${channelId}`).then((data) => data.items).catch(() => []),
        ]);
        const names = await loadTitles(loadedPlaylists);
        if (!active) {
          return;
        }
        setChannel(card);
        setVideos(loadedVideos);
        setPlaylists(loadedPlaylists);
        setTitles(names);
      })
      .catch(() => {
        if (active) {
          setMissing(true);
        }
      });
    return () => {
      active = false;
    };
  }, [channelId, token]);

  async function refresh() {
    const card = await api(`/channels/${channelId}`);
    const [loadedVideos, loadedPlaylists] = await Promise.all([
      loadVideos(card),
      api(`/playlists?channel_id=${channelId}`).then((data) => data.items),
    ]);
    setChannel(card);
    setVideos(loadedVideos);
    setPlaylists(loadedPlaylists);
    setTitles(await loadTitles(loadedPlaylists));
  }

  async function toggleSubscribe() {
    if (!token || !channel) {
      return;
    }
    const path = `/channels/${channel.id}/subscribe`;
    if (channel.subscribed) {
      await api(path, { method: "DELETE" });
    } else {
      await api(path, { method: "POST" });
    }
    const next = await api(`/channels/${channel.id}`);
    setChannel(next);
  }

  async function createPlaylist(event) {
    event.preventDefault();
    const title = playlistTitle.trim();
    if (!title) {
      return;
    }
    const created = await api("/playlists", {
      method: "POST",
      body: { channel_id: channelId, title, visibility: "public" },
    });
    if (pickedVideo) {
      await api(`/playlists/${created.id}/items`, {
        method: "POST",
        body: { video_id: pickedVideo, position: 1 },
      });
    }
    setPlaylistTitle("");
    setPickedVideo("");
    await refresh();
    setTab("playlists");
  }

  async function addVideo(playlist, videoId) {
    if (!videoId) {
      return;
    }
    const next = playlist.items.reduce((max, item) => Math.max(max, item.position), 0) + 1;
    await api(`/playlists/${playlist.id}/items`, {
      method: "POST",
      body: { video_id: videoId, position: next },
    });
    await refresh();
  }

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

  const isOwner = account?.channel_id === channel.id;
  const ownVideos = videos.filter((video) => video.status !== "hidden");
  const letter = channel.name.slice(0, 1).toUpperCase();
  const latest = videos.slice(0, 8);

  return (
    <section className="channel">
      <div className="channel-banner" />
      <div className="channel-head">
        <span className="channel-avatar channel-avatar--large" aria-hidden="true">
          {letter}
        </span>
        <div className="channel-identity">
          <h1>{channel.name}</h1>
          <p>
            {formatSubscribers(channel.subscriber_count)} • {formatVideoCount(channel.videos.length)}
          </p>
          {isOwner ? (
            <Link className="subscribe" to="/upload">
              Управление видео
            </Link>
          ) : token ? (
            <button
              type="button"
              className={channel.subscribed ? "subscribe subscribe--on" : "subscribe"}
              onClick={toggleSubscribe}
            >
              {channel.subscribed ? "Вы подписаны" : "Подписаться"}
            </button>
          ) : (
            <Link className="subscribe" to="/login">
              Подписаться
            </Link>
          )}
        </div>
      </div>
      <div className="channel-tabs" role="tablist">
        <button type="button" role="tab" aria-selected={tab === "home"} className={tab === "home" ? "channel-tab channel-tab--on" : "channel-tab"} onClick={() => setTab("home")}>
          Главная
        </button>
        <button type="button" role="tab" aria-selected={tab === "videos"} className={tab === "videos" ? "channel-tab channel-tab--on" : "channel-tab"} onClick={() => setTab("videos")}>
          Видео
        </button>
        <button type="button" role="tab" aria-selected={tab === "shorts"} className={tab === "shorts" ? "channel-tab channel-tab--on" : "channel-tab"} onClick={() => setTab("shorts")}>
          Shorts
        </button>
        <button type="button" role="tab" aria-selected={tab === "playlists"} className={tab === "playlists" ? "channel-tab channel-tab--on" : "channel-tab"} onClick={() => setTab("playlists")}>
          Плейлисты
        </button>
      </div>
      {tab === "home" ? (
        <div className="channel-home">
          <section className="channel-shelf">
            <div className="channel-shelf__head">
              <h2>Видео</h2>
              <button type="button" onClick={() => setTab("videos")}>
                Все
              </button>
            </div>
            {latest.length === 0 ? (
              <p className="channel-empty">Видео пока нет</p>
            ) : (
              <div className="channel-shelf__row">
                {latest.map((video) => (
                  <VideoCard key={video.id} video={video} />
                ))}
              </div>
            )}
          </section>
          {playlists.length > 0 ? (
            <section className="channel-shelf">
              <div className="channel-shelf__head">
                <h2>Плейлисты</h2>
                <button type="button" onClick={() => setTab("playlists")}>
                  Все
                </button>
              </div>
              <ul className="playlist-list">
                {playlists.map((playlist) => (
                  <li key={playlist.id}>
                    <button type="button" className="channel-shelf__playlist" onClick={() => setTab("playlists")}>
                      {playlist.title}
                    </button>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}
        </div>
      ) : null}
      {tab === "shorts" ? <p className="channel-empty">Смотреть пока нечего</p> : null}
      {tab === "videos" ? (
        videos.length === 0 ? (
          <p className="channel-empty">Видео пока нет</p>
        ) : (
          <div className="video-grid">
            {videos.map((video) => (
              <VideoCard key={video.id} video={video} />
            ))}
          </div>
        )
      ) : null}
      {tab === "playlists" ? (
        <div className="playlist-panel">
          {isOwner ? (
            <form className="playlist-form" onSubmit={createPlaylist}>
              <input
                value={playlistTitle}
                placeholder="Название плейлиста"
                onChange={(event) => setPlaylistTitle(event.target.value)}
              />
              <select value={pickedVideo} aria-label="Ролик" onChange={(event) => setPickedVideo(event.target.value)}>
                <option value="">Свой ролик</option>
                {ownVideos.map((video) => (
                  <option key={video.id} value={video.id}>
                    {video.title}
                  </option>
                ))}
              </select>
              <button type="submit">Создать</button>
            </form>
          ) : null}
          {playlists.length === 0 ? <p className="channel-empty">Плейлистов пока нет</p> : null}
          <ul className="playlist-list">
            {playlists.map((playlist) => (
              <li key={playlist.id} className="playlist">
                <h2>{playlist.title}</h2>
                <ol>
                  {[...playlist.items]
                    .sort((left, right) => left.position - right.position)
                    .map((item) => (
                      <li key={`${item.video_id}-${item.position}`}>
                        <Link to={`/watch/${item.video_id}`}>{titles[item.video_id] || "Ролик"}</Link>
                      </li>
                    ))}
                </ol>
                {isOwner ? <AddVideo videos={ownVideos} onAdd={(videoId) => addVideo(playlist, videoId)} /> : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}

function AddVideo({ videos, onAdd }) {
  const [videoId, setVideoId] = useState("");
  return (
    <form
      className="playlist-form"
      onSubmit={(event) => {
        event.preventDefault();
        onAdd(videoId);
        setVideoId("");
      }}
    >
      <select value={videoId} aria-label="Добавить ролик" onChange={(event) => setVideoId(event.target.value)}>
        <option value="">Добавить ролик</option>
        {videos.map((video) => (
          <option key={video.id} value={video.id}>
            {video.title}
          </option>
        ))}
      </select>
      <button type="submit">Добавить</button>
    </form>
  );
}

async function loadVideos(channel) {
  return Promise.all(
    channel.videos.map(async (item) => {
      try {
        return await api(`/videos/${item.id}`);
      } catch {
        return {
          id: item.id,
          title: item.title,
          visibility: item.visibility,
          status: item.status,
          hidden_mark: item.hidden_mark,
          channel_name: channel.name,
          view_count: 0,
          duration_sec: 0,
          created_at: "",
          thumbnail_url: null,
        };
      }
    }),
  );
}

async function loadTitles(playlists) {
  const ids = [...new Set(playlists.flatMap((playlist) => playlist.items.map((item) => item.video_id)))];
  const pairs = await Promise.all(
    ids.map(async (id) => {
      try {
        const card = await api(`/videos/${id}`);
        return [id, card.title];
      } catch {
        return [id, ""];
      }
    }),
  );
  return Object.fromEntries(pairs);
}
