import React, { useState } from 'react'
import { Card, Table, Button, Input, Space, Tag, Select, Typography, Progress } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  CheckOutlined,
  FileTextOutlined,
} from '@ant-design/icons'
import '../styles/audits.css'

const { Title } = Typography
const { Search } = Input

interface Audit {
  key: string
  id: number
  name: string
  site: string
  date: string
  totalTasks: number
  completedTasks: number
  status: 'pending' | 'in-progress' | 'completed'
  assignedTo: string
  type: 'safety' | 'quality' | 'maintenance' | 'compliance'
}

const Audits: React.FC = () => {
  const [selectedType, setSelectedType] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')

  // Mock data - will be replaced with API calls
  const mockData: Audit[] = [
    {
      key: '1',
      id: 1,
      name: 'Q4 Safety Audit',
      site: 'Main Plant',
      date: '2025-11-15',
      totalTasks: 45,
      completedTasks: 38,
      status: 'in-progress',
      assignedTo: 'Safety Team',
      type: 'safety',
    },
    {
      key: '2',
      id: 2,
      name: 'Equipment Quality Check',
      site: 'Warehouse',
      date: '2025-10-28',
      totalTasks: 32,
      completedTasks: 32,
      status: 'completed',
      assignedTo: 'QA Team',
      type: 'quality',
    },
    {
      key: '3',
      id: 3,
      name: 'Monthly Maintenance Review',
      site: 'Main Plant',
      date: '2025-11-10',
      totalTasks: 28,
      completedTasks: 15,
      status: 'in-progress',
      assignedTo: 'Maintenance',
      type: 'maintenance',
    },
    {
      key: '4',
      id: 4,
      name: 'ISO Compliance Audit',
      site: 'All Sites',
      date: '2025-12-01',
      totalTasks: 67,
      completedTasks: 0,
      status: 'pending',
      assignedTo: 'Compliance',
      type: 'compliance',
    },
  ]

  const columns: ColumnsType<Audit> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Audit Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const colors: Record<string, string> = {
          safety: 'red',
          quality: 'blue',
          maintenance: 'orange',
          compliance: 'purple',
        }
        return <Tag color={colors[type]}>{type.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Site',
      dataIndex: 'site',
      key: 'site',
    },
    {
      title: 'Date',
      dataIndex: 'date',
      key: 'date',
      sorter: (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime(),
    },
    {
      title: 'Progress',
      key: 'progress',
      render: (_, record) => {
        const percent = Math.round((record.completedTasks / record.totalTasks) * 100)
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Progress
              percent={percent}
              size="small"
              status={percent === 100 ? 'success' : 'active'}
            />
            <span className="progress-text">
              {record.completedTasks}/{record.totalTasks} tasks
            </span>
          </Space>
        )
      },
      width: 200,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          pending: 'default',
          'in-progress': 'blue',
          completed: 'green',
        }
        return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Assigned To',
      dataIndex: 'assignedTo',
      key: 'assignedTo',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<FileTextOutlined />}
            size="small"
            title="View Details"
          />
          {record.status !== 'completed' && (
            <Button
              type="text"
              icon={<CheckOutlined />}
              size="small"
              title="Complete"
              style={{ color: '#52c41a' }}
            />
          )}
        </Space>
      ),
    },
  ]

  return (
    <div className="audits-container">
      <div className="audits-header">
        <Title level={2}>Audits</Title>
      </div>

      <Card className="audits-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="audits-controls">
            <Space wrap>
              <Search
                placeholder="Search audits..."
                allowClear
                style={{ width: 300 }}
                prefix={<SearchOutlined />}
              />
              <Select
                value={selectedType}
                onChange={setSelectedType}
                style={{ width: 150 }}
                options={[
                  { value: 'all', label: 'All Types' },
                  { value: 'safety', label: 'Safety' },
                  { value: 'quality', label: 'Quality' },
                  { value: 'maintenance', label: 'Maintenance' },
                  { value: 'compliance', label: 'Compliance' },
                ]}
              />
              <Select
                value={selectedStatus}
                onChange={setSelectedStatus}
                style={{ width: 150 }}
                options={[
                  { value: 'all', label: 'All Status' },
                  { value: 'pending', label: 'Pending' },
                  { value: 'in-progress', label: 'In Progress' },
                  { value: 'completed', label: 'Completed' },
                ]}
              />
            </Space>
            <Space>
              <Button icon={<ReloadOutlined />}>Refresh</Button>
              <Button type="primary" icon={<PlusOutlined />}>
                New Audit
              </Button>
            </Space>
          </div>

          <div className="audits-summary">
            <Space size="large">
              <div className="summary-item">
                <span className="summary-label">Total Audits:</span>
                <span className="summary-value">{mockData.length}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Pending:</span>
                <span className="summary-value summary-pending">
                  {mockData.filter((a) => a.status === 'pending').length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">In Progress:</span>
                <span className="summary-value summary-progress">
                  {mockData.filter((a) => a.status === 'in-progress').length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Completed:</span>
                <span className="summary-value summary-completed">
                  {mockData.filter((a) => a.status === 'completed').length}
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
              showTotal: (total) => `Total ${total} audits`,
            }}
          />
        </Space>
      </Card>
    </div>
  )
}

export default Audits
