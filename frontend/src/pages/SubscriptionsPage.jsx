import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { api } from "../api/client";
import { useSession } from "../session";

export function SubscriptionsPage() {
  const { token } = useSession();
  const [items, setItems] = useState(null);

  useEffect(() => {
    if (!token) {
      return undefined;
    }
    let active = true;
    api("/subscriptions")
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
  }, [token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }
  if (items === null) {
    return null;
  }
  if (items.length === 0) {
    return (
      <section className="empty">
        <h1>Подписок пока нет</h1>
      </section>
    );
  }
  return (
    <ul className="sub-list">
      {items.map((channel) => (
        <li key={channel.id}>
          <Link to={`/channel/${channel.id}`}>{channel.name}</Link>
        </li>
      ))}
    </ul>
  );
}
