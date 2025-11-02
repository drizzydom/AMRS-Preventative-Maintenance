import React from 'react'
import { Card, Typography, Space, Tag, Row, Col, Collapse, Progress, Divider } from 'antd'
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  MinusCircleOutlined,
  SafetyOutlined,
  FileProtectOutlined,
} from '@ant-design/icons'
import '../../styles/reports.css'

const { Title, Text, Paragraph } = Typography
const { Panel } = Collapse

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
 * Option C: Compliance-Focused Format
 * Organized by categories with regulatory focus
 * Best for: Regulatory compliance, ISO audits, safety inspections
 */
const AuditReportOptionC: React.FC<AuditReportProps> = ({ 
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
  const categorizedData = data.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = []
    }
    acc[item.category].push(item)
    return acc
  }, {} as Record<string, AuditItem[]>)

  const getCategoryStats = (items: AuditItem[]) => {
    const pass = items.filter(i => i.status === 'pass').length
    const fail = items.filter(i => i.status === 'fail').length
    const na = items.filter(i => i.status === 'na').length
    const applicable = items.length - na
    const score = applicable > 0 ? (pass / applicable) * 100 : 0
    return { pass, fail, na, score, applicable }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircleOutlined style={{ color: '#52c41a', fontSize: 18 }} />
      case 'fail':
        return <CloseCircleOutlined style={{ color: '#ff4d4f', fontSize: 18 }} />
      case 'na':
        return <MinusCircleOutlined style={{ color: '#8c8c8c', fontSize: 18 }} />
    }
  }

  return (
    <div className="report-container option-c audit-report-compliance">
      {/* Header */}
      <Card className="compliance-header">
        <Row gutter={16}>
          <Col xs={24} md={16}>
            <Space direction="vertical" size="small">
              <Title level={2} style={{ margin: 0 }}>
                <FileProtectOutlined /> Compliance Audit Report
              </Title>
              <Title level={4} style={{ margin: 0, fontWeight: 'normal' }}>
                {auditName}
              </Title>
              <Space wrap>
                <Tag icon={<SafetyOutlined />} color="blue">
                  Site: {site}
                </Tag>
                <Tag color="geekblue">Date: {auditDate}</Tag>
                <Tag>Auditor: {auditor}</Tag>
              </Space>
            </Space>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" className="compliance-score-card">
              <div style={{ textAlign: 'center' }}>
                <Title level={4}>Compliance Score</Title>
                <Progress
                  type="circle"
                  percent={Math.round(passRate)}
                  width={100}
                  strokeWidth={10}
                  status={passRate >= 95 ? 'success' : passRate >= 80 ? 'normal' : 'exception'}
                />
              </div>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* Audit Summary */}
      <Card style={{ marginTop: 16 }} className="audit-summary-compliance">
        <Title level={4}>Audit Summary</Title>
        <Row gutter={16}>
          <Col xs={12} md={6}>
            <div className="compliance-stat">
              <CheckCircleOutlined style={{ fontSize: 32, color: '#52c41a' }} />
              <div className="stat-value-comp">{passCount}</div>
              <div className="stat-label-comp">Compliant</div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div className="compliance-stat">
              <CloseCircleOutlined style={{ fontSize: 32, color: '#ff4d4f' }} />
              <div className="stat-value-comp">{failCount}</div>
              <div className="stat-label-comp">Non-Compliant</div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div className="compliance-stat">
              <MinusCircleOutlined style={{ fontSize: 32, color: '#8c8c8c' }} />
              <div className="stat-value-comp">{naCount}</div>
              <div className="stat-label-comp">Not Applicable</div>
            </div>
          </Col>
          <Col xs={12} md={6}>
            <div className="compliance-stat">
              <FileProtectOutlined style={{ fontSize: 32, color: '#1890ff' }} />
              <div className="stat-value-comp">{data.length}</div>
              <div className="stat-label-comp">Total Items</div>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Category-by-Category Assessment */}
      <Card style={{ marginTop: 16 }}>
        <Title level={4}>Category Assessment</Title>
        <Collapse defaultActiveKey={Object.keys(categorizedData)} accordion={false}>
          {Object.entries(categorizedData).map(([category, items]) => {
            const stats = getCategoryStats(items)
            return (
              <Panel
                key={category}
                header={
                  <Row justify="space-between" align="middle" style={{ width: '100%' }}>
                    <Col>
                      <Text strong style={{ fontSize: 16 }}>{category}</Text>
                      <Text type="secondary" style={{ marginLeft: 16 }}>
                        ({items.length} items)
                      </Text>
                    </Col>
                    <Col>
                      <Space>
                        <Tag color="green">{stats.pass} Pass</Tag>
                        <Tag color="red">{stats.fail} Fail</Tag>
                        <Progress
                          percent={Math.round(stats.score)}
                          steps={10}
                          size="small"
                          strokeColor="#52c41a"
                          style={{ width: 120 }}
                        />
                      </Space>
                    </Col>
                  </Row>
                }
              >
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  {items.map((item) => (
                    <Card
                      key={item.id}
                      size="small"
                      className={`compliance-item-card ${item.status}`}
                      style={{
                        borderLeft: `4px solid ${
                          item.status === 'pass' ? '#52c41a' :
                          item.status === 'fail' ? '#ff4d4f' : '#d9d9d9'
                        }`,
                      }}
                    >
                      <Row gutter={16} align="middle">
                        <Col flex="40px">
                          {getStatusIcon(item.status)}
                        </Col>
                        <Col flex="auto">
                          <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <div>
                              <Text strong>{item.checkpoint}</Text>
                              <Tag 
                                color={
                                  item.status === 'pass' ? 'green' :
                                  item.status === 'fail' ? 'red' : 'default'
                                }
                                style={{ marginLeft: 8 }}
                              >
                                {item.status.toUpperCase()}
                              </Tag>
                            </div>
                            {item.notes && (
                              <Text type="secondary" style={{ fontSize: 13 }}>
                                <strong>Notes:</strong> {item.notes}
                              </Text>
                            )}
                            <Text type="secondary" style={{ fontSize: 12 }}>
                              Verified by: {item.auditor}
                            </Text>
                          </Space>
                        </Col>
                      </Row>
                    </Card>
                  ))}
                </Space>
              </Panel>
            )
          })}
        </Collapse>
      </Card>

      {/* Non-Compliance Items */}
      {failCount > 0 && (
        <Card style={{ marginTop: 16 }} className="non-compliance-section">
          <Title level={4} style={{ color: '#ff4d4f' }}>
            <CloseCircleOutlined /> Non-Compliance Items Requiring Action
          </Title>
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            {data
              .filter(item => item.status === 'fail')
              .map((item, index) => (
                <Card
                  key={item.id}
                  size="small"
                  style={{
                    background: '#fff1f0',
                    borderLeft: '4px solid #ff4d4f',
                  }}
                >
                  <Row gutter={16}>
                    <Col flex="60px">
                      <div className="finding-number">
                        NC-{index + 1}
                      </div>
                    </Col>
                    <Col flex="auto">
                      <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <Text strong style={{ fontSize: 15 }}>
                          {item.category}: {item.checkpoint}
                        </Text>
                        <Paragraph style={{ marginBottom: 0 }}>
                          <Text type="secondary">
                            <strong>Finding:</strong> {item.notes}
                          </Text>
                        </Paragraph>
                        <Paragraph style={{ marginBottom: 0 }}>
                          <Text type="secondary">
                            <strong>Required Action:</strong> Implement corrective measures and document resolution within 30 days.
                          </Text>
                        </Paragraph>
                      </Space>
                    </Col>
                  </Row>
                </Card>
              ))}
          </Space>
        </Card>
      )}

      {/* Compliance Statement */}
      <Card style={{ marginTop: 16 }} className="compliance-statement">
        <Title level={4}>Compliance Statement</Title>
        <Paragraph>
          This compliance audit was conducted on <strong>{auditDate}</strong> at <strong>{site}</strong> by <strong>{auditor}</strong> in accordance with applicable standards and regulations.
        </Paragraph>
        <Paragraph>
          <strong>Audit Scope:</strong> This audit covered {data.length} checkpoints across {Object.keys(categorizedData).length} categories.
        </Paragraph>
        <Paragraph>
          <strong>Overall Assessment:</strong> The facility achieved a compliance score of <strong>{Math.round(passRate)}%</strong>, with {passCount} compliant items, {failCount} non-compliant items, and {naCount} not applicable items.
        </Paragraph>
        {passRate >= 95 ? (
          <Paragraph style={{ color: '#52c41a' }}>
            <CheckCircleOutlined /> The facility demonstrates full compliance with applicable standards and regulations.
          </Paragraph>
        ) : passRate >= 80 ? (
          <Paragraph style={{ color: '#faad14' }}>
            <FileProtectOutlined /> The facility demonstrates substantial compliance with minor corrective actions required.
          </Paragraph>
        ) : (
          <Paragraph style={{ color: '#ff4d4f' }}>
            <CloseCircleOutlined /> The facility requires significant corrective actions to achieve full compliance.
          </Paragraph>
        )}
      </Card>

      {/* Certification */}
      <Card style={{ marginTop: 16 }} className="certification-section">
        <Divider>Audit Certification</Divider>
        <Row gutter={[32, 16]}>
          <Col xs={24} md={12}>
            <div className="signature-box">
              <div className="signature-line"></div>
              <Space direction="vertical" size="small">
                <Text strong>Auditor Signature</Text>
                <Text type="secondary">{auditor}</Text>
                <Text type="secondary">Date: {auditDate}</Text>
              </Space>
            </div>
          </Col>
          <Col xs={24} md={12}>
            <div className="signature-box">
              <div className="signature-line"></div>
              <Space direction="vertical" size="small">
                <Text strong>Management Review</Text>
                <Text type="secondary">_____________________</Text>
                <Text type="secondary">Date: __________</Text>
              </Space>
            </div>
          </Col>
        </Row>
      </Card>

      {/* Footer */}
      <Card style={{ marginTop: 16 }} className="report-footer">
        <Text type="secondary" style={{ fontSize: 12 }}>
          Generated by AMRS Maintenance Tracker on {new Date().toLocaleString()} | 
          Document ID: AUDIT-{auditDate.replace(/-/g, '')}-{site.replace(/\s/g, '').toUpperCase()}
        </Text>
      </Card>
    </div>
  )
}

export default AuditReportOptionC
