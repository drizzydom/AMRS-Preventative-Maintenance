import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import TitleBar from './components/TitleBar'
import MenuBar from './components/MenuBar'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Machines from './pages/Machines'
import Maintenance from './pages/Maintenance'
import Audits from './pages/Audits'
import Sites from './pages/Sites'
import Users from './pages/admin/Users'
import Settings from './pages/Settings'
import ReportsPreview from './pages/reports/ReportsPreview'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/auth/ProtectedRoute'
import './styles/App.css'

const { Content } = Layout

function App() {
  return (
    <AuthProvider>
      <Layout className="app-layout">
        <TitleBar />
        <MenuBar />
        <Layout hasSider>
          <Sidebar />
          <Layout className="content-layout">
            <Content className="app-content">
              <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/machines"
                  element={
                    <ProtectedRoute>
                      <Machines />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/maintenance"
                  element={
                    <ProtectedRoute>
                      <Maintenance />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/audits"
                  element={
                    <ProtectedRoute>
                      <Audits />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/sites"
                  element={
                    <ProtectedRoute>
                      <Sites />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/users"
                  element={
                    <ProtectedRoute>
                      <Users />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/settings"
                  element={
                    <ProtectedRoute>
                      <Settings />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/reports"
                  element={
                    <ProtectedRoute>
                      <ReportsPreview />
                    </ProtectedRoute>
                  }
                />
                <Route path="/" element={<Navigate to="/login" replace />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      </Layout>
    </AuthProvider>
  )
}

export default App
