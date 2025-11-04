import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Input, Space, Tag, Select, Typography, Progress, message, Modal } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  CheckOutlined,
  FileTextOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import apiClient from '../utils/api'
import AuditModal from '../components/modals/AuditModal'
import '../styles/audits.css'

const { Title } = Typography
const { Search } = Input
const { confirm } = Modal

interface Audit {
  key: string
  id: number
  name: string
  description?: string
  site: string
  site_id: number
  interval: string
  custom_interval_days?: number
  totalMachines: number
  completedToday: number
  status: 'pending' | 'in-progress' | 'completed'
  machines: Array<{ id: number; name: string }>
  created_at?: string
}

const Audits: React.FC = () => {
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [audits, setAudits] = useState<Audit[]>([])
  const [sites, setSites] = useState<any[]>([])
  const [machines, setMachines] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedAudit, setSelectedAudit] = useState<Audit | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchAudits = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/audits')
      const auditsData = response.data.data.map((audit: any) => ({
        key: audit.id.toString(),
        id: audit.id,
        name: audit.name,
        description: audit.description || '',
        site: audit.site,
        site_id: audit.site_id,
        interval: audit.interval,
        custom_interval_days: audit.custom_interval_days,
        totalMachines: audit.totalMachines || 0,
        completedToday: audit.completedToday || 0,
        status: audit.status,
        machines: audit.machines || [],
        created_at: audit.created_at,
      }))
      setAudits(auditsData)
    } catch (error: any) {
      console.error('Failed to load audits:', error)
      message.error('Failed to load audits')
    } finally {
      setLoading(false)
    }
  }

  const fetchSites = async () => {
    try {
      const response = await apiClient.get('/api/v1/sites')
      setSites(response.data.data)
    } catch (error) {
      console.error('Failed to load sites:', error)
    }
  }

  const fetchMachines = async () => {
    try {
      const response = await apiClient.get('/api/v1/machines')
      setMachines(response.data.data)
    } catch (error) {
      console.error('Failed to load machines:', error)
    }
  }

  useEffect(() => {
    fetchAudits()
    fetchSites()
    fetchMachines()
  }, [])

  const handleAddAudit = () => {
    setSelectedAudit(null)
    setModalOpen(true)
  }

  const handleEditAudit = (audit: Audit) => {
    setSelectedAudit(audit)
    setModalOpen(true)
  }

  const handleSubmitAudit = async (values: any) => {
    try {
      setSubmitting(true)
      const formData = new FormData()
      formData.append('name', values.name)
      formData.append('description', values.description || '')
      formData.append('site_id', values.site_id.toString())
      formData.append('interval', values.interval)
      
      if (values.interval === 'custom' && values.custom_interval_days) {
        formData.append('custom_interval_days', values.custom_interval_days.toString())
      }

      // Add machine_ids as array
      if (values.machine_ids && values.machine_ids.length > 0) {
        values.machine_ids.forEach((id: number) => {
          formData.append('machine_ids', id.toString())
        })
      }

      formData.append('create_audit', '1')

      if (selectedAudit) {
        // Edit not supported in current backend - would need new endpoint
        message.warning('Edit functionality not yet available')
      } else {
        // Create new audit
        await apiClient.post('/audits', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        message.success('Audit task created successfully')
      }

      setModalOpen(false)
      setSelectedAudit(null)
      await fetchAudits()
    } catch (error: any) {
      console.error('Failed to save audit:', error)
      const errorMsg = error.response?.data?.message || 'Failed to save audit'
      message.error(errorMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteAudit = (audit: Audit) => {
    confirm({
      title: 'Delete Audit Task',
      icon: <ExclamationCircleOutlined />,
      content: `Are you sure you want to delete "${audit.name}"? This will also delete all completion records.`,
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      async onOk() {
        try {
          await apiClient.post(`/audit-tasks/delete/${audit.id}`)
          message.success('Audit task deleted successfully')
          await fetchAudits()
        } catch (error: any) {
          console.error('Failed to delete audit:', error)
          const errorMsg = error.response?.data?.message || 'Failed to delete audit'
          message.error(errorMsg)
        }
      },
    })
  }

  // Mock data removed - now using real API data from fetchAudits()

  const columns: ColumnsType<Audit> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Task Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: 'Site',
      dataIndex: 'site',
      key: 'site',
    },
    {
      title: 'Interval',
      dataIndex: 'interval',
      key: 'interval',
      render: (interval: string, record) => {
        if (interval === 'custom' && record.custom_interval_days) {
          return `Every ${record.custom_interval_days} day${record.custom_interval_days > 1 ? 's' : ''}`
        }
        return interval.charAt(0).toUpperCase() + interval.slice(1)
      },
    },
    {
      title: 'Machines',
      dataIndex: 'totalMachines',
      key: 'totalMachines',
      render: (total) => <Tag color="blue">{total}</Tag>,
    },
    {
      title: 'Today\'s Progress',
      key: 'progress',
      render: (_, record) => {
        const percent = record.totalMachines > 0 
          ? Math.round((record.completedToday / record.totalMachines) * 100) 
          : 0
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Progress
              percent={percent}
              size="small"
              status={percent === 100 ? 'success' : 'active'}
            />
            <span className="progress-text">
              {record.completedToday}/{record.totalMachines} completed
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
      title: 'Actions',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            title="Edit"
            onClick={() => handleEditAudit(record)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            size="small"
            title="Delete"
            onClick={() => handleDeleteAudit(record)}
          />
        </Space>
      ),
    },
  ]

  return (
    <div className="audits-container">
      <div className="audits-header">
        <Title level={2}>Audit Tasks</Title>
      </div>

      <Card className="audits-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="audits-controls">
            <Space wrap>
              <Search
                placeholder="Search audit tasks..."
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
                  { value: 'in-progress', label: 'In Progress' },
                  { value: 'completed', label: 'Completed' },
                ]}
              />
            </Space>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchAudits} loading={loading}>
                Refresh
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddAudit}>
                New Audit Task
              </Button>
            </Space>
          </div>

          <div className="audits-summary">
            <Space size="large">
              <div className="summary-item">
                <span className="summary-label">Total Tasks:</span>
                <span className="summary-value">{audits.length}</span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Pending:</span>
                <span className="summary-value summary-pending">
                  {audits.filter((a) => a.status === 'pending').length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">In Progress:</span>
                <span className="summary-value summary-progress">
                  {audits.filter((a) => a.status === 'in-progress').length}
                </span>
              </div>
              <div className="summary-item">
                <span className="summary-label">Completed:</span>
                <span className="summary-value summary-completed">
                  {audits.filter((a) => a.status === 'completed').length}
                </span>
              </div>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={audits}
            loading={loading}
            pagination={{
              pageSize: 25,
              showSizeChanger: true,
              pageSizeOptions: ['25', '50', '100'],
              showTotal: (total) => `Total ${total} audit tasks`,
            }}
          />
        </Space>
      </Card>

      <AuditModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setSelectedAudit(null)
        }}
        onSubmit={handleSubmitAudit}
        audit={selectedAudit}
        sites={sites}
        machines={machines}
        loading={submitting}
      />
    </div>
  )
}

export default Audits
