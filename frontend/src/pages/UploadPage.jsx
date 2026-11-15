import { useEffect, useState } from "react";
import { Link, Navigate } from "react-router-dom";

import { api } from "../api/client";
import { useSession } from "../session";

const VISIBILITY = [
  { value: "public", label: "Открытый доступ" },
  { value: "unlisted", label: "Доступ по ссылке" },
  { value: "private", label: "Ограниченный доступ" },
];

export function UploadPage() {
  const { token } = useSession();
  const [step, setStep] = useState("file");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const [draft, setDraft] = useState(null);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [visibility, setVisibility] = useState("public");
  const [query, setQuery] = useState("");
  const [found, setFound] = useState([]);
  const [grants, setGrants] = useState([]);
  const [status, setStatus] = useState("processing");

  useEffect(() => {
    if (visibility !== "private" || query.trim().length < 2) {
      setFound([]);
      return undefined;
    }
    let active = true;
    api(`/users?q=${encodeURIComponent(query.trim())}`)
      .then((data) => {
        if (active) {
          setFound(data.items);
        }
      })
      .catch(() => {
        if (active) {
          setFound([]);
        }
      });
    return () => {
      active = false;
    };
  }, [query, visibility]);

  useEffect(() => {
    if (step !== "processing" || !draft) {
      return undefined;
    }
    let active = true;
    const timer = setInterval(() => {
      api(`/videos/${draft.id}`)
        .then((card) => {
          if (active) {
            setStatus(card.status);
          }
        })
        .catch(() => {});
    }, 2000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, [step, draft]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  async function onFile(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }
    const mp4 = file.type === "video/mp4" || file.name.toLowerCase().endsWith(".mp4");
    if (!mp4) {
      setError("Нужен файл mp4");
      return;
    }
    setError("");
    setProgress(0);
    const draftTitle = file.name.replace(/\.mp4$/i, "") || "Черновик";
    try {
      const created = await api("/videos", {
        method: "POST",
        body: { title: draftTitle, description: "", visibility: "public", grant_user_ids: [] },
      });
      setDraft(created);
      setTitle(draftTitle);
      await putFile(created.upload_url, file, setProgress);
      setProgress(100);
    } catch (err) {
      setError(err.message || "Не удалось создать ролик");
    }
  }

  async function save(event) {
    event.preventDefault();
    if (!draft || progress < 100) {
      return;
    }
    setError("");
    await api(`/videos/${draft.id}`, {
      method: "PATCH",
      body: {
        title: title.trim(),
        description,
        visibility,
        grant_user_ids: visibility === "private" ? grants.map((person) => person.id) : [],
      },
    });
    await api(`/videos/${draft.id}/complete`, { method: "POST" });
    setStatus("processing");
    setStep("processing");
  }

  return (
    <section className="upload">
      <h1>Загрузка</h1>
      {error ? <p className="upload__error">{error}</p> : null}
      {step === "file" ? (
        <div className="upload__step">
          <label className="upload__file">
            Выбрать mp4
            <input type="file" accept="video/mp4,.mp4" onChange={onFile} />
          </label>
          <div className="upload__bar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress} role="progressbar">
            <span style={{ width: `${progress}%` }} />
          </div>
          <p>{progress}%</p>
          <button type="button" disabled={progress < 100} onClick={() => setStep("details")}>
            Далее
          </button>
        </div>
      ) : null}
      {step === "details" ? (
        <form className="upload__step" onSubmit={save}>
          <label>
            Название
            <input value={title} onChange={(event) => setTitle(event.target.value)} required />
          </label>
          <label>
            Описание
            <textarea value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <fieldset>
            <legend>Видимость</legend>
            {VISIBILITY.map((item) => (
              <label key={item.value}>
                <input
                  type="radio"
                  name="visibility"
                  value={item.value}
                  checked={visibility === item.value}
                  onChange={() => setVisibility(item.value)}
                />
                {item.label}
              </label>
            ))}
          </fieldset>
          {visibility === "private" ? (
            <div className="upload__people">
              <input
                value={query}
                placeholder="Имя пользователя"
                aria-label="Имя пользователя"
                onChange={(event) => setQuery(event.target.value)}
              />
              <ul>
                {found.map((person) => (
                  <li key={person.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setGrants((items) => (items.some((item) => item.id === person.id) ? items : [...items, person]));
                      }}
                    >
                      {person.username}
                    </button>
                  </li>
                ))}
              </ul>
              <p>{grants.map((person) => person.username).join(", ")}</p>
            </div>
          ) : null}
          <button type="submit" disabled={progress < 100 || !title.trim()}>
            Сохранить
          </button>
        </form>
      ) : null}
      {step === "processing" ? (
        <div className="upload__step">
          {status === "ready" ? (
            <p>
              Ролик готов. <Link to={`/watch/${draft.id}`}>Смотреть</Link>
            </p>
          ) : status === "failed" ? (
            <p>Не удалось обработать ролик</p>
          ) : (
            <p>Ролик обрабатывается</p>
          )}
        </div>
      ) : null}
    </section>
  );
}

function putFile(url, file, onProgress) {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    xhr.setRequestHeader("Content-Type", "video/mp4");
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress(100);
        resolve();
      } else {
        reject(new Error("Не удалось отправить файл"));
      }
    };
    xhr.onerror = () => reject(new Error("Не удалось отправить файл"));
    xhr.send(file);
  });
}
