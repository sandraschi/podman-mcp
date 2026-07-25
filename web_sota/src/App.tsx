import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from '@/components/layout/app-layout';
import { Dashboard } from '@/pages/dashboard';
import { Containers } from '@/pages/containers';
import { Pods } from '@/pages/pods';
import { Images } from '@/pages/images';
import { Volumes } from '@/pages/volumes';
import { Networks } from '@/pages/networks';
import { Chat } from '@/pages/chat';
import { Tools } from '@/pages/tools';
import { Help } from '@/pages/help';
import { Settings } from '@/pages/settings';
import { LogsPage } from '@/pages/logs';
import { Compose } from '@/pages/compose';
import { MigratePage } from '@/pages/migrate';

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
