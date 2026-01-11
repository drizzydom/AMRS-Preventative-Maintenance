import React, { useEffect, useState } from 'react'
import { Modal, Button, Table, Space, Typography, message, Form, Input, InputNumber, Select, DatePicker, Popconfirm } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ArrowLeftOutlined } from '@ant-design/icons'
import apiClient from '../../utils/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select
const { TextArea } = Input

interface Part {
  id: number
  name: string
  description: string
  maintenance_frequency: number | null
  maintenance_unit: string
  next_maintenance: string | null
  last_maintenance: string | null
}

interface ManageServicesModalProps {
  open: boolean
  onClose: () => void
  machineId: number | null
  machineName: string
}

const ManageServicesModal: React.FC<ManageServicesModalProps> = ({
  open,
  onClose,
  machineId,
  machineName,
}) => {
  const [parts, setParts] = useState<Part[]>([])
  const [loading, setLoading] = useState(false)
  const [view, setView] = useState<'list' | 'edit' | 'create'>('list')
  const [editingPart, setEditingPart] = useState<Part | null>(null)
  
  // Form handling
  const [form] = Form.useForm()
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open && machineId) {
      fetchParts()
      setView('list')
    }
  }, [open, machineId])

  const fetchParts = async () => {
    if (!machineId) return

    try {
      setLoading(true)
      const response = await apiClient.get(`/api/v1/machines/${machineId}/parts`)
      setParts(response.data.data || [])
    } catch (error: any) {
      console.error('Failed to load services:', error)
      message.error('Failed to load services')
    } finally {
      setLoading(false)
    }
  }

  const handleEdit = (part: Part) => {
    setEditingPart(part)
    form.setFieldsValue({
      name: part.name,
      description: part.description,
      maintenance_frequency: part.maintenance_frequency,
      maintenance_unit: part.maintenance_unit,
      next_maintenance: part.next_maintenance ? dayjs(part.next_maintenance) : null
    })
    setView('edit')
  }

  const handleCreate = () => {
    setEditingPart(null)
    form.resetFields()
    form.setFieldsValue({
      maintenance_unit: 'days',
      maintenance_frequency: 30
    })
    setView('create')
  }

  const handleDelete = async (id: number) => {
    try {
      setLoading(true)
      await apiClient.post(`/api/v1/parts/${id}/delete`)
      message.success('Service deleted successfully')
      fetchParts()
    } catch (error: any) {
      console.error('Failed to delete service:', error)
      message.error('Failed to delete service')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (values: any) => {
    if (!machineId) return

    try {
      setSubmitting(true)
      
      const formData = new FormData()
      formData.append('machine_id', machineId.toString())
      formData.append('name', values.name)
      if (values.description) formData.append('description', values.description)
      if (values.maintenance_frequency) formData.append('maintenance_frequency', values.maintenance_frequency)
      if (values.maintenance_unit) formData.append('maintenance_unit', values.maintenance_unit)
      if (values.next_maintenance) formData.append('next_maintenance', values.next_maintenance.format('YYYY-MM-DD'))

      if (view === 'edit' && editingPart) {
        await apiClient.post(`/api/v1/parts/${editingPart.id}`, formData)
        message.success('Service updated successfully')
      } else {
        await apiClient.post('/api/v1/parts', formData)
        message.success('Service created successfully')
      }
      
      setView('list')
      fetchParts()
    } catch (error: any) {
      console.error('Failed to save service:', error)
      message.error(error.response?.data?.error || 'Failed to save service')
    } finally {
      setSubmitting(false)
    }
  }

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: Part) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: '0.85em', color: '#666' }}>{record.description}</div>
        </div>
      )
    },
    {
      title: 'Frequency',
      key: 'frequency',
      render: (_: any, record: Part) => (
        record.maintenance_frequency 
          ? `${record.maintenance_frequency} ${record.maintenance_unit}`
          : 'N/A'
      )
    },
    {
      title: 'Next Due',
      dataIndex: 'next_maintenance',
      key: 'next_maintenance',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: Part) => (
        <Space>
          <Button 
            type="text" 
            icon={<EditOutlined />} 
            onClick={() => handleEdit(record)}
          />
          <Popconfirm
            title="Are you sure you want to delete this service?"
            onConfirm={() => handleDelete(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ]

  const renderList = () => (
    <>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text>Manage maintenance services/tasks for <strong>{machineName}</strong></Text>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Add Service
        </Button>
      </div>
      <Table
        columns={columns}
        dataSource={parts}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 5 }}
        size="small"
      />
    </>
  )

  const renderForm = () => (
    <>
      <div style={{ marginBottom: 16 }}>
        <Button icon={<ArrowLeftOutlined />} onClick={() => setView('list')}>
          Back to List
        </Button>
      </div>
      <div style={{ marginBottom: 16 }}>
        <Title level={4}>{view === 'create' ? 'Add New Service' : 'Edit Service'}</Title>
      </div>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
      >
        <Form.Item
          name="name"
          label="Service Name"
          rules={[{ required: true, message: 'Please enter service name' }]}
        >
          <Input placeholder="e.g. Oil Change, Filter Replacement" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Description"
        >
          <TextArea rows={2} placeholder="Optional description or instructions" />
        </Form.Item>

        <div style={{ display: 'flex', gap: 16 }}>
          <Form.Item
            name="maintenance_frequency"
            label="Frequency"
            style={{ flex: 1 }}
          >
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          
          <Form.Item
            name="maintenance_unit"
            label="Unit"
            style={{ width: 120 }}
          >
            <Select>
              <Option value="days">Days</Option>
              <Option value="months">Months</Option>
              <Option value="years">Years</Option>
              <Option value="hours">Hours</Option>
              <Option value="cycles">Cycles</Option>
            </Select>
          </Form.Item>
        </div>

        <Form.Item
          name="next_maintenance"
          label="Next Maintenance Date"
          help="Manually override the next due date if needed"
        >
          <DatePicker style={{ width: '100%' }} />
        </Form.Item>

        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit" loading={submitting}>
              {view === 'create' ? 'Create Service' : 'Update Service'}
            </Button>
            <Button onClick={() => setView('list')}>Cancel</Button>
          </Space>
        </Form.Item>
      </Form>
    </>
  )

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="Maintenance Services"
      footer={null}
      width={700}
      destroyOnClose
    >
      {view === 'list' ? renderList() : renderForm()}
    </Modal>
  )
}

export default ManageServicesModal
