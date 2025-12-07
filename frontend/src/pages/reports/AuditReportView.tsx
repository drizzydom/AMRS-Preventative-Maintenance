import React, { useEffect, useState } from 'react'
import { Card, Select, Spin, Button, Table, message, Typography } from 'antd'
import dayjs from 'dayjs'
import api from '../../utils/api'

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

const AuditReportView: React.FC = () => {
  const [loading, setLoading] = useState(true)
  const [audits, setAudits] = useState<AuditTask[]>([])
  const [selectedAuditId, setSelectedAuditId] = useState<number | null>(null)
  const [machines, setMachines] = useState<AuditMachine[]>([])
  const [machinesLoading, setMachinesLoading] = useState(false)
  const search = new URLSearchParams(window.location.search)
  const reportType = (search.get('report_type') || 'compact') as 'compact' | 'expanded'

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
        const res = await api.get(`/api/v1/audits/${auditId}/machines`)
        const data = res?.data?.data || []
        setMachines(Array.isArray(data) ? data : [])
      } catch (err) {
        console.error('[AuditReportView] Failed to load machines for audit:', err)
        message.error('Failed to load machines for selected audit')
        setMachines([])
      } finally {
        setMachinesLoading(false)
      }
    }

    if (selectedAuditId) {
      loadMachines(selectedAuditId)
    } else {
      setMachines([])
    }
  }, [selectedAuditId])

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
    <div style={{ padding: 24 }}>
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

      <Card>
        <div style={{ marginBottom: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontWeight: 700 }}>{selectedAudit ? selectedAudit.name : 'No audit selected'}</div>
            <div style={{ color: '#666' }}>{selectedAudit ? `${selectedAudit.site || ''}` : ''}</div>
            <div style={{ color: '#666' }}>{`Date: ${dayjs().format('YYYY-MM-DD')}`}</div>
          </div>
        </div>

        <Table
          dataSource={machines}
          columns={columns}
          rowKey={(row: any) => row.id}
          loading={machinesLoading}
          pagination={false}
        />
      </Card>
    </div>
  )
}

export default AuditReportView
