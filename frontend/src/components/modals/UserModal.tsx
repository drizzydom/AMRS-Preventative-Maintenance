import React, { useEffect } from 'react'
import { Modal, Form, Input, Select } from 'antd'

interface Role {
  id: number
  name: string
}

interface User {
  id?: number
  username: string
  email: string
  full_name?: string
  role_id?: number
  password?: string
}

interface UserModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (values: any) => void
  user: User | null
  roles: Role[]
  loading?: boolean
}

const UserModal: React.FC<UserModalProps> = ({
  open,
  onClose,
  onSubmit,
  user,
  roles,
  loading = false,
}) => {
  const [form] = Form.useForm()

  useEffect(() => {
    if (open) {
      if (user) {
        // Edit mode - populate form with user data (no password field)
        form.setFieldsValue({
          username: user.username,
          email: user.email,
          full_name: user.full_name || '',
          role_id: user.role_id,
        })
      } else {
        // Create mode - reset form
        form.resetFields()
      }
    }
  }, [open, user, form])

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
      title={user ? 'Edit User' : 'Create New User'}
      open={open}
      onOk={handleSubmit}
      onCancel={onClose}
      confirmLoading={loading}
      width={600}
      okText={user ? 'Update' : 'Create'}
      cancelText="Cancel"
    >
      <Form
        form={form}
        layout="vertical"
        autoComplete="off"
      >
        <Form.Item
          name="username"
          label="Username"
          rules={[
            { required: true, message: 'Please enter username' },
            { min: 3, message: 'Username must be at least 3 characters' },
          ]}
        >
          <Input placeholder="Enter username" disabled={!!user} />
        </Form.Item>

        <Form.Item
          name="email"
          label="Email"
          rules={[
            { required: true, message: 'Please enter email' },
            { type: 'email', message: 'Please enter a valid email' },
          ]}
        >
          <Input placeholder="Enter email" type="email" />
        </Form.Item>

        <Form.Item
          name="full_name"
          label="Full Name"
        >
          <Input placeholder="Enter full name (optional)" />
        </Form.Item>

        {!user && (
          <Form.Item
            name="password"
            label="Password"
            rules={[
              { required: true, message: 'Please enter password' },
              { min: 8, message: 'Password must be at least 8 characters' },
            ]}
          >
            <Input.Password placeholder="Enter password (min 8 characters)" />
          </Form.Item>
        )}

        <Form.Item
          name="role_id"
          label="Role"
          rules={[{ required: true, message: 'Please select a role' }]}
        >
          <Select placeholder="Select a role">
            {roles.map(role => (
              <Select.Option key={role.id} value={role.id}>
                {role.name}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default UserModal
