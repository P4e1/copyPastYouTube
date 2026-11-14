import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client";
import { formatSubscribers, formatViews } from "../format";
import { useSession } from "../session";

export function WatchPage() {
  const { videoId } = useParams();
  const { token, account } = useSession();
  const [video, setVideo] = useState(null);
  const [missing, setMissing] = useState(false);
  const [src, setSrc] = useState("");
  const [channel, setChannel] = useState(null);
  const [reactions, setReactions] = useState({ likes: 0, dislikes: 0, mine: 0 });
  const [comments, setComments] = useState([]);
  const [draft, setDraft] = useState("");
  const [replyTo, setReplyTo] = useState(null);
  const [open, setOpen] = useState(false);
  const [reportReason, setReportReason] = useState("");
  const [reportSent, setReportSent] = useState(false);
  const [reportError, setReportError] = useState("");

  useEffect(() => {
    let active = true;
    setMissing(false);
    setVideo(null);
    setSrc("");
    api(`/videos/${videoId}`)
      .then(async (card) => {
        if (!active) {
          return;
        }
        setVideo(card);
        const [play, channelCard, reactionCard, commentCard] = await Promise.all([
          api(`/videos/${videoId}/playback`).catch(() => null),
          api(`/channels/${card.channel_id}`).catch(() => null),
          api(`/videos/${videoId}/reactions`).catch(() => ({ likes: 0, dislikes: 0, mine: 0 })),
          token ? api(`/videos/${videoId}/comments`).catch(() => ({ items: [] })) : Promise.resolve({ items: [] }),
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
        if (token) {
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
  }, [videoId, token]);

  async function react(value) {
    if (!token) {
      return;
    }
    await api(`/videos/${videoId}/like`, { method: "POST", body: { value } });
    const next = await api(`/videos/${videoId}/reactions`);
    setReactions(next);
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
  const long = (video.description || "").length > 140;

  return (
    <article className="watch">
      <video className="player" src={src} controls autoPlay />
      <h1 className="watch__title">{video.title}</h1>
      <div className="watch__row">
        <span>{formatViews(video.view_count)}</span>
        <div className="watch__actions">
          <button type="button" className={reactions.mine === 1 ? "action action--on" : "action"} onClick={() => react(1)}>
            Нравится {reactions.likes}
          </button>
          <button type="button" className={reactions.mine === -1 ? "action action--on" : "action"} onClick={() => react(-1)}>
            Не нравится {reactions.dislikes}
          </button>
          <button type="button" className="action">
            Поделиться
          </button>
        </div>
      </div>
      <div className="watch__channel">
        <Link className="channel-avatar" to={`/channel/${video.channel_id}`}>
          {(channel?.name || video.channel_name || "?").slice(0, 1).toUpperCase()}
        </Link>
        <div>
          <Link className="watch__channel-name" to={`/channel/${video.channel_id}`}>
            {channel?.name || video.channel_name}
          </Link>
          <p className="watch__subs">{channel ? formatSubscribers(channel.subscriber_count) : ""}</p>
        </div>
        {token ? (
          <button type="button" className={channel?.subscribed ? "subscribe subscribe--on" : "subscribe"} onClick={toggleSubscribe}>
            {channel?.subscribed ? "Вы подписаны" : "Подписаться"}
          </button>
        ) : null}
      </div>
      <div className={open || !long ? "description description--open" : "description"}>
        <p>{video.description}</p>
        {long ? (
          <button type="button" onClick={() => setOpen((value) => !value)}>
            {open ? "Свернуть" : "Ещё"}
          </button>
        ) : null}
      </div>
      {token ? (
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
      ) : null}
      <section className="comments">
        <h2>Комментарии</h2>
        {token ? (
          <form className="comment-form" onSubmit={sendComment}>
            {replyTo ? <p className="comment-form__hint">Ответ</p> : null}
            <input
              value={draft}
              placeholder="Введите комментарий"
              onChange={(event) => setDraft(event.target.value)}
            />
            <button type="submit">Отправить</button>
          </form>
        ) : (
          <p className="comments__login">
            <Link to="/login">Войдите</Link>, чтобы комментировать
          </p>
        )}
        <ul className="comment-list">
          {roots.map((comment) => (
            <li key={comment.id}>
              <CommentItem comment={comment} onReply={() => setReplyTo(comment.id)} />
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
    </article>
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
