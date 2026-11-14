import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { RegisterPage } from "./pages/RegisterPage";
import { useSession } from "./session";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/shorts" element={<PlaceholderPage text="Смотреть пока нечего" />} />
        <Route path="/subscriptions" element={<PlaceholderPage text="Смотреть пока нечего" />} />
        <Route path="/history" element={<PlaceholderPage text="Смотреть пока нечего" />} />
        <Route path="/you" element={<YouGate />} />
      </Route>
    </Routes>
  );
}

function YouGate() {
  const { token } = useSession();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <PlaceholderPage text="Смотреть пока нечего" />;
}
