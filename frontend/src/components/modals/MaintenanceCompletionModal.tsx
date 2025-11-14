import React, { useEffect, useState } from 'react'
import { Modal, Checkbox, Button, message, Space, List, Typography, Input, Select, DatePicker, Divider, Alert } from 'antd'
import { CheckOutlined, WarningOutlined, ClockCircleOutlined } from '@ant-design/icons'
import apiClient from '../../utils/api'
import dayjs from 'dayjs'

const { Text, Title } = Typography
const { TextArea } = Input
const { Option } = Select

interface Part {
  id: number
  name: string
  description: string
  last_maintenance: string | null
  next_maintenance: string | null
  maintenance_frequency: number | null
  maintenance_unit: string
  status: 'overdue' | 'due-soon' | 'up-to-date'
  days_info: number | null
}

interface MaintenanceCompletionModalProps {
  open: boolean
  onClose: () => void
  machineId: number | null
  machineName: string
  onComplete: () => void
}

const MaintenanceCompletionModal: React.FC<MaintenanceCompletionModalProps> = ({
  open,
  onClose,
  machineId,
  machineName,
  onComplete,
}) => {
  const [parts, setParts] = useState<Part[]>([])
  const [selectedParts, setSelectedParts] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [maintenanceType, setMaintenanceType] = useState('Routine')
  const [maintenanceDate, setMaintenanceDate] = useState(dayjs())
  const [description, setDescription] = useState('')
  const [notes, setNotes] = useState('')

  useEffect(() => {
    if (open && machineId) {
      fetchParts()
    }
  }, [open, machineId])

  const fetchParts = async () => {
    if (!machineId) return

    try {
      setLoading(true)
      const response = await apiClient.get(`/api/v1/machines/${machineId}/parts`)
      const partsData = response.data.data

      setParts(partsData)

      // Pre-select overdue and due-soon parts
      const needsMaintenanceIds = partsData
        .filter((p: Part) => p.status === 'overdue' || p.status === 'due-soon')
        .map((p: Part) => p.id)
      setSelectedParts(needsMaintenanceIds)
    } catch (error: any) {
      console.error('Failed to load parts:', error)
      message.error('Failed to load parts for machine')
    } finally {
      setLoading(false)
    }
  }

  const handlePartToggle = (partId: number) => {
    setSelectedParts((prev) =>
      prev.includes(partId)
        ? prev.filter((id) => id !== partId)
        : [...prev, partId]
    )
  }

  const handleSubmit = async () => {
    if (!machineId) {
      message.error('No machine selected. Please select a machine first.')
      return
    }

    if (selectedParts.length === 0) {
      message.warning('Please select at least one part to complete maintenance')
      return
    }

    try {
      setSubmitting(true)

      await apiClient.post(`/api/v1/maintenance/complete-multiple`, {
        machine_id: machineId,
        part_ids: selectedParts,
        date: maintenanceDate.format('YYYY-MM-DD'),
        type: maintenanceType,
        description: description || `Maintenance completed for ${selectedParts.length} part(s)`,
        notes: notes,
      })

      message.success(`Successfully completed maintenance for ${selectedParts.length} part(s)`)
      onComplete()
      handleCancel()
    } catch (error: any) {
      console.error('Failed to complete maintenance:', error)
      const errorMsg = error.response?.data?.error || 'Failed to complete maintenance'
      message.error(errorMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = () => {
    setSelectedParts([])
    setMaintenanceType('Routine')
    setMaintenanceDate(dayjs())
    setDescription('')
    setNotes('')
    onClose()
  }

  const getStatusIcon = (status: string) => {
    if (status === 'overdue') return <WarningOutlined style={{ color: '#ff4d4f' }} />
    if (status === 'due-soon') return <ClockCircleOutlined style={{ color: '#faad14' }} />
    return <CheckOutlined style={{ color: '#52c41a' }} />
  }

  const getStatusText = (part: Part) => {
    if (part.status === 'overdue') {
      return <Text type="danger" strong>{part.days_info} days overdue</Text>
    }
    if (part.status === 'due-soon') {
      return <Text type="warning">Due in {part.days_info} days</Text>
    }
    return <Text type="success">Up to date</Text>
  }

  const overdueParts = parts.filter((p) => p.status === 'overdue')
  const dueSoonParts = parts.filter((p) => p.status === 'due-soon')
  const upToDateParts = parts.filter((p) => p.status === 'up-to-date')

  return (
    <Modal
      title={`Complete Maintenance: ${machineName}`}
      open={open}
      onCancel={handleCancel}
      width={700}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          Cancel
        </Button>,
        <Button
          key="submit"
          type="primary"
          icon={<CheckOutlined />}
          onClick={handleSubmit}
          loading={submitting}
          disabled={loading || selectedParts.length === 0}
        >
          Complete Maintenance
        </Button>,
      ]}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {!machineId ? (
          <Alert 
            message="No Machine Selected" 
            description="Please select a machine from the maintenance page to complete maintenance." 
            type="info" 
            showIcon 
          />
        ) : loading ? (
          <Text>Loading parts...</Text>
        ) : (
          <>
            {/* Maintenance Details */}
            <div>
              <Title level={5}>Maintenance Details</Title>
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
                  <Text strong>Type:</Text>
                  <Select
                    value={maintenanceType}
                    onChange={setMaintenanceType}
                    style={{ width: '100%', marginTop: 4 }}
                  >
                    <Option value="Routine">Routine</Option>
                    <Option value="Preventive">Preventive</Option>
                    <Option value="Corrective">Corrective</Option>
                    <Option value="Emergency">Emergency</Option>
                    <Option value="Inspection">Inspection</Option>
                  </Select>
                </div>
                <div>
                  <Text strong>Date:</Text>
                  <DatePicker
                    value={maintenanceDate}
                    onChange={(date) => date && setMaintenanceDate(date)}
                    style={{ width: '100%', marginTop: 4 }}
                    format="YYYY-MM-DD"
                  />
                </div>
                <div>
                  <Text strong>Description (optional):</Text>
                  <Input
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of work performed"
                    style={{ marginTop: 4 }}
                  />
                </div>
                <div>
                  <Text strong>Notes (optional):</Text>
                  <TextArea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Additional notes or observations"
                    rows={2}
                    style={{ marginTop: 4 }}
                  />
                </div>
              </Space>
            </div>

            <Divider />

            {/* Parts Selection */}
            <div>
              <Title level={5}>Select Parts Completed</Title>
              <Text type="secondary">
                Check the parts you completed maintenance on.
              </Text>
            </div>

            {overdueParts.length > 0 && (
              <>
                <Text strong style={{ color: '#ff4d4f' }}>
                  ⚠️ Overdue Parts ({overdueParts.length}):
                </Text>
                <List
                  size="small"
                  dataSource={overdueParts}
                  renderItem={(part) => (
                    <List.Item>
                      <Checkbox
                        checked={selectedParts.includes(part.id)}
                        onChange={() => handlePartToggle(part.id)}
                      >
                        <Space>
                          {getStatusIcon(part.status)}
                          <div>
                            <Text strong>{part.name}</Text>
                            {part.description && (
                              <Text type="secondary"> - {part.description}</Text>
                            )}
                            <br />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              Last: {part.last_maintenance || 'Never'} | Next:{' '}
                              {part.next_maintenance || 'Not set'}
                            </Text>
                            <br />
                            {getStatusText(part)}
                          </div>
                        </Space>
                      </Checkbox>
                    </List.Item>
                  )}
                />
              </>
            )}

            {dueSoonParts.length > 0 && (
              <>
                <Text strong style={{ color: '#faad14' }}>
                  ⏰ Due Soon ({dueSoonParts.length}):
                </Text>
                <List
                  size="small"
                  dataSource={dueSoonParts}
                  renderItem={(part) => (
                    <List.Item>
                      <Checkbox
                        checked={selectedParts.includes(part.id)}
                        onChange={() => handlePartToggle(part.id)}
                      >
                        <Space>
                          {getStatusIcon(part.status)}
                          <div>
                            <Text strong>{part.name}</Text>
                            {part.description && (
                              <Text type="secondary"> - {part.description}</Text>
                            )}
                            <br />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              Last: {part.last_maintenance || 'Never'} | Next:{' '}
                              {part.next_maintenance || 'Not set'}
                            </Text>
                            <br />
                            {getStatusText(part)}
                          </div>
                        </Space>
                      </Checkbox>
                    </List.Item>
                  )}
                />
              </>
            )}

            {upToDateParts.length > 0 && (
              <>
                <Text strong style={{ color: '#52c41a' }}>
                  ✓ Up to Date ({upToDateParts.length}):
                </Text>
                <List
                  size="small"
                  dataSource={upToDateParts}
                  renderItem={(part) => (
                    <List.Item>
                      <Checkbox
                        checked={selectedParts.includes(part.id)}
                        onChange={() => handlePartToggle(part.id)}
                      >
                        <Space>
                          {getStatusIcon(part.status)}
                          <div>
                            <Text>{part.name}</Text>
                            {part.description && (
                              <Text type="secondary"> - {part.description}</Text>
                            )}
                            <br />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              Last: {part.last_maintenance || 'Never'} | Next:{' '}
                              {part.next_maintenance || 'Not set'}
                            </Text>
                          </div>
                        </Space>
                      </Checkbox>
                    </List.Item>
                  )}
                />
              </>
            )}

            {parts.length === 0 && !loading && (
              <Text type="secondary">No parts found for this machine.</Text>
            )}

            {selectedParts.length > 0 && (
              <Text strong>
                {selectedParts.length} part(s) selected for completion
              </Text>
            )}
          </>
        )}
      </Space>
    </Modal>
  )
}

export default MaintenanceCompletionModal
