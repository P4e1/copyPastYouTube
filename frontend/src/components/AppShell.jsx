import { useEffect, useRef, useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { api } from "../api/client";
import { channelHandle } from "../channel";
import { guideItemActive, guideMode, guideYouLinks, visibleSubscriptions } from "../guide";
import { applyKey, keyLabel, keyboardRows, toggleLayout } from "../keyboard";
import { SHORTCUTS, THEME_OPTIONS, headerChrome, subscriptionNotices, themeLabel, voiceQueryPath } from "../settings";
import { useSettings } from "../settings-context";
import { useSession } from "../session";

const NARROW = "(max-width: 791px)";

const PATHS = {
  menu: "M20 5H4a1 1 0 000 2h16a1 1 0 100-2Zm0 6H4a1 1 0 000 2h16a1 1 0 000-2Zm0 6H4a1 1 0 000 2h16a1 1 0 000-2Z",
  search:
    "M11 2a9 9 0 105.641 16.01.966.966 0 00.152.197l3.5 3.5a1 1 0 101.414-1.414l-3.5-3.5a1 1 0 00-.197-.153A8.96 8.96 0 0020 11a9 9 0 00-9-9Zm0 2a7 7 0 110 14 7 7 0 010-14Z",
  mic: "M18.063 14.5a1 1 0 111.73 1A8.998 8.998 0 0113 19.942V22a1 1 0 11-2 0v-2.058A8.999 8.999 0 014.206 15.5l.866-.5.865-.5a7.002 7.002 0 0012.125 0ZM12 1a5 5 0 015 5v5a5 5 0 01-10 0V6a5 5 0 015-5ZM4.572 14.134a1 1 0 011.365.366l-1.731 1a1 1 0 01.366-1.366ZM12 3a3 3 0 00-3 3v5a3 3 0 106 0V6a3 3 0 00-3-3Z",
  home: "m11.485 2.143-8 4.8-2 1.2a1 1 0 001.03 1.714L3 9.567V20a2 2 0 002 2h5v-8h4v8h5a2 2 0 002-2V9.567l.485.29a1 1 0 001.03-1.714l-2-1.2-8-4.8a1 1 0 00-1.03 0Z",
  shorts:
    "m13.467 1.19-8 4.7a5 5 0 00-.255 8.46 5 5 0 005.32 8.462l8-4.7a5 5 0 00.258-8.462 5 5 0 001.641-6.464l-.12-.217a5 5 0 00-6.844-1.78m5.12 2.79a2.999 2.999 0 01-1.067 4.107l-1.327.78a1 1 0 00.096 1.775l.943.423a3 3 0 01.288 5.323l-8 4.7a3 3 0 01-3.039-5.173l1.327-.78a1 1 0 00-.097-1.775l-.942-.423a3 3 0 01-.288-5.323l8-4.7a3 3 0 014.106 1.066ZM15 12l-5-3v6l5-3Z",
  subs: "M18 1H6a2 2 0 00-2 2h16a2 2 0 00-2-2Zm3 4H3a2 2 0 00-2 2v13a2 2 0 002 2h18a2 2 0 002-2V7a2 2 0 00-2-2ZM3 20V7h18v13H3Zm13-6.5L10 10v7l6-3.5Z",
  you: "M12 1C5.925 1 1 5.925 1 12s4.925 11 11 11 11-4.925 11-11S18.075 1 12 1Zm0 2a9 9 0 016.447 15.276 7 7 0 00-12.895 0A9 9 0 0112 3Zm0 2a4 4 0 100 8 4 4 0 000-8Zm0 2a2 2 0 110 4 2 2 0 010-4Zm-.1 9.001L11.899 16a5 5 0 014.904 3.61A8.96 8.96 0 0112 21a8.96 8.96 0 01-4.804-1.391 5 5 0 014.704-3.608Z",
  history:
    "M8.76 1.487a11 11 0 11-7.54 12.706 1 1 0 011.96-.4 9 9 0 0014.254 5.38A9 9 0 0016.79 4.38 9 9 0 004.518 7H7a1 1 0 010 2H1V3a1 1 0 012 0v2.678a11 11 0 015.76-4.192ZM12 6a1 1 0 00-1 1v5.58l.504.288 3.5 2a1 1 0 10.992-1.736L13 11.42V7a1 1 0 00-1-1Z",
  list: "M4 6h16a1 1 0 010 2H4a1 1 0 010-2zm0 5h16a1 1 0 010 2H4a1 1 0 010-2zm0 5h10a1 1 0 010 2H4a1 1 0 010-2z",
  film: "M4 6.5A2.5 2.5 0 016.5 4h11A2.5 2.5 0 0120 6.5v11a2.5 2.5 0 01-2.5 2.5h-11A2.5 2.5 0 014 17.5v-11zM10 9.2v5.6l4.4-2.8L10 9.2z",
  shield: "M12 2 4 5v6c0 5.25 3.4 8.74 8 10 4.6-1.26 8-4.75 8-10V5l-8-3Zm0 2.18 6 2.25V11c0 4.16-2.62 7.12-6 8.22C8.62 18.12 6 15.16 6 11V6.43l6-2.25Z",
  create: "M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z",
  bell: "M12 22a2.5 2.5 0 002.45-2h-4.9A2.5 2.5 0 0012 22zm7-6v-5a6.7 6.7 0 00-5-6.46V4a2 2 0 10-4 0v.54A6.7 6.7 0 005 11v5l-1.7 1.7A1 1 0 004 20h16a1 1 0 00.7-1.7L19 16z",
  gear: "M19.4 13a7.7 7.7 0 000-2l2-1.6-2-3.4-2.4 1a7.4 7.4 0 00-1.7-1L15 3h-4l-.3 2.9a7.4 7.4 0 00-1.7 1l-2.4-1-2 3.4L6.6 11a7.7 7.7 0 000 2l-2 1.6 2 3.4 2.4-1a7.4 7.4 0 001.7 1L11 21h4l.3-2.9a7.4 7.4 0 001.7-1l2.4 1 2-3.4-2-1.7zM13 15.5A3.5 3.5 0 1113 8a3.5 3.5 0 010 7.5z",
};

export function AppShell() {
  const navigate = useNavigate();
  const location = useLocation();
  const [params] = useSearchParams();
  const [query, setQuery] = useState(params.get("q") || "");
  const { token, account, logout } = useSession();
  const { settings, updateSettings } = useSettings();
  const [narrow, setNarrow] = useState(() => window.matchMedia(NARROW).matches);
  const [open, setOpen] = useState(() => !window.matchMedia(NARROW).matches);
  const [searchOpen, setSearchOpen] = useState(false);
  const [keyboard, setKeyboard] = useState(false);
  const [layout, setLayout] = useState("ru");
  const [shift, setShift] = useState(false);
  const [menu, setMenu] = useState(false);
  const [panel, setPanel] = useState("main");
  const [createMenu, setCreateMenu] = useState(false);
  const [notify, setNotify] = useState(false);
  const [notices, setNotices] = useState([]);
  const [voice, setVoice] = useState("");
  const [keys, setKeys] = useState(false);
  const [subscriptions, setSubscriptions] = useState([]);
  const [subsOpen, setSubsOpen] = useState(false);
  const [youOpen, setYouOpen] = useState(true);
  const miniGuide = guideMode({ open, narrow }) === "mini";
  const voiceRef = useRef(null);

  useEffect(() => {
    function onFrame(event) {
      const narrowNow = window.matchMedia(NARROW).matches;
      setOpen(event.detail !== "full" && !narrowNow);
    }
    window.addEventListener("cpy-player-frame", onFrame);
    return () => window.removeEventListener("cpy-player-frame", onFrame);
  }, []);

  useEffect(() => {
    const query = window.matchMedia(NARROW);
    const onChange = (event) => {
      setNarrow(event.matches);
      setOpen(!event.matches);
      setMenu(false);
    };
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    setQuery(params.get("q") || "");
  }, [params]);

  useEffect(() => {
    if (!token) {
      setSubscriptions([]);
      return undefined;
    }
    let active = true;
    api("/subscriptions")
      .then((data) => {
        if (active) {
          setSubscriptions(data.items || []);
        }
      })
      .catch(() => {
        if (active) {
          setSubscriptions([]);
        }
      });
    return () => {
      active = false;
    };
  }, [token]);

  function closeIfNarrow() {
    if (narrow) {
      setOpen(false);
    }
  }

  useEffect(() => {
    if (!createMenu && !menu && !notify) {
      return undefined;
    }
    function onPointer(event) {
      if (event.target.closest(".topbar__end")) {
        return;
      }
      setCreateMenu(false);
      setMenu(false);
      setPanel("main");
      setNotify(false);
    }
    document.addEventListener("mousedown", onPointer);
    return () => document.removeEventListener("mousedown", onPointer);
  }, [createMenu, menu, notify]);

  useEffect(() => {
    if (!notify || !token || !settings.notifySubscriptions) {
      setNotices([]);
      return undefined;
    }
    let active = true;
    Promise.all([api("/feed"), api("/subscriptions")])
      .then(([feed, subs]) => {
        if (!active) {
          return;
        }
        const names = (subs.items || []).map((item) => item.name);
        setNotices(subscriptionNotices(feed.items || [], names, true));
      })
      .catch(() => {
        if (active) {
          setNotices([]);
        }
      });
    return () => {
      active = false;
    };
  }, [notify, token, settings.notifySubscriptions]);

  function onCreate() {
    if (!token) {
      navigate("/login");
      return;
    }
    setMenu(false);
    setNotify(false);
    setCreateMenu((value) => !value);
  }

  function onKeyboard(key) {
    if (key === "shift") {
      setShift((value) => !value);
      return;
    }
    if (key === "layout") {
      setLayout((value) => toggleLayout(value));
      return;
    }
    setQuery((value) => applyKey(value, key, shift));
    setShift(false);
  }

  function onVoice() {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      setVoice("Голосовой поиск недоступен в этом браузере.");
      return;
    }
    const recognition = new Recognition();
    voiceRef.current = recognition;
    recognition.lang = "ru-RU";
    recognition.onresult = (event) => {
      const path = voiceQueryPath(event.results?.[0]?.[0]?.transcript);
      setVoice("");
      if (path) {
        navigate(path);
      }
    };
    recognition.onerror = () => setVoice("Голосовой поиск недоступен в этом браузере.");
    setVoice("Слушаю…");
    try {
      recognition.start();
    } catch {
      setVoice("Голосовой поиск недоступен в этом браузере.");
    }
  }

  function onLogout() {
    logout();
    setMenu(false);
    navigate("/");
  }

  const letter = (account?.username || account?.email || "?").slice(0, 1).toUpperCase();
  const canModerate = account?.role === "moderator" || account?.role === "admin";
  const chrome = headerChrome({ narrow, searchOpen });
  const channelTo = account?.channel_id ? `/channel/${account.channel_id}` : "/you";

  return (
    <div className={open ? "shell shell--nav-open" : "shell"}>
      <header className={narrow && searchOpen ? "topbar topbar--search" : "topbar"}>
        <div className="topbar__start">
          <button
            type="button"
            className="icon-button"
            aria-label="Гид"
            aria-expanded={open}
            onClick={() => setOpen((value) => !value)}
          >
            <Glyph d={PATHS.menu} />
          </button>
          <Link className="logo" to="/" aria-label="Главная страница YouTube">
            <Logo />
            <span className="logo__region">RU</span>
          </Link>
        </div>
        <div className="topbar__center">
          {chrome.showSearchButton ? (
            <button type="button" className="icon-button" aria-label="Поиск" onClick={() => setSearchOpen(true)}>
              <Glyph d={PATHS.search} fillRule="evenodd" />
            </button>
          ) : null}
          {chrome.showSearchForm ? (
            <form
              className="search"
              role="search"
              onSubmit={(event) => {
                event.preventDefault();
                navigate(`/search?q=${encodeURIComponent(query.trim())}`);
              }}
            >
              {narrow ? (
                <button type="button" className="search__back" aria-label="Назад" onClick={() => setSearchOpen(false)}>
                  <Glyph d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z" />
                </button>
              ) : null}
              <div className="search__field">
                <input
                  className="search__input"
                  type="search"
                  aria-label="Поиск"
                  placeholder="Поиск"
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
                <div className="search__tools">
                  <button
                    type="button"
                    className="search__tool"
                    aria-label="Клавиатура"
                    aria-expanded={keyboard}
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => setKeyboard((value) => !value)}
                  >
                    <Glyph d="M4 6h16a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V8a2 2 0 012-2zm1 3v2h2V9H5zm4 0v2h2V9H9zm4 0v2h2V9h-2zm4 0v2h2V9h-2zM5 13v2h4v-2H5zm6 0v2h8v-2h-8z" />
                  </button>
                  {query ? (
                    <button
                      type="button"
                      className="search__tool"
                      aria-label="Очистить поле поиска"
                      onClick={() => setQuery("")}
                    >
                      <Glyph d="M18.3 5.7L12 12l6.3 6.3-1.4 1.4L10.6 13.4 4.3 19.7 2.9 18.3 9.2 12 2.9 5.7 4.3 4.3l6.3 6.3 6.3-6.3 1.4 1.4z" />
                    </button>
                  ) : null}
                </div>
              </div>
              <button className="search__button" type="submit" aria-label="Поиск">
                <Glyph d={PATHS.search} fillRule="evenodd" />
              </button>
            </form>
          ) : null}
          {keyboard && chrome.showSearchForm ? (
            <div className="osk" role="dialog" aria-label={layout === "ru" ? "Русская клавиатура" : "English"}>
              <div className="osk__head">
                <span>{layout === "ru" ? "Русская клавиатура" : "English"}</span>
                <button type="button" aria-label="Закрыть" onClick={() => setKeyboard(false)}>
                  <Glyph d="M18.3 5.7L12 12l6.3 6.3-1.4 1.4L10.6 13.4 4.3 19.7 2.9 18.3 9.2 12 2.9 5.7 4.3 4.3l6.3 6.3 6.3-6.3 1.4 1.4z" />
                </button>
              </div>
              {keyboardRows(layout).map((row, index) => (
                <div className="osk__row" key={index}>
                  {row.map((key, keyIndex) => (
                    <button
                      key={`${key}-${keyIndex}`}
                      type="button"
                      className={key === " " ? "osk__key osk__key--space" : key === "shift" || key === "backspace" || key === "layout" ? "osk__key osk__key--wide" : "osk__key"}
                      aria-label={key === " " ? "Пробел" : key === "backspace" ? "Стереть" : key === "shift" ? "Shift" : key === "layout" ? "Ctrl + Alt" : undefined}
                      aria-pressed={key === "shift" ? shift : undefined}
                      onMouseDown={(event) => event.preventDefault()}
                      onClick={() => onKeyboard(key)}
                    >
                      {keyLabel(key, shift)}
                    </button>
                  ))}
                </div>
              ))}
            </div>
          ) : null}
          <button type="button" className="icon-button mic" aria-label="Голосовой поиск" onClick={onVoice}>
            <Glyph d={PATHS.mic} />
          </button>
        </div>
        <div className="topbar__end">
          <div className="create-wrap">
            <button
              type="button"
              className="chip"
              aria-expanded={token ? createMenu : undefined}
              aria-haspopup={token ? "menu" : undefined}
              onClick={onCreate}
            >
              <Glyph d={PATHS.create} />
              <span>Создать</span>
            </button>
            {token && createMenu ? (
              <div className="create-menu" role="menu">
                <Link role="menuitem" to="/upload" onClick={() => setCreateMenu(false)}>
                  <VideoGlyph />
                  Добавить видео
                </Link>
              </div>
            ) : null}
          </div>
          {token ? (
            <>
              <div className="notify-wrap">
                <button
                  type="button"
                  className="icon-button"
                  aria-label="Уведомления"
                  aria-expanded={notify}
                  onClick={() => {
                    setCreateMenu(false);
                    setMenu(false);
                    setNotify((value) => !value);
                  }}
                >
                  <Glyph d={PATHS.bell} />
                </button>
                {notify ? (
                  <div className="notify-panel" role="dialog" aria-label="Уведомления">
                    <div className="notify-panel__head">
                      <h2>Уведомления</h2>
                      <Link to="/account/notifications" aria-label="Настройки" onClick={() => setNotify(false)}>
                        <Glyph d={PATHS.gear} />
                      </Link>
                    </div>
                    {!settings.notifySubscriptions ? (
                      <p>Уведомления о новых видео с подписок выключены.</p>
                    ) : notices.length ? (
                      <ul className="notify-list">
                        {notices.map((item) => (
                          <li key={item.id}>
                            <Link to={`/watch/${item.id}`} onClick={() => setNotify(false)}>
                              {item.title}
                            </Link>
                            <span>{item.channel_name}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <>
                        <p>Здесь пока ничего нет</p>
                        <p>Подписывайтесь на каналы, чтобы получать уведомления о новых видео.</p>
                      </>
                    )}
                  </div>
                ) : null}
              </div>
              <div className="avatar-wrap">
                <button
                  type="button"
                  className="avatar"
                  aria-label="Меню аккаунта"
                  aria-expanded={menu}
                  onClick={() => {
                    setCreateMenu(false);
                    setNotify(false);
                    setMenu((value) => !value);
                    setPanel("main");
                  }}
                >
                  {letter}
                </button>
                {menu ? (
                  <div className="account-menu" role="menu">
                    {panel === "theme" ? (
                      <>
                        <button type="button" onClick={() => setPanel("main")}>
                          Назад
                        </button>
                        {THEME_OPTIONS.map((option) => (
                          <button
                            key={option.id}
                            type="button"
                            role="menuitemradio"
                            aria-checked={settings.theme === option.id}
                            onClick={() => updateSettings({ theme: option.id })}
                          >
                            {option.label}
                          </button>
                        ))}
                      </>
                    ) : (
                      <>
                        <div className="account-menu__head">
                          <span className="avatar" aria-hidden="true">
                            {letter}
                          </span>
                          <span>
                            <strong>{account?.username || account?.email}</strong>
                            <span className="account-menu__muted">{channelHandle(account?.username || account?.email)}</span>
                          </span>
                        </div>
                        <Link role="menuitem" to={channelTo} onClick={() => setMenu(false)}>
                          Посмотреть канал
                        </Link>
                        <button type="button" role="menuitem" onClick={onLogout}>
                          Выйти
                        </button>
                        <button type="button" role="menuitem" onClick={() => setPanel("theme")}>
                          Тема: {themeLabel(settings.theme)}
                        </button>
                        <p className="account-menu__note">Язык интерфейса: Русский</p>
                        <button
                          type="button"
                          role="menuitemcheckbox"
                          aria-checked={settings.restricted}
                          onClick={() => updateSettings({ restricted: !settings.restricted })}
                        >
                          Безопасный режим: {settings.restricted ? "вкл." : "откл."}
                        </button>
                        <p className="account-menu__note">Страна: Россия</p>
                        <button
                          type="button"
                          role="menuitem"
                          onClick={() => {
                            setMenu(false);
                            setKeys(true);
                          }}
                        >
                          Быстрые клавиши
                        </button>
                        <Link role="menuitem" to="/account" onClick={() => setMenu(false)}>
                          Настройки
                        </Link>
                      </>
                    )}
                  </div>
                ) : null}
              </div>
            </>
          ) : (
            <Link className="signin" to="/login">
              <Glyph d={PATHS.you} />
              Войти
            </Link>
          )}
        </div>
      </header>
      {narrow && open ? (
        <button type="button" className="backdrop" aria-label="Закрыть гид" onClick={() => setOpen(false)} />
      ) : null}
      {voice ? (
        <div className="dialog" role="dialog" aria-label="Голосовой поиск">
          <div className="dialog__card">
            <p>{voice}</p>
            <button
              type="button"
              onClick={() => {
                voiceRef.current?.abort?.();
                setVoice("");
              }}
            >
              Закрыть
            </button>
          </div>
        </div>
      ) : null}
      {keys ? (
        <div className="dialog" role="dialog" aria-label="Быстрые клавиши">
          <div className="dialog__card">
            <h2>Быстрые клавиши</h2>
            <ul>
              {SHORTCUTS.map(([key, action]) => (
                <li key={key}>
                  <span>{key}</span>
                  <span>{action}</span>
                </li>
              ))}
            </ul>
            <button type="button" onClick={() => setKeys(false)}>
              Закрыть
            </button>
          </div>
        </div>
      ) : null}
      <div className="shell__body">
        <nav className="sidebar" aria-label="Разделы">
          <NavLink to="/" end onClick={closeIfNarrow}>
            <Glyph d={PATHS.home} />
            Главная
          </NavLink>
          <NavLink to="/shorts" onClick={closeIfNarrow}>
            <Glyph d={PATHS.shorts} />
            Shorts
          </NavLink>
          <div className="guide-block">
            <NavLink to="/subscriptions" onClick={closeIfNarrow}>
              <Glyph d={PATHS.subs} />
              Подписки
            </NavLink>
            {visibleSubscriptions(subscriptions, subsOpen).map((channel) => (
              <NavLink key={channel.id} className="guide-sub" to={`/channel/${channel.id}`} onClick={closeIfNarrow}>
                <span className="guide-sub__mark" aria-hidden="true">
                  {(channel.name || "?").slice(0, 1).toUpperCase()}
                </span>
                {channel.name}
              </NavLink>
            ))}
            {subscriptions.length > 7 ? (
              <button type="button" className="guide-more" onClick={() => setSubsOpen((value) => !value)}>
                {subsOpen ? "Свернуть" : "Развернуть"}
              </button>
            ) : null}
          </div>
          {token ? (
            <div className="guide-block">
              {miniGuide ? (
                <Link className="guide-head" to={account?.channel_id ? `/channel/${account.channel_id}` : "/you"} onClick={closeIfNarrow}>
                  <Glyph d={PATHS.you} />
                  Вы
                </Link>
              ) : (
                <button type="button" className="guide-head" aria-expanded={youOpen} onClick={() => setYouOpen((value) => !value)}>
                  <Glyph d={PATHS.you} />
                  Вы
                </button>
              )}
              {youOpen
                ? guideYouLinks(account).map((item) => (
                    <Link
                      key={item.id}
                      to={item.to}
                      className={guideItemActive(item, location) ? "active" : undefined}
                      aria-current={guideItemActive(item, location) ? "page" : undefined}
                      onClick={closeIfNarrow}
                    >
                      <Glyph d={PATHS[{ channel: "you", history: "history", playlists: "list", videos: "film" }[item.id]]} />
                      {item.label}
                    </Link>
                  ))
                : null}
            </div>
          ) : (
            <div className="guide-note">
              <p>Войдите, чтобы ставить отметки «Нравится», комментировать и подписываться.</p>
              <Link className="signin" to="/login" onClick={closeIfNarrow}>
                <Glyph d={PATHS.you} />
                Войти
              </Link>
            </div>
          )}
          {canModerate ? (
            <NavLink to="/moderation" onClick={closeIfNarrow}>
              <Glyph d={PATHS.shield} />
              Модерация
            </NavLink>
          ) : null}
        </nav>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

function VideoGlyph() {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
      <path d="M4 6.5A2.5 2.5 0 0 1 6.5 4h11A2.5 2.5 0 0 1 20 6.5v11a2.5 2.5 0 0 1-2.5 2.5h-11A2.5 2.5 0 0 1 4 17.5v-11Zm1.6 0v11c0 .5.4.9.9.9h11c.5 0 .9-.4.9-.9v-11c0-.5-.4-.9-.9-.9h-11c-.5 0-.9.4-.9.9Z" />
      <path d="M10.2 8.7a.7.7 0 0 0-1.1.6v5.4a.7.7 0 0 0 1.1.6l4.2-2.7a.7.7 0 0 0 0-1.2l-4.2-2.7Z" />
    </svg>
  );
}

function Glyph({ d, fillRule }) {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
      <path d={d} fillRule={fillRule} />
    </svg>
  );
}

function Logo() {
  return (
    <svg className="logo__svg" viewBox="0 0 93 20" width="93" height="20" aria-hidden="true">
      <path
        d="M14.4848 20C14.4848 20 23.5695 20 25.8229 19.4C27.0917 19.06 28.0459 18.08 28.3808 16.87C29 14.65 29 9.98 29 9.98C29 9.98 29 5.34 28.3808 3.14C28.0459 1.9 27.0917 0.94 25.8229 0.61C23.5695 0 14.4848 0 14.4848 0C14.4848 0 5.42037 0 3.17711 0.61C1.9286 0.94 0.954148 1.9 0.59888 3.14C0 5.34 0 9.98 0 9.98C0 9.98 0 14.65 0.59888 16.87C0.954148 18.08 1.9286 19.06 3.17711 19.4C5.42037 20 14.4848 20 14.4848 20Z"
        fill="#FF0033"
      />
      <path d="M19 10L11.5 5.75V14.25L19 10Z" fill="#fff" />
      <path d="M37.1384 18.8999V13.4399L40.6084 2.09994H38.0184L36.6984 7.24994C36.3984 8.42994 36.1284 9.65994 35.9284 10.7999H35.7684C35.6584 9.79994 35.3384 8.48994 35.0184 7.22994L33.7384 2.09994H31.1484L34.5684 13.4399V18.8999H37.1384Z" />
      <path d="M44.1003 6.29994C41.0703 6.29994 40.0303 8.04994 40.0303 11.8199V13.6099C40.0303 16.9899 40.6803 19.1099 44.0403 19.1099C47.3503 19.1099 48.0603 17.0899 48.0603 13.6099V11.8199C48.0603 8.44994 47.3803 6.29994 44.1003 6.29994ZM45.3903 14.7199C45.3903 16.3599 45.1003 17.3899 44.0503 17.3899C43.0203 17.3899 42.7303 16.3499 42.7303 14.7199V10.6799C42.7303 9.27994 42.9303 8.02994 44.0503 8.02994C45.2303 8.02994 45.3903 9.34994 45.3903 10.6799V14.7199Z" />
      <path d="M52.2713 19.0899C53.7313 19.0899 54.6413 18.4799 55.3913 17.3799H55.5013L55.6113 18.8999H57.6012V6.53994H54.9613V16.4699C54.6812 16.9599 54.0312 17.3199 53.4212 17.3199C52.6512 17.3199 52.4113 16.7099 52.4113 15.6899V6.53994H49.7812V15.8099C49.7812 17.8199 50.3613 19.0899 52.2713 19.0899Z" />
      <path d="M62.8261 18.8999V4.14994H65.8661V2.09994H57.1761V4.14994H60.2161V18.8999H62.8261Z" />
      <path d="M67.8728 19.0899C69.3328 19.0899 70.2428 18.4799 70.9928 17.3799H71.1028L71.2128 18.8999H73.2028V6.53994H70.5628V16.4699C70.2828 16.9599 69.6328 17.3199 69.0228 17.3199C68.2528 17.3199 68.0128 16.7099 68.0128 15.6899V6.53994H65.3828V15.8099C65.3828 17.8199 65.9628 19.0899 67.8728 19.0899Z" />
      <path d="M80.6744 6.26994C79.3944 6.26994 78.4744 6.82994 77.8644 7.73994H77.7344C77.8144 6.53994 77.8744 5.51994 77.8744 4.70994V1.43994H75.3244L75.3144 12.1799L75.3244 18.8999H77.5444L77.7344 17.6999H77.8044C78.3944 18.5099 79.3044 19.0199 80.5144 19.0199C82.5244 19.0199 83.3844 17.2899 83.3844 13.6099V11.6999C83.3844 8.25994 82.9944 6.26994 80.6744 6.26994ZM80.7644 13.6099C80.7644 15.9099 80.4244 17.2799 79.3544 17.2799C78.8544 17.2799 78.1644 17.0399 77.8544 16.5899V9.23994C78.1244 8.53994 78.7244 8.02994 79.3944 8.02994C80.4744 8.02994 80.7644 9.33994 80.7644 11.7299V13.6099Z" />
      <path d="M92.6517 11.4999C92.6517 8.51994 92.3517 6.30994 88.9217 6.30994C85.6917 6.30994 84.9717 8.45994 84.9717 11.6199V13.7899C84.9717 16.8699 85.6317 19.1099 88.8417 19.1099C91.3817 19.1099 92.6917 17.8399 92.5417 15.3799L90.2917 15.2599C90.2617 16.7799 89.9117 17.3999 88.9017 17.3999C87.6317 17.3999 87.5717 16.1899 87.5717 14.3899V13.5499H92.6517V11.4999ZM88.8617 7.96994C90.0817 7.96994 90.1717 9.11994 90.1717 11.0699V12.0799H87.5717V11.0699C87.5717 9.13994 87.6517 7.96994 88.8617 7.96994Z" />
    </svg>
  );
}
