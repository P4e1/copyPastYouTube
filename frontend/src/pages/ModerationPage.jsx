import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api/client";
import { useSession } from "../session";

export function ModerationPage() {
  const { token, account } = useSession();
  const allowed = account?.role === "moderator" || account?.role === "admin";
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!allowed) {
      return undefined;
    }
    let active = true;
    api("/moderation/reports")
      .then((data) => {
        if (active) {
          setItems(data.items || []);
        }
      })
      .catch((exc) => {
        if (active) {
          setError(exc.message);
        }
      });
    return () => {
      active = false;
    };
  }, [allowed]);

  if (!token || (account && !allowed)) {
    return (
      <section className="refusal">
        <h1>Недостаточно прав</h1>
      </section>
    );
  }
  if (!account) {
    return null;
  }

  async function hide(videoId) {
    setError("");
    try {
      await api(`/moderation/videos/${videoId}/hide`, { method: "POST" });
      setItems((current) => current.filter((item) => item.video_id !== videoId));
    } catch (exc) {
      setError(exc.message);
    }
  }

  return (
    <section className="moderation">
      <h1>Модерация</h1>
      {error ? <p className="moderation__error">{error}</p> : null}
      {items.length === 0 ? <p>Открытых жалоб нет</p> : null}
      <ul className="report-list">
        {items.map((item) => (
          <li key={item.id} className="report-row moderation-card">
            <Link to={`/watch/${item.video_id}`}>{item.video_title || "Ролик"}</Link>
            <p>{item.reason}</p>
            <p>{item.reporter_username}</p>
            <button type="button" onClick={() => hide(item.video_id)}>
              Скрыть
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
