import React, { useEffect } from 'react'
import { Modal, Form, Input, Select, InputNumber, Row, Col } from 'antd'

const { TextArea } = Input

interface Machine {
  id: number
  name: string
}

interface Site {
  id: number
  name: string
}

interface Audit {
  id?: number
  name: string
  description?: string
  site_id: number
  interval: string
  custom_interval_days?: number
  machines: Array<{ id: number; name: string }> | number[]
}

interface AuditModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (values: any) => void
  audit: Audit | null
  sites: Site[]
  machines: Machine[]
  loading?: boolean
}

const AuditModal: React.FC<AuditModalProps> = ({
  open,
  onClose,
  onSubmit,
  audit,
  sites,
  machines,
  loading = false,
}) => {
  const [form] = Form.useForm()
  const interval = Form.useWatch('interval', form)

  useEffect(() => {
    if (open) {
      if (audit) {
        // Edit mode - populate form with audit data
        // Extract machine IDs from machines array (could be objects or numbers)
        const machineIds = Array.isArray(audit.machines) 
          ? audit.machines.map(m => typeof m === 'object' ? m.id : m)
          : []
        
        form.setFieldsValue({
          name: audit.name,
          description: audit.description || '',
          site_id: audit.site_id,
          interval: audit.interval,
          custom_interval_days: audit.custom_interval_days || 1,
          machine_ids: machineIds,
        })
      } else {
        // Create mode - reset form
        form.resetFields()
        form.setFieldsValue({
          interval: 'daily',
          custom_interval_days: 1,
        })
      }
    }
  }, [open, audit, form])

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
      title={audit ? 'Edit Audit Task' : 'Create New Audit Task'}
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={loading}
      width={700}
      okText={audit ? 'Update' : 'Create'}
      cancelText="Cancel"
    >
      <Form
        form={form}
        layout="vertical"
        autoComplete="off"
      >
        <Form.Item
          name="name"
          label="Audit Task Name"
          rules={[
            { required: true, message: 'Please enter the audit task name' },
            { min: 3, message: 'Task name must be at least 3 characters' },
          ]}
        >
          <Input placeholder="Enter audit task name" />
        </Form.Item>

        <Form.Item
          name="description"
          label="Description"
        >
          <TextArea 
            rows={3} 
            placeholder="Enter task description (optional)" 
          />
        </Form.Item>

        <Form.Item
          name="site_id"
          label="Site"
          rules={[{ required: true, message: 'Please select a site' }]}
        >
          <Select placeholder="Select a site">
            {sites.map(site => (
              <Select.Option key={site.id} value={site.id}>
                {site.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="interval"
          label="Interval"
          rules={[{ required: true, message: 'Please select an interval' }]}
        >
          <Select placeholder="Select interval">
            <Select.Option value="daily">Daily</Select.Option>
            <Select.Option value="weekly">Weekly</Select.Option>
            <Select.Option value="monthly">Monthly</Select.Option>
            <Select.Option value="custom">Custom</Select.Option>
          </Select>
        </Form.Item>

        {interval === 'custom' && (
          <Form.Item
            name="custom_interval_days"
            label="Custom Interval (days)"
            rules={[
              { required: true, message: 'Please enter custom interval' },
            ]}
          >
            <InputNumber
              min={1}
              max={365}
              placeholder="Enter number of days"
              style={{ width: '100%' }}
            />
          </Form.Item>
        )}

        <Form.Item
          name="machine_ids"
          label="Machines"
          rules={[
            { required: true, message: 'Please select at least one machine' },
          ]}
        >
          <Select
            mode="multiple"
            placeholder="Select machines for this audit task"
            filterOption={(input, option) =>
              (option?.children as unknown as string)
                .toLowerCase()
                .includes(input.toLowerCase())
            }
          >
            {machines.map(machine => (
              <Select.Option key={machine.id} value={machine.id}>
                {machine.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default AuditModal
