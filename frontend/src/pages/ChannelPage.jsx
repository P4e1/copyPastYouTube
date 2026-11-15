import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { api } from "../api/client";
import { VIDEO_SORTS, channelHandle, channelTab, filterByTitle, sortChannelVideos } from "../channel";
import { VideoCard } from "../components/VideoCard";
import { formatSubscribers, formatVideoCount } from "../format";
import { useSession } from "../session";

export function ChannelPage() {
  const { channelId } = useParams();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { token, account } = useSession();
  const [channel, setChannel] = useState(null);
  const [videos, setVideos] = useState([]);
  const [playlists, setPlaylists] = useState([]);
  const [titles, setTitles] = useState({});
  const [tab, setTab] = useState(() => channelTab(params.get("tab")));
  const [missing, setMissing] = useState(false);
  const [playlistTitle, setPlaylistTitle] = useState("");
  const [pickedVideo, setPickedVideo] = useState("");
  const [sort, setSort] = useState("latest");
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [aboutOpen, setAboutOpen] = useState(false);
  const [openPlaylist, setOpenPlaylist] = useState("");

  useEffect(() => {
    let active = true;
    setMissing(false);
    setChannel(null);
    setQuery("");
    setAboutOpen(false);
    setOpenPlaylist("");
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

  useEffect(() => {
    setTab(channelTab(params.get("tab")));
  }, [params]);

  function selectTab(next) {
    setTab(next);
    navigate(next === "home" ? `/channel/${channelId}` : `/channel/${channelId}?tab=${next}`, { replace: true });
  }

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
    selectTab("playlists");
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
  const latest = sortChannelVideos(videos, "latest").slice(0, 8);
  const popular = sortChannelVideos(videos, "popular").slice(0, 8);
  const ordered = sortChannelVideos(videos, sort);
  const found = filterByTitle(ordered, query);
  const about = channel.description || "";
  const aboutLong = about.length > 80;

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
            {channelHandle(channel.name)} • {formatSubscribers(channel.subscriber_count)} •{" "}
            {formatVideoCount(channel.videos.length)}
          </p>
          {about ? (
            <p className="channel-about">
              {aboutOpen || !aboutLong ? about : `${about.slice(0, 80)}…`}
              {aboutLong ? (
                <button type="button" className="description__more" onClick={() => setAboutOpen((value) => !value)}>
                  {aboutOpen ? "Свернуть" : "ещё"}
                </button>
              ) : null}
            </p>
          ) : null}
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
        <button type="button" role="tab" aria-selected={tab === "home"} className={tab === "home" ? "channel-tab channel-tab--on" : "channel-tab"} onClick={() => selectTab("home")}>
          Главная
        </button>
        <button type="button" role="tab" aria-selected={tab === "videos"} className={tab === "videos" ? "channel-tab channel-tab--on" : "channel-tab"} onClick={() => selectTab("videos")}>
          Видео
        </button>
        <button type="button" role="tab" aria-selected={tab === "shorts"} className={tab === "shorts" ? "channel-tab channel-tab--on" : "channel-tab"} onClick={() => selectTab("shorts")}>
          Shorts
        </button>
        <button type="button" role="tab" aria-selected={tab === "playlists"} className={tab === "playlists" ? "channel-tab channel-tab--on" : "channel-tab"} onClick={() => selectTab("playlists")}>
          Плейлисты
        </button>
        <button
          type="button"
          className="channel-search"
          aria-label="Поиск"
          aria-expanded={searchOpen}
          onClick={() => setSearchOpen((value) => !value)}
        >
          <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
            <path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0016 9.5 6.5 6.5 0 109.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 5 1.5-1.5-5-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z" />
          </svg>
        </button>
      </div>
      {searchOpen ? (
        <input
          className="channel-search__input"
          aria-label="Поиск по каналу"
          placeholder="Поиск"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      ) : null}
      {query.trim() ? (
        found.length === 0 ? (
          <p className="channel-empty">Ничего не найдено</p>
        ) : (
          <div className="video-grid">
            {found.map((video) => (
              <VideoCard key={video.id} video={video} dense />
            ))}
          </div>
        )
      ) : tab === "home" ? (
        <div className="channel-home">
          <section className="channel-shelf">
            <div className="channel-shelf__head">
              <h2>Видео</h2>
              <button type="button" onClick={() => selectTab("videos")}>
                Все
              </button>
            </div>
            {latest.length === 0 ? (
              <p className="channel-empty">Видео пока нет</p>
            ) : (
              <div className="channel-shelf__row">
                {latest.map((video) => (
                  <VideoCard key={video.id} video={video} dense />
                ))}
              </div>
            )}
          </section>
          {popular.length > 1 ? (
            <section className="channel-shelf">
              <div className="channel-shelf__head">
                <h2>Популярные видео</h2>
                <button
                  type="button"
                  onClick={() => {
                    setSort("popular");
                    selectTab("videos");
                  }}
                >
                  Все
                </button>
              </div>
              <div className="channel-shelf__row">
                {popular.map((video) => (
                  <VideoCard key={video.id} video={video} dense />
                ))}
              </div>
            </section>
          ) : null}
          {playlists.length > 0 ? (
            <section className="channel-shelf">
              <div className="channel-shelf__head">
                <h2>Плейлисты</h2>
                <button type="button" onClick={() => selectTab("playlists")}>
                  Все
                </button>
              </div>
              <div className="channel-shelf__row">
                {playlists.map((playlist) => (
                  <PlaylistCard
                    key={playlist.id}
                    playlist={playlist}
                    cover={playlistCover(playlist, videos)}
                    onOpen={() => {
                      setOpenPlaylist(playlist.id);
                      selectTab("playlists");
                    }}
                  />
                ))}
              </div>
            </section>
          ) : null}
        </div>
      ) : null}
      {!query.trim() && tab === "shorts" ? <p className="channel-empty">Смотреть пока нечего</p> : null}
      {!query.trim() && tab === "videos" ? (
        videos.length === 0 ? (
          <p className="channel-empty">Видео пока нет</p>
        ) : (
          <>
            <div className="channel-sort" role="tablist" aria-label="Сортировка">
              {VIDEO_SORTS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  role="tab"
                  aria-selected={sort === item.id}
                  onClick={() => setSort(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>
            <div className="video-grid">
              {ordered.map((video) => (
                <VideoCard key={video.id} video={video} dense />
              ))}
            </div>
          </>
        )
      ) : null}
      {!query.trim() && tab === "playlists" ? (
        <div className="playlist-panel">
          <div className="playlist-grid">
            {playlists.map((playlist) => (
              <PlaylistCard
                key={playlist.id}
                playlist={playlist}
                cover={playlistCover(playlist, videos)}
                onOpen={() => setOpenPlaylist((current) => (current === playlist.id ? "" : playlist.id))}
              />
            ))}
          </div>
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
            {(openPlaylist ? playlists.filter((playlist) => playlist.id === openPlaylist) : playlists).map((playlist) => (
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

function playlistCover(playlist, videos) {
  const first = [...playlist.items].sort((left, right) => left.position - right.position)[0];
  if (!first) {
    return null;
  }
  return videos.find((video) => video.id === first.video_id)?.thumbnail_url || null;
}

function PlaylistCard({ playlist, cover, onOpen }) {
  return (
    <button type="button" className="playlist-card" onClick={onOpen}>
      <div className="thumb">{cover ? <img src={cover} alt="" /> : <div className="thumb__empty" />}</div>
      <h3>{playlist.title}</h3>
      <p>{formatVideoCount(playlist.items.length)}</p>
    </button>
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
