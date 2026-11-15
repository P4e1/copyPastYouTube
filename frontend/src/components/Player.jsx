import { useEffect, useRef, useState } from "react";

import {
  PLAYBACK_RATES,
  bufferedFraction,
  formatPlayerClock,
  formatPlayerTimeLabel,
  rateLabel,
  seekToRatio,
} from "../player";

const ICONS = {
  play: "M8 5v14l11-7z",
  pause: "M6 5h4v14H6zm8 0h4v14h-4z",
  volume:
    "M3 10v4h4l5 5V5L7 10H3zm13.5 2a4.5 4.5 0 00-2.5-4.03v8.05A4.5 4.5 0 0016.5 12zM14 3.23v2.06a7 7 0 010 13.42v2.06a9 9 0 000-17.54z",
  mute: "M16.5 12l4.5 4.5-1.5 1.5L15 13.5 10.5 18 9 16.5 13.5 12 9 7.5 10.5 6 15 10.5 19.5 6 21 7.5 16.5 12zM3 10v4h4l5 5V5L7 10H3z",
  gear: "M19.4 13a7.7 7.7 0 000-2l2-1.6-2-3.4-2.4 1a7.4 7.4 0 00-1.7-1L15 3h-4l-.3 2.9a7.4 7.4 0 00-1.7 1l-2.4-1-2 3.4L6.6 11a7.7 7.7 0 000 2l-2 1.6 2 3.4 2.4-1a7.4 7.4 0 001.7 1L11 21h4l.3-2.9a7.4 7.4 0 001.7-1l2.4 1 2-3.4-2-1.7zM13 15.5A3.5 3.5 0 1113 8a3.5 3.5 0 010 7.5z",
  theater: "M3 5h18v14H3V5zm11 2v10h5V7h-5z",
  theaterOn: "M3 5h18v14H3V5zm2 2v10h5V7H5z",
  full: "M7 14H5v5h5v-2H7v-3zm0-4h3V7h2V5H5v5zm10 7h-3v2h5v-5h-2v3zM14 7V5h5v5h-2V7h-3z",
  exitFull: "M5 16h3v3h2v-5H5v2zm3-8H5v2h5V5H8v3zm6 11h2v-3h3v-2h-5v5zm2-11V5h-2v5h5V8h-3z",
  captions: "M20 4H4a2 2 0 00-2 2v12a2 2 0 002 2h16a2 2 0 002-2V6a2 2 0 00-2-2zM7 15H5v-2h2v2zm0-4H5V9h2v2zm10 4h-6v-2h6v2zm0-4h-6V9h6v2z",
};

export function Player({ src, autoPlay = false, theater = false, onTheater, onAutoplayNext }) {
  const rootRef = useRef(null);
  const videoRef = useRef(null);
  const barRef = useRef(null);
  const hideTimer = useRef(0);
  const clickTimer = useRef(0);
  const [playing, setPlaying] = useState(false);
  const [time, setTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [buffered, setBuffered] = useState(0);
  const [volume, setVolume] = useState(1);
  const [muted, setMuted] = useState(false);
  const [rate, setRate] = useState(1);
  const [menu, setMenu] = useState(null);
  const [chrome, setChrome] = useState(true);
  const [remaining, setRemaining] = useState(false);
  const [full, setFull] = useState(false);
  const [autoplay, setAutoplay] = useState(false);
  const [nudge, setNudge] = useState("");

  useEffect(() => {
    const node = videoRef.current;
    if (!node) {
      return undefined;
    }
    node.playbackRate = rate;
    node.volume = volume;
    node.muted = muted;
    if (autoPlay) {
      node.play().catch(() => setPlaying(false));
    }
    return undefined;
  }, [src]);

  useEffect(() => {
    function onFull() {
      setFull(document.fullscreenElement === rootRef.current);
    }
    document.addEventListener("fullscreenchange", onFull);
    return () => document.removeEventListener("fullscreenchange", onFull);
  }, []);

  useEffect(() => {
    function onKey(event) {
      const tag = event.target?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || event.target?.isContentEditable) {
        return;
      }
      if (event.metaKey || event.ctrlKey || event.altKey) {
        return;
      }
      const video = videoRef.current;
      if (!video) {
        return;
      }
      const key = event.key.toLowerCase();
      if (key === " " || key === "k") {
        event.preventDefault();
        togglePlay();
      } else if (key === "m") {
        event.preventDefault();
        setMuted((value) => !value);
      } else if (key === "f") {
        event.preventDefault();
        toggleFull();
      } else if (key === "t") {
        event.preventDefault();
        onTheater?.(!theater);
      } else if (event.key === "ArrowLeft" || event.key === "ArrowRight") {
        event.preventDefault();
        const delta = event.key === "ArrowLeft" ? -5 : 5;
        video.currentTime = Math.min(video.duration || 0, Math.max(0, video.currentTime + delta));
      } else if (event.key === "ArrowUp" || event.key === "ArrowDown") {
        event.preventDefault();
        setMuted(false);
        setVolume((value) => Math.min(1, Math.max(0, value + (event.key === "ArrowUp" ? 0.05 : -0.05))));
      }
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  });

  useEffect(() => {
    const video = videoRef.current;
    if (video) {
      video.volume = volume;
      video.muted = muted || volume === 0;
    }
  }, [volume, muted]);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = rate;
    }
  }, [rate]);

  useEffect(() => {
    if (!nudge) {
      return undefined;
    }
    const timer = window.setTimeout(() => setNudge(""), 700);
    return () => window.clearTimeout(timer);
  }, [nudge]);

  function reveal() {
    setChrome(true);
    window.clearTimeout(hideTimer.current);
    if (videoRef.current && !videoRef.current.paused) {
      hideTimer.current = window.setTimeout(() => setChrome(false), 2500);
    }
  }

  function togglePlay() {
    const video = videoRef.current;
    if (!video) {
      return;
    }
    if (video.paused) {
      video.play().catch(() => {});
    } else {
      video.pause();
    }
  }

  function toggleFull() {
    const node = rootRef.current;
    if (!node) {
      return;
    }
    if (document.fullscreenElement) {
      document.exitFullscreen?.();
    } else {
      node.requestFullscreen?.();
    }
  }

  function seekFromClient(clientX) {
    const bar = barRef.current;
    const video = videoRef.current;
    if (!bar || !video) {
      return;
    }
    const rect = bar.getBoundingClientRect();
    const ratio = rect.width ? (clientX - rect.left) / rect.width : 0;
    video.currentTime = seekToRatio(ratio, video.duration || 0);
  }

  function onPointerDown(event) {
    event.preventDefault();
    seekFromClient(event.clientX);
    function move(next) {
      seekFromClient(next.clientX);
    }
    function up() {
      document.removeEventListener("pointermove", move);
      document.removeEventListener("pointerup", up);
    }
    document.addEventListener("pointermove", move);
    document.addEventListener("pointerup", up);
  }

  function onSurfaceClick(event) {
    if (event.target.closest(".yt-player__chrome, .yt-player__menu")) {
      return;
    }
    if (clickTimer.current) {
      window.clearTimeout(clickTimer.current);
      clickTimer.current = 0;
      return;
    }
    clickTimer.current = window.setTimeout(() => {
      clickTimer.current = 0;
      togglePlay();
    }, 220);
  }

  function onSurfaceDoubleClick(event) {
    if (event.target.closest(".yt-player__chrome, .yt-player__menu")) {
      return;
    }
    window.clearTimeout(clickTimer.current);
    clickTimer.current = 0;
    const video = videoRef.current;
    const rect = event.currentTarget.getBoundingClientRect();
    const backward = event.clientX < rect.left + rect.width / 2;
    if (!video) {
      return;
    }
    video.currentTime = Math.min(video.duration || 0, Math.max(0, video.currentTime + (backward ? -10 : 10)));
    setNudge(backward ? "« 10 секунд" : "10 секунд »");
  }

  function sync(event) {
    const video = event.currentTarget;
    const ranges = [];
    for (let index = 0; index < video.buffered.length; index += 1) {
      ranges.push([video.buffered.start(index), video.buffered.end(index)]);
    }
    setTime(video.currentTime || 0);
    setDuration(Number.isFinite(video.duration) ? video.duration : 0);
    setBuffered(bufferedFraction(ranges, video.currentTime || 0, video.duration || 0));
    setPlaying(!video.paused);
  }

  function onEnded() {
    setPlaying(false);
    setChrome(true);
    if (autoplay) {
      onAutoplayNext?.();
    }
  }

  const played = duration ? Math.min(1, time / duration) : 0;
  const clock = remaining
    ? `-${formatPlayerClock(Math.max(0, duration - time))}`
    : `${formatPlayerClock(time)} / ${formatPlayerClock(duration)}`;
  const shown = chrome || !playing || menu;

  return (
    <div
      ref={rootRef}
      className={shown ? "yt-player yt-player--chrome" : "yt-player"}
      onMouseMove={reveal}
      onMouseLeave={() => playing && !menu && setChrome(false)}
      onClick={onSurfaceClick}
      onDoubleClick={onSurfaceDoubleClick}
    >
      <video
        ref={videoRef}
        className="yt-player__video"
        src={src}
        autoPlay={autoPlay}
        playsInline
        onPlay={() => {
          setPlaying(true);
          reveal();
        }}
        onPause={() => {
          setPlaying(false);
          setChrome(true);
        }}
        onTimeUpdate={sync}
        onProgress={sync}
        onLoadedMetadata={sync}
        onEnded={onEnded}
      />
      {nudge ? <div className={nudge.startsWith("«") ? "yt-player__nudge yt-player__nudge--left" : "yt-player__nudge yt-player__nudge--right"}>{nudge}</div> : null}
      <div className="yt-player__chrome">
        <div
          ref={barRef}
          className="yt-player__progress"
          role="slider"
          aria-label="Ползунок поиска"
          aria-valuemin={0}
          aria-valuemax={Math.floor(duration)}
          aria-valuenow={Math.floor(time)}
          onPointerDown={onPointerDown}
        >
          <div className="yt-player__track">
            <div className="yt-player__buffer" style={{ width: `${buffered * 100}%` }} />
            <div className="yt-player__played" style={{ width: `${played * 100}%` }} />
            <div className="yt-player__knob" style={{ left: `${played * 100}%` }} />
          </div>
        </div>
        <div className="yt-player__bar">
          <div className="yt-player__group">
            <button type="button" className="yt-player__btn" aria-label={playing ? "Пауза (k)" : "Воспроизвести (k)"} onClick={togglePlay}>
              <Glyph d={playing ? ICONS.pause : ICONS.play} />
            </button>
            <div className="yt-player__volume">
              <button
                type="button"
                className="yt-player__btn"
                aria-label={muted || volume === 0 ? "Включить звук (m)" : "Отключение звука (m)"}
                onClick={() => setMuted((value) => !value)}
              >
                <Glyph d={muted || volume === 0 ? ICONS.mute : ICONS.volume} />
              </button>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                aria-label="Громкость"
                value={muted ? 0 : volume}
                onChange={(event) => {
                  const next = Number(event.target.value);
                  setVolume(next);
                  setMuted(next === 0);
                }}
              />
            </div>
            <button
              type="button"
              className="yt-player__time"
              aria-label={formatPlayerTimeLabel(time, duration)}
              onClick={() => setRemaining((value) => !value)}
            >
              {clock}
            </button>
          </div>
          <div className="yt-player__group">
            <button
              type="button"
              className={autoplay ? "yt-player__btn yt-player__btn--on" : "yt-player__btn"}
              aria-label={autoplay ? "Автовоспроизведение включено" : "Автовоспроизведение выключено"}
              aria-pressed={autoplay}
              onClick={() => setAutoplay((value) => !value)}
            >
              <Glyph d={ICONS.play} />
            </button>
            <button type="button" className="yt-player__btn" aria-label="Субтитры недоступны" disabled>
              <Glyph d={ICONS.captions} />
            </button>
            <button
              type="button"
              className="yt-player__btn"
              aria-label="Настройки"
              aria-expanded={Boolean(menu)}
              onClick={() => setMenu((value) => (value ? null : "root"))}
            >
              <Glyph d={ICONS.gear} />
            </button>
            <button
              type="button"
              className="yt-player__btn"
              aria-label={theater ? "Обычный экран (t)" : "Широкий экран (t)"}
              aria-pressed={theater}
              onClick={() => onTheater?.(!theater)}
            >
              <Glyph d={theater ? ICONS.theaterOn : ICONS.theater} />
            </button>
            <button
              type="button"
              className="yt-player__btn"
              aria-label={full ? "Выйти из полноэкранного режима (f)" : "Во весь экран (f)"}
              onClick={toggleFull}
            >
              <Glyph d={full ? ICONS.exitFull : ICONS.full} />
            </button>
          </div>
        </div>
      </div>
      {menu ? (
        <div className="yt-player__menu" role="menu" aria-label="Настройки">
          {menu === "root" ? (
            <button type="button" onClick={() => setMenu("speed")}>
              <span>Скорость воспроизведения</span>
              <span>{rateLabel(rate)}</span>
            </button>
          ) : (
            <>
              <button type="button" onClick={() => setMenu("root")}>
                Скорость воспроизведения
              </button>
              {PLAYBACK_RATES.map((item) => (
                <button
                  key={item}
                  type="button"
                  role="menuitemradio"
                  aria-checked={item === rate}
                  onClick={() => {
                    setRate(item);
                    setMenu(null);
                  }}
                >
                  <span>{item === rate ? "✓" : ""}</span>
                  <span>{rateLabel(item)}</span>
                </button>
              ))}
            </>
          )}
        </div>
      ) : null}
    </div>
  );
}

function Glyph({ d }) {
  return (
    <svg viewBox="0 0 24 24" width="24" height="24" aria-hidden="true">
      <path d={d} />
    </svg>
  );
}
