import React from 'react'
import { Card, Typography, Space, Tag, Timeline, Row, Col, Statistic, Divider } from 'antd'
import {
  CheckCircleOutlined,
  ClockCircleOutlined,
  WarningOutlined,
  ToolOutlined,
  CalendarOutlined,
} from '@ant-design/icons'
import '../../styles/reports.css'

const { Title, Text, Paragraph } = Typography

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
 * Option C: Timeline-Based Layout
 * Chronological view showing maintenance history
 * Best for: Historical tracking, compliance audits
 */
const MaintenanceReportOptionC: React.FC<ReportProps> = ({ 
  startDate, 
  endDate, 
  site = 'All Sites',
  data 
}) => {
  const completedCount = data.filter(r => r.status === 'completed').length
  const pendingCount = data.filter(r => r.status === 'pending').length
  const overdueCount = data.filter(r => r.status === 'overdue').length

  // Sort data by date
  const sortedData = [...data].sort((a, b) => 
    new Date(b.date).getTime() - new Date(a.date).getTime()
  )

  // Group by date
  const groupedByDate = sortedData.reduce((acc, record) => {
    if (!acc[record.date]) {
      acc[record.date] = []
    }
    acc[record.date].push(record)
    return acc
  }, {} as Record<string, MaintenanceRecord[]>)

  const getTimelineDot = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ fontSize: 16, color: '#52c41a' }} />
      case 'pending':
        return <ClockCircleOutlined style={{ fontSize: 16, color: '#1890ff' }} />
      case 'overdue':
        return <WarningOutlined style={{ fontSize: 16, color: '#ff4d4f' }} />
      default:
        return <ToolOutlined style={{ fontSize: 16 }} />
    }
  }

  const getTimelineColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'green'
      case 'pending':
        return 'blue'
      case 'overdue':
        return 'red'
      default:
        return 'gray'
    }
  }

  return (
    <div className="report-container option-c">
      {/* Header */}
      <Card className="report-header-timeline">
        <Row gutter={16}>
          <Col span={16}>
            <Space direction="vertical" size="small">
              <Title level={2} style={{ margin: 0 }}>
                <CalendarOutlined /> Maintenance History Report
              </Title>
              <Text type="secondary">AMRS Maintenance Tracker - Timeline View</Text>
              <Space>
                <Tag icon={<CalendarOutlined />}>{startDate} to {endDate}</Tag>
                <Tag>{site}</Tag>
              </Space>
            </Space>
          </Col>
          <Col span={8}>
            <div className="report-metadata">
              <Text type="secondary">Generated: {new Date().toLocaleDateString()}</Text>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Summary Statistics */}
      <Card style={{ marginTop: 16 }} className="statistics-panel">
        <Row gutter={16}>
          <Col xs={24} md={6}>
            <Statistic 
              title="Total Activities" 
              value={data.length} 
              prefix={<ToolOutlined />}
            />
          </Col>
          <Col xs={24} md={6}>
            <Statistic 
              title="Completed" 
              value={completedCount} 
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Col>
          <Col xs={24} md={6}>
            <Statistic 
              title="Pending" 
              value={pendingCount} 
              valueStyle={{ color: '#1890ff' }}
              prefix={<ClockCircleOutlined />}
            />
          </Col>
          <Col xs={24} md={6}>
            <Statistic 
              title="Overdue" 
              value={overdueCount} 
              valueStyle={{ color: '#ff4d4f' }}
              prefix={<WarningOutlined />}
            />
          </Col>
        </Row>
      </Card>

      {/* Timeline */}
      <Card style={{ marginTop: 16 }} className="timeline-container">
        <Title level={4}>Maintenance Timeline</Title>
        <Timeline mode="left">
          {Object.entries(groupedByDate).map(([date, records]) => (
            <Timeline.Item 
              key={date}
              label={<Text strong>{date}</Text>}
              dot={<CalendarOutlined style={{ fontSize: 16 }} />}
            >
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {records.map((record) => (
                  <Card 
                    key={record.id} 
                    size="small" 
                    className="timeline-record-card"
                    bordered={false}
                    style={{ 
                      borderLeft: `4px solid ${
                        record.status === 'completed' ? '#52c41a' :
                        record.status === 'pending' ? '#1890ff' : '#ff4d4f'
                      }`,
                      paddingLeft: 12,
                    }}
                  >
                    <Row gutter={16} align="middle">
                      <Col flex="40px">
                        {getTimelineDot(record.status)}
                      </Col>
                      <Col flex="auto">
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                          <div>
                            <Text strong style={{ fontSize: 15 }}>{record.machine}</Text>
                            {' '}
                            <Tag color={getTimelineColor(record.status)} style={{ marginLeft: 8 }}>
                              {record.status}
                            </Tag>
                          </div>
                          <Text>{record.task}</Text>
                          <Space size="middle">
                            <Text type="secondary">
                              <span style={{ marginRight: 4 }}>👤</span>
                              {record.technician}
                            </Text>
                            <Text type="secondary">
                              <span style={{ marginRight: 4 }}>⏱️</span>
                              {record.duration}
                            </Text>
                          </Space>
                          {record.notes && (
                            <Paragraph 
                              type="secondary" 
                              style={{ 
                                marginTop: 8, 
                                marginBottom: 0,
                                fontSize: 13,
                                fontStyle: 'italic',
                              }}
                            >
                              Note: {record.notes}
                            </Paragraph>
                          )}
                        </Space>
                      </Col>
                    </Row>
                  </Card>
                ))}
              </Space>
            </Timeline.Item>
          ))}
        </Timeline>
      </Card>

      {/* Footer */}
      <Card style={{ marginTop: 16 }} className="report-footer">
        <Divider />
        <Space direction="vertical" size="small">
          <Text type="secondary">
            This timeline report contains {data.length} maintenance activities performed between {startDate} and {endDate}.
          </Text>
          <Text type="secondary">
            Generated by AMRS Maintenance Tracker on {new Date().toLocaleString()}
          </Text>
        </Space>
      </Card>
    </div>
  )
}

export default MaintenanceReportOptionC
