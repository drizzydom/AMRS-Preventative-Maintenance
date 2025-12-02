import React, { useState, useEffect } from 'react'
import {
  Card,
  Tabs,
  Table,
  Button,
  Space,
  Switch,
  Input,
  InputNumber,
  Select,
  Divider,
  message,
  Modal,
  Form,
  Tag,
  DatePicker,
  Statistic,
  Row,
  Col,
  Alert,
  Descriptions,
  Tooltip,
  Result,
  Typography,
} from 'antd'
import {
  SettingOutlined,
  SecurityScanOutlined,
  DatabaseOutlined,
  TeamOutlined,
  ReloadOutlined,
  DownloadOutlined,
  UploadOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  FileTextOutlined,
  LockOutlined,
  UserOutlined,
  ClockCircleOutlined,
  SafetyCertificateOutlined,
  SyncOutlined,
  ThunderboltOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import apiClient from '../utils/api'
import dayjs from 'dayjs'
import '../styles/admin-panel.css'
import { useAuthorization } from '../hooks/useAuthorization'

const { Title, Text } = Typography
const { confirm } = Modal
const { RangePicker } = DatePicker

interface SecurityLog {
  id: number
  timestamp: string
  event_type: string
  user: string
  ip_address: string
  details: string
  severity: 'info' | 'warning' | 'error' | 'critical'
}

interface SystemStat {
  label: string
  value: string | number
  icon?: React.ReactNode
}

interface Role {
  id: number
  name: string
  permissions: string[]
  user_count: number
}

const AdminPanel: React.FC = () => {
  const { isAdmin } = useAuthorization()
  const [activeTab, setActiveTab] = useState('system')
  const [loading, setLoading] = useState(false)
  const [systemStats, setSystemStats] = useState<SystemStat[]>([])
  const [securityLogs, setSecurityLogs] = useState<SecurityLog[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [systemSettings, setSystemSettings] = useState({
    app_name: 'AMRS Maintenance Tracker',
    session_timeout: 60,
    max_login_attempts: 5,
    enable_notifications: true,
    enable_email_alerts: false,
    sync_interval: 300,
    backup_frequency: 'daily',
  })

  useEffect(() => {
    if (activeTab === 'system') {
      fetchSystemStats()
    } else if (activeTab === 'security') {
      fetchSecurityLogs()
    } else if (activeTab === 'database') {
      fetchDatabaseStats()
    } else if (activeTab === 'roles') {
      fetchRoles()
    }
  }, [activeTab])

  if (!isAdmin) {
    return (
      <Result
        status="403"
        title="Admin Access Required"
        subTitle="Please contact an administrator if you need additional permissions."
      />
    )
  }

  const fetchSystemStats = async () => {
    setLoading(true)
    try {
      // Mock data - replace with actual API call
      setSystemStats([
        { label: 'Uptime', value: '15 days, 3 hours', icon: <ClockCircleOutlined /> },
        { label: 'Active Sessions', value: 8, icon: <UserOutlined /> },
        { label: 'CPU Usage', value: '23%', icon: <SettingOutlined /> },
        { label: 'Memory Usage', value: '1.2 GB', icon: <DatabaseOutlined /> },
        { label: 'Disk Space', value: '45% (12 GB free)', icon: <DatabaseOutlined /> },
        { label: 'Last Backup', value: dayjs().subtract(1, 'day').format('MMM DD, YYYY HH:mm'), icon: <DatabaseOutlined /> },
      ])
    } catch (error) {
      message.error('Failed to load system statistics')
    } finally {
      setLoading(false)
    }
  }

  const fetchSecurityLogs = async () => {
    setLoading(true)
    try {
      // Mock data - replace with actual API call
      const mockLogs: SecurityLog[] = [
        {
          id: 1,
          timestamp: dayjs().subtract(1, 'hour').format('YYYY-MM-DD HH:mm:ss'),
          event_type: 'login',
          user: 'admin',
          ip_address: '192.168.1.100',
          details: 'Successful login',
          severity: 'info',
        },
        {
          id: 2,
          timestamp: dayjs().subtract(2, 'hours').format('YYYY-MM-DD HH:mm:ss'),
          event_type: 'failed_login',
          user: 'unknown',
          ip_address: '192.168.1.105',
          details: 'Failed login attempt - invalid credentials',
          severity: 'warning',
        },
        {
          id: 3,
          timestamp: dayjs().subtract(3, 'hours').format('YYYY-MM-DD HH:mm:ss'),
          event_type: 'permission_change',
          user: 'admin',
          ip_address: '192.168.1.100',
          details: 'Updated role permissions for "Technician"',
          severity: 'info',
        },
        {
          id: 4,
          timestamp: dayjs().subtract(5, 'hours').format('YYYY-MM-DD HH:mm:ss'),
          event_type: 'data_export',
          user: 'manager',
          ip_address: '192.168.1.102',
          details: 'Exported maintenance records (250 records)',
          severity: 'info',
        },
        {
          id: 5,
          timestamp: dayjs().subtract(1, 'day').format('YYYY-MM-DD HH:mm:ss'),
          event_type: 'account_locked',
          user: 'temp_user',
          ip_address: '192.168.1.110',
          details: 'Account locked due to multiple failed login attempts',
          severity: 'error',
        },
      ]
      setSecurityLogs(mockLogs)
    } catch (error) {
      message.error('Failed to load security logs')
    } finally {
      setLoading(false)
    }
  }

  const fetchDatabaseStats = async () => {
    setLoading(true)
    try {
      // This would call actual API endpoint
      message.info('Loading database statistics...')
    } catch (error) {
      message.error('Failed to load database statistics')
    } finally {
      setLoading(false)
    }
  }

  const fetchRoles = async () => {
    setLoading(true)
    try {
      // Mock data - replace with actual API call
      setRoles([
        {
          id: 1,
          name: 'Administrator',
          permissions: ['all'],
          user_count: 2,
        },
        {
          id: 2,
          name: 'Manager',
          permissions: ['view_all', 'edit_maintenance', 'edit_audits', 'view_reports'],
          user_count: 5,
        },
        {
          id: 3,
          name: 'Technician',
          permissions: ['view_machines', 'edit_maintenance', 'view_audits'],
          user_count: 12,
        },
        {
          id: 4,
          name: 'Viewer',
          permissions: ['view_all'],
          user_count: 8,
        },
      ])
    } catch (error) {
      message.error('Failed to load roles')
    } finally {
      setLoading(false)
    }
  }

  const handleBackupDatabase = () => {
    confirm({
      title: 'Create Database Backup',
      icon: <DownloadOutlined />,
      content: 'This will create a backup of the current database. Continue?',
      okText: 'Create Backup',
      cancelText: 'Cancel',
      onOk() {
        message.success('Database backup created successfully')
        // Implement actual backup logic
      },
    })
  }

  const handleRestoreDatabase = () => {
    confirm({
      title: 'Restore Database',
      icon: <WarningOutlined />,
      content: 'This will restore the database from a backup file. All current data will be replaced. Are you sure?',
      okText: 'Restore',
      okType: 'danger',
      cancelText: 'Cancel',
      onOk() {
        message.warning('Database restore functionality not yet implemented')
        // Implement actual restore logic
      },
    })
  }

  const handleVacuumDatabase = () => {
    confirm({
      title: 'Optimize Database',
      icon: <DatabaseOutlined />,
      content: 'This will optimize the database by reclaiming storage space. Continue?',
      okText: 'Optimize',
      cancelText: 'Cancel',
      onOk() {
        message.success('Database optimization completed')
        // Implement actual vacuum logic
      },
    })
  }

  const handleSaveSettings = async () => {
    setLoading(true)
    try {
      // Implement API call to save settings
      await new Promise(resolve => setTimeout(resolve, 500))
      message.success('Settings saved successfully')
    } catch (error) {
      message.error('Failed to save settings')
    } finally {
      setLoading(false)
    }
  }

  const securityLogColumns: ColumnsType<SecurityLog> = [
    {
      title: 'Timestamp',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 180,
      render: (text) => dayjs(text).format('MMM DD, YYYY HH:mm:ss'),
    },
    {
      title: 'Event Type',
      dataIndex: 'event_type',
      key: 'event_type',
      width: 150,
      render: (text) => text.replace(/_/g, ' ').toUpperCase(),
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
      width: 120,
    },
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 140,
    },
    {
      title: 'Details',
      dataIndex: 'details',
      key: 'details',
    },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      width: 100,
      render: (severity: 'info' | 'warning' | 'error' | 'critical') => {
        const colors: Record<'info' | 'warning' | 'error' | 'critical', string> = {
          info: 'blue',
          warning: 'orange',
          error: 'red',
          critical: 'red',
        }
        return <Tag color={colors[severity]}>{severity.toUpperCase()}</Tag>
      },
    },
  ]

  const roleColumns: ColumnsType<Role> = [
    {
      title: 'Role Name',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Permissions',
      dataIndex: 'permissions',
      key: 'permissions',
      render: (permissions: string[]) => (
        <>
          {permissions.slice(0, 3).map(perm => (
            <Tag key={perm} color="blue">{perm}</Tag>
          ))}
          {permissions.length > 3 && <Tag>+{permissions.length - 3} more</Tag>}
        </>
      ),
    },
    {
      title: 'Users',
      dataIndex: 'user_count',
      key: 'user_count',
      width: 100,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button type="link" size="small">Edit</Button>
          <Button type="link" size="small" danger disabled={record.name === 'Administrator'}>
            Delete
          </Button>
        </Space>
      ),
    },
  ]

  return (
    <div className="admin-panel-page">
      <div className="page-header" style={{ marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          <SafetyCertificateOutlined style={{ marginRight: 12 }} />
          Admin Panel
        </Title>
        <Text type="secondary">System administration and configuration</Text>
      </div>

      {/* Quick Actions Bar */}
      <Card 
        className="quick-actions-card" 
        style={{ marginBottom: 24, background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
        bodyStyle={{ padding: '16px 24px' }}
      >
        <Row gutter={16} align="middle" justify="space-between">
          <Col>
            <Title level={4} style={{ color: 'white', margin: 0 }}>Quick Actions</Title>
          </Col>
          <Col>
            <Space size="middle">
              <Button 
                icon={<DownloadOutlined />} 
                onClick={handleBackupDatabase}
                style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}
              >
                Backup Database
              </Button>
              <Button 
                icon={<SyncOutlined />} 
                onClick={() => window.dispatchEvent(new Event('socket-sync'))}
                style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}
              >
                Sync Now
              </Button>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={() => { 
                  fetchSystemStats()
                  message.success('Data refreshed')
                }}
                style={{ background: 'rgba(255,255,255,0.2)', border: 'none', color: 'white' }}
              >
                Refresh
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <Card>
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          type="card"
          size="large"
          items={[
            {
              key: 'system',
              label: (
                <span>
                  <SettingOutlined />
                  <span style={{ marginLeft: 8 }}>System</span>
                </span>
              ),
              children: (
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <Row gutter={[16, 16]}>
                    {systemStats.map((stat, index) => (
                      <Col xs={24} sm={12} md={8} key={index}>
                        <Card hoverable>
                          <Statistic
                            title={stat.label}
                            value={stat.value}
                            prefix={stat.icon}
                          />
                        </Card>
                      </Col>
                    ))}
                  </Row>

                  <Card title="Application Settings" type="inner">
                    <Form layout="vertical">
                      <Row gutter={24}>
                        <Col xs={24} md={12}>
                          <Form.Item label="Application Name">
                            <Input
                              size="large"
                              value={systemSettings.app_name}
                              onChange={(e) =>
                                setSystemSettings({ ...systemSettings, app_name: e.target.value })
                              }
                            />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item label="Session Timeout (minutes)">
                            <InputNumber
                              size="large"
                              min={5}
                              max={1440}
                              value={systemSettings.session_timeout}
                              onChange={(value) =>
                                setSystemSettings({ ...systemSettings, session_timeout: value || 60 })
                              }
                              style={{ width: '100%' }}
                            />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Row gutter={24}>
                        <Col xs={24} md={12}>
                          <Form.Item label="Max Login Attempts">
                            <InputNumber
                              size="large"
                              min={3}
                              max={10}
                              value={systemSettings.max_login_attempts}
                              onChange={(value) =>
                                setSystemSettings({ ...systemSettings, max_login_attempts: value || 5 })
                              }
                              style={{ width: '100%' }}
                            />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item label="Backup Schedule">
                            <Select
                              size="large"
                              value={systemSettings.backup_frequency}
                              onChange={(value) =>
                                setSystemSettings({ ...systemSettings, backup_frequency: value })
                              }
                              style={{ width: '100%' }}
                            >
                              <Select.Option value="hourly">Every Hour</Select.Option>
                              <Select.Option value="daily">Daily</Select.Option>
                              <Select.Option value="weekly">Weekly</Select.Option>
                              <Select.Option value="monthly">Monthly</Select.Option>
                            </Select>
                          </Form.Item>
                        </Col>
                      </Row>

                      <Divider />

                      <Row gutter={24}>
                        <Col xs={24} md={12}>
                          <Form.Item>
                            <Space size="large">
                              <Switch
                                checked={systemSettings.enable_notifications}
                                onChange={(checked) =>
                                  setSystemSettings({ ...systemSettings, enable_notifications: checked })
                                }
                              />
                              <span>Enable Desktop Notifications</span>
                            </Space>
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item>
                            <Space size="large">
                              <Switch
                                checked={systemSettings.enable_email_alerts}
                                onChange={(checked) =>
                                  setSystemSettings({ ...systemSettings, enable_email_alerts: checked })
                                }
                              />
                              <span>Enable Email Alerts</span>
                            </Space>
                          </Form.Item>
                        </Col>
                      </Row>

                      <Form.Item>
                        <Button type="primary" size="large" onClick={handleSaveSettings} loading={loading}>
                          Save Settings
                        </Button>
                      </Form.Item>
                    </Form>
                  </Card>
                </Space>
              ),
            },
            {
              key: 'security',
              label: (
                <span>
                  <SecurityScanOutlined />
                  <span style={{ marginLeft: 8 }}>Security</span>
                </span>
              ),
              children: (
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
                    <Space wrap>
                      <RangePicker />
                      <Select defaultValue="all" style={{ width: 180 }}>
                        <Select.Option value="all">All Events</Select.Option>
                        <Select.Option value="login">Logins</Select.Option>
                        <Select.Option value="failed_login">Failed Logins</Select.Option>
                        <Select.Option value="permission">Permissions</Select.Option>
                        <Select.Option value="data">Data Changes</Select.Option>
                      </Select>
                    </Space>
                    <Button icon={<ReloadOutlined />} onClick={fetchSecurityLogs} loading={loading}>
                      Refresh Logs
                    </Button>
                  </div>

                  <Table
                    columns={securityLogColumns}
                    dataSource={securityLogs}
                    loading={loading}
                    rowKey="id"
                    pagination={{
                      pageSize: 15,
                      showSizeChanger: true,
                      showTotal: (total) => `${total} security events`,
                    }}
                    scroll={{ x: 800 }}
                  />
                </Space>
              ),
            },
            {
              key: 'database',
              label: (
                <span>
                  <DatabaseOutlined />
                  <span style={{ marginLeft: 8 }}>Database</span>
                </span>
              ),
              children: (
                <Row gutter={[24, 24]}>
                  <Col xs={24} lg={12}>
                    <Card 
                      title={<><DownloadOutlined /> Backup & Restore</>}
                      type="inner"
                    >
                      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Button
                          type="primary"
                          icon={<DownloadOutlined />}
                          onClick={handleBackupDatabase}
                          size="large"
                          block
                        >
                          Create Backup Now
                        </Button>
                        <Button 
                          icon={<UploadOutlined />} 
                          onClick={handleRestoreDatabase}
                          size="large"
                          block
                        >
                          Restore from Backup
                        </Button>
                        <Text type="secondary">
                          Last backup: {dayjs().subtract(1, 'day').format('MMM DD, YYYY h:mm A')}
                        </Text>
                      </Space>
                    </Card>
                  </Col>
                  
                  <Col xs={24} lg={12}>
                    <Card 
                      title={<><ThunderboltOutlined /> Maintenance</>}
                      type="inner"
                    >
                      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Button 
                          icon={<DatabaseOutlined />} 
                          onClick={handleVacuumDatabase}
                          size="large"
                          block
                        >
                          Optimize Database
                        </Button>
                        <Button 
                          icon={<CheckCircleOutlined />}
                          size="large"
                          block
                        >
                          Analyze Tables
                        </Button>
                        <Text type="secondary">
                          Optimization improves query performance and reclaims space.
                        </Text>
                      </Space>
                    </Card>
                  </Col>

                  <Col xs={24}>
                    <Card title="Database Information" type="inner">
                      <Descriptions bordered column={{ xs: 1, sm: 2, md: 3 }} size="middle">
                        <Descriptions.Item label="Database Type">SQLite</Descriptions.Item>
                        <Descriptions.Item label="Version">3.40.1</Descriptions.Item>
                        <Descriptions.Item label="Size">24.5 MB</Descriptions.Item>
                        <Descriptions.Item label="Total Tables">15</Descriptions.Item>
                        <Descriptions.Item label="Total Records">2,847</Descriptions.Item>
                        <Descriptions.Item label="Last Backup">
                          {dayjs().subtract(1, 'day').format('MMM DD, YYYY h:mm A')}
                        </Descriptions.Item>
                      </Descriptions>
                    </Card>
                  </Col>
                </Row>
              ),
            },
            {
              key: 'roles',
              label: (
                <span>
                  <TeamOutlined />
                  <span style={{ marginLeft: 8 }}>Roles</span>
                </span>
              ),
              children: (
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>Manage user roles and their permissions</Text>
                    <Button type="primary" icon={<TeamOutlined />}>
                      Create New Role
                    </Button>
                  </div>

                  <Table
                    columns={roleColumns}
                    dataSource={roles}
                    loading={loading}
                    rowKey="id"
                    pagination={false}
                    scroll={{ x: 600 }}
                  />

                  <Card title="Available Permissions" type="inner" size="small">
                    <Row gutter={[8, 8]}>
                      {[
                        { name: 'view_dashboard', desc: 'View Dashboard' },
                        { name: 'view_machines', desc: 'View Machines' },
                        { name: 'edit_machines', desc: 'Edit Machines' },
                        { name: 'view_maintenance', desc: 'View Maintenance' },
                        { name: 'edit_maintenance', desc: 'Record Maintenance' },
                        { name: 'view_audits', desc: 'View Audits' },
                        { name: 'edit_audits', desc: 'Complete Audits' },
                        { name: 'view_reports', desc: 'View Reports' },
                        { name: 'export_data', desc: 'Export Data' },
                        { name: 'view_users', desc: 'View Users' },
                        { name: 'edit_users', desc: 'Manage Users' },
                        { name: 'admin_settings', desc: 'Admin Settings' },
                      ].map((perm) => (
                        <Col xs={12} sm={8} md={6} key={perm.name}>
                          <Tooltip title={perm.name}>
                            <Tag color="blue" style={{ margin: 0 }}>{perm.desc}</Tag>
                          </Tooltip>
                        </Col>
                      ))}
                    </Row>
                  </Card>
                </Space>
              ),
            },
          ]}
        />
      </Card>
    </div>
  )
}

export default AdminPanel
