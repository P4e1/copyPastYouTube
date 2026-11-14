import { createContext, useContext, useEffect, useMemo, useState } from "react";

import { api, clearToken, readToken, writeToken } from "./api/client";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const [token, setToken] = useState(() => readToken());
  const [account, setAccount] = useState(null);

  useEffect(() => {
    if (!token) {
      setAccount(null);
      return undefined;
    }
    let active = true;
    api("/auth/me")
      .then((next) => {
        if (active) {
          setAccount(next);
        }
      })
      .catch(() => {
        if (!active) {
          return;
        }
        clearToken();
        setToken(null);
        setAccount(null);
      });
    return () => {
      active = false;
    };
  }, [token]);

  const value = useMemo(
    () => ({
      token,
      account,
      async login(email, password) {
        const data = await api("/auth/login", {
          method: "POST",
          auth: false,
          body: { email, password },
        });
        writeToken(data.access_token);
        setToken(data.access_token);
        setAccount(data.user);
      },
      async register(email, username, password) {
        await api("/auth/register", {
          method: "POST",
          auth: false,
          body: { email, username, password },
        });
        const data = await api("/auth/login", {
          method: "POST",
          auth: false,
          body: { email, password },
        });
        writeToken(data.access_token);
        setToken(data.access_token);
        setAccount(data.user);
      },
      logout() {
        clearToken();
        setToken(null);
        setAccount(null);
      },
    }),
    [token, account],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const value = useContext(SessionContext);
  if (value === null) {
    throw new Error("Сессия не подключена");
  }
  return value;
}
