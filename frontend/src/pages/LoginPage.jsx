import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useSession } from "../session";

export function LoginPage() {
  const navigate = useNavigate();
  const { login } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event) {
    event.preventDefault();
    setError("");
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      setError(err.message || "Неверный email или пароль");
    }
  }

  return (
    <main className="auth">
      <form className="auth__card" onSubmit={onSubmit}>
        <h1>Вход</h1>
        <label>
          Email
          <input type="email" value={email} autoComplete="email" onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label>
          Пароль
          <input
            type="password"
            value={password}
            autoComplete="current-password"
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        {error ? <p className="auth__error">{error}</p> : null}
        <button type="submit">Войти</button>
        <p className="auth__switch">
          Нет аккаунта? <Link to="/register">Регистрация</Link>
        </p>
      </form>
    </main>
  );
}
