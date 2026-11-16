import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client";
import { Player } from "../components/Player";
import { nextPlaylistPosition, playlistAction } from "../playlist";
import { playerView } from "../player";
import { formatAgo, formatCompact, formatSubscribers, formatViews, formatDuration } from "../format";
import { subscribeControl } from "../subscribe";
import { useSession } from "../session";
import { useSettings } from "../settings-context";

const ICONS = {
  like: "M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z",
  dislike:
    "M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L9.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z",
  share:
    "M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92s2.92-1.31 2.92-2.92-1.31-2.92-2.92-2.92z",
  save: "M17 3H7c-1.1 0-2 .9-2 2v16l7-3 7 3V5c0-1.1-.9-2-2-2z",
  more: "M6 10a2 2 0 100 4 2 2 0 000-4zm6 0a2 2 0 100 4 2 2 0 000-4zm6 0a2 2 0 100 4 2 2 0 000-4z",
  bell: "M12 22a2.2 2.2 0 002.15-1.75h-4.3A2.2 2.2 0 0012 22zm6.5-6v-5a6.2 6.2 0 00-4.7-6V4a1.8 1.8 0 10-3.6 0v1a6.2 6.2 0 00-4.7 6v5L4 18.5V20h16v-1.5L18.5 16z",
};

const CHIPS = [
  { id: "all", label: "Все видео" },
  { id: "channel", label: "С этого канала" },
  { id: "recent", label: "Недавно опубликованные" },
];

export function WatchPage() {
  const { videoId } = useParams();
  const navigate = useNavigate();
  const { token, account } = useSession();
  const { settings } = useSettings();
  const [video, setVideo] = useState(null);
  const [missing, setMissing] = useState(false);
  const [src, setSrc] = useState("");
  const [channel, setChannel] = useState(null);
  const [reactions, setReactions] = useState({ likes: 0, dislikes: 0, mine: 0 });
  const [comments, setComments] = useState([]);
  const [feed, setFeed] = useState([]);
  const [chip, setChip] = useState("all");
  const [draft, setDraft] = useState("");
  const [replyTo, setReplyTo] = useState(null);
  const [open, setOpen] = useState(false);
  const [panel, setPanel] = useState(null);
  const [copied, setCopied] = useState(false);
  const [playlists, setPlaylists] = useState([]);
  const [playlistTitle, setPlaylistTitle] = useState("");
  const [saveNote, setSaveNote] = useState("");
  const [saveError, setSaveError] = useState("");
  const [reportReason, setReportReason] = useState("");
  const [reportSent, setReportSent] = useState(false);
  const [reportError, setReportError] = useState("");
  const [theater, setTheater] = useState(false);
  const view = playerView(theater);

  useEffect(() => {
    document.documentElement.dataset.player = view.frame;
    if (view.guide === "closed") {
      window.dispatchEvent(new CustomEvent("cpy-player-frame", { detail: "full" }));
    }
    return () => {
      delete document.documentElement.dataset.player;
      if (view.guide === "closed") {
        window.dispatchEvent(new CustomEvent("cpy-player-frame", { detail: "half" }));
      }
    };
  }, [view.frame, view.guide]);

  useEffect(() => {
    let active = true;
    setMissing(false);
    setVideo(null);
    setSrc("");
    setPanel(null);
    setChip("all");
    setOpen(false);
    api(`/videos/${videoId}`)
      .then(async (card) => {
        if (!active) {
          return;
        }
        setVideo(card);
        const [play, channelCard, reactionCard, commentCard, feedCard] = await Promise.all([
          api(`/videos/${videoId}/playback`).catch(() => null),
          api(`/channels/${card.channel_id}`).catch(() => null),
          api(`/videos/${videoId}/reactions`).catch(() => ({ likes: 0, dislikes: 0, mine: 0 })),
          api(`/videos/${videoId}/comments`).catch(() => ({ items: [] })),
          api("/feed").catch(() => ({ items: [] })),
        ]);
        if (!active) {
          return;
        }
        if (!play?.url) {
          setMissing(true);
          setVideo(null);
          return;
        }
        setSrc(play.url);
        setChannel(channelCard);
        setReactions(reactionCard);
        setComments(commentCard.items || []);
        setFeed(feedCard.items || []);
        if (token && settings.saveViews) {
          api(`/videos/${videoId}/view`, { method: "POST" })
            .then((view) => {
              if (active) {
                setVideo((current) => (current ? { ...current, view_count: view.view_count } : current));
              }
            })
            .catch(() => {});
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
  }, [videoId, token, settings.saveViews]);

  useEffect(() => {
    if (panel !== "save" || !token || !account?.channel_id) {
      return undefined;
    }
    let active = true;
    api(`/playlists?channel_id=${account.channel_id}`)
      .then((data) => {
        if (active) {
          setPlaylists(data.items || []);
        }
      })
      .catch(() => {
        if (active) {
          setPlaylists([]);
        }
      });
    return () => {
      active = false;
    };
  }, [panel, token, account]);

  useEffect(() => {
    if (!panel) {
      return undefined;
    }
    function onPointer(event) {
      if (!event.target.closest(".watch-tools")) {
        setPanel(null);
      }
    }
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [panel]);

  function signIn() {
    navigate("/login");
  }

  async function react(value) {
    if (!token) {
      signIn();
      return;
    }
    await api(`/videos/${videoId}/like`, { method: "POST", body: { value } });
    setReactions(await api(`/videos/${videoId}/reactions`));
  }

  async function toggleSubscribe() {
    if (!token) {
      signIn();
      return;
    }
    if (!channel) {
      return;
    }
    const path = `/channels/${channel.id}/subscribe`;
    if (channel.subscribed) {
      await api(path, { method: "DELETE" });
    } else {
      await api(path, { method: "POST" });
    }
    setChannel(await api(`/channels/${channel.id}`));
  }

  function togglePanel(name) {
    if ((name === "save" || name === "more") && !token) {
      signIn();
      return;
    }
    setCopied(false);
    setSaveNote("");
    setSaveError("");
    setPanel((current) => (current === name ? null : name));
  }

  async function copyLink() {
    const link = `${window.location.origin}/watch/${videoId}`;
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  }

  async function saveTo(playlist) {
    setSaveError("");
    const action = playlistAction(playlist.items, videoId);
    try {
      if (action === "remove") {
        await api(`/playlists/${playlist.id}/items/${videoId}`, { method: "DELETE" });
        setSaveNote(`Удалено из «${playlist.title}»`);
      } else {
        await api(`/playlists/${playlist.id}/items`, {
          method: "POST",
          body: { video_id: videoId, position: nextPlaylistPosition(playlist.items) },
        });
        setSaveNote(`Добавлено в «${playlist.title}»`);
      }
      if (account?.channel_id) {
        const data = await api(`/playlists?channel_id=${account.channel_id}`);
        setPlaylists(data.items || []);
      }
    } catch (exc) {
      setSaveError(exc.message);
    }
  }

  async function createPlaylist(event) {
    event.preventDefault();
    const title = playlistTitle.trim();
    if (!title || !account?.channel_id) {
      return;
    }
    setSaveError("");
    try {
      const created = await api("/playlists", {
        method: "POST",
        body: { channel_id: account.channel_id, title, visibility: "public" },
      });
      await api(`/playlists/${created.id}/items`, {
        method: "POST",
        body: { video_id: videoId, position: 1 },
      });
      setPlaylistTitle("");
      setSaveNote(`Добавлено в «${created.title}»`);
      const data = await api(`/playlists?channel_id=${account.channel_id}`);
      setPlaylists(data.items || []);
    } catch (exc) {
      setSaveError(exc.message);
    }
  }

  async function sendReport(event) {
    event.preventDefault();
    const reason = reportReason.trim();
    if (!reason || !token) {
      return;
    }
    setReportError("");
    try {
      await api("/reports", { method: "POST", body: { video_id: videoId, reason } });
      setReportReason("");
      setReportSent(true);
    } catch (exc) {
      setReportError(exc.message);
    }
  }

  async function sendComment(event) {
    event.preventDefault();
    const body = draft.trim();
    if (!body || !token) {
      return;
    }
    const created = await api(`/videos/${videoId}/comments`, {
      method: "POST",
      body: { body, parent_id: replyTo },
    });
    setComments((items) => [...items, { ...created, username: created.username || account?.username || "" }]);
    setDraft("");
    setReplyTo(null);
  }

  if (missing) {
    return (
      <section className="unavailable">
        <h1>Видео недоступно</h1>
      </section>
    );
  }
  if (!video || !src) {
    return null;
  }

  const roots = comments.filter((item) => !item.parent_id);
  const repliesOf = (id) => comments.filter((item) => item.parent_id === id);
  const long = (video.description || "").length > 80;
  const link = `${window.location.origin}/watch/${videoId}`;
  const letter = (account?.username || account?.email || "?").slice(0, 1).toUpperCase();
  const others = feed.filter((item) => item.id !== video.id);
  const related =
    chip === "channel"
      ? others.filter((item) => item.channel_id === video.channel_id)
      : chip === "recent"
        ? [...others].sort((left, right) => String(right.created_at).localeCompare(String(left.created_at)))
        : others;

  return (
    <article className={view.watchClass}>
      <div className="watch__left">
      <div className="watch__main">
        <Player
          src={src}
          autoPlay
          theater={theater}
          onTheater={setTheater}
          onAutoplayNext={() => {
            if (related[0]) {
              navigate(`/watch/${related[0].id}`);
            }
          }}
        />
        <h1 className="watch__title">{video.title}</h1>
        <div className="watch__bar">
          <div className="watch__owner">
            <Link className="channel-avatar channel-avatar--watch" to={`/channel/${video.channel_id}`}>
              {(channel?.name || video.channel_name || "?").slice(0, 1).toUpperCase()}
            </Link>
            <div className="watch__identity">
              <Link className="watch__channel-name" to={`/channel/${video.channel_id}`}>
                {channel?.name || video.channel_name}
              </Link>
              <p className="watch__subs">{channel ? formatSubscribers(channel.subscriber_count) : ""}</p>
            </div>
            {(() => {
              const control = subscribeControl({
                ownChannel: Boolean(account?.channel_id && video.channel_id === account.channel_id),
                signedIn: Boolean(token),
                subscribed: Boolean(channel?.subscribed),
              });
              if (control === "hidden") {
                return null;
              }
              if (control === "subscribed") {
                return (
                  <button type="button" className="icon-button watch-bell" aria-label="Вы подписаны" onClick={toggleSubscribe}>
                    <Icon d={ICONS.bell} />
                  </button>
                );
              }
              return (
                <button type="button" className="subscribe" onClick={toggleSubscribe}>
                  Подписаться
                </button>
              );
            })()}
          </div>
          <div className="watch-tools">
            <div className="watch__actions">
              <button
                type="button"
                className={reactions.mine === 1 ? "action action--on" : "action"}
                aria-label={`Нравится, ${reactions.likes}`}
                onClick={() => react(1)}
              >
                <Icon d={ICONS.like} />
                <span>{formatCompact(reactions.likes)}</span>
              </button>
              <button
                type="button"
                className={reactions.mine === -1 ? "action action--icon action--on" : "action action--icon"}
                aria-label="Не нравится"
                onClick={() => react(-1)}
              >
                <Icon d={ICONS.dislike} />
              </button>
              <button type="button" className="action action--icon" aria-label="Поделиться" onClick={() => togglePanel("share")}>
                <Icon d={ICONS.share} />
              </button>
              <button type="button" className="action action--icon" aria-label="Добавить в плейлист" onClick={() => togglePanel("save")}>
                <Icon d={ICONS.save} />
              </button>
              <button type="button" className="action action--icon" aria-label="Ещё" onClick={() => togglePanel("more")}>
                <Icon d={ICONS.more} />
              </button>
            </div>
            {panel === "share" ? (
              <div className="watch-pop" role="dialog" aria-label="Поделиться">
                <p>Ссылка</p>
                <input readOnly value={link} aria-label="Ссылка на ролик" />
                <button type="button" onClick={copyLink}>
                  Копировать
                </button>
                {copied ? <p>Ссылка скопирована</p> : null}
              </div>
            ) : null}
            {panel === "save" ? (
              <div className="watch-pop" role="dialog" aria-label="Добавить в плейлист">
                <p>Добавить в плейлист</p>
                <ul className="watch-pop__list">
                  {playlists.map((playlist) => (
                    <li key={playlist.id}>
                      <button
                        type="button"
                        aria-pressed={playlistAction(playlist.items, videoId) === "remove"}
                        onClick={() => saveTo(playlist)}
                      >
                        {playlistAction(playlist.items, videoId) === "remove" ? "✓ " : ""}
                        {playlist.title}
                      </button>
                    </li>
                  ))}
                </ul>
                <form className="watch-pop__form" onSubmit={createPlaylist}>
                  <input
                    value={playlistTitle}
                    placeholder="Новый плейлист"
                    onChange={(event) => setPlaylistTitle(event.target.value)}
                  />
                  <button type="submit">Создать</button>
                </form>
                {saveNote ? <p>{saveNote}</p> : null}
                {saveError ? <p className="report-form__error">{saveError}</p> : null}
              </div>
            ) : null}
            {panel === "more" ? (
              <div className="watch-pop" role="dialog" aria-label="Ещё">
                <form className="report-form" onSubmit={sendReport}>
                  <label>
                    Пожаловаться
                    <textarea
                      value={reportReason}
                      maxLength={2000}
                      onChange={(event) => setReportReason(event.target.value)}
                    />
                  </label>
                  <button type="submit">Отправить жалобу</button>
                  {reportSent ? <p>Жалоба отправлена</p> : null}
                  {reportError ? <p className="report-form__error">{reportError}</p> : null}
                </form>
              </div>
            ) : null}
          </div>
        </div>
        <div className={open || !long ? "description description--open" : "description"}>
          <p className="description__meta">
            <strong>{formatViews(video.view_count)}</strong> <strong>{formatAgo(video.created_at)}</strong>
          </p>
          <p className="description__text">{video.description}</p>
          {long ? (
            <button type="button" className="description__more" onClick={() => setOpen((value) => !value)}>
              {open ? "Свернуть" : "ещё"}
            </button>
          ) : null}
        </div>
      </div>
      <section className="comments">
        <h2>
          Комментарии <span>{comments.length}</span>
        </h2>
        {token ? (
          <form className="comment-form" onSubmit={sendComment}>
            <span className="channel-avatar" aria-hidden="true">
              {letter}
            </span>
            <div className="comment-form__field">
              {replyTo ? <p className="comment-form__hint">Ответ</p> : null}
              <input
                value={draft}
                placeholder="Введите комментарий"
                onChange={(event) => setDraft(event.target.value)}
              />
              <button type="submit">Отправить</button>
            </div>
          </form>
        ) : (
          <p className="comments__login">
            <Link to="/login">Войдите</Link>, чтобы комментировать
          </p>
        )}
        <ul className="comment-list">
          {roots.map((comment) => (
            <li key={comment.id}>
              <CommentItem comment={comment} onReply={token ? () => setReplyTo(comment.id) : null} />
              <ul className="comment-list comment-list--reply">
                {repliesOf(comment.id).map((reply) => (
                  <li key={reply.id}>
                    <CommentItem comment={reply} />
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      </section>
      </div>
      <aside className="watch__side">
        <div className="filter-row" role="tablist" aria-label="Рекомендации">
          {CHIPS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={chip === item.id}
              className={chip === item.id ? "filter-chip filter-chip--on" : "filter-chip"}
              onClick={() => setChip(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        {related.length === 0 ? (
          <p className="watch__empty">Других роликов нет</p>
        ) : (
          <ul className="related-list">
            {related.map((item) => (
              <li key={item.id}>
                <Link className="related-card" to={`/watch/${item.id}`}>
                  <div className="thumb">
                    {item.thumbnail_url ? <img src={item.thumbnail_url} alt="" /> : <div className="thumb__empty" />}
                    <span className="thumb__time">{formatDuration(item.duration_sec)}</span>
                  </div>
                  <div>
                    <h3>{item.title}</h3>
                    <p>{item.channel_name}</p>
                    <p>
                      {formatCompact(item.view_count)} • {formatAgo(item.created_at)}
                    </p>
                  </div>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </aside>
    </article>
  );
}

function Icon({ d }) {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}

function CommentItem({ comment, onReply }) {
  const letter = (comment.username || "?").slice(0, 1).toUpperCase();
  return (
    <div className="comment">
      <span className="channel-avatar">{letter}</span>
      <div>
        <strong>{comment.username || "Зритель"}</strong>
        <p>{comment.body}</p>
        {onReply ? (
          <button type="button" className="text-button" onClick={onReply}>
            Ответить
          </button>
        ) : null}
      </div>
    </div>
  );
}
