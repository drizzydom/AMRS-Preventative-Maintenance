import React from 'react'
import { Card, Typography, Space, Tag, Row, Col, Divider, Progress } from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ToolOutlined,
} from '@ant-design/icons'
import '../../styles/reports.css'

const { Title, Text } = Typography

interface MaintenanceRecord {
  id: number
  date: string
  machine: string
  task: string
  technician: string
  duration: string
  status: 'completed' | 'pending' | 'overdue'
  notes: string
}

interface ReportProps {
  startDate: string
  endDate: string
  site?: string
  data: MaintenanceRecord[]
}

/**
 * Option B: Card-Based Layout with Visual Indicators
 * Modern, visual approach with cards and icons
 * Best for: Executive summaries, visual presentations
 */
const MaintenanceReportOptionB: React.FC<ReportProps> = ({ 
  startDate, 
  endDate, 
  site = 'All Sites',
  data 
}) => {
  const completedCount = data.filter(r => r.status === 'completed').length
  const pendingCount = data.filter(r => r.status === 'pending').length
  const overdueCount = data.filter(r => r.status === 'overdue').length
  const completionRate = data.length > 0 ? (completedCount / data.length) * 100 : 0

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 20 }} />
      case 'pending':
        return <ClockCircleOutlined style={{ color: '#1890ff', fontSize: 20 }} />
      case 'overdue':
        return <WarningOutlined style={{ color: '#ff4d4f', fontSize: 20 }} />
      default:
        return <ToolOutlined style={{ fontSize: 20 }} />
    }
  }

  return (
    <div className="report-container option-b">
      {/* Header */}
      <Card className="report-header-card">
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2} style={{ margin: 0 }}>
              <ToolOutlined /> Maintenance Report
            </Title>
            <Text type="secondary">AMRS Maintenance Tracker</Text>
          </Col>
          <Col>
            <Space direction="vertical" size="small" align="end">
              <Text strong>{startDate} to {endDate}</Text>
              <Text type="secondary">{site}</Text>
              <Text type="secondary">{new Date().toLocaleDateString()}</Text>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Summary Dashboard */}
      <Card className="summary-dashboard" style={{ marginTop: 16 }}>
        <Title level={4}>Performance Overview</Title>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} md={6}>
            <Card className="metric-card">
              <div className="metric-content">
                <div className="metric-value">{data.length}</div>
                <div className="metric-label">Total Tasks</div>
                <ToolOutlined className="metric-icon" />
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card className="metric-card success">
              <div className="metric-content">
                <div className="metric-value">{completedCount}</div>
                <div className="metric-label">Completed</div>
                <CheckCircleOutlined className="metric-icon" />
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card className="metric-card warning">
              <div className="metric-content">
                <div className="metric-value">{pendingCount}</div>
                <div className="metric-label">Pending</div>
                <ClockCircleOutlined className="metric-icon" />
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} md={6}>
            <Card className="metric-card danger">
              <div className="metric-content">
                <div className="metric-value">{overdueCount}</div>
                <div className="metric-label">Overdue</div>
                <WarningOutlined className="metric-icon" />
              </div>
            </Card>
          </Col>
        </Row>

        <Divider />

        <div className="completion-progress">
          <Text strong>Completion Rate</Text>
          <Progress 
            percent={Math.round(completionRate)} 
            status={completionRate >= 80 ? 'success' : completionRate >= 50 ? 'normal' : 'exception'}
            strokeWidth={12}
          />
        </div>
      </Card>

      {/* Maintenance Records */}
      <div style={{ marginTop: 16 }}>
        <Title level={4}>Maintenance Records</Title>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {data.map((record) => (
            <Card key={record.id} className="maintenance-record-card" size="small">
              <Row gutter={16} align="middle">
                <Col flex="50px">
                  {getStatusIcon(record.status)}
                </Col>
                <Col flex="auto">
                  <div className="record-details">
                    <div className="record-header">
                      <Text strong style={{ fontSize: 16 }}>{record.machine}</Text>
                      <Tag color={
                        record.status === 'completed' ? 'green' :
                        record.status === 'pending' ? 'blue' : 'red'
                      }>
                        {record.status.toUpperCase()}
                      </Tag>
                    </div>
                    <div className="record-info">
                      <Text>{record.task}</Text>
                    </div>
                    <Space size="large" className="record-meta">
                      <Text type="secondary">📅 {record.date}</Text>
                      <Text type="secondary">👤 {record.technician}</Text>
                      <Text type="secondary">⏱️ {record.duration}</Text>
                    </Space>
                  </div>
                </Col>
              </Row>
            </Card>
          ))}
        </Space>
      </div>

      {/* Footer */}
      <Card style={{ marginTop: 16 }} className="report-footer-card">
        <Text type="secondary" style={{ fontSize: 12 }}>
          Report generated by AMRS Maintenance Tracker on {new Date().toLocaleString()}
          <br />
          Contains {data.length} maintenance records for the period {startDate} to {endDate}
        </Text>
      </Card>
    </div>
  )
}

export default MaintenanceReportOptionB
