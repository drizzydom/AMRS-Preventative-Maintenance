import React, { useEffect } from 'react'
import { Form, Input, Select, Button, Space, message } from 'antd'
import BaseModal from './BaseModal'

interface Machine {
  id?: number
  name: string
  serial: string
  model: string
  machine_number?: string
  site: string
  site_id?: number
  status: 'active' | 'inactive' | 'maintenance'
}

interface MachineModalProps {
  visible: boolean
  machine?: Machine
  sites?: any[]
  onCancel: () => void
  onSubmit: (values: any) => Promise<void>
}

const MachineModal: React.FC<MachineModalProps> = ({
  visible,
  machine,
  sites = [],
  onCancel,
  onSubmit,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)

  useEffect(() => {
    if (visible && machine) {
      form.setFieldsValue({
        name: machine.name,
        serial: machine.serial,
        model: machine.model,
        machine_number: machine.machine_number,
        site_id: machine.site_id,
        status: machine.status
      })
    } else if (visible) {
      form.resetFields()
    }
  }, [visible, machine, form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      setLoading(true)
      await onSubmit(values)
      message.success(machine ? 'Machine updated successfully' : 'Machine created successfully')
      form.resetFields()
      onCancel()
    } catch (error: any) {
      if (error.errorFields) {
        message.error('Please fill in all required fields')
      } else {
        message.error('Failed to save machine')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <BaseModal
      title={machine ? 'Edit Machine' : 'Add New Machine'}
      open={visible}
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          key="submit"
          type="primary"
          loading={loading}
          onClick={handleSubmit}
        >
          {machine ? 'Update' : 'Create'}
        </Button>,
      ]}
      width={600}
    >
      <Form
        form={form}
        layout="vertical"
        autoComplete="off"
      >
        <Form.Item
          name="name"
          label="Machine Name"
          rules={[{ required: true, message: 'Please enter machine name' }]}
        >
          <Input placeholder="Enter machine name" />
        </Form.Item>

        <Form.Item
          name="serial"
          label="Serial Number"
        >
          <Input placeholder="Enter serial number" />
        </Form.Item>

        <Form.Item
          name="model"
          label="Model"
        >
          <Input placeholder="Enter model" />
        </Form.Item>

        <Form.Item
          name="machine_number"
          label="Machine Number"
        >
          <Input placeholder="Enter machine number" />
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
          name="status"
          label="Status"
          rules={[{ required: true, message: 'Please select status' }]}
          initialValue="active"
        >
          <Select>
            <Select.Option value="active">Active</Select.Option>
            <Select.Option value="inactive">Inactive</Select.Option>
            <Select.Option value="maintenance">Maintenance</Select.Option>
          </Select>
        </Form.Item>
      </Form>
    </BaseModal>
  )
}

export default MachineModal
