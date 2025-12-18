import React, { useEffect, useRef, useState } from 'react'
import { Form, Input, Button, Checkbox, Card, Space, Typography, Alert, Steps, Tag, Spin } from 'antd'
import { UserOutlined, LockOutlined, LoadingOutlined, CheckCircleOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useAuth, LoginFeedback, LoginError } from '../contexts/AuthContext'
import '../styles/login.css'

const { Title, Text, Link } = Typography

interface LoginFormValues {
  username: string
  password: string
  remember: boolean
}

type StepVisualStatus = 'wait' | 'process' | 'finish' | 'error'

const mapStepStatus = (status?: string): StepVisualStatus => {
  switch (status) {
    case 'success':
      return 'finish'
    case 'pending':
      return 'process'
    case 'error':
      return 'error'
    default:
      return 'wait'
  }
}

const formatStatusLabel = (value?: string) => {
  if (!value) return 'Pending'
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

const finalStatusColor = (value?: string) => {
  switch (value) {
    case 'session_ready':
      return 'green'
    case 'invalid_credentials':
    case 'account_locked':
      return 'red'
    case 'validation_failed':
      return 'gold'
    case 'error':
      return 'red'
    default:
      return 'blue'
  }
}

const createSubmissionFeedback = (remember: boolean): LoginFeedback => ({
  attemptId: `local-${Date.now()}`,
  finalStatus: 'submitting',
  steps: [
    { key: 'credentials', label: 'Verify credentials', status: 'pending', detail: 'Sending credentials to server.' },
    { key: 'session', label: 'Secure session', status: 'skipped', detail: 'Waiting for server confirmation.' },
    {
      key: 'trust_device',
      label: 'Trust this device',
      status: remember ? 'pending' : 'skipped',
      detail: remember ? 'Will trust this device after a successful login.' : 'Not selected for this attempt.',
    },
    { key: 'workspace', label: 'Prepare workspace', status: 'skipped', detail: 'Starts after authentication succeeds.' },
  ],
})

const createErrorFeedback = (message: string): LoginFeedback => ({
  attemptId: `error-${Date.now()}`,
  finalStatus: 'error',
  steps: [
    { key: 'credentials', label: 'Verify credentials', status: 'error', detail: message },
    { key: 'session', label: 'Secure session', status: 'skipped', detail: 'Session not created.' },
    { key: 'workspace', label: 'Prepare workspace', status: 'skipped', detail: 'Retry after fixing the issue.' },
  ],
})

const formatTimestamp = (value?: string) => {
  if (!value) return ''
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }
  return parsed.toLocaleTimeString()
}

const Login: React.FC = () => {
  const { login, isLoading } = useAuth()
  const navigate = useNavigate()
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [feedback, setFeedback] = useState<LoginFeedback | null>(null)
  const [bannerKey, setBannerKey] = useState<number>(0) // force re-animate
  const redirectTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (redirectTimeout.current) {
        clearTimeout(redirectTimeout.current)
      }
    }
  }, [])

  const onFinish = async (values: LoginFormValues) => {
    setError('')
    setSuccess(false)
    setIsSubmitting(true)
    setBannerKey((k) => k + 1)
    // const optimisticFeedback = createSubmissionFeedback(values.remember)
    // setFeedback(optimisticFeedback)
    
    try {
      const result = await login(values.username, values.password, values.remember)
      setSuccess(true)
      setSyncing(true)
      setBannerKey((k) => k + 1)
      // setFeedback(result?.feedback || optimisticFeedback)

      if (redirectTimeout.current) {
        clearTimeout(redirectTimeout.current)
      }

      redirectTimeout.current = setTimeout(() => {
        setSyncing(false)
        navigate('/dashboard', { replace: true })
      }, 2000)
    } catch (err: any) {
      setIsSubmitting(false)
      const loginError = err as LoginError
      const errorMessage = loginError.message || 'Login failed. Please try again.'
      setError(errorMessage)
      setSuccess(false)
      setSyncing(false)
      // setFeedback(loginError.feedback || createErrorFeedback(errorMessage))
    }
  }

  return (
    <div className="login-container">
      <Card className="login-card">
        <div className="login-header">
          <Title level={2}>AMRS Maintenance Tracker</Title>
          <Text type="secondary">{success ? 'Signing you in...' : 'Sign in to continue'}</Text>
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

        {(success || syncing) && (
          <div key={bannerKey} className="login-status-banner" style={{ textAlign: 'center', padding: '20px 0' }}>
             <Space direction="vertical" size="large">
                <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                <Title level={3}>Login Successful</Title>
                <Space>
                  <Spin indicator={<LoadingOutlined style={{ fontSize: 24 }} spin />} />
                  <Text>Loading dashboard...</Text>
                </Space>
             </Space>
          </div>
        )}

        {isSubmitting && !success && !error && (
           <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Spin size="large" tip="Verifying credentials..." />
           </div>
        )}

        {!success && !isSubmitting && (
          <>
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
          </>
        )}
      </Card>
    </div>
  )
}

export default Login
