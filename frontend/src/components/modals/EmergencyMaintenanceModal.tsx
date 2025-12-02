import React, { useState, useEffect } from 'react'
import { Modal, Form, Select, Input, DatePicker, message, Typography, Alert, Space } from 'antd'
import { WarningOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import apiClient from '../../utils/api'

const { TextArea } = Input
const { Text, Title } = Typography
const { Option } = Select

interface Site {
  id: number
  name: string
}

interface Machine {
  id: number
  name: string
  site_id: number
  serial_number?: string
}

interface Service {
  id: number
  name: string
  description?: string
}

interface EmergencyMaintenanceModalProps {
  open: boolean
  onClose: () => void
  onSuccess: () => void
}

const EmergencyMaintenanceModal: React.FC<EmergencyMaintenanceModalProps> = ({
  open,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm()
  const [sites, setSites] = useState<Site[]>([])
  const [machines, setMachines] = useState<Machine[]>([])
  const [services, setServices] = useState<Service[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  
  const [selectedSite, setSelectedSite] = useState<number | null>(null)
  const [selectedMachine, setSelectedMachine] = useState<number | null>(null)

  useEffect(() => {
    if (open) {
      fetchSites()
      form.setFieldsValue({
        date: dayjs(),
        type: 'Emergency',
      })
    }
  }, [open, form])

  const fetchSites = async () => {
    try {
      setLoading(true)
      const response = await apiClient.get('/api/v1/sites')
      setSites(response.data.data || [])
    } catch (error) {
      console.error('Failed to load sites:', error)
      message.error('Failed to load sites')
    } finally {
      setLoading(false)
    }
  }

  const fetchMachines = async (siteId: number) => {
    try {
      const response = await apiClient.get(`/api/v1/sites/${siteId}/machines`)
      setMachines(response.data.data || [])
    } catch (error) {
      console.error('Failed to load machines:', error)
      message.error('Failed to load machines')
    }
  }

  const fetchServices = async (machineId: number) => {
    try {
      const response = await apiClient.get(`/api/v1/machines/${machineId}/parts`)
      setServices(response.data.data || [])
    } catch (error) {
      console.error('Failed to load services:', error)
      message.error('Failed to load services')
    }
  }

  const handleSiteChange = (siteId: number) => {
    setSelectedSite(siteId)
    setSelectedMachine(null)
    setMachines([])
    setServices([])
    form.setFieldsValue({ machine_id: undefined, service_ids: undefined })
    fetchMachines(siteId)
  }

  const handleMachineChange = (machineId: number) => {
    setSelectedMachine(machineId)
    setServices([])
    form.setFieldsValue({ service_ids: undefined })
    fetchServices(machineId)
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setSubmitting(true)

      const payload = {
        machine_id: values.machine_id,
        part_ids: values.service_ids,
        date: values.date.format('YYYY-MM-DD'),
        type: 'Emergency', // Always Emergency for this modal
        description: values.description,
        notes: values.notes || '',
        po_number: values.po_number,
        work_order_number: values.work_order_number,
      }

      await apiClient.post('/api/v1/maintenance/complete-multiple', payload)
      
      message.success('Emergency maintenance logged successfully')
      form.resetFields()
      setSelectedSite(null)
      setSelectedMachine(null)
      setMachines([])
      setServices([])
      onSuccess()
      onClose()
    } catch (error: any) {
      console.error('Failed to log emergency maintenance:', error)
      const errorMsg = error.response?.data?.error || 'Failed to log emergency maintenance'
      message.error(errorMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = () => {
    form.resetFields()
    setSelectedSite(null)
    setSelectedMachine(null)
    setMachines([])
    setServices([])
    onClose()
  }

  return (
    <Modal
      title={
        <Space>
          <WarningOutlined style={{ color: '#ff4d4f' }} />
          <span>Log Emergency Maintenance</span>
        </Space>
      }
      open={open}
      onOk={handleSubmit}
      onCancel={handleCancel}
      okText="Log Emergency Maintenance"
      okButtonProps={{ 
        loading: submitting, 
        danger: true,
        icon: <WarningOutlined />
      }}
      width={600}
    >
      <Alert
        message="Emergency Maintenance"
        description="Use this form to quickly log unscheduled or emergency maintenance. All entries will be marked as 'Emergency' type."
        type="warning"
        showIcon
        style={{ marginBottom: 16 }}
      />

      <Form
        form={form}
        layout="vertical"
        initialValues={{
          date: dayjs(),
          type: 'Emergency',
        }}
      >
        <Form.Item
          name="site_id"
          label="Site"
          rules={[{ required: true, message: 'Please select a site' }]}
        >
          <Select
            placeholder="Select site"
            onChange={handleSiteChange}
            loading={loading}
            showSearch
            filterOption={(input, option) =>
              (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {sites.map((site) => (
              <Option key={site.id} value={site.id}>
                {site.name}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="machine_id"
          label="Machine"
          rules={[{ required: true, message: 'Please select a machine' }]}
        >
          <Select
            placeholder="Select machine"
            onChange={handleMachineChange}
            disabled={!selectedSite}
            showSearch
            filterOption={(input, option) =>
              (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {machines.map((machine) => (
              <Option key={machine.id} value={machine.id}>
                {machine.name}
                {machine.serial_number && ` (S/N: ${machine.serial_number})`}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="service_ids"
          label="Service(s) Affected"
          rules={[{ required: true, message: 'Please select at least one service' }]}
        >
          <Select
            mode="multiple"
            placeholder="Select affected services"
            disabled={!selectedMachine}
            showSearch
            filterOption={(input, option) =>
              (option?.children as unknown as string)?.toLowerCase().includes(input.toLowerCase())
            }
          >
            {services.map((service) => (
              <Option key={service.id} value={service.id}>
                {service.name}
              </Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="date"
          label="Date"
          rules={[{ required: true, message: 'Please select a date' }]}
        >
          <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Description"
          rules={[{ required: true, message: 'Please describe the emergency maintenance' }]}
        >
          <TextArea
            rows={3}
            placeholder="Describe the issue and work performed..."
          />
        </Form.Item>

        <Form.Item
          name="notes"
          label="Additional Notes"
        >
          <TextArea
            rows={2}
            placeholder="Any additional notes or observations..."
          />
        </Form.Item>

        <Space style={{ width: '100%' }} size="middle">
          <Form.Item
            name="po_number"
            label="PO Number"
            rules={[{ required: true, message: 'PO Number is required' }]}
            style={{ flex: 1, marginBottom: 0 }}
          >
            <Input placeholder="Enter PO number" maxLength={32} />
          </Form.Item>

          <Form.Item
            name="work_order_number"
            label="Work Order Number"
            rules={[{ required: true, message: 'Work Order is required' }]}
            style={{ flex: 1, marginBottom: 0 }}
          >
            <Input placeholder="Enter work order" maxLength={128} />
          </Form.Item>
        </Space>
      </Form>
    </Modal>
  )
}

export default EmergencyMaintenanceModal
