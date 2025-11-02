import React, { useState } from 'react'
import { Card, Table, Button, Input, Space, Tag, Typography, Badge } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  LockOutlined,
  UnlockOutlined,
} from '@ant-design/icons'
import '../../styles/users.css'

const { Title } = Typography
const { Search } = Input

interface User {
  key: string
  id: number
  username: string
  email: string
  role: string
  isActive: boolean
  lastLogin: string
  createdAt: string
}

const Users: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('')

  // Mock data - will be replaced with API calls
  const mockData: User[] = [
    {
      key: '1',
      id: 1,
      username: 'admin',
      email: 'admin@amrs.com',
      role: 'Administrator',
      isActive: true,
      lastLogin: '2025-11-01 10:30:00',
      createdAt: '2024-01-15',
    },
    {
      key: '2',
      id: 2,
      username: 'john.doe',
      email: 'john.doe@amrs.com',
      role: 'Manager',
      isActive: true,
      lastLogin: '2025-11-01 09:15:00',
      createdAt: '2024-03-20',
    },
    {
      key: '3',
      id: 3,
      username: 'jane.smith',
      email: 'jane.smith@amrs.com',
      role: 'Technician',
      isActive: true,
      lastLogin: '2025-10-31 16:45:00',
      createdAt: '2024-06-10',
    },
    {
      key: '4',
      id: 4,
      username: 'bob.johnson',
      email: 'bob.johnson@amrs.com',
      role: 'Technician',
      isActive: false,
      lastLogin: '2025-10-15 14:20:00',
      createdAt: '2024-02-28',
    },
  ]

  const columns: ColumnsType<User> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
      sorter: (a, b) => a.username.localeCompare(b.username),
      render: (text, record) => (
        <Space>
          <UserOutlined style={{ color: record.isActive ? '#1890ff' : '#8c8c8c' }} />
          <strong>{text}</strong>
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const colors: Record<string, string> = {
          Administrator: 'red',
          Manager: 'blue',
          Technician: 'green',
          Viewer: 'default',
        }
        return <Tag color={colors[role] || 'default'}>{role}</Tag>
      },
      filters: [
        { text: 'Administrator', value: 'Administrator' },
        { text: 'Manager', value: 'Manager' },
        { text: 'Technician', value: 'Technician' },
        { text: 'Viewer', value: 'Viewer' },
      ],
      onFilter: (value, record) => record.role === value,
    },
    {
      title: 'Status',
      dataIndex: 'isActive',
      key: 'isActive',
      render: (isActive: boolean) => (
        <Badge
          status={isActive ? 'success' : 'error'}
          text={isActive ? 'Active' : 'Inactive'}
        />
      ),
      filters: [
        { text: 'Active', value: true },
        { text: 'Inactive', value: false },
      ],
      onFilter: (value, record) => record.isActive === value,
    },
    {
      title: 'Last Login',
      dataIndex: 'lastLogin',
      key: 'lastLogin',
      sorter: (a, b) => new Date(a.lastLogin).getTime() - new Date(b.lastLogin).getTime(),
    },
    {
      title: 'Created',
      dataIndex: 'createdAt',
      key: 'createdAt',
      sorter: (a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime(),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            title="Edit User"
          />
          <Button
            type="text"
            icon={record.isActive ? <LockOutlined /> : <UnlockOutlined />}
            size="small"
            title={record.isActive ? 'Deactivate' : 'Activate'}
            style={{ color: record.isActive ? '#ff4d4f' : '#52c41a' }}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            size="small"
            title="Delete User"
          />
        </Space>
      ),
    },
  ]

  return (
    <div className="users-container">
      <div className="users-header">
        <Title level={2}>User Management</Title>
      </div>

      <Card className="users-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="users-controls">
            <Space wrap>
              <Search
                placeholder="Search users..."
                allowClear
                onSearch={setSearchTerm}
                style={{ width: 300 }}
                prefix={<SearchOutlined />}
              />
            </Space>
            <Space>
              <Button icon={<ReloadOutlined />}>Refresh</Button>
              <Button type="primary" icon={<PlusOutlined />}>
                Add User
              </Button>
            </Space>
          </div>

          <div className="users-summary">
            <Space size="large">
              <div className="summary-item">
                <span className="summary-label">Total Users:</span>
                <span className="summary-value">{mockData.length}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Active:</span>
                <span className="summary-value summary-active">
                  {mockData.filter((u) => u.isActive).length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Inactive:</span>
                <span className="summary-value summary-inactive">
                  {mockData.filter((u) => !u.isActive).length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Administrators:</span>
                <span className="summary-value summary-admin">
                  {mockData.filter((u) => u.role === 'Administrator').length}
                </span>
              </div>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={mockData}
            pagination={{
              pageSize: 25,
              showSizeChanger: true,
              pageSizeOptions: ['25', '50', '100'],
              showTotal: (total) => `Total ${total} users`,
            }}
          />
        </Space>
      </Card>
    </div>
  )
}

export default Users
