import { Navigate, Route, Routes } from 'react-router-dom';

import { useAuth } from './context/AuthContext';
import DashboardPage from './pages/DashboardPage';
import LoginPage from './pages/LoginPage';
import ProjectDetailPage from './pages/ProjectDetailPage';

function ProtectedRoute({ children }) {
  const { token } = useAuth();
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/projects/:projectId"
        element={
          <ProtectedRoute>
            <ProjectDetailPage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
