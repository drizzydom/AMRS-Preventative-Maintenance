import React, { useState } from 'react'
import { Card, Tabs, Typography, Space, Button, DatePicker, Select, Row, Col, Divider } from 'antd'
import { DownloadOutlined, PrinterOutlined, EyeOutlined } from '@ant-design/icons'
import MaintenanceReportOptionA from '../../components/reports/MaintenanceReportOptionA'
import MaintenanceReportOptionB from '../../components/reports/MaintenanceReportOptionB'
import MaintenanceReportOptionC from '../../components/reports/MaintenanceReportOptionC'
import '../../styles/reports.css'

const { Title, Text, Paragraph } = Typography
const { RangePicker } = DatePicker
const { TabPane } = Tabs

const ReportsPreview: React.FC = () => {
  const [dateRange, setDateRange] = useState<[string, string]>(['2025-10-01', '2025-10-31'])
  const [selectedSite, setSelectedSite] = useState('All Sites')

  // Sample maintenance data for preview
  const sampleData = [
    {
      id: 1,
      date: '2025-10-28',
      machine: 'CNC Machine A',
      task: 'Oil Change',
      technician: 'John Doe',
      duration: '2.5 hrs',
      status: 'completed' as const,
      notes: 'Routine maintenance completed successfully',
    },
    {
      id: 2,
      date: '2025-10-27',
      machine: 'Lathe Machine B',
      task: 'Filter Replacement',
      technician: 'Jane Smith',
      duration: '1.5 hrs',
      status: 'completed' as const,
      notes: 'Replaced air and oil filters',
    },
    {
      id: 3,
      date: '2025-10-26',
      machine: 'Press Machine C',
      task: 'Safety Inspection',
      technician: 'Bob Johnson',
      duration: '3.0 hrs',
      status: 'completed' as const,
      notes: 'All safety systems operational',
    },
    {
      id: 4,
      date: '2025-10-25',
      machine: 'CNC Machine A',
      task: 'Belt Replacement',
      technician: 'John Doe',
      duration: '2.0 hrs',
      status: 'overdue' as const,
      notes: 'Waiting for replacement parts',
    },
    {
      id: 5,
      date: '2025-10-24',
      machine: 'Drill Press D',
      task: 'Lubrication',
      technician: 'Mike Wilson',
      duration: '0.5 hrs',
      status: 'completed' as const,
      notes: 'Standard lubrication performed',
    },
    {
      id: 6,
      date: '2025-10-23',
      machine: 'Milling Machine E',
      task: 'Calibration',
      technician: 'Sarah Davis',
      duration: '4.0 hrs',
      status: 'completed' as const,
      notes: 'Precision calibration completed',
    },
    {
      id: 7,
      date: '2025-10-22',
      machine: 'Grinder F',
      task: 'Wheel Replacement',
      technician: 'Tom Anderson',
      duration: '1.0 hrs',
      status: 'pending' as const,
      notes: 'Scheduled for next week',
    },
    {
      id: 8,
      date: '2025-10-21',
      machine: 'Lathe Machine B',
      task: 'Chuck Inspection',
      technician: 'Jane Smith',
      duration: '1.5 hrs',
      status: 'completed' as const,
      notes: 'Chuck mechanism working properly',
    },
  ]

  return (
    <div className="reports-preview-container">
      <Card className="reports-header">
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={2}>Report Design Options</Title>
            <Paragraph type="secondary">
              Review and select the best report design for your maintenance records.
              Each option offers a different visual approach to presenting your data.
            </Paragraph>
          </div>

          {/* Filters */}
          <Row gutter={16}>
            <Col xs={24} md={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text strong>Date Range</Text>
                <RangePicker 
                  style={{ width: '100%' }}
                  format="YYYY-MM-DD"
                />
              </Space>
            </Col>
            <Col xs={24} md={12}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Text strong>Site</Text>
                <Select
                  value={selectedSite}
                  onChange={setSelectedSite}
                  style={{ width: '100%' }}
                  options={[
                    { value: 'All Sites', label: 'All Sites' },
                    { value: 'Main Plant', label: 'Main Plant' },
                    { value: 'Warehouse', label: 'Warehouse' },
                    { value: 'Assembly Line', label: 'Assembly Line' },
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
                Option A: Minimalist Table
              </span>
            } 
            key="1"
          >
            <div className="option-description">
              <Card size="small" style={{ marginBottom: 16, background: '#f0f2f5' }}>
                <Space direction="vertical">
                  <Text strong>Option A: Minimalist Table Layout</Text>
                  <Paragraph style={{ marginBottom: 0 }}>
                    <ul style={{ paddingLeft: 20, marginBottom: 0 }}>
                      <li>Clean, professional table with clear hierarchy</li>
                      <li>Compact design fits more data on a page</li>
                      <li>Easy to scan and read</li>
                      <li>Excellent for printing and PDF export</li>
                      <li><strong>Best for:</strong> Monthly reports, management reviews, formal documentation</li>
                    </ul>
                  </Paragraph>
                </Space>
              </Card>
            </div>
            <div className="report-preview-wrapper">
              <MaintenanceReportOptionA
                startDate={dateRange[0]}
                endDate={dateRange[1]}
                site={selectedSite}
                data={sampleData}
              />
            </div>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <EyeOutlined />
                Option B: Card-Based Visual
              </span>
            } 
            key="2"
          >
            <div className="option-description">
              <Card size="small" style={{ marginBottom: 16, background: '#f0f2f5' }}>
                <Space direction="vertical">
                  <Text strong>Option B: Card-Based Layout with Visual Indicators</Text>
                  <Paragraph style={{ marginBottom: 0 }}>
                    <ul style={{ paddingLeft: 20, marginBottom: 0 }}>
                      <li>Modern, visual approach with cards and icons</li>
                      <li>Color-coded status indicators</li>
                      <li>Performance dashboard with metrics</li>
                      <li>Easy to understand at a glance</li>
                      <li><strong>Best for:</strong> Executive summaries, visual presentations, stakeholder meetings</li>
                    </ul>
                  </Paragraph>
                </Space>
              </Card>
            </div>
            <div className="report-preview-wrapper">
              <MaintenanceReportOptionB
                startDate={dateRange[0]}
                endDate={dateRange[1]}
                site={selectedSite}
                data={sampleData}
              />
            </div>
          </TabPane>

          <TabPane 
            tab={
              <span>
                <EyeOutlined />
                Option C: Timeline View
              </span>
            } 
            key="3"
          >
            <div className="option-description">
              <Card size="small" style={{ marginBottom: 16, background: '#f0f2f5' }}>
                <Space direction="vertical">
                  <Text strong>Option C: Timeline-Based Layout</Text>
                  <Paragraph style={{ marginBottom: 0 }}>
                    <ul style={{ paddingLeft: 20, marginBottom: 0 }}>
                      <li>Chronological view showing maintenance history</li>
                      <li>Timeline visualization of activities</li>
                      <li>Grouped by date for easy tracking</li>
                      <li>Shows progression over time</li>
                      <li><strong>Best for:</strong> Historical tracking, compliance audits, regulatory reports</li>
                    </ul>
                  </Paragraph>
                </Space>
              </Card>
            </div>
            <div className="report-preview-wrapper">
              <MaintenanceReportOptionC
                startDate={dateRange[0]}
                endDate={dateRange[1]}
                site={selectedSite}
                data={sampleData}
              />
            </div>
          </TabPane>
        </Tabs>
      </Card>

      {/* Decision Helper */}
      <Card style={{ marginTop: 16 }}>
        <Title level={4}>Which Option Should I Choose?</Title>
        <Row gutter={16}>
          <Col xs={24} md={8}>
            <Card size="small" style={{ height: '100%' }}>
              <Text strong>Choose Option A if:</Text>
              <ul style={{ paddingLeft: 20 }}>
                <li>You need formal documentation</li>
                <li>You're printing physical copies</li>
                <li>You want maximum data density</li>
                <li>Your audience prefers traditional reports</li>
              </ul>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" style={{ height: '100%' }}>
              <Text strong>Choose Option B if:</Text>
              <ul style={{ paddingLeft: 20 }}>
                <li>You're presenting to executives</li>
                <li>You need visual impact</li>
                <li>You want quick insights</li>
                <li>Your audience prefers dashboards</li>
              </ul>
            </Card>
          </Col>
          <Col xs={24} md={8}>
            <Card size="small" style={{ height: '100%' }}>
              <Text strong>Choose Option C if:</Text>
              <ul style={{ paddingLeft: 20 }}>
                <li>You need historical tracking</li>
                <li>You're doing compliance audits</li>
                <li>You want chronological order</li>
                <li>Your audience needs context</li>
              </ul>
            </Card>
          </Col>
        </Row>
      </Card>
    </div>
  )
}

export default ReportsPreview
