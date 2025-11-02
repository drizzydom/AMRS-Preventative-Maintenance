import React, { useEffect } from 'react'
import { Form, Input, Select, DatePicker, Button, message } from 'antd'
import BaseModal from './BaseModal'
import dayjs from 'dayjs'

interface MaintenanceTask {
  id?: number
  machine: string
  task: string
  dueDate: string
  assignedTo: string
  site: string
  priority: 'low' | 'medium' | 'high' | 'critical'
  status?: 'pending' | 'overdue' | 'completed' | 'in-progress'
}

interface MaintenanceTaskModalProps {
  visible: boolean
  task?: MaintenanceTask
  onCancel: () => void
  onSubmit: (values: MaintenanceTask) => Promise<void>
}

const MaintenanceTaskModal: React.FC<MaintenanceTaskModalProps> = ({
  visible,
  task,
  onCancel,
  onSubmit,
}) => {
  const [form] = Form.useForm()
  const [loading, setLoading] = React.useState(false)

  useEffect(() => {
    if (visible && task) {
      form.setFieldsValue({
        ...task,
        dueDate: dayjs(task.dueDate),
      })
    } else if (visible) {
      form.resetFields()
    }
  }, [visible, task, form])

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const formattedValues = {
        ...values,
        dueDate: values.dueDate.format('YYYY-MM-DD'),
      }
      setLoading(true)
      await onSubmit(formattedValues)
      message.success(task ? 'Task updated successfully' : 'Task created successfully')
      form.resetFields()
      onCancel()
    } catch (error: any) {
      if (error.errorFields) {
        message.error('Please fill in all required fields')
      } else {
        message.error('Failed to save task')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <BaseModal
      title={task ? 'Edit Maintenance Task' : 'Create New Maintenance Task'}
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
          {task ? 'Update' : 'Create'}
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
          name="machine"
          label="Machine"
          rules={[{ required: true, message: 'Please enter machine name' }]}
        >
          <Input placeholder="Enter machine name" />
        </Form.Item>

        <Form.Item
          name="task"
          label="Task Description"
          rules={[{ required: true, message: 'Please enter task description' }]}
        >
          <Input.TextArea 
            placeholder="Enter task description" 
            rows={3}
          />
        </Form.Item>

        <Form.Item
          name="dueDate"
          label="Due Date"
          rules={[{ required: true, message: 'Please select due date' }]}
        >
          <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
        </Form.Item>

        <Form.Item
          name="priority"
          label="Priority"
          rules={[{ required: true, message: 'Please select priority' }]}
          initialValue="medium"
        >
          <Select>
            <Select.Option value="low">Low</Select.Option>
            <Select.Option value="medium">Medium</Select.Option>
            <Select.Option value="high">High</Select.Option>
            <Select.Option value="critical">Critical</Select.Option>
          </Select>
        </Form.Item>

        <Form.Item
          name="assignedTo"
          label="Assigned To"
          rules={[{ required: true, message: 'Please enter assignee' }]}
        >
          <Input placeholder="Enter assignee name" />
        </Form.Item>

        <Form.Item
          name="site"
          label="Site"
          rules={[{ required: true, message: 'Please select a site' }]}
        >
          <Select placeholder="Select a site">
            <Select.Option value="Main Plant">Main Plant</Select.Option>
            <Select.Option value="Warehouse">Warehouse</Select.Option>
            <Select.Option value="Assembly Line">Assembly Line</Select.Option>
          </Select>
        </Form.Item>
      </Form>
    </BaseModal>
  )
}

export default MaintenanceTaskModal
