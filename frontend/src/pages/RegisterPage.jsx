import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useSession } from "../session";

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useSession();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      await register(email, username, password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Не удалось зарегистрироваться");
    }
  }

  return (
    <main className="auth">
      <form className="auth__card" onSubmit={onSubmit}>
        <h1>Регистрация</h1>
        <label>
          Email
          <input type="email" value={email} autoComplete="email" onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label>
          Имя
          <input value={username} autoComplete="username" onChange={(event) => setUsername(event.target.value)} required />
        </label>
        <label>
          Пароль
          <input
            type="password"
            value={password}
            autoComplete="new-password"
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error ? <p className="auth__error">{error}</p> : null}
        <button type="submit">Создать аккаунт</button>
        <p className="auth__switch">
          Уже есть аккаунт? <Link to="/login">Вход</Link>
        </p>
      </form>
    </main>
  );
}
