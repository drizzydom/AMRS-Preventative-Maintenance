import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Input, Space, Tag, Select, Typography, DatePicker, message, Modal, Spin } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  CheckOutlined,
  CloseOutlined,
  CalendarOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import MaintenanceTaskModal from '../components/modals/MaintenanceTaskModal'
import apiClient from '../utils/api'
import '../styles/maintenance.css'

const { Title } = Typography
const { Search } = Input
const { RangePicker } = DatePicker
const { confirm } = Modal

interface MaintenanceTask {
  key: string
  id: number
  machine: string
  task: string
  dueDate: string | null
  status: 'pending' | 'overdue' | 'completed' | 'in-progress' | 'due-soon'
  assignedTo: string
  site: string
  priority: 'low' | 'medium' | 'high' | 'critical'
}

const Maintenance: React.FC = () => {
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [selectedSite, setSelectedSite] = useState<string>('all')
  const [modalVisible, setModalVisible] = useState(false)
  const [selectedTask, setSelectedTask] = useState<MaintenanceTask | undefined>(undefined)
  const [tasks, setTasks] = useState<MaintenanceTask[]>([])
  const [loading, setLoading] = useState(true)

  const fetchMaintenanceTasks = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/maintenance')
      const tasksData = response.data.data.map((task: any) => ({
        key: task.id.toString(),
        id: task.id,
        machine: task.machine,
        task: task.task,
        dueDate: task.dueDate,
        status: task.status,
        assignedTo: task.assignedTo || '',
        site: task.site,
        priority: task.priority || 'medium',
      }))
      setTasks(tasksData)
    } catch (error: any) {
      console.error('Failed to load maintenance tasks:', error)
      message.error('Failed to load maintenance tasks')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMaintenanceTasks()
  }, [])

  // Remove mock data that was here before
  const [mockTasksRemoved] = useState<MaintenanceTask[]>([
    {
      key: '1',
      id: 1,
      machine: 'CNC Machine A',
      task: 'Oil Change',
      dueDate: '2025-11-05',
      status: 'pending',
      assignedTo: 'John Doe',
      site: 'Main Plant',
      priority: 'medium',
    },
    {
      key: '2',
      id: 2,
      machine: 'Lathe Machine B',
      task: 'Filter Replacement',
      dueDate: '2025-11-03',
      status: 'overdue',
      assignedTo: 'Jane Smith',
      site: 'Warehouse',
      priority: 'high',
    },
    {
      key: '3',
      id: 3,
      machine: 'Press Machine C',
      task: 'Inspection',
      dueDate: '2025-10-25',
      status: 'completed',
      assignedTo: 'Bob Johnson',
      site: 'Main Plant',
      priority: 'low',
    },
    {
      key: '4',
      id: 4,
      machine: 'CNC Machine A',
      task: 'Belt Replacement',
      dueDate: '2025-11-02',
      status: 'in-progress',
      assignedTo: 'John Doe',
      site: 'Main Plant',
      priority: 'critical',
    },
  ])

  const handleCreateTask = () => {
    setSelectedTask(undefined)
    setModalVisible(true)
  }

  const handleCompleteTask = (task: MaintenanceTask) => {
    confirm({
      title: 'Complete Task',
      icon: <CheckOutlined />,
      content: `Mark "${task.task}" as completed?`,
      okText: 'Complete',
      okType: 'primary',
      cancelText: 'Cancel',
      onOk() {
        setTasks(tasks.map(t => 
          t.id === task.id 
            ? { ...t, status: 'completed' as const }
            : t
        ))
        message.success('Task marked as completed')
      },
    })
  }

  const handleCancelTask = (task: MaintenanceTask) => {
    confirm({
      title: 'Cancel Task',
      icon: <ExclamationCircleOutlined />,
      content: `Are you sure you want to cancel "${task.task}"?`,
      okText: 'Cancel Task',
      okType: 'danger',
      cancelText: 'Go Back',
      onOk() {
        setTasks(tasks.filter(t => t.id !== task.id))
        message.success('Task cancelled')
      },
    })
  }

  const handleSubmitTask = async (values: any) => {
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500))
    
    if (selectedTask) {
      // Update existing task
      setTasks(tasks.map(t => 
        t.id === selectedTask.id 
          ? { ...t, ...values, key: t.key, status: t.status }
          : t
      ))
    } else {
      // Create new task
      const newTask: MaintenanceTask = {
        ...values,
        id: Math.max(...tasks.map(t => t.id)) + 1,
        key: `${tasks.length + 1}`,
        status: 'pending',
      }
      setTasks([...tasks, newTask])
    }
  }

  const columns: ColumnsType<MaintenanceTask> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Machine',
      dataIndex: 'machine',
      key: 'machine',
      sorter: (a, b) => a.machine.localeCompare(b.machine),
    },
    {
      title: 'Task',
      dataIndex: 'task',
      key: 'task',
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: 'Due Date',
      dataIndex: 'dueDate',
      key: 'dueDate',
      sorter: (a, b) => {
        const dateA = a.dueDate ? new Date(a.dueDate).getTime() : 0
        const dateB = b.dueDate ? new Date(b.dueDate).getTime() : 0
        return dateA - dateB
      },
      render: (date: string | null) => {
        if (!date) return 'N/A'
        const dueDate = new Date(date)
        const today = new Date()
        const isOverdue = dueDate < today
        return (
          <span style={{ color: isOverdue ? '#ff4d4f' : 'inherit' }}>
            {dueDate.toLocaleDateString()}
          </span>
        )
      },
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const colors: Record<string, string> = {
          pending: 'blue',
          overdue: 'red',
          completed: 'green',
          'in-progress': 'orange',
        }
        return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => {
        const colors: Record<string, string> = {
          low: 'default',
          medium: 'blue',
          high: 'orange',
          critical: 'red',
        }
        return <Tag color={colors[priority]}>{priority.toUpperCase()}</Tag>
      },
    },
    {
      title: 'Assigned To',
      dataIndex: 'assignedTo',
      key: 'assignedTo',
    },
    {
      title: 'Site',
      dataIndex: 'site',
      key: 'site',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          {record.status !== 'completed' && (
            <Button
              type="text"
              icon={<CheckOutlined />}
              size="small"
              title="Complete"
              style={{ color: '#52c41a' }}
              onClick={() => handleCompleteTask(record)}
            />
          )}
          <Button
            type="text"
            danger
            icon={<CloseOutlined />}
            size="small"
            title="Cancel"
            onClick={() => handleCancelTask(record)}
          />
        </Space>
      ),
    },
  ]

  return (
    <div className="maintenance-container">
      <div className="maintenance-header">
        <Title level={2}>Maintenance Tasks</Title>
      </div>

      <Card className="maintenance-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="maintenance-controls">
            <Space wrap>
              <Search
                placeholder="Search tasks..."
                allowClear
                style={{ width: 300 }}
                prefix={<SearchOutlined />}
              />
              <Select
                value={selectedStatus}
                onChange={setSelectedStatus}
                style={{ width: 150 }}
                options={[
                  { value: 'all', label: 'All Status' },
                  { value: 'pending', label: 'Pending' },
                  { value: 'overdue', label: 'Overdue' },
                  { value: 'in-progress', label: 'In Progress' },
                  { value: 'completed', label: 'Completed' },
                ]}
              />
              <Select
                value={selectedSite}
                onChange={setSelectedSite}
                style={{ width: 150 }}
                options={[
                  { value: 'all', label: 'All Sites' },
                  { value: 'main', label: 'Main Plant' },
                  { value: 'warehouse', label: 'Warehouse' },
                ]}
              />
              <RangePicker
                placeholder={['Start Date', 'End Date']}
                style={{ width: 280 }}
              />
            </Space>
            <Space>
              <Button icon={<CalendarOutlined />}>Schedule</Button>
              <Button icon={<ReloadOutlined />} onClick={fetchMaintenanceTasks} loading={loading}>
                Refresh
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleCreateTask}
              >
                New Task
              </Button>
            </Space>
          </div>

          <div className="maintenance-summary">
            <Space size="large">
              <div className="summary-item">
                <span className="summary-label">Overdue:</span>
                <span className="summary-value summary-overdue">
                  {tasks.filter((t) => t.status === 'overdue').length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">In Progress:</span>
                <span className="summary-value summary-progress">
                  {tasks.filter((t) => t.status === 'in-progress').length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Pending:</span>
                <span className="summary-value summary-pending">
                  {tasks.filter((t) => t.status === 'pending' || t.status === 'due-soon').length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Completed:</span>
                <span className="summary-value summary-completed">
                  {tasks.filter((t) => t.status === 'completed').length}
                </span>
              </div>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={tasks}
            loading={loading}
            pagination={{
              pageSize: 25,
              showSizeChanger: true,
              pageSizeOptions: ['25', '50', '100'],
              showTotal: (total) => `Total ${total} tasks`,
            }}
            scroll={{ x: 1200 }}
          />
        </Space>
      </Card>

      <MaintenanceTaskModal
        visible={modalVisible}
        task={selectedTask}
        onCancel={() => setModalVisible(false)}
        onSubmit={handleSubmitTask}
      />
    </div>
  )
}

export default Maintenance
