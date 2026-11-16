import { Navigate, Route, Routes } from "react-router-dom";

import { AppShell } from "./components/AppShell";
import { ChannelPage } from "./pages/ChannelPage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { ModerationPage } from "./pages/ModerationPage";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { SearchPage } from "./pages/SearchPage";
import { ShortsPage } from "./pages/ShortsPage";
import { SettingsPage } from "./pages/SettingsPage";
import { SubscriptionsPage } from "./pages/SubscriptionsPage";
import { UploadPage } from "./pages/UploadPage";
import { WatchPage } from "./pages/WatchPage";
import { useSession } from "./session";

export function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<AppShell />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/watch/:videoId" element={<WatchPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/shorts" element={<ShortsPage />} />
        <Route path="/subscriptions" element={<SubscriptionsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/moderation" element={<ModerationPage />} />
        <Route path="/channel/:channelId" element={<ChannelPage />} />
        <Route path="/account" element={<SettingsPage />} />
        <Route path="/account/:section" element={<SettingsPage />} />
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
