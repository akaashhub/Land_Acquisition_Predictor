import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Projects from "./pages/Projects";
import ProjectDetail from "./pages/ProjectDetail";
import RiskMonitor from "./pages/RiskMonitor";
import Alerts from "./pages/Alerts";
import MapPage from "./pages/MapPage";
import Analytics from "./pages/Analytics";
import WhatIf from "./pages/WhatIf";
import Upload from "./pages/Upload";
import ModelInsights from "./pages/ModelInsights";
import Settings from "./pages/Settings";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem("token");
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Dashboard />} />
          <Route path="projects" element={<Projects />} />
          <Route path="projects/:id" element={<ProjectDetail />} />
          <Route path="risk-monitor" element={<RiskMonitor />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="map" element={<MapPage />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="what-if" element={<WhatIf />} />
          <Route path="upload" element={<Upload />} />
          <Route path="model" element={<ModelInsights />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
