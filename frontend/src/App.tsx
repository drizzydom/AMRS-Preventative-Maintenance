import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import TitleBar from './components/TitleBar'
import MenuBar from './components/MenuBar'
import Sidebar from './components/Sidebar'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
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
