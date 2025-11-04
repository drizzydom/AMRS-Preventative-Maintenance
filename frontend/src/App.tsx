import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout, Spin } from 'antd'
import TitleBar from './components/TitleBar'
import MenuBar from './components/MenuBar'
import Sidebar from './components/Sidebar'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/auth/ProtectedRoute'
import './styles/App.css'

const { Content } = Layout

// Lazy load pages for better performance
const Login = lazy(() => import('./pages/Login'))
const Dashboard = lazy(() => import('./pages/Dashboard'))
const Machines = lazy(() => import('./pages/Machines'))
const Maintenance = lazy(() => import('./pages/Maintenance'))
const Audits = lazy(() => import('./pages/Audits'))
const Sites = lazy(() => import('./pages/Sites'))
const Users = lazy(() => import('./pages/admin/Users'))
const Settings = lazy(() => import('./pages/Settings'))
const ReportsPreview = lazy(() => import('./pages/reports/ReportsPreview'))
const AuditReportsPreview = lazy(() => import('./pages/reports/AuditReportsPreview'))

// Loading component for lazy loaded pages
const PageLoader = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '100%',
    minHeight: '400px'
  }}>
    <Spin size="large" tip="Loading..." />
  </div>
)

function App() {
  return (
    <AuthProvider>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          {/* Public route - Login page without sidebar/menubar */}
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes with app layout */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout className="app-layout">
                  <TitleBar />
                  <MenuBar />
                  <Layout hasSider>
                    <Sidebar />
                    <Layout className="content-layout">
                      <Content className="app-content">
                        <Routes>
                          <Route path="/dashboard" element={<Dashboard />} />
                          <Route path="/machines" element={<Machines />} />
                          <Route path="/maintenance" element={<Maintenance />} />
                          <Route path="/audits" element={<Audits />} />
                          <Route path="/sites" element={<Sites />} />
                          <Route path="/users" element={<Users />} />
                          <Route path="/settings" element={<Settings />} />
                          <Route path="/reports" element={<ReportsPreview />} />
                          <Route path="/reports/audits" element={<AuditReportsPreview />} />
                          <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        </Routes>
                      </Content>
                    </Layout>
                  </Layout>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </Suspense>
    </AuthProvider>
  )
}

export default App
