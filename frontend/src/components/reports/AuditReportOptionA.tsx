import React from 'react'
import { Card, Table, Typography, Space, Tag, Divider, Progress } from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import '../../styles/reports.css'

const { Title, Text } = Typography

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
 * Option A: Detailed Checklist Format
 * Comprehensive checklist with all inspection points
 * Best for: Compliance audits, detailed inspections
 */
const AuditReportOptionA: React.FC<AuditReportProps> = ({ 
  auditName,
  auditDate,
  site,
  auditor,
  data 
}) => {
  const columns: ColumnsType<AuditItem> = [
    {
      title: '#',
      dataIndex: 'id',
      key: 'id',
      width: 50,
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: 150,
    },
    {
      title: 'Checkpoint',
      dataIndex: 'checkpoint',
      key: 'checkpoint',
      width: 300,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => {
        const config = {
          pass: { color: 'green', icon: <CheckCircleOutlined />, text: 'PASS' },
          fail: { color: 'red', icon: <CloseCircleOutlined />, text: 'FAIL' },
          na: { color: 'default', icon: null, text: 'N/A' },
        }
        const { color, icon, text } = config[status as keyof typeof config]
        return (
          <Tag color={color} icon={icon}>
            {text}
          </Tag>
        )
      },
    },
    {
      title: 'Notes',
      dataIndex: 'notes',
      key: 'notes',
    },
    {
      title: 'Auditor',
      dataIndex: 'auditor',
      key: 'auditor',
      width: 120,
    },
  ]

  const passCount = data.filter(item => item.status === 'pass').length
  const failCount = data.filter(item => item.status === 'fail').length
  const naCount = data.filter(item => item.status === 'na').length
  const applicableItems = data.length - naCount
  const passRate = applicableItems > 0 ? (passCount / applicableItems) * 100 : 0

  return (
    <div className="report-container option-a audit-report">
      {/* Header */}
      <div className="report-header">
        <div className="company-branding">
          <Title level={2}>AMRS Maintenance Tracker</Title>
          <Text type="secondary">Audit Inspection Report</Text>
        </div>
        <div className="report-meta">
          <Space direction="vertical" size="small">
            <Text><strong>Audit:</strong> {auditName}</Text>
            <Text><strong>Date:</strong> {auditDate}</Text>
            <Text><strong>Site:</strong> {site}</Text>
            <Text><strong>Auditor:</strong> {auditor}</Text>
          </Space>
        </div>
      </div>

      <Divider />

      {/* Executive Summary */}
      <div className="audit-summary-section">
        <Title level={4}>Executive Summary</Title>
        <Card className="audit-summary-card">
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <div className="audit-score">
              <Text strong style={{ fontSize: 18 }}>Overall Compliance Score</Text>
              <div style={{ marginTop: 12 }}>
                <Progress
                  type="circle"
                  percent={Math.round(passRate)}
                  width={120}
                  strokeWidth={10}
                  status={passRate >= 95 ? 'success' : passRate >= 80 ? 'normal' : 'exception'}
                />
              </div>
            </div>
            <Divider style={{ margin: '12px 0' }} />
            <Space size="large">
              <div className="summary-stat">
                <div className="stat-value" style={{ color: '#52c41a' }}>{passCount}</div>
                <div className="stat-label">Passed</div>
              </div>
              <div className="summary-stat">
                <div className="stat-value" style={{ color: '#ff4d4f' }}>{failCount}</div>
                <div className="stat-label">Failed</div>
              </div>
              <div className="summary-stat">
                <div className="stat-value" style={{ color: '#8c8c8c' }}>{naCount}</div>
                <div className="stat-label">N/A</div>
              </div>
              <div className="summary-stat">
                <div className="stat-value">{data.length}</div>
                <div className="stat-label">Total Items</div>
              </div>
            </Space>
          </Space>
        </Card>
      </div>

      <Divider />

      {/* Detailed Checklist */}
      <div className="report-table">
        <Title level={4}>Detailed Checklist</Title>
        <Table
          columns={columns}
          dataSource={data}
          pagination={false}
          size="small"
          bordered
          className="print-friendly-table audit-table"
          rowClassName={(record) => 
            record.status === 'fail' ? 'audit-fail-row' : ''
          }
        />
      </div>

      {/* Findings & Recommendations */}
      {failCount > 0 && (
        <>
          <Divider />
          <div className="findings-section">
            <Title level={4}>Findings & Recommendations</Title>
            <Card>
              <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                {data
                  .filter(item => item.status === 'fail')
                  .map((item, index) => (
                    <div key={item.id} className="finding-item">
                      <Text strong>
                        {index + 1}. {item.category} - {item.checkpoint}
                      </Text>
                      <br />
                      <Text type="secondary">{item.notes}</Text>
                    </div>
                  ))}
              </Space>
            </Card>
          </div>
        </>
      )}

      {/* Footer */}
      <div className="report-footer">
        <Divider />
        <Space direction="vertical" size="small">
          <Text type="secondary">
            This audit report contains {data.length} inspection points with {passCount} passes, {failCount} failures, and {naCount} not applicable items.
          </Text>
          <Text type="secondary">
            Generated by AMRS Maintenance Tracker on {new Date().toLocaleDateString()}
          </Text>
        </Space>
      </div>

      {/* Signature Section */}
      <div className="signature-section">
        <Divider />
        <Space size="large" style={{ width: '100%', justifyContent: 'space-between' }}>
          <div className="signature-block">
            <div className="signature-line"></div>
            <Text>Auditor Signature</Text>
            <br />
            <Text type="secondary">Date: {auditDate}</Text>
          </div>
          <div className="signature-block">
            <div className="signature-line"></div>
            <Text>Supervisor Signature</Text>
            <br />
            <Text type="secondary">Date: __________</Text>
          </div>
        </Space>
      </div>
    </div>
  )
}

export default AuditReportOptionA
