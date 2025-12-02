import React, { useEffect, useState } from 'react'
import { Modal, Checkbox, Button, message, Space, List, Typography, Input, Select, DatePicker, Divider, Alert, Spin } from 'antd'
import { CheckOutlined, WarningOutlined, ClockCircleOutlined } from '@ant-design/icons'
import apiClient from '../../utils/api'
import dayjs from 'dayjs'

const { Text, Title } = Typography
const { TextArea } = Input
const { Option } = Select
const HISTORY_PAGE_SIZE = 5
const MAX_HISTORY_LIMIT = 50

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

interface MaintenanceHistoryEntry {
  id: number
  date: string | null
  performed_by: string
  maintenance_type: string
  description: string
  notes: string
  status: string
}

interface HistoryState {
  entries: MaintenanceHistoryEntry[]
  total: number
  limit: number
  partName: string
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
  const [poNumber, setPoNumber] = useState('')
  const [workOrderNumber, setWorkOrderNumber] = useState('')
  const [historyCache, setHistoryCache] = useState<Record<number, HistoryState>>({})
  const [activePartId, setActivePartId] = useState<number | null>(null)
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyError, setHistoryError] = useState('')

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
      setHistoryCache({})
      setActivePartId(null)
      setHistoryError('')
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

    const trimmedPo = poNumber.trim()
    const trimmedWorkOrder = workOrderNumber.trim()

    if (!trimmedPo || !trimmedWorkOrder) {
      message.error('PO Number and Work Order Number are required.')
      return
    }

    if (trimmedPo.length > 32) {
      message.error('PO Number must be 32 characters or fewer.')
      return
    }

    if (trimmedWorkOrder.length > 128) {
      message.error('Work Order Number must be 128 characters or fewer.')
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
        po_number: trimmedPo,
        work_order_number: trimmedWorkOrder,
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
    setPoNumber('')
    setWorkOrderNumber('')
    setHistoryCache({})
    setActivePartId(null)
    setHistoryError('')
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

  const handleViewHistory = (part: Part) => {
    setActivePartId(part.id)
    setHistoryError('')
    if (historyCache[part.id]) {
      return
    }
    fetchPartHistory(part, HISTORY_PAGE_SIZE)
  }

  const fetchPartHistory = async (part: Part, limit: number) => {
    try {
      setHistoryLoading(true)
      const response = await apiClient.get(`/api/v1/maintenance/part/${part.id}`, {
        params: { history_limit: limit }
      })
      const detail = response.data.data
      setHistoryCache((prev) => ({
        ...prev,
        [part.id]: {
          entries: detail.history || [],
          total: detail.history_total || 0,
          limit,
          partName: detail.part_name || part.name,
        }
      }))
    } catch (error: any) {
      console.error('Failed to load maintenance history:', error)
      setHistoryError('Failed to load maintenance history. Please try again.')
      message.error('Failed to load maintenance history')
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleLoadMoreHistory = () => {
    if (!activePartId) return
    const part = parts.find((p) => p.id === activePartId)
    if (!part) return
    const cacheEntry = historyCache[activePartId]
    const currentLimit = cacheEntry?.limit || HISTORY_PAGE_SIZE
    const nextLimit = Math.min(currentLimit + HISTORY_PAGE_SIZE, MAX_HISTORY_LIMIT)
    if (nextLimit === currentLimit) return
    if (cacheEntry && cacheEntry.total <= cacheEntry.entries.length) return
    fetchPartHistory(part, nextLimit)
  }

  const overdueParts = parts.filter((p) => p.status === 'overdue')
  const dueSoonParts = parts.filter((p) => p.status === 'due-soon')
  const upToDateParts = parts.filter((p) => p.status === 'up-to-date')
  const activeHistory = activePartId ? historyCache[activePartId] : null

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
                <div>
                  <Text strong>PO Number:</Text>
                  <Input
                    value={poNumber}
                    onChange={(e) => setPoNumber(e.target.value)}
                    placeholder="Enter the related PO"
                    maxLength={32}
                    style={{ marginTop: 4 }}
                  />
                </div>
                <div>
                  <Text strong>Work Order Number:</Text>
                  <Input
                    value={workOrderNumber}
                    onChange={(e) => setWorkOrderNumber(e.target.value)}
                    placeholder="Enter the work order reference"
                    maxLength={128}
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
                            <div>
                              <Button
                                type="link"
                                size="small"
                                onClick={(e) => {
                                  e.preventDefault()
                                  e.stopPropagation()
                                  handleViewHistory(part)
                                }}
                              >
                                View history
                              </Button>
                            </div>
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
                            <div>
                              <Button
                                type="link"
                                size="small"
                                onClick={(e) => {
                                  e.preventDefault()
                                  e.stopPropagation()
                                  handleViewHistory(part)
                                }}
                              >
                                View history
                              </Button>
                            </div>
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
                            <div>
                              <Button
                                type="link"
                                size="small"
                                onClick={(e) => {
                                  e.preventDefault()
                                  e.stopPropagation()
                                  handleViewHistory(part)
                                }}
                              >
                                View history
                              </Button>
                            </div>
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

            <Divider />
            <div>
              <Title level={5}>Recent Maintenance History</Title>
              {activePartId && activeHistory && (
                <Text type="secondary">Showing latest entries for {activeHistory.partName}</Text>
              )}
            </div>
            {historyError && <Alert type="error" message={historyError} showIcon />}
            {historyLoading ? (
              <div style={{ textAlign: 'center', padding: '12px 0' }}>
                <Spin size="small" />
              </div>
            ) : activePartId && activeHistory ? (
              activeHistory.entries.length > 0 ? (
                <>
                  <List
                    size="small"
                    bordered
                    dataSource={activeHistory.entries}
                    renderItem={(entry) => (
                      <List.Item>
                        <Space direction="vertical" style={{ width: '100%' }}>
                          <Space wrap>
                            <Text strong>
                              {entry.date ? dayjs(entry.date).format('MMMM D, YYYY') : 'Date not recorded'}
                            </Text>
                            {entry.maintenance_type && (
                              <Text type="secondary">{entry.maintenance_type}</Text>
                            )}
                          </Space>
                          {entry.performed_by && (
                            <Text type="secondary">Performed by {entry.performed_by}</Text>
                          )}
                          {entry.description && <Text>{entry.description}</Text>}
                          {entry.notes && (
                            <Text type="secondary" style={{ whiteSpace: 'pre-wrap' }}>{entry.notes}</Text>
                          )}
                        </Space>
                      </List.Item>
                    )}
                  />
                  <div style={{ textAlign: 'center', marginTop: 8 }}>
                    <Text type="secondary">
                      Showing {activeHistory.entries.length} of {activeHistory.total} entries
                    </Text>
                  </div>
                  {activeHistory.total > activeHistory.entries.length && (
                    <div style={{ textAlign: 'center', marginTop: 8 }}>
                      <Button size="small" onClick={handleLoadMoreHistory}>
                        Load more history
                      </Button>
                    </div>
                  )}
                </>
              ) : (
                <Text type="secondary">No maintenance history recorded for this part yet.</Text>
              )
            ) : (
              <Text type="secondary">Select "View history" on a part above to see recent maintenance entries.</Text>
            )}
          </>
        )}
      </Space>
    </Modal>
  )
}

export default MaintenanceCompletionModal
