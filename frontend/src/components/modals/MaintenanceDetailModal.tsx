import React, { useEffect, useState } from 'react'
import { Modal, Spin, Descriptions, Typography, Tag, Alert, Divider, Space, List, Button } from 'antd'
import { 
  ClockCircleOutlined, 
  ToolOutlined, 
  UserOutlined, 
  EnvironmentOutlined,
  FileTextOutlined,
  CheckCircleOutlined
} from '@ant-design/icons'
import apiClient from '../../utils/api'
import dayjs from 'dayjs'

const { Title, Text } = Typography

const HISTORY_PAGE_SIZE = 10
const MAX_HISTORY_LIMIT = 100

interface MaintenanceHistoryEntry {
  id: number
  date: string | null
  performed_by: string
  maintenance_type: string
  description: string
  notes: string
  status: string
}

interface MaintenanceDetail {
  id: number
  part_name: string
  machine: string
  machine_id: number | null
  site: string
  site_id: number | null
  description: string
  status: string
  days_info: number | null
  next_maintenance: string | null
  last_maintenance: string | null
  maintenance_frequency: number | null
  maintenance_unit: string
  frequency: string
  materials: string
  quantity: string
  notes: string
  lastCompletedDate: string
  lastCompletedBy: string
  lastMaintenanceType: string
  comments: string
  history: MaintenanceHistoryEntry[]
  history_limit: number
  history_total: number
}

interface MaintenanceDetailModalProps {
  open: boolean
  onClose: () => void
  recordId: number | null
}

const MaintenanceDetailModal: React.FC<MaintenanceDetailModalProps> = ({
  open,
  onClose,
  recordId,
}) => {
  const [loading, setLoading] = useState(false)
  const [detail, setDetail] = useState<MaintenanceDetail | null>(null)
  const [error, setError] = useState<string>('')
  const [historyLimit, setHistoryLimit] = useState(HISTORY_PAGE_SIZE)
  const [historyLoading, setHistoryLoading] = useState(false)

  useEffect(() => {
    if (open && recordId) {
      setHistoryLimit(HISTORY_PAGE_SIZE)
      fetchDetail(HISTORY_PAGE_SIZE)
    } else {
      setDetail(null)
      setError('')
    }
  }, [open, recordId])

  const fetchDetail = async (limit = historyLimit, options?: { suppressGlobalLoading?: boolean }) => {
    if (!recordId) return

    try {
      if (options?.suppressGlobalLoading) {
        setHistoryLoading(true)
      } else {
        setLoading(true)
      }
      setError('')
      const response = await apiClient.get(`/api/v1/maintenance/part/${recordId}`, {
        params: { history_limit: limit }
      })
      setDetail(response.data.data)
      setHistoryLimit(limit)
    } catch (error: any) {
      console.error('Failed to load maintenance detail:', error)
      setError('Failed to load maintenance details. Please try again.')
    } finally {
      if (options?.suppressGlobalLoading) {
        setHistoryLoading(false)
      } else {
        setLoading(false)
      }
    }
  }

  const handleLoadMoreHistory = () => {
    if (!detail) return
    const nextLimit = Math.min(historyLimit + HISTORY_PAGE_SIZE, MAX_HISTORY_LIMIT)
    if (nextLimit === historyLimit) return
    fetchDetail(nextLimit, { suppressGlobalLoading: true })
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'pending': return 'warning'
      case 'overdue': return 'error'
      default: return 'default'
    }
  }

  return (
    <Modal
      title={
        <Space>
          <ToolOutlined />
          <span>Maintenance Record Details</span>
        </Space>
      }
      open={open}
      onCancel={onClose}
      footer={null}
      width={700}
    >
      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <Spin size="large" tip="Loading maintenance details..." />
        </div>
      ) : error ? (
        <Alert message="Error" description={error} type="error" showIcon />
      ) : detail ? (
        <>
          <Descriptions bordered column={1} size="small">
            <Descriptions.Item 
              label={<><EnvironmentOutlined /> Site</>}
            >
              <Text strong>{detail.site}</Text>
            </Descriptions.Item>

            <Descriptions.Item 
              label={<><ToolOutlined /> Machine</>}
            >
              <Text strong>{detail.machine}</Text>
            </Descriptions.Item>

            <Descriptions.Item 
              label={<><ToolOutlined /> Part/Component</>}
            >
              <Text>{detail.part_name}</Text>
            </Descriptions.Item>

            <Descriptions.Item 
              label={<><CheckCircleOutlined /> Status</>}
            >
              <Tag color={getStatusColor(detail.status)}>
                {detail.status.replace('_', ' ').toUpperCase()}
                {detail.days_info !== null && ` (${detail.days_info} days)`}
              </Tag>
            </Descriptions.Item>

            {detail.next_maintenance && (
              <Descriptions.Item 
                label={<><ClockCircleOutlined /> Next Maintenance Due</>}
              >
                <Text>{dayjs(detail.next_maintenance).format('MMMM D, YYYY')}</Text>
              </Descriptions.Item>
            )}

            {detail.last_maintenance && (
              <Descriptions.Item 
                label="Last Maintenance Performed"
              >
                <Text>{dayjs(detail.last_maintenance).format('MMMM D, YYYY')}</Text>
              </Descriptions.Item>
            )}

            {detail.lastCompletedDate && (
              <Descriptions.Item 
                label={<><UserOutlined /> Last Completed By</>}
              >
                <Text>{detail.lastCompletedBy || 'Not recorded'} on {dayjs(detail.lastCompletedDate).format('MMMM D, YYYY')}</Text>
              </Descriptions.Item>
            )}

            {detail.lastMaintenanceType && (
              <Descriptions.Item 
                label="Last Maintenance Type"
              >
                <Tag color="blue">{detail.lastMaintenanceType}</Tag>
              </Descriptions.Item>
            )}
          </Descriptions>

          {(detail.materials || detail.quantity || detail.frequency) && (
            <>
              <Divider orientation="left">Materials & Specifications</Divider>
              <Descriptions bordered column={1} size="small">
                {detail.materials && (
                  <Descriptions.Item label="Materials Used">
                    <Text>{detail.materials}</Text>
                  </Descriptions.Item>
                )}

                {detail.quantity && (
                  <Descriptions.Item label="Quantity">
                    <Text>{detail.quantity}</Text>
                  </Descriptions.Item>
                )}

                {detail.frequency && (
                  <Descriptions.Item label="Maintenance Frequency">
                    <Text>{detail.frequency}</Text>
                  </Descriptions.Item>
                )}
              </Descriptions>
            </>
          )}

          <Divider orientation="left">Maintenance History</Divider>
          {detail.history && detail.history.length > 0 ? (
            <>
              <List
                size="small"
                bordered
                dataSource={detail.history}
                renderItem={(entry) => (
                  <List.Item>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <Space wrap>
                        <Text strong>
                          {entry.date ? dayjs(entry.date).format('MMMM D, YYYY') : 'Date not recorded'}
                        </Text>
                        {entry.status && (
                          <Tag color={getStatusColor(entry.status)}>
                            {entry.status.replace('_', ' ').toUpperCase()}
                          </Tag>
                        )}
                        {entry.maintenance_type && (
                          <Tag color="blue">{entry.maintenance_type}</Tag>
                        )}
                      </Space>
                      {entry.performed_by && (
                        <Text type="secondary">Performed by {entry.performed_by}</Text>
                      )}
                      {entry.description && (
                        <Text>{entry.description}</Text>
                      )}
                      {entry.notes && (
                        <Text type="secondary" style={{ whiteSpace: 'pre-wrap' }}>{entry.notes}</Text>
                      )}
                    </Space>
                  </List.Item>
                )}
              />
              <div style={{ textAlign: 'center', marginTop: 12 }}>
                <Text type="secondary">
                  Showing {detail.history.length} of {detail.history_total} entries
                </Text>
              </div>
              {detail.history_total > detail.history.length && (
                <div style={{ textAlign: 'center', marginTop: 8 }}>
                  <Button onClick={handleLoadMoreHistory} loading={historyLoading}>
                    Load more history
                  </Button>
                </div>
              )}
            </>
          ) : (
            <Text type="secondary">No historical maintenance records available.</Text>
          )}

          {(detail.description || detail.comments || detail.notes) && (
            <>
              <Divider orientation="left">Additional Information</Divider>
              <Descriptions bordered column={1} size="small">
                {detail.description && (
                  <Descriptions.Item 
                    label={<><FileTextOutlined /> Description</>}
                  >
                    <Text style={{ whiteSpace: 'pre-wrap' }}>{detail.description}</Text>
                  </Descriptions.Item>
                )}

                {detail.comments && (
                  <Descriptions.Item 
                    label={<><FileTextOutlined /> Comments</>}
                  >
                    <Text style={{ whiteSpace: 'pre-wrap' }}>{detail.comments}</Text>
                  </Descriptions.Item>
                )}

                {detail.notes && !detail.materials && (
                  <Descriptions.Item 
                    label={<><FileTextOutlined /> Notes</>}
                  >
                    <Text style={{ whiteSpace: 'pre-wrap' }}>{detail.notes}</Text>
                  </Descriptions.Item>
                )}
              </Descriptions>
            </>
          )}
        </>
      ) : null}
    </Modal>
  )
}

export default MaintenanceDetailModal
