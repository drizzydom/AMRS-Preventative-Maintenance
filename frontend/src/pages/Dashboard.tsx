import React from 'react'
import { Card, Row, Col, Statistic, Table, Button, Space, Typography } from 'antd'
import {
  ToolOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons'
import '../styles/dashboard.css'

const { Title } = Typography

const Dashboard: React.FC = () => {
  // Mock data - will be replaced with API calls
  const statsData = [
    { title: 'Total Machines', value: 156, icon: <ToolOutlined />, color: '#1890ff' },
    { title: 'Overdue', value: 12, icon: <WarningOutlined />, color: '#ff4d4f' },
    { title: 'Due Soon', value: 28, icon: <ClockCircleOutlined />, color: '#faad14' },
    { title: 'Completed', value: 89, icon: <CheckCircleOutlined />, color: '#52c41a' },
  ]

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

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <Title level={2}>Dashboard</Title>
        <Space>
          <Button type="primary">New Task</Button>
          <Button>Export Report</Button>
          <Button>Refresh</Button>
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
