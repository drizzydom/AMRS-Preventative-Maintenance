import React from 'react'
import { Card, Typography, Space, Tag, Row, Col, Progress, Divider } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  FileTextOutlined,
  SafetyOutlined,
} from '@ant-design/icons'
import '../../styles/reports.css'

const { Title, Text, Paragraph } = Typography

interface AuditItem {
  id: number
  category: string
  checkpoint: string
  status: 'pass' | 'fail' | 'na'
  notes: string
  auditor: string
}

interface AuditReportProps {
  auditName: string
  auditDate: string
  site: string
  auditor: string
  data: AuditItem[]
}

/**
 * Option B: Executive Summary Format
 * High-level overview focusing on key metrics
 * Best for: Management reviews, stakeholder presentations
 */
const AuditReportOptionB: React.FC<AuditReportProps> = ({ 
  auditName,
  auditDate,
  site,
  auditor,
  data 
}) => {
  const passCount = data.filter(item => item.status === 'pass').length
  const failCount = data.filter(item => item.status === 'fail').length
  const naCount = data.filter(item => item.status === 'na').length
  const applicableItems = data.length - naCount
  const passRate = applicableItems > 0 ? (passCount / applicableItems) * 100 : 0

  // Group by category
  const categoryStats = data.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = { pass: 0, fail: 0, na: 0, total: 0 }
    }
    acc[item.category][item.status]++
    acc[item.category].total++
    return acc
  }, {} as Record<string, { pass: number; fail: number; na: number; total: number }>)

  const getCategoryScore = (stats: { pass: number; fail: number; na: number; total: number }) => {
    const applicable = stats.total - stats.na
    return applicable > 0 ? (stats.pass / applicable) * 100 : 0
  }

  return (
    <div className="report-container option-b audit-report-executive">
      {/* Header */}
      <Card className="report-header-card audit-header">
        <Row justify="space-between" align="middle">
          <Col>
            <Space direction="vertical" size="small">
              <Title level={2} style={{ margin: 0, color: 'white' }}>
                <SafetyOutlined /> {auditName}
              </Title>
              <Text style={{ color: 'rgba(255, 255, 255, 0.85)' }}>
                Executive Audit Summary
              </Text>
            </Space>
          </Col>
          <Col>
            <Space direction="vertical" size="small" align="end" style={{ color: 'white' }}>
              <Text strong style={{ color: 'white' }}>{auditDate}</Text>
              <Text style={{ color: 'rgba(255, 255, 255, 0.85)' }}>{site}</Text>
              <Text style={{ color: 'rgba(255, 255, 255, 0.85)' }}>Auditor: {auditor}</Text>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Key Performance Indicator */}
      <Card className="kpi-card" style={{ marginTop: 16 }}>
        <Row align="middle" justify="center">
          <Col xs={24} md={8} style={{ textAlign: 'center' }}>
            <Progress
              type="circle"
              percent={Math.round(passRate)}
              width={180}
              strokeWidth={12}
              status={passRate >= 95 ? 'success' : passRate >= 80 ? 'normal' : 'exception'}
            />
            <Title level={3} style={{ marginTop: 16 }}>Overall Compliance</Title>
          </Col>
          <Col xs={24} md={16}>
            <Row gutter={[16, 16]}>
              <Col xs={12} md={6}>
                <Card className="metric-card-small success">
                  <div className="metric-value-large">{passCount}</div>
                  <div className="metric-label-large">Passed</div>
                  <CheckCircleOutlined className="metric-icon-large" />
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card className="metric-card-small danger">
                  <div className="metric-value-large">{failCount}</div>
                  <div className="metric-label-large">Failed</div>
                  <CloseCircleOutlined className="metric-icon-large" />
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card className="metric-card-small neutral">
                  <div className="metric-value-large">{naCount}</div>
                  <div className="metric-label-large">N/A</div>
                  <FileTextOutlined className="metric-icon-large" />
                </Card>
              </Col>
              <Col xs={12} md={6}>
                <Card className="metric-card-small info">
                  <div className="metric-value-large">{data.length}</div>
                  <div className="metric-label-large">Total</div>
                  <FileTextOutlined className="metric-icon-large" />
                </Card>
              </Col>
            </Row>
          </Col>
        </Row>
      </Card>

      {/* Category Breakdown */}
      <Card style={{ marginTop: 16 }}>
        <Title level={4}>Category Performance</Title>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {Object.entries(categoryStats).map(([category, stats]) => {
            const score = getCategoryScore(stats)
            return (
              <Card key={category} size="small" className="category-performance-card">
                <Row align="middle" gutter={16}>
                  <Col xs={24} md={8}>
                    <Text strong style={{ fontSize: 16 }}>{category}</Text>
                  </Col>
                  <Col xs={24} md={10}>
                    <Progress
                      percent={Math.round(score)}
                      status={score >= 95 ? 'success' : score >= 80 ? 'normal' : 'exception'}
                      strokeWidth={16}
                    />
                  </Col>
                  <Col xs={24} md={6}>
                    <Space>
                      <Tag color="green">{stats.pass} Pass</Tag>
                      <Tag color="red">{stats.fail} Fail</Tag>
                      <Tag>{stats.na} N/A</Tag>
                    </Space>
                  </Col>
                </Row>
              </Card>
            )
          })}
        </Space>
      </Card>

      {/* Critical Findings */}
      {failCount > 0 && (
        <Card style={{ marginTop: 16 }} className="critical-findings-card">
          <Title level={4} style={{ color: '#ff4d4f' }}>
            <CloseCircleOutlined /> Critical Findings ({failCount})
          </Title>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {data
              .filter(item => item.status === 'fail')
              .map((item, index) => (
                <Card 
                  key={item.id} 
                  size="small"
                  style={{ 
                    borderLeft: '4px solid #ff4d4f',
                    background: '#fff1f0',
                  }}
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <div>
                      <Tag color="red">Finding {index + 1}</Tag>
                      <Text strong> {item.category}</Text>
                    </div>
                    <Text>{item.checkpoint}</Text>
                    <Paragraph 
                      type="secondary" 
                      style={{ marginBottom: 0, fontStyle: 'italic' }}
                    >
                      {item.notes}
                    </Paragraph>
                  </Space>
                </Card>
              ))}
          </Space>
        </Card>
      )}

      {/* Recommendations */}
      {failCount > 0 && (
        <Card style={{ marginTop: 16 }} className="recommendations-card">
          <Title level={4}>Recommendations</Title>
          <ul style={{ paddingLeft: 20 }}>
            <li>
              <Text>Address all {failCount} critical findings within 30 days</Text>
            </li>
            <li>
              <Text>Conduct follow-up inspection after corrective actions</Text>
            </li>
            <li>
              <Text>Provide additional training for identified gaps</Text>
            </li>
            <li>
              <Text>Update procedures and documentation as needed</Text>
            </li>
          </ul>
        </Card>
      )}

      {/* Conclusion */}
      <Card style={{ marginTop: 16 }} className="conclusion-card">
        <Title level={4}>Conclusion</Title>
        <Paragraph>
          This audit was conducted on {auditDate} at {site} by {auditor}. 
          The overall compliance score of {Math.round(passRate)}% indicates that {
            passRate >= 95 ? 'the facility meets all required standards and best practices.' :
            passRate >= 80 ? 'the facility generally meets standards with some areas requiring attention.' :
            'significant improvements are needed to meet required standards.'
          }
        </Paragraph>
        {failCount > 0 && (
          <Paragraph>
            There are {failCount} critical finding(s) that require immediate attention and corrective action.
            A follow-up audit is recommended within 60 days to verify implementation of corrective measures.
          </Paragraph>
        )}
      </Card>

      {/* Footer */}
      <Card style={{ marginTop: 16 }} className="report-footer-card">
        <Row justify="space-between">
          <Col>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Report generated by AMRS Maintenance Tracker on {new Date().toLocaleString()}
            </Text>
          </Col>
          <Col>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Page 1 of 1
            </Text>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default AuditReportOptionB
