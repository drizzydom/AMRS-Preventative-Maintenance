import React, { useState } from 'react'
import { Card, Tabs, Typography, Space, Button, DatePicker, Select, Row, Col, Divider } from 'antd'
import { DownloadOutlined, PrinterOutlined, EyeOutlined } from '@ant-design/icons'
import AuditReportOptionA from '../../components/reports/AuditReportOptionA'
import AuditReportOptionB from '../../components/reports/AuditReportOptionB'
import AuditReportOptionC from '../../components/reports/AuditReportOptionC'
import '../../styles/reports.css'

const { Title, Text, Paragraph } = Typography
const { TabPane } = Tabs

const AuditReportsPreview: React.FC = () => {
  const [selectedSite, setSelectedSite] = useState('Main Plant')

  // Sample audit data for preview
  const sampleAuditData = [
    {
      id: 1,
      category: 'Safety Equipment',
      checkpoint: 'Emergency stop buttons functional',
      status: 'pass' as const,
      notes: 'All emergency stop buttons tested and operational',
      auditor: 'John Doe',
    },
    {
      id: 2,
      category: 'Safety Equipment',
      checkpoint: 'Fire extinguishers accessible and inspected',
      status: 'pass' as const,
      notes: 'All fire extinguishers within inspection dates',
      auditor: 'John Doe',
    },
    {
      id: 3,
      category: 'Safety Equipment',
      checkpoint: 'First aid kits stocked and accessible',
      status: 'fail' as const,
      notes: 'First aid kit in Assembly Area missing bandages and antiseptic',
      auditor: 'John Doe',
    },
    {
      id: 4,
      category: 'Machine Guards',
      checkpoint: 'All rotating parts properly guarded',
      status: 'pass' as const,
      notes: 'Guards in place and secured',
      auditor: 'Jane Smith',
    },
    {
      id: 5,
      category: 'Machine Guards',
      checkpoint: 'Interlock systems functional',
      status: 'fail' as const,
      notes: 'Interlock on CNC Machine B not functioning - requires immediate repair',
      auditor: 'Jane Smith',
    },
    {
      id: 6,
      category: 'Electrical Safety',
      checkpoint: 'Electrical panels properly labeled',
      status: 'pass' as const,
      notes: 'All panels clearly labeled with circuit information',
      auditor: 'Bob Johnson',
    },
    {
      id: 7,
      category: 'Electrical Safety',
      checkpoint: 'Ground fault circuit interrupters (GFCI) operational',
      status: 'pass' as const,
      notes: 'All GFCI outlets tested and functioning',
      auditor: 'Bob Johnson',
    },
    {
      id: 8,
      category: 'Housekeeping',
      checkpoint: 'Aisles and walkways clear',
      status: 'pass' as const,
      notes: 'All aisles meet minimum width requirements',
      auditor: 'Sarah Davis',
    },
    {
      id: 9,
      category: 'Housekeeping',
      checkpoint: 'Spill cleanup materials available',
      status: 'pass' as const,
      notes: 'Spill kits located in designated areas',
      auditor: 'Sarah Davis',
    },
    {
      id: 10,
      category: 'PPE Compliance',
      checkpoint: 'Required PPE available and used',
      status: 'fail' as const,
      notes: 'Three employees observed not wearing safety glasses in designated area',
      auditor: 'Mike Wilson',
    },
    {
      id: 11,
      category: 'PPE Compliance',
      checkpoint: 'PPE storage and maintenance adequate',
      status: 'pass' as const,
      notes: 'PPE properly stored and in good condition',
      auditor: 'Mike Wilson',
    },
    {
      id: 12,
      category: 'Documentation',
      checkpoint: 'Training records up to date',
      status: 'pass' as const,
      notes: 'All employee training records current',
      auditor: 'Tom Anderson',
    },
    {
      id: 13,
      category: 'Documentation',
      checkpoint: 'Inspection logs maintained',
      status: 'pass' as const,
      notes: 'Daily inspection logs properly filled out',
      auditor: 'Tom Anderson',
    },
    {
      id: 14,
      category: 'Environmental Controls',
      checkpoint: 'Ventilation systems operational',
      status: 'pass' as const,
      notes: 'All ventilation systems tested and adequate',
      auditor: 'Lisa Brown',
    },
    {
      id: 15,
      category: 'Environmental Controls',
      checkpoint: 'Hazardous materials properly stored',
      status: 'na' as const,
      notes: 'No hazardous materials used at this location',
      auditor: 'Lisa Brown',
    },
  ]

  return (
    <div className="reports-preview-container">
      <Card className="reports-header">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2}>Audit Report Design Options</Title>
            <Paragraph type="secondary">
              Review and select the best audit report design for your compliance documentation.
              Each option is optimized for different audit types and audiences.
            </Paragraph>
          </div>

          {/* Filters */}
          <Row gutter={16}>
            <Col xs={24} md={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text strong>Audit Date</Text>
                <DatePicker style={{ width: '100%' }} format="YYYY-MM-DD" />
              </Space>
            </Col>
            <Col xs={24} md={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text strong>Site</Text>
                <Select
                  value={selectedSite}
                  onChange={setSelectedSite}
                  style={{ width: '100%' }}
                  options={[
                    { value: 'Main Plant', label: 'Main Plant' },
                    { value: 'Warehouse', label: 'Warehouse' },
                    { value: 'Assembly Line', label: 'Assembly Line' },
                  ]}
                />
              </Space>
            </Col>
            <Col xs={24} md={8}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text strong>Audit Type</Text>
                <Select
                  defaultValue="safety"
                  style={{ width: '100%' }}
                  options={[
                    { value: 'safety', label: 'Safety Audit' },
                    { value: 'quality', label: 'Quality Audit' },
                    { value: 'maintenance', label: 'Maintenance Audit' },
                    { value: 'compliance', label: 'Compliance Audit' },
                  ]}
                />
              </Space>
            </Col>
          </Row>

          <Space>
            <Button type="primary" icon={<EyeOutlined />}>
              Preview Report
            </Button>
            <Button icon={<DownloadOutlined />}>
              Export to PDF
            </Button>
            <Button icon={<PrinterOutlined />}>
              Print
            </Button>
          </Space>
        </Space>
      </Card>

      <Divider />

      {/* Report Options Tabs */}
      <Card>
        <Tabs defaultActiveKey="1" type="card" size="large">
          <TabPane 
            tab={
              <span>
                <EyeOutlined />
                Option A: Detailed Checklist
              </span>
            } 
            key="1"
          >
            <div className="option-description">
              <Card size="small" style={{ marginBottom: 16, background: '#f0f2f5' }}>
                <Space direction="vertical">
                  <Text strong>Option A: Detailed Checklist Format</Text>
                  <Paragraph style={{ marginBottom: 0 }}>
                    <ul style={{ paddingLeft: 20, marginBottom: 0 }}>
                      <li>Comprehensive checklist with all inspection points</li>
                      <li>Table format for easy scanning</li>
                      <li>Overall compliance score with progress circle</li>
                      <li>Dedicated findings and recommendations section</li>
                      <li>Signature blocks for auditor and supervisor</li>
                      <li><strong>Best for:</strong> Compliance audits, detailed inspections, regulatory requirements</li>
                    </ul>
                  </Paragraph>
                </Space>
              </Card>
            </div>
            <div className="report-preview-wrapper">
              <AuditReportOptionA
                auditName="Safety Compliance Audit"
                auditDate="2025-11-01"
                site={selectedSite}
                auditor="John Doe"
                data={sampleAuditData}
              />
            </div>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <EyeOutlined />
                Option B: Executive Summary
              </span>
            } 
            key="2"
          >
            <div className="option-description">
              <Card size="small" style={{ marginBottom: 16, background: '#f0f2f5' }}>
                <Space direction="vertical">
                  <Text strong>Option B: Executive Summary Format</Text>
                  <Paragraph style={{ marginBottom: 0 }}>
                    <ul style={{ paddingLeft: 20, marginBottom: 0 }}>
                      <li>High-level overview focusing on key metrics</li>
                      <li>Visual KPI dashboard with large compliance score</li>
                      <li>Category performance breakdown with progress bars</li>
                      <li>Critical findings highlighted prominently</li>
                      <li>Recommendations and conclusion sections</li>
                      <li><strong>Best for:</strong> Management reviews, stakeholder presentations, board meetings</li>
                    </ul>
                  </Paragraph>
                </Space>
              </Card>
            </div>
            <div className="report-preview-wrapper">
              <AuditReportOptionB
                auditName="Safety Compliance Audit"
                auditDate="2025-11-01"
                site={selectedSite}
                auditor="John Doe"
                data={sampleAuditData}
              />
            </div>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <EyeOutlined />
                Option C: Compliance Report
              </span>
            } 
            key="3"
          >
            <div className="option-description">
              <Card size="small" style={{ marginBottom: 16, background: '#f0f2f5' }}>
                <Space direction="vertical">
                  <Text strong>Option C: Compliance-Focused Format</Text>
                  <Paragraph style={{ marginBottom: 0 }}>
                    <ul style={{ paddingLeft: 20, marginBottom: 0 }}>
                      <li>Organized by categories with regulatory focus</li>
                      <li>Collapsible category sections for easy navigation</li>
                      <li>Non-compliance items with required actions</li>
                      <li>Formal compliance statement</li>
                      <li>Certification section with document ID</li>
                      <li><strong>Best for:</strong> Regulatory compliance, ISO audits, safety inspections, certification</li>
                    </ul>
                  </Paragraph>
                </Space>
              </Card>
            </div>
            <div className="report-preview-wrapper">
              <AuditReportOptionC
                auditName="Safety Compliance Audit"
                auditDate="2025-11-01"
                site={selectedSite}
                auditor="John Doe"
                data={sampleAuditData}
              />
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* Decision Helper */}
      <Card style={{ marginTop: 16 }}>
        <Title level={4}>Which Audit Report Option Should I Choose?</Title>
        <Row gutter={16}>
          <Col xs={24} md={8}>
            <Card size="small" style={{ height: '100%' }}>
              <Text strong>Choose Option A if:</Text>
              <ul style={{ paddingLeft: 20 }}>
                <li>You need complete audit documentation</li>
                <li>You're conducting compliance audits</li>
                <li>You need detailed checklist format</li>
                <li>You require signature certification</li>
                <li>You're doing regulatory inspections</li>
              </ul>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" style={{ height: '100%' }}>
              <Text strong>Choose Option B if:</Text>
              <ul style={{ paddingLeft: 20 }}>
                <li>You're presenting to executives</li>
                <li>You need visual impact</li>
                <li>You want focus on key metrics</li>
                <li>Your audience prefers dashboards</li>
                <li>You're doing internal reviews</li>
              </ul>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" style={{ height: '100%' }}>
              <Text strong>Choose Option C if:</Text>
              <ul style={{ paddingLeft: 20 }}>
                <li>You need ISO/regulatory format</li>
                <li>You're seeking certification</li>
                <li>You need formal compliance docs</li>
                <li>You want category organization</li>
                <li>You're doing safety inspections</li>
              </ul>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* Audit Types Guide */}
      <Card style={{ marginTop: 16 }}>
        <Title level={4}>Audit Types & Report Recommendations</Title>
        <Row gutter={16}>
          <Col xs={24} md={12}>
            <Card size="small">
              <Text strong>Safety Audits</Text>
              <Paragraph>
                <strong>Recommended:</strong> Option C (Compliance Format)
                <br />
                Safety audits require formal documentation with compliance statements and certification.
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card size="small">
              <Text strong>Quality Audits</Text>
              <Paragraph>
                <strong>Recommended:</strong> Option A (Detailed Checklist)
                <br />
                Quality audits benefit from comprehensive checklists with findings documentation.
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card size="small">
              <Text strong>Internal Management Reviews</Text>
              <Paragraph>
                <strong>Recommended:</strong> Option B (Executive Summary)
                <br />
                Management reviews focus on key metrics and visual performance indicators.
              </Paragraph>
            </Card>
          </Col>
          <Col xs={24} md={12}>
            <Card size="small">
              <Text strong>Regulatory Compliance</Text>
              <Paragraph>
                <strong>Recommended:</strong> Option C (Compliance Format)
                <br />
                Regulatory audits require formal compliance statements and structured documentation.
              </Paragraph>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default AuditReportsPreview
