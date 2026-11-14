import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { api } from "../api/client";
import { formatViews } from "../format";

export function SearchPage() {
  const [params] = useSearchParams();
  const query = params.get("q") || "";
  const [items, setItems] = useState(null);

  useEffect(() => {
    if (!query.trim()) {
      setItems(null);
      return undefined;
    }
    let active = true;
    setItems(null);
    api(`/search?q=${encodeURIComponent(query)}`)
      .then((data) => {
        if (active) {
          setItems(data.items);
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
  }, [query]);

  if (!query.trim()) {
    return (
      <section className="empty">
        <h1>Введите запрос</h1>
      </section>
    );
  }
  if (items === null) {
    return null;
  }
  if (items.length === 0) {
    return (
      <section className="empty">
        <h1>Ничего не найдено</h1>
      </section>
    );
  }
  return (
    <ul className="search-list">
      {items.map((video) => (
        <li key={video.id}>
          <Link className="search-row" to={`/watch/${video.id}`}>
            <div className="thumb thumb--row">
              {video.thumbnail_url ? <img src={video.thumbnail_url} alt="" /> : <div className="thumb__empty" />}
            </div>
            <div>
              <h2>{video.title}</h2>
              <p>
                {video.channel_name} • {formatViews(video.view_count)}
              </p>
              <p className="search-row__desc">{video.description}</p>
            </div>
          </Link>
        </li>
      ))}
    </ul>
  );
}
