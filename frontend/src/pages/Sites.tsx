import React, { useState, useEffect } from 'react'
import { Card, Table, Button, Input, Space, Tag, Typography, Row, Col, Statistic, message, Spin, Modal } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import {
  PlusOutlined,
  SearchOutlined,
  ReloadOutlined,
  EditOutlined,
  DeleteOutlined,
  EnvironmentOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import apiClient from '../utils/api'
import SiteModal from '../components/modals/SiteModal'
import '../styles/sites.css'

const { Title } = Typography
const { Search } = Input
const { confirm } = Modal

interface Site {
  key: string
  id: number
  name: string
  location: string
  contact_email?: string
  notification_threshold?: number
  enable_notifications?: boolean
  machineCount: number
  activeCount: number
  maintenanceThreshold: number
  contactPerson: string
  phone: string
  status: 'active' | 'inactive'
}

const Sites: React.FC = () => {
  const [sites, setSites] = useState<Site[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedSite, setSelectedSite] = useState<Site | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const fetchSites = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/sites')
      const sitesData = response.data.data.map((site: any) => ({
        key: site.id.toString(),
        id: site.id,
        name: site.name,
        location: site.location || '',
        contact_email: site.contact_email || '',
        notification_threshold: site.notification_threshold || 30,
        enable_notifications: site.enable_notifications || false,
        machineCount: site.machineCount || 0,
        activeCount: site.activeCount || 0,
        maintenanceThreshold: site.maintenanceThreshold || 7,
        contactPerson: site.contactPerson || '',
        phone: site.phone || '',
        status: site.status || 'active',
      }))
      setSites(sitesData)
    } catch (error: any) {
      console.error('Failed to load sites:', error)
      message.error('Failed to load sites')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSites()
  }, [])

  // Listen for keyboard shortcuts
  useEffect(() => {
    const handleKeyboardNew = () => {
      handleAddSite()
    }
    const handleKeyboardRefresh = () => {
      fetchSites()
      message.info('Refreshing sites...')
    }

    window.addEventListener('keyboard-new', handleKeyboardNew)
    window.addEventListener('keyboard-refresh', handleKeyboardRefresh)

    return () => {
      window.removeEventListener('keyboard-new', handleKeyboardNew)
      window.removeEventListener('keyboard-refresh', handleKeyboardRefresh)
    }
  }, [])

  const handleAddSite = () => {
    setSelectedSite(null)
    setModalOpen(true)
  }

  const handleEditSite = (site: Site) => {
    setSelectedSite(site)
    setModalOpen(true)
  }

  const handleSubmitSite = async (values: any) => {
    try {
      setSubmitting(true)
      const formData = new FormData()
      formData.append('name', values.name)
      formData.append('location', values.location || '')
      formData.append('contact_email', values.contact_email || '')
      formData.append('notification_threshold', values.notification_threshold?.toString() || '30')
      
      if (values.enable_notifications) {
        formData.append('enable_notifications', 'on')
      }

      if (selectedSite) {
        // Edit existing site
        await apiClient.post(`/site/edit/${selectedSite.id}`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        message.success('Site updated successfully')
      } else {
        // Create new site
        await apiClient.post('/sites', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        message.success('Site created successfully')
      }

      setModalOpen(false)
      setSelectedSite(null)
      await fetchSites()
    } catch (error: any) {
      console.error('Failed to save site:', error)
      const errorMsg = error.response?.data?.message || 'Failed to save site'
      message.error(errorMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteSite = (site: Site) => {
    confirm({
      title: 'Delete Site',
      icon: <ExclamationCircleOutlined />,
      content: `Are you sure you want to delete "${site.name}"? This action cannot be undone.`,
      okText: 'Delete',
      okType: 'danger',
      cancelText: 'Cancel',
      async onOk() {
        try {
          await apiClient.post(`/sites/delete/${site.id}`)
          message.success('Site deleted successfully')
          await fetchSites()
        } catch (error: any) {
          console.error('Failed to delete site:', error)
          const errorMsg = error.response?.data?.message || 'Failed to delete site'
          message.error(errorMsg)
        }
      },
    })
  }

  const columns: ColumnsType<Site> = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Site Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text) => (
        <Space>
          <EnvironmentOutlined style={{ color: '#1890ff' }} />
          <strong>{text}</strong>
        </Space>
      ),
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
    },
    {
      title: 'Total Machines',
      dataIndex: 'machineCount',
      key: 'machineCount',
      sorter: (a, b) => a.machineCount - b.machineCount,
      render: (count) => <Tag color="blue">{count}</Tag>,
    },
    {
      title: 'Active Machines',
      dataIndex: 'activeCount',
      key: 'activeCount',
      sorter: (a, b) => a.activeCount - b.activeCount,
      render: (count) => <Tag color="green">{count}</Tag>,
    },
    {
      title: 'Maintenance Threshold (days)',
      dataIndex: 'maintenanceThreshold',
      key: 'maintenanceThreshold',
      sorter: (a, b) => a.maintenanceThreshold - b.maintenanceThreshold,
    },
    {
      title: 'Contact Person',
      dataIndex: 'contactPerson',
      key: 'contactPerson',
    },
    {
      title: 'Phone',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'red'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space size="small">
          <Button
            type="text"
            icon={<EditOutlined />}
            size="small"
            title="Edit"
            onClick={() => handleEditSite(record)}
          />
          <Button
            type="text"
            danger
            icon={<DeleteOutlined />}
            size="small"
            title="Delete"
            onClick={() => handleDeleteSite(record)}
          />
        </Space>
      ),
    },
  ]

  const totalMachines = sites.reduce((sum: number, site: Site) => sum + site.machineCount, 0)
  const totalActive = sites.reduce((sum: number, site: Site) => sum + site.activeCount, 0)

  return (
    <div className="sites-container">
      <div className="sites-header">
        <Title level={2}>Sites Management</Title>
      </div>

      <Row gutter={[16, 16]} className="sites-stats">
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Sites"
              value={sites.length}
              prefix={<EnvironmentOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Total Machines"
              value={totalMachines}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Active Machines"
              value={totalActive}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={6}>
          <Card>
            <Statistic
              title="Inactive Machines"
              value={totalMachines - totalActive}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Card className="sites-table-card">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div className="sites-controls">
            <Search
              placeholder="Search sites..."
              allowClear
              style={{ width: 300 }}
              prefix={<SearchOutlined />}
            />
            <Space>
              <Button icon={<ReloadOutlined />} onClick={fetchSites} loading={loading}>
                Refresh
              </Button>
              <Button type="primary" icon={<PlusOutlined />} onClick={handleAddSite}>
                Add Site
              </Button>
            </Space>
          </div>

          <Table
            columns={columns}
            dataSource={sites}
            loading={loading}
            pagination={{
              pageSize: 10,
              showSizeChanger: true,
              pageSizeOptions: ['10', '20', '50'],
              showTotal: (total) => `Total ${total} sites`,
            }}
          />
        </Space>
      </Card>

      <SiteModal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setSelectedSite(null)
        }}
        onSubmit={handleSubmitSite}
        site={selectedSite}
        loading={submitting}
      />
    </div>
  )
}

export default Sites
