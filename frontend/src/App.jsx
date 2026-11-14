import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { ChannelPage } from "./pages/ChannelPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { PlaceholderPage } from "./pages/PlaceholderPage";
import { RegisterPage } from "./pages/RegisterPage";
import { SearchPage } from "./pages/SearchPage";
import { SubscriptionsPage } from "./pages/SubscriptionsPage";
import { WatchPage } from "./pages/WatchPage";
import { useSession } from "./session";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/watch/:videoId" element={<WatchPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/shorts" element={<PlaceholderPage text="Смотреть пока нечего" />} />
        <Route path="/subscriptions" element={<SubscriptionsPage />} />
        <Route path="/history" element={<PlaceholderPage text="Смотреть пока нечего" />} />
        <Route path="/channel/:channelId" element={<ChannelPage />} />
        <Route path="/you" element={<YouGate />} />
      </Route>
    </Routes>
  );
}

function YouGate() {
  const { token, account } = useSession();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  if (!account?.channel_id) {
    return null;
  }
  return <Navigate to={`/channel/${account.channel_id}`} replace />;
}
