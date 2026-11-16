import { Link, Navigate, NavLink, useNavigate, useParams } from "react-router-dom";

import { channelHandle } from "../channel";
import { PLAYBACK_RATES, rateLabel } from "../player";
import { BREAK_OPTIONS, SETTINGS_NAV, THEME_OPTIONS, roleLabel } from "../settings";
import { useSettings } from "../settings-context";
import { useSession } from "../session";

export function SettingsPage() {
  const navigate = useNavigate();
  const { token, account, logout } = useSession();
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
              <p className="settings__muted">Роль: {roleLabel(account?.role)}</p>
              <h2>Ваш канал YouTube</h2>
              <Link className="channel-mini" to={channelTo}>
                <span className="avatar">{name.slice(0, 1).toUpperCase()}</span>
                <span>
                  <strong>{name}</strong>
                  <span className="settings__muted">{channelHandle(name)}</span>
                </span>
              </Link>
              <button
                type="button"
                className="settings__action"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
              >
                Выйти
              </button>
            </>
          ) : null}
          {current === "time" ? (
            <>
              <h2>Напоминание о перерыве</h2>
              <p>Плеер ставится на паузу, когда непрерывный просмотр достигает выбранного срока. Таймер живёт в этом браузере.</p>
              <label className="settings__line">
                <span>Напоминать</span>
                <select
                  aria-label="Напоминание о перерыве"
                  value={settings.breakMinutes}
                  onChange={(event) => updateSettings({ breakMinutes: Number(event.target.value) })}
                >
                  {BREAK_OPTIONS.map((option) => (
                    <option key={option.id} value={option.id}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </>
          ) : null}
          {current === "notifications" ? (
            <>
              <h2>Настройки уведомлений</h2>
              <label className="settings__line">
                <span>Видео с каналов, на которые вы подписаны</span>
                <input
                  type="checkbox"
                  checked={settings.notifySubscriptions}
                  onChange={(event) => updateSettings({ notifySubscriptions: event.target.checked })}
                />
              </label>
              <p>Колокол в шапке показывает новые ролики этих каналов из ленты. Письма и уведомления браузера эта копия не отправляет.</p>
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
              <label className="settings__line">
                <span>Скорость воспроизведения</span>
                <select
                  aria-label="Скорость воспроизведения"
                  value={settings.playbackRate}
                  onChange={(event) => updateSettings({ playbackRate: Number(event.target.value) })}
                >
                  {PLAYBACK_RATES.map((rate) => (
                    <option key={rate} value={rate}>
                      {rateLabel(rate)}
                    </option>
                  ))}
                </select>
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
              <label className="settings__line">
                <span>Засчитывать мой просмотр</span>
                <input
                  type="checkbox"
                  checked={settings.saveViews}
                  onChange={(event) => updateSettings({ saveViews: event.target.checked })}
                />
              </label>
              <p>Если выключить, этот браузер не увеличивает счётчик просмотров.</p>
            </>
          ) : null}
          {current === "apps" ? (
            <>
              <h2>Связанные приложения</h2>
              <p>Приложений с доступом к аккаунту нет.</p>
            </>
          ) : null}
          {current === "billing" ? (
            <>
              <h2>Покупки и платные подписки</h2>
              <p>Платных подписок нет.</p>
            </>
          ) : null}
          {current === "advanced" ? (
            <>
              <h2>Расширенные настройки</h2>
              <fieldset className="settings__choices">
                <legend>Тема</legend>
                {THEME_OPTIONS.map((option) => (
                  <label key={option.id}>
                    <input
                      type="radio"
                      name="theme"
                      checked={settings.theme === option.id}
                      onChange={() => updateSettings({ theme: option.id })}
                    />
                    {option.label}
                  </label>
                ))}
              </fieldset>
              <p>Язык интерфейса: Русский</p>
              <p>Страна: Россия</p>
            </>
          ) : null}
        </section>
      </div>
    </div>
  );
}
