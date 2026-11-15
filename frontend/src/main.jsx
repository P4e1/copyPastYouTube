import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";

import { App } from "./App";
import { SettingsProvider } from "./settings-context";
import { SessionProvider } from "./session";
import "./styles.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <SettingsProvider>
        <SessionProvider>
          <App />
        </SessionProvider>
      </SettingsProvider>
    </BrowserRouter>
  </StrictMode>,
);
