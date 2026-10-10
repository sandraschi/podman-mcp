import { Navigate, Route, BrowserRouter as Router, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/app-layout";
import { Chat } from "@/pages/chat";
import { Compose } from "@/pages/compose";
import { Containers } from "@/pages/containers";
import { Dashboard } from "@/pages/dashboard";
import { Help } from "@/pages/help";
import { Images } from "@/pages/images";
import { Inbox } from "@/pages/inbox";
import { LogsPage } from "@/pages/logs";
import { MigratePage } from "@/pages/migrate";
import { Networks } from "@/pages/networks";
import { Pods } from "@/pages/pods";
import { Settings } from "@/pages/settings";
import { Skills } from "@/pages/skills";
import { Tools } from "@/pages/tools";
import { Volumes } from "@/pages/volumes";

function App() {
  return (
    <Router>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/containers" element={<Containers />} />
          <Route path="/pods" element={<Pods />} />
          <Route path="/images" element={<Images />} />
          <Route path="/volumes" element={<Volumes />} />
          <Route path="/networks" element={<Networks />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/tools" element={<Tools />} />
          <Route path="/inbox" element={<Inbox />} />
          <Route path="/skills" element={<Skills />} />
          <Route path="/help" element={<Help />} />
          <Route path="/logs" element={<LogsPage />} />
          <Route path="/compose" element={<Compose />} />
          <Route path="/migrate" element={<MigratePage />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppLayout>
    </Router>
  );
}

export default App;
