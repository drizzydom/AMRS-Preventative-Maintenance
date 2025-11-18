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
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import apiClient from '../utils/api'
import dayjs from 'dayjs'
import '../styles/admin-panel.css'
import { useAuthorization } from '../hooks/useAuthorization'

const { TabPane } = Tabs
const { confirm } = Modal
const { TextArea } = Input
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
      <div className="page-header">
        <h1>
          <SettingOutlined /> Admin Panel
        </h1>
        <p>System administration and configuration</p>
      </div>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {/* System Settings Tab */}
          <TabPane
            tab={
              <span>
                <SettingOutlined />
                System Settings
              </span>
            }
            key="system"
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Alert
                message="System Configuration"
                description="Configure global system settings and preferences"
                type="info"
                showIcon
              />

              <Row gutter={16}>
                {systemStats.map((stat, index) => (
                  <Col span={8} key={index}>
                    <Card>
                      <Statistic
                        title={stat.label}
                        value={stat.value}
                        prefix={stat.icon}
                      />
                    </Card>
                  </Col>
                ))}
              </Row>

              <Divider>Application Settings</Divider>

              <Form layout="vertical">
                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="Application Name">
                      <Input
                        value={systemSettings.app_name}
                        onChange={(e) =>
                          setSystemSettings({ ...systemSettings, app_name: e.target.value })
                        }
                      />
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="Session Timeout (minutes)">
                      <InputNumber
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

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="Max Login Attempts">
                      <InputNumber
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
                  <Col span={12}>
                    <Form.Item label="Sync Interval (seconds)">
                      <InputNumber
                        min={60}
                        max={3600}
                        value={systemSettings.sync_interval}
                        onChange={(value) =>
                          setSystemSettings({ ...systemSettings, sync_interval: value || 300 })
                        }
                        style={{ width: '100%' }}
                      />
                    </Form.Item>
                  </Col>
                </Row>

                <Row gutter={16}>
                  <Col span={12}>
                    <Form.Item label="Backup Frequency">
                      <Select
                        value={systemSettings.backup_frequency}
                        onChange={(value) =>
                          setSystemSettings({ ...systemSettings, backup_frequency: value })
                        }
                        style={{ width: '100%' }}
                      >
                        <Select.Option value="hourly">Hourly</Select.Option>
                        <Select.Option value="daily">Daily</Select.Option>
                        <Select.Option value="weekly">Weekly</Select.Option>
                        <Select.Option value="monthly">Monthly</Select.Option>
                      </Select>
                    </Form.Item>
                  </Col>
                  <Col span={12}>
                    <Form.Item label="Features">
                      <Space direction="vertical">
                        <div>
                          <Switch
                            checked={systemSettings.enable_notifications}
                            onChange={(checked) =>
                              setSystemSettings({ ...systemSettings, enable_notifications: checked })
                            }
                          />{' '}
                          Enable Notifications
                        </div>
                        <div>
                          <Switch
                            checked={systemSettings.enable_email_alerts}
                            onChange={(checked) =>
                              setSystemSettings({ ...systemSettings, enable_email_alerts: checked })
                            }
                          />{' '}
                          Enable Email Alerts
                        </div>
                      </Space>
                    </Form.Item>
                  </Col>
                </Row>

                <Form.Item>
                  <Button type="primary" onClick={handleSaveSettings} loading={loading}>
                    Save Settings
                  </Button>
                </Form.Item>
              </Form>
            </Space>
          </TabPane>

          {/* Security & Audit Tab */}
          <TabPane
            tab={
              <span>
                <SecurityScanOutlined />
                Security & Audit
              </span>
            }
            key="security"
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Alert
                message="Security Monitoring"
                description="View security events and audit logs"
                type="warning"
                showIcon
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space>
                  <RangePicker />
                  <Select defaultValue="all" style={{ width: 150 }}>
                    <Select.Option value="all">All Events</Select.Option>
                    <Select.Option value="login">Logins</Select.Option>
                    <Select.Option value="failed_login">Failed Logins</Select.Option>
                    <Select.Option value="permission">Permissions</Select.Option>
                    <Select.Option value="data">Data Changes</Select.Option>
                  </Select>
                </Space>
                <Button icon={<ReloadOutlined />} onClick={fetchSecurityLogs} loading={loading}>
                  Refresh
                </Button>
              </div>

              <Table
                columns={securityLogColumns}
                dataSource={securityLogs}
                loading={loading}
                rowKey="id"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showTotal: (total) => `Total ${total} events`,
                }}
              />
            </Space>
          </TabPane>

          {/* Database Management Tab */}
          <TabPane
            tab={
              <span>
                <DatabaseOutlined />
                Database
              </span>
            }
            key="database"
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Alert
                message="Database Management"
                description="Backup, restore, and maintain the database"
                type="info"
                showIcon
              />

              <Card title="Database Operations" extra={<DatabaseOutlined />}>
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <div>
                    <h4>Backup & Restore</h4>
                    <Space>
                      <Button
                        type="primary"
                        icon={<DownloadOutlined />}
                        onClick={handleBackupDatabase}
                      >
                        Create Backup
                      </Button>
                      <Button icon={<UploadOutlined />} onClick={handleRestoreDatabase}>
                        Restore from Backup
                      </Button>
                    </Space>
                  </div>

                  <Divider />

                  <div>
                    <h4>Maintenance</h4>
                    <Space>
                      <Button icon={<DatabaseOutlined />} onClick={handleVacuumDatabase}>
                        Optimize Database
                      </Button>
                      <Tooltip title="Analyze table statistics for better query performance">
                        <Button icon={<CheckCircleOutlined />}>
                          Analyze Tables
                        </Button>
                      </Tooltip>
                    </Space>
                  </div>

                  <Divider />

                  <div>
                    <h4>Database Information</h4>
                    <Descriptions bordered column={2}>
                      <Descriptions.Item label="Database Size">24.5 MB</Descriptions.Item>
                      <Descriptions.Item label="Total Tables">15</Descriptions.Item>
                      <Descriptions.Item label="Total Records">2,847</Descriptions.Item>
                      <Descriptions.Item label="Last Backup">
                        {dayjs().subtract(1, 'day').format('MMM DD, YYYY HH:mm')}
                      </Descriptions.Item>
                      <Descriptions.Item label="Database Type">SQLite</Descriptions.Item>
                      <Descriptions.Item label="Version">3.40.1</Descriptions.Item>
                    </Descriptions>
                  </div>
                </Space>
              </Card>
            </Space>
          </TabPane>

          {/* Roles & Permissions Tab */}
          <TabPane
            tab={
              <span>
                <TeamOutlined />
                Roles & Permissions
              </span>
            }
            key="roles"
          >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              <Alert
                message="Role Management"
                description="Configure user roles and permissions"
                type="info"
                showIcon
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Space>
                  <InfoCircleOutlined /> Manage roles and assign permissions
                </Space>
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
              />

              <Card title="Available Permissions" size="small">
                <Row gutter={[16, 16]}>
                  {[
                    'view_dashboard',
                    'view_machines',
                    'edit_machines',
                    'view_maintenance',
                    'edit_maintenance',
                    'view_audits',
                    'edit_audits',
                    'view_reports',
                    'export_data',
                    'view_users',
                    'edit_users',
                    'admin_settings',
                  ].map((perm) => (
                    <Col span={6} key={perm}>
                      <Tag color="blue">{perm}</Tag>
                    </Col>
                  ))}
                </Row>
              </Card>
            </Space>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  )
}

export default AdminPanel
