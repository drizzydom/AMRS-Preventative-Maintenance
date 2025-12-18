import React, { useState, useEffect } from 'react'
import { Card, Form, Switch, Select, Slider, Typography, Button, Space, message, Divider, Radio, Input } from 'antd'
import { SaveOutlined, ReloadOutlined, BulbOutlined, BulbFilled } from '@ant-design/icons'
import { useTheme } from '../contexts/ThemeContext'
import apiClient from '../utils/api'
import '../styles/settings.css'

const { Title, Text, Paragraph } = Typography

interface AccessibilitySettings {
  highContrast: boolean
  colorBlindMode: boolean
  fontSize: number
  fontFamily: 'sans-serif' | 'serif'
  reduceMotion: boolean
  zoomLevel: number
}

const Settings: React.FC = () => {
  const { themeMode, isDark, setThemeMode } = useTheme()
  const [settings, setSettings] = useState<AccessibilitySettings>({
    highContrast: false,
    colorBlindMode: false,
    fontSize: 14,
    fontFamily: 'sans-serif',
    reduceMotion: false,
    zoomLevel: 100,
  })

  const [hasChanges, setHasChanges] = useState(false)
  const [passwordForm] = Form.useForm()
  const [changingPassword, setChangingPassword] = useState(false)

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('accessibilitySettings')
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings))
        applySettings(JSON.parse(savedSettings))
      } catch (error) {
        console.error('Failed to load settings:', error)
      }
    }
  }, [])

  const applySettings = (newSettings: AccessibilitySettings) => {
    const root = document.documentElement

    // Apply high contrast
    if (newSettings.highContrast) {
      root.classList.add('high-contrast')
    } else {
      root.classList.remove('high-contrast')
    }

    // Apply color blind mode
    if (newSettings.colorBlindMode) {
      root.classList.add('color-blind-mode')
    } else {
      root.classList.remove('color-blind-mode')
    }

    // Apply font size
    root.style.setProperty('--base-font-size', `${newSettings.fontSize}px`)

    // Apply font family
    root.style.setProperty('--font-family', newSettings.fontFamily)

    // Apply reduce motion
    if (newSettings.reduceMotion) {
      root.classList.add('reduce-motion')
    } else {
      root.classList.remove('reduce-motion')
    }

    // Apply zoom level
    root.style.setProperty('--zoom-level', `${newSettings.zoomLevel / 100}`)
  }

  const handleSettingChange = (key: keyof AccessibilitySettings, value: any) => {
    const newSettings = { ...settings, [key]: value }
    setSettings(newSettings)
    setHasChanges(true)
    applySettings(newSettings)
  }

  const handleSave = () => {
    try {
      localStorage.setItem('accessibilitySettings', JSON.stringify(settings))
      message.success('Settings saved successfully')
      setHasChanges(false)
    } catch (error) {
      message.error('Failed to save settings')
    }
  }

  const handleReset = () => {
    const defaultSettings: AccessibilitySettings = {
      highContrast: false,
      colorBlindMode: false,
      fontSize: 14,
      fontFamily: 'sans-serif',
      reduceMotion: false,
      zoomLevel: 100,
    }
    setSettings(defaultSettings)
    applySettings(defaultSettings)
    localStorage.removeItem('accessibilitySettings')
    message.success('Settings reset to defaults')
    setHasChanges(false)
  }

  const handleChangePassword = async (values: any) => {
    try {
      setChangingPassword(true)
      await apiClient.post('/api/v1/auth/change-password', {
        current_password: values.currentPassword,
        new_password: values.newPassword
      })
      message.success('Password changed successfully')
      passwordForm.resetFields()
    } catch (error: any) {
      message.error(error.response?.data?.error || 'Failed to change password')
    } finally {
      setChangingPassword(false)
    }
  }

  return (
    <div className="settings-container">
      <div className="settings-header">
        <Title level={2}>Accessibility Settings</Title>
        <Paragraph type="secondary">
          Customize the application to meet your accessibility needs
        </Paragraph>
      </div>

      <Card className="settings-card">
        <Form layout="vertical">
          <Title level={4}>
            {isDark ? <BulbFilled style={{ marginRight: 8 }} /> : <BulbOutlined style={{ marginRight: 8 }} />}
            Theme
          </Title>

          <Form.Item label="Color Theme">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Radio.Group 
                value={themeMode} 
                onChange={(e) => setThemeMode(e.target.value)}
                optionType="button"
                buttonStyle="solid"
                size="large"
              >
                <Radio.Button value="light">☀️ Light</Radio.Button>
                <Radio.Button value="dark">🌙 Dark</Radio.Button>
                <Radio.Button value="system">💻 System</Radio.Button>
              </Radio.Group>
              <Text type="secondary" style={{ fontSize: 13 }}>
                {themeMode === 'system' 
                  ? `Currently using ${isDark ? 'dark' : 'light'} mode based on your system preference`
                  : `Using ${themeMode} mode`
                }
              </Text>
            </Space>
          </Form.Item>

          <Divider />

          <Title level={4}>Visual Settings</Title>

          <Form.Item label="High Contrast Mode">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Switch
                checked={settings.highContrast}
                onChange={(checked) => handleSettingChange('highContrast', checked)}
              />
              <Text type="secondary" style={{ fontSize: 13 }}>
                Increases contrast between text and background for better readability
              </Text>
            </Space>
          </Form.Item>

          <Form.Item label="Color Blind Mode">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Switch
                checked={settings.colorBlindMode}
                onChange={(checked) => handleSettingChange('colorBlindMode', checked)}
              />
              <Text type="secondary" style={{ fontSize: 13 }}>
                Uses patterns and text labels in addition to colors for status indicators
              </Text>
            </Space>
          </Form.Item>

          <Form.Item label="Font Size">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                value={settings.fontSize}
                onChange={(value) => handleSettingChange('fontSize', value)}
                style={{ width: 200 }}
              >
                <Select.Option value={12}>Small (12px)</Select.Option>
                <Select.Option value={14}>Medium (14px)</Select.Option>
                <Select.Option value={16}>Large (16px)</Select.Option>
                <Select.Option value={18}>Extra Large (18px)</Select.Option>
              </Select>
              <Text type="secondary" style={{ fontSize: 13 }}>
                Adjusts the base font size throughout the application
              </Text>
            </Space>
          </Form.Item>

          <Form.Item label="Font Family">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Select
                value={settings.fontFamily}
                onChange={(value) => handleSettingChange('fontFamily', value)}
                style={{ width: 200 }}
              >
                <Select.Option value="sans-serif">Sans-serif (Default)</Select.Option>
                <Select.Option value="serif">Serif</Select.Option>
              </Select>
              <Text type="secondary" style={{ fontSize: 13 }}>
                Choose the font style that's easiest for you to read
              </Text>
            </Space>
          </Form.Item>

          <Form.Item label="Zoom Level">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Space align="center" style={{ width: '100%' }}>
                <Slider
                  value={settings.zoomLevel}
                  onChange={(value) => handleSettingChange('zoomLevel', value)}
                  min={50}
                  max={200}
                  step={10}
                  style={{ width: 300 }}
                  tooltip={{ formatter: (value) => `${value}%` }}
                />
                <Text strong>{settings.zoomLevel}%</Text>
              </Space>
              <Text type="secondary" style={{ fontSize: 13 }}>
                Scale the entire interface (50% to 200%)
              </Text>
            </Space>
          </Form.Item>

          <Divider />

          <Title level={4}>Motion & Animation</Title>

          <Form.Item label="Reduce Motion">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Switch
                checked={settings.reduceMotion}
                onChange={(checked) => handleSettingChange('reduceMotion', checked)}
              />
              <Text type="secondary" style={{ fontSize: 13 }}>
                Reduces or removes animations and transitions throughout the application
              </Text>
            </Space>
          </Form.Item>

          <Divider />

          <Form.Item>
            <Space>
              <Button
                type="primary"
                icon={<SaveOutlined />}
                onClick={handleSave}
                disabled={!hasChanges}
              >
                Save Settings
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={handleReset}
              >
                Reset to Defaults
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card className="settings-info-card" style={{ marginTop: 16 }}>
        <Title level={5}>Onboarding Tour</Title>
        <Paragraph>
          New to AMRS Maintenance Tracker? Take the guided tour to learn about all the features.
        </Paragraph>
        <Button 
          onClick={() => {
            localStorage.removeItem('amrs_onboarding_complete')
            message.success('Onboarding tour will show on next page reload')
            // Optionally reload to show immediately
            setTimeout(() => window.location.reload(), 1000)
          }}
        >
          Restart Onboarding Tour
        </Button>
      </Card>

      <Card className="settings-info-card" style={{ marginTop: 16 }}>
        <Title level={5}>Keyboard Navigation</Title>
        <Paragraph>
          The application fully supports keyboard navigation:
        </Paragraph>
        <ul>
          <li><kbd>Tab</kbd> - Navigate between interactive elements</li>
          <li><kbd>Shift + Tab</kbd> - Navigate backward</li>
          <li><kbd>Enter</kbd> or <kbd>Space</kbd> - Activate buttons and links</li>
          <li><kbd>Esc</kbd> - Close modals and dropdowns</li>
          <li><kbd>Arrow keys</kbd> - Navigate within menus and lists</li>
        </ul>
      </Card>

      <Card title="Account Security" style={{ marginTop: 16 }}>
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            name="currentPassword"
            label="Current Password"
            rules={[{ required: true, message: 'Please enter your current password' }]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="newPassword"
            label="New Password"
            rules={[
              { required: true, message: 'Please enter a new password' },
              { min: 8, message: 'Password must be at least 8 characters' }
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Form.Item
            name="confirmPassword"
            label="Confirm New Password"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: 'Please confirm your new password' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve()
                  }
                  return Promise.reject(new Error('The two passwords that you entered do not match!'))
                },
              }),
            ]}
          >
            <Input.Password />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={changingPassword}>
            Change Password
          </Button>
        </Form>
      </Card>
    </div>
  )
}

export default Settings
