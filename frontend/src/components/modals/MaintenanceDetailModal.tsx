import React, { useEffect, useState } from 'react'
import { Modal, Spin, Descriptions, Typography, Tag, Alert, Divider, Space } from 'antd'
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

  useEffect(() => {
    if (open && recordId) {
      fetchDetail()
    } else {
      setDetail(null)
      setError('')
    }
  }, [open, recordId])

  const fetchDetail = async () => {
    if (!recordId) return

    try {
      setLoading(true)
      setError('')
      const response = await apiClient.get(`/api/v1/maintenance/part/${recordId}`)
      setDetail(response.data.data)
    } catch (error: any) {
      console.error('Failed to load maintenance detail:', error)
      setError('Failed to load maintenance details. Please try again.')
    } finally {
      setLoading(false)
    }
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
