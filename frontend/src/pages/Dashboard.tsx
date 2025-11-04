import React, { useEffect, useState } from 'react'
import { Card, Row, Col, Statistic, Table, Button, Space, Typography, Spin, message } from 'antd'
import {
  ToolOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
} from '@ant-design/icons'
import apiClient from '../utils/api'
import '../styles/dashboard.css'

const { Title } = Typography

interface DashboardStats {
  total_machines: number
  overdue: number
  due_soon: number
  completed: number
}

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/dashboard')
      setStats(response.data.data)
    } catch (error: any) {
      console.error('Failed to load dashboard data:', error)
      message.error('Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const statsData = stats ? [
    { title: 'Total Machines', value: stats.total_machines, icon: <ToolOutlined />, color: '#1890ff' },
    { title: 'Overdue', value: stats.overdue, icon: <WarningOutlined />, color: '#ff4d4f' },
    { title: 'Due Soon', value: stats.due_soon, icon: <ClockCircleOutlined />, color: '#faad14' },
    { title: 'Completed', value: stats.completed, icon: <CheckCircleOutlined />, color: '#52c41a' },
  ] : []

  const recentTasksColumns = [
    { title: 'Machine', dataIndex: 'machine', key: 'machine' },
    { title: 'Task', dataIndex: 'task', key: 'task' },
    { title: 'Due Date', dataIndex: 'dueDate', key: 'dueDate' },
    { title: 'Status', dataIndex: 'status', key: 'status' },
    { title: 'Site', dataIndex: 'site', key: 'site' },
  ]

  const recentTasksData = [
    {
      key: '1',
      machine: 'Machine A',
      task: 'Oil Change',
      dueDate: '2025-11-05',
      status: 'Pending',
      site: 'Main Plant',
    },
    {
      key: '2',
      machine: 'Machine B',
      task: 'Filter Replacement',
      dueDate: '2025-11-03',
      status: 'Overdue',
      site: 'Warehouse',
    },
  ]

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <Spin size="large" tip="Loading dashboard data..." />
      </div>
    )
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <Title level={2}>Dashboard</Title>
        <Space>
          <Button type="primary">New Task</Button>
          <Button>Export Report</Button>
          <Button icon={<ReloadOutlined />} onClick={fetchDashboardData}>Refresh</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} className="stats-row">
        {statsData.map((stat, index) => (
          <Col xs={24} sm={12} md={6} key={index}>
            <Card>
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={stat.icon}
                valueStyle={{ color: stat.color }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Card className="recent-tasks-card" title="Recent Maintenance Tasks">
        <Table
          columns={recentTasksColumns}
          dataSource={recentTasksData}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  )
}

export default Dashboard
