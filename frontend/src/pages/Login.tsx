import React, { useState } from 'react'
import { Form, Input, Button, Checkbox, Card, Space, Typography, Alert } from 'antd'
import { UserOutlined, LockOutlined, LoadingOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useAuth } from '../contexts/AuthContext'
import '../styles/login.css'

const { Title, Text, Link } = Typography

interface LoginFormValues {
  username: string
  password: string
  remember: boolean
}

const Login: React.FC = () => {
  const { login, isLoading } = useAuth()
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState(false)
  const [syncing, setSyncing] = useState(false)

  const onFinish = async (values: LoginFormValues) => {
    setError('')
    setSuccess(false)
    
    try {
      await login(values.username, values.password, values.remember)
      setSuccess(true)
      setSyncing(true)
      
      // Simulate sync progress
      setTimeout(() => {
        setSyncing(false)
      }, 1500)
    } catch (err: any) {
      const errorMessage = err.response?.data?.message || 'Login failed. Please try again.'
      setError(errorMessage)
      setSuccess(false)
      setSyncing(false)
    }
  }

  return (
    <div className="login-container">
      <Card className="login-card">
        <div className="login-header">
          <Title level={2}>AMRS Maintenance Tracker</Title>
          <Text type="secondary">Sign in to continue</Text>
        </div>

        {error && (
          <Alert
            message="Login Failed"
            description={error}
            type="error"
            closable
            onClose={() => setError('')}
            style={{ marginBottom: 16 }}
          />
        )}

        {success && (
          <Alert
            message="Login Successful"
            description="Redirecting to dashboard..."
            type="success"
            icon={<CheckCircleOutlined />}
            style={{ marginBottom: 16 }}
          />
        )}

        {syncing && (
          <Alert
            message="Syncing data..."
            description="Please wait while we sync your data."
            type="info"
            icon={<LoadingOutlined />}
            style={{ marginBottom: 16 }}
          />
        )}

        <Form
          name="login"
          initialValues={{ remember: false }}
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: 'Please input your username!' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="Username" 
              disabled={isLoading || success}
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: 'Please input your password!' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Password"
              disabled={isLoading || success}
            />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Form.Item name="remember" valuePropName="checked" noStyle>
                <Checkbox disabled={isLoading || success}>Remember me</Checkbox>
              </Form.Item>
              <Link href="/forgot-password">Forgot password?</Link>
            </Space>
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={isLoading || syncing}
              disabled={success}
              block
            >
              {success ? 'Redirecting...' : 'Sign In'}
            </Button>
          </Form.Item>
        </Form>

        <div className="login-footer">
          <Text type="secondary">Version 1.4.6</Text>
        </div>
      </Card>
    </div>
  )
}

export default Login
