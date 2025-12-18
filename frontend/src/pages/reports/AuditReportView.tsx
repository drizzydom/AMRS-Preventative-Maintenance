import React, { useEffect, useState } from 'react'
import { Card, Select, Spin, Button, Table, message, Typography } from 'antd'
import dayjs from 'dayjs'
import api from '../../utils/api'
import '../../styles/reports.css'

const { Title, Paragraph } = Typography

interface AuditTask {
  id: number
  name: string
  description?: string
  site?: string
  site_id?: number
}

interface AuditMachine {
  id: number
  name: string
  model?: string
  serial_number?: string
  completed?: boolean
  completed_at?: string | null
  completed_by?: string | null
}

interface DailyAuditData {
  date: string
  machines: AuditMachine[]
}

const AuditReportView: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [audits, setAudits] = useState<AuditTask[]>([])
  const [selectedAuditId, setSelectedAuditId] = useState<number | null>(null)
  const [machines, setMachines] = useState<AuditMachine[]>([])
  const [groupedData, setGroupedData] = useState<DailyAuditData[]>([])
  const [machinesLoading, setMachinesLoading] = useState(false)
  const search = new URLSearchParams(window.location.search)
  const reportType = (search.get('report_type') || 'compact') as 'compact' | 'expanded'
  const dateFrom = search.get('date_from')
  const dateTo = search.get('date_to')
  const isGrouped = !!(dateFrom && dateTo)

  useEffect(() => {
    const loadAudits = async () => {
      try {
        setLoading(true)
        const res = await api.get('/api/v1/audits')
        const data = res?.data?.data || []
        setAudits(Array.isArray(data) ? data : [])
        if (Array.isArray(data) && data.length > 0) {
          setSelectedAuditId(data[0].id)
        }
      } catch (err) {
        console.error('[AuditReportView] Failed to load audits:', err)
        message.error('Failed to load audits')
      } finally {
        setLoading(false)
      }
    }

    loadAudits()
  }, [])

  useEffect(() => {
    const loadMachines = async (auditId: number) => {
      try {
        setMachinesLoading(true)
        const params: any = {}
        if (dateFrom) params.date_from = dateFrom
        if (dateTo) params.date_to = dateTo
        if (dateFrom && dateTo) params.grouped_by_date = '1'

        const res = await api.get(`/api/v1/audits/${auditId}/machines`, { params })
        const data = res?.data?.data || []
        
        if (dateFrom && dateTo) {
          setGroupedData(Array.isArray(data) ? data : [])
          setMachines([])
        } else {
          setMachines(Array.isArray(data) ? data : [])
          setGroupedData([])
        }
      } catch (err) {
        console.error('[AuditReportView] Failed to load machines for audit:', err)
        message.error('Failed to load machines for selected audit')
        setMachines([])
        setGroupedData([])
      } finally {
        setMachinesLoading(false)
      }
    }

    if (selectedAuditId) {
      loadMachines(selectedAuditId)
    } else {
      setMachines([])
      setGroupedData([])
    }
  }, [selectedAuditId, dateFrom, dateTo])

  const onPrint = () => {
    window.print()
  }

  if (loading) return <div style={{ padding: 24, textAlign: 'center' }}><Spin size="large" /></div>

  const selectedAudit = audits.find((a) => a.id === selectedAuditId) || null

  const columns = [
    { title: 'Machine', dataIndex: 'name', key: 'name' },
    ...(reportType === 'expanded' ? [{ title: 'Model', dataIndex: 'model', key: 'model' }] : []),
    ...(reportType === 'expanded' ? [{ title: 'Serial', dataIndex: 'serial_number', key: 'serial_number' }] : []),
    {
      title: 'Completed',
      dataIndex: 'completed',
      key: 'completed',
      render: (val: boolean) => (val ? 'Yes' : 'No'),
    },
    ...(reportType === 'expanded' ? [{ title: 'Completed By', dataIndex: 'completed_by', key: 'completed_by' }] : []),
    ...(reportType === 'expanded' ? [{ title: 'Completed At', dataIndex: 'completed_at', key: 'completed_at' }] : []),
  ]

  return (
    <div className="report-container">
      <div className="report-header no-print">
        <Card style={{ marginBottom: 16 }}>
          <Title level={2}>Audit Report</Title>
          <Paragraph type="secondary">Select an audit task and generate a printable audit report showing completion status for machines (today).</Paragraph>
        </Card>

        <Card style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <div style={{ minWidth: 320 }}>
              <div style={{ marginBottom: 8, fontWeight: 600 }}>Audit Task</div>
              <Select
                value={selectedAuditId ?? undefined}
                onChange={(v) => setSelectedAuditId(v ?? null)}
                style={{ minWidth: 320 }}
                allowClear
              >
                {audits.map((a) => (
                  <Select.Option key={a.id} value={a.id}>{a.name}</Select.Option>
                ))}
              </Select>
            </div>

            <div style={{ marginLeft: 'auto' }}>
              <Button type="primary" onClick={onPrint} disabled={!selectedAuditId || machinesLoading}>Print</Button>
            </div>
          </div>
        </Card>
      </div>

      {/* Print Header - Visible only when printing */}
      <div className="report-header print-only" style={{ display: 'none' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 20 }}>
          <div>
            <Title level={3}>Audit Report</Title>
            <Paragraph>Generated: {dayjs().format('YYYY-MM-DD HH:mm')}</Paragraph>
          </div>
          <div style={{ textAlign: 'right' }}>
            <Paragraph><strong>AMRS Maintenance Tracker</strong></Paragraph>
          </div>
        </div>
      </div>

      <div className="report-section">
        <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '16px' }}>{selectedAudit ? selectedAudit.name : 'No audit selected'}</div>
            <div style={{ color: '#666' }}>{selectedAudit ? `${selectedAudit.site || ''}` : ''}</div>
            <div style={{ color: '#666' }}>
              {dateFrom && dateTo 
                ? `Date Range: ${dateFrom} to ${dateTo}`
                : `Date: ${dayjs().format('YYYY-MM-DD')}`}
            </div>
          </div>
        </div>

      {isGrouped && groupedData.length > 0 ? (
        <div style={{ marginTop: 20 }}>
          {groupedData.map((group) => (
            <div key={group.date} className="date-group-section" style={{ marginBottom: 24 }}>
              <div style={{ 
                fontWeight: 600, 
                marginBottom: 8, 
                fontSize: '15px',
                borderBottom: '1px solid #eee',
                paddingBottom: 4,
                pageBreakAfter: 'avoid',
                breakAfter: 'avoid'
              }}>
                Date: {group.date}
              </div>
              <Table
                dataSource={group.machines}
                columns={columns}
                rowKey={(row: any) => row.id}
                loading={machinesLoading}
                pagination={false}
                className="report-table print-friendly-table"
                bordered
                size="small"
              />
            </div>
          ))}
        </div>
      ) : (
        <Table
          dataSource={machines}
          columns={columns}
          rowKey={(row: any) => row.id}
          loading={machinesLoading}
          pagination={false}
          className="report-table print-friendly-table"
          bordered
        />
      )}
      </div>

      <style>{`
        @media print {
          html, body, #root {
            height: auto !important;
            overflow: visible !important;
            width: auto !important;
          }

          .no-print { display: none !important; }
          .print-only { display: block !important; }
          .report-container { 
            padding: 0; 
            width: 100% !important;
            max-width: none !important;
            overflow: visible !important;
          }
          
          .date-group-section {
            page-break-inside: avoid;
            break-inside: avoid;
            display: block;
            position: relative;
            margin-bottom: 24px;
          }

          /* Ensure table rows try not to break */
          tr {
            page-break-inside: avoid;
            break-inside: avoid;
          }

          /* Ensure header stays with table */
          .ant-table-thead > tr > th {
            background-color: #f0f0f0 !important;
            -webkit-print-color-adjust: exact;
          }

          body { background: white; }
          /* Hide Ant Design table pagination and other non-print elements */
          .ant-pagination { display: none !important; }
        }
      `}</style>
    </div>
  )
}

export default AuditReportView
