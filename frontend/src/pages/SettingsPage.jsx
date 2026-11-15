import { Link, Navigate, NavLink, useParams } from "react-router-dom";

import { channelHandle } from "../channel";
import { SETTINGS_NAV } from "../settings";
import { useSettings } from "../settings-context";
import { useSession } from "../session";

export function SettingsPage() {
  const { token, account } = useSession();
  const { settings, updateSettings } = useSettings();
  const { section } = useParams();
  const current = SETTINGS_NAV.some((item) => item.id === section) ? section : "account";

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  const name = account?.username || account?.email || "";
  const channelTo = account?.channel_id ? `/channel/${account.channel_id}` : "/you";

  return (
    <div className="settings">
      <h1>Настройки</h1>
      <div className="settings__layout">
        <nav className="settings__nav" aria-label="Разделы настроек">
          {SETTINGS_NAV.map((item) => (
            <NavLink key={item.id} to={item.to} end={item.id === "account"}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <section className="settings__section">
          {current === "account" ? (
            <>
              <p>Вы вошли в аккаунт {account?.email}</p>
              <h2>Ваш канал YouTube</h2>
              <Link className="channel-mini" to={channelTo}>
                <span className="avatar">{name.slice(0, 1).toUpperCase()}</span>
                <span>
                  <strong>{name}</strong>
                  <span className="settings__muted">{channelHandle(name)}</span>
                </span>
              </Link>
            </>
          ) : null}
          {current === "time" ? <p>Таймеры просмотра в этой копии не хранятся.</p> : null}
          {current === "notifications" ? (
            <>
              <h2>Настройки уведомлений</h2>
              <p>
                Колокол в шапке открывает список. Сейчас в нём нет уведомлений. Письма и уведомления браузера эта копия не
                отправляет.
              </p>
            </>
          ) : null}
          {current === "playback" ? (
            <>
              <h2>Воспроизведение</h2>
              <p>Настройки воспроизведения действуют только в этом браузере.</p>
              <label className="settings__line">
                <span>Автовоспроизведение следующего видео</span>
                <input
                  type="checkbox"
                  checked={settings.autoplayNext}
                  onChange={(event) => updateSettings({ autoplayNext: event.target.checked })}
                />
              </label>
            </>
          ) : null}
          {current === "privacy" ? (
            <>
              <h2>Конфиденциальность</h2>
              <label className="settings__line">
                <span>Безопасный режим</span>
                <input
                  type="checkbox"
                  checked={settings.restricted}
                  onChange={(event) => updateSettings({ restricted: event.target.checked })}
                />
              </label>
              <p>В каталоге нет роликов с ограничением по возрасту, поэтому лента от переключателя не меняется.</p>
            </>
          ) : null}
          {current === "apps" ? <p>Подключённых приложений нет.</p> : null}
          {current === "billing" ? <p>Платных подписок нет.</p> : null}
          {current === "advanced" ? (
            <>
              <h2>Расширенные настройки</h2>
              <p>Язык интерфейса: Русский</p>
              <p>Страна: Россия</p>
            </>
          ) : null}
        </section>
      </div>
    </div>
  );
}
