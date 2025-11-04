import React, { useEffect } from 'react'
import { Modal, Form, Input, InputNumber, Checkbox } from 'antd'

interface Site {
  id?: number
  name: string
  location?: string
  contact_email?: string
  notification_threshold?: number
  enable_notifications?: boolean
}

interface SiteModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (values: any) => void
  site: Site | null
  loading?: boolean
}

const SiteModal: React.FC<SiteModalProps> = ({
  open,
  onClose,
  onSubmit,
  site,
  loading = false,
}) => {
  const [form] = Form.useForm()

  useEffect(() => {
    if (open) {
      if (site) {
        // Edit mode - populate form with site data
        form.setFieldsValue({
          name: site.name,
          location: site.location || '',
          contact_email: site.contact_email || '',
          notification_threshold: site.notification_threshold || 30,
          enable_notifications: site.enable_notifications || false,
        })
      } else {
        // Create mode - reset form
        form.resetFields()
        form.setFieldsValue({
          notification_threshold: 30,
          enable_notifications: true,
        })
      }
    }
  }, [open, site, form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      onSubmit(values)
    } catch (error) {
      console.error('Form validation failed:', error)
    }
  }

  return (
    <Modal
      title={site ? 'Edit Site' : 'Add New Site'}
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={loading}
      width={600}
      okText={site ? 'Update' : 'Create'}
      cancelText="Cancel"
    >
      <Form
        form={form}
        layout="vertical"
        autoComplete="off"
      >
        <Form.Item
          name="name"
          label="Site Name"
          rules={[
            { required: true, message: 'Please enter the site name' },
            { min: 2, message: 'Site name must be at least 2 characters' },
          ]}
        >
          <Input placeholder="Enter site name" />
        </Form.Item>

        <Form.Item
          name="location"
          label="Location"
        >
          <Input placeholder="Enter location address" />
        </Form.Item>

        <Form.Item
          name="contact_email"
          label="Contact Email"
          rules={[
            { type: 'email', message: 'Please enter a valid email address' },
          ]}
        >
          <Input placeholder="Enter contact email" type="email" />
        </Form.Item>

        <Form.Item
          name="notification_threshold"
          label="Notification Threshold (days)"
          tooltip="Number of days before maintenance is due to send notifications"
          rules={[
            { required: true, message: 'Please enter notification threshold' },
          ]}
        >
          <InputNumber
            min={1}
            max={365}
            placeholder="30"
            style={{ width: '100%' }}
          />
        </Form.Item>

        <Form.Item
          name="enable_notifications"
          valuePropName="checked"
        >
          <Checkbox>Enable Notifications</Checkbox>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default SiteModal
