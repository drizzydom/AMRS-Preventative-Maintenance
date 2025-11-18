import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Input, Space, Tag, Typography, Badge, message, Modal, Result } from 'antd'
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
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import apiClient from '../../utils/api'
import UserModal from '../../components/modals/UserModal'
import '../../styles/users.css'
import { useAuthorization } from '../../hooks/useAuthorization'

const { Title } = Typography
const { Search } = Input
const { confirm } = Modal

interface User {
  key: string
  id: number
  username: string
  email: string
  full_name?: string
  role: string
  role_id?: number
  is_admin: boolean
  created_at?: string
}

const Users: React.FC = () => {
  const { isAdmin } = useAuthorization()
  const [searchTerm, setSearchTerm] = useState('')
  const [users, setUsers] = useState<User[]>([])
  const [roles, setRoles] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchUsers = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/users')
      const usersData = response.data.data.map((user: any) => ({
        key: user.id.toString(),
        id: user.id,
        username: user.username,
        email: user.email,
        full_name: user.full_name || '',
        role: user.role,
        role_id: user.role_id,
        is_admin: user.is_admin || false,
        created_at: user.created_at,
      }))
      setUsers(usersData)
    } catch (error: any) {
      console.error('Failed to load users:', error)
      message.error('Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  const fetchRoles = async () => {
    try {
      const response = await apiClient.get('/api/v1/roles')
      setRoles(response.data.data)
    } catch (error) {
      console.error('Failed to load roles:', error)
    }
  }

  useEffect(() => {
    if (!isAdmin) {
      return
    }
    fetchUsers()
    fetchRoles()
  }, [isAdmin])

  if (!isAdmin) {
    return (
      <Result
        status="403"
        title="Admin Access Required"
        subTitle="You must be an administrator to manage users."
      />
    )
  }

  const handleAddUser = () => {
    setSelectedUser(null)
    setModalOpen(true)
  }

  const handleEditUser = (user: User) => {
    setSelectedUser(user)
    setModalOpen(true)
  }

  const handleSubmitUser = async (values: any) => {
    try {
      setSubmitting(true)
      const formData = new FormData()
      formData.append('username', values.username)
      formData.append('email', values.email)
      formData.append('full_name', values.full_name || '')
      formData.append('role_id', values.role_id.toString())
      
      if (values.password) {
        formData.append('password', values.password)
      }

      if (selectedUser) {
        // Edit existing user
        await apiClient.post(`/user/edit/${selectedUser.id}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        message.success('User updated successfully')
      } else {
        // Create new user
        await apiClient.post('/admin/users', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        message.success('User created successfully')
      }

      setModalOpen(false)
      setSelectedUser(null)
      await fetchUsers()
    } catch (error: any) {
      console.error('Failed to save user:', error)
      const errorMsg = error.response?.data?.message || 'Failed to save user'
      message.error(errorMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteUser = (user: User) => {
    confirm({
      title: 'Delete User',
      icon: <ExclamationCircleOutlined />,
      content: `Are you sure you want to delete user "${user.username}"? This action cannot be undone.`,
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      async onOk() {
        try {
          await apiClient.post(`/user/delete/${user.id}`)
          message.success('User deleted successfully')
          await fetchUsers()
        } catch (error: any) {
          console.error('Failed to delete user:', error)
          const errorMsg = error.response?.data?.message || 'Failed to delete user'
          message.error(errorMsg)
        }
      },
    })
  }

  // Mock data removed - now using real API data from fetchUsers()

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
          <UserOutlined style={{ color: '#1890ff' }} />
          <strong>{text}</strong>
          {record.is_admin && <Tag color="red">Admin</Tag>}
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: 'Full Name',
      dataIndex: 'full_name',
      key: 'full_name',
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => {
        const colors: Record<string, string> = {
          Administrator: 'red',
          Admin: 'red',
          Manager: 'blue',
          Technician: 'green',
          User: 'default',
        }
        return <Tag color={colors[role] || 'default'}>{role}</Tag>
      },
      onFilter: (value, record) => record.role === value,
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => date ? new Date(date).toLocaleDateString() : '-',
      sorter: (a, b) => {
        if (!a.created_at) return 1
        if (!b.created_at) return -1
        return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            title="Edit User"
            onClick={() => handleEditUser(record)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            size="small"
            title="Delete User"
            onClick={() => handleDeleteUser(record)}
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
              <Button icon={<ReloadOutlined />} onClick={fetchUsers} loading={loading}>
                Refresh
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddUser}>
                Add User
              </Button>
            </Space>
          </div>

          <div className="users-summary">
            <Space size="large">
              <div className="summary-item">
                <span className="summary-label">Total Users:</span>
                <span className="summary-value">{users.length}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Admins:</span>
                <span className="summary-value summary-admin">
                  {users.filter((u) => u.is_admin).length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Roles:</span>
                <span className="summary-value">{roles.length}</span>
              </div>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={users}
            loading={loading}
            pagination={{
              pageSize: 25,
              showSizeChanger: true,
              pageSizeOptions: ['25', '50', '100'],
              showTotal: (total) => `Total ${total} users`,
            }}
          />
        </Space>
      </Card>

      <UserModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setSelectedUser(null)
        }}
        onSubmit={handleSubmitUser}
        user={selectedUser}
        roles={roles}
        loading={submitting}
      />
    </div>
  )
}

export default Users
