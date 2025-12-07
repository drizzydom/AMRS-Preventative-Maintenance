import React, { useEffect, useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Card, Typography, Spin, Button } from 'antd'
import apiClient from '../../utils/api'
import dayjs from 'dayjs'

const { Title, Paragraph } = Typography

interface RecordItem {
  id: number
  machine: string
  machineName?: string
  machine_id?: number
  part: string
  partName?: string
  completedDate: string // YYYY-MM-DD
  completedBy?: string
  siteName?: string
  site_id?: number
  notes?: string
  maintenanceType?: string
}

function groupByDate(records: RecordItem[]) {
  const groups: Record<string, RecordItem[]> = {}
  records.forEach((r) => {
    const d = r.completedDate || 'No Date'
    groups[d] = groups[d] || []
    groups[d].push(r)
  })
  return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]))
}

function groupByMachine(records: RecordItem[]) {
  const groups: Record<string, RecordItem[]> = {}
  records.forEach((r) => {
    const key = r.machineName || r.machine || 'Unknown Machine'
    groups[key] = groups[key] || []
    groups[key].push(r)
  })
  return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]))
}

function groupBySite(records: RecordItem[]) {
  const groups: Record<string, RecordItem[]> = {}
  records.forEach((r) => {
    const key = r.siteName || 'No Site'
    groups[key] = groups[key] || []
    groups[key].push(r)
  })
  return Object.entries(groups).sort((a, b) => a[0].localeCompare(b[0]))
}

const MaintenanceReportView: React.FC = () => {
  const [searchParams] = useSearchParams()
  const [loading, setLoading] = useState(true)
  const [records, setRecords] = useState<RecordItem[]>([])
  const [error, setError] = useState<string | null>(null)

  // Parse query params
  const siteId = searchParams.get('site_id') || undefined
  const machineId = searchParams.get('machine_id') || undefined
  const dateFrom = searchParams.get('date_from') || undefined
  const dateTo = searchParams.get('date_to') || undefined
  const groupBy = searchParams.get('group_by') || 'date'
  const reportType = (searchParams.get('report_type') || 'compact') as 'compact' | 'expanded'

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        setError(null)

        // Fetch maintenance history records; page_size large to capture report range
        const resp = await apiClient.get('/api/v1/maintenance/history', {
          params: {
            site_id: siteId || undefined,
            machine_id: machineId ? Number(machineId) : undefined,
            page: 1,
            page_size: 500,
          },
        })

        const payload = resp.data?.data || resp.data || {}
        const fetched: RecordItem[] = (payload.records || []).map((r: any) => ({
          id: r.id,
          machine: r.machine || r.machineName,
          machineName: r.machineName || r.machine,
          machine_id: r.machine_id,
          part: r.part || r.partName,
          partName: r.partName || r.part,
          completedDate: r.completedDate || r.completedDate || '',
          completedBy: r.completedBy,
          siteName: r.siteName || r.site,
          site_id: r.site_id,
          notes: r.notes,
          maintenanceType: r.maintenanceType,
        }))

        // Filter by date range client-side if provided
        let filtered = fetched
        if (dateFrom || dateTo) {
          const from = dateFrom ? dayjs(dateFrom) : null
          const to = dateTo ? dayjs(dateTo) : null
          filtered = fetched.filter((rec) => {
            if (!rec.completedDate) return false
            const d = dayjs(rec.completedDate)
            if (from && d.isBefore(from, 'day')) return false
            if (to && d.isAfter(to, 'day')) return false
            return true
          })
        }

        setRecords(filtered)
      } catch (err: any) {
        console.error('[MaintenanceReportView] Failed to load records', err)
        setError(err.response?.data?.error || err.message || 'Failed to load records')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [siteId, machineId, dateFrom, dateTo])

  const grouped = useMemo(() => {
    if (groupBy === 'machine') return groupByMachine(records)
    if (groupBy === 'site') return groupBySite(records)
    return groupByDate(records)
  }, [records, groupBy])

  const onPrint = () => {
    window.print()
  }

  if (loading) return <div style={{ padding: 24, textAlign: 'center' }}><Spin size="large" /></div>

  const compactRowStyle = { padding: 4, fontSize: '12px' }
  const expandedRowStyle = { padding: 10, fontSize: '14px' }

  return (
    <div style={{ padding: reportType === 'compact' ? 12 : 24 }}>
      <Card style={{ marginBottom: 16 }}>
        <Title level={2}>Maintenance Report</Title>
        <Paragraph type="secondary">Printable client-side report. Use the browser print dialog to print or save as PDF.</Paragraph>
        <div style={{ marginTop: 12 }}>
          <Button type="primary" onClick={onPrint} style={{ marginRight: 8 }}>Print</Button>
        </div>
      </Card>

      {error && (
        <Card style={{ marginBottom: 16 }}>
          <div style={{ color: 'red' }}>{error}</div>
        </Card>
      )}

      {grouped.map(([groupKey, items]) => (
        <Card key={groupKey} style={{ marginBottom: 12 }}>
          <Title level={reportType === 'compact' ? 5 : 4}>{groupKey}</Title>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left', padding: reportType === 'compact' ? 4 : 8 }}>Date</th>
                <th style={{ textAlign: 'left', padding: reportType === 'compact' ? 4 : 8 }}>Machine</th>
                <th style={{ textAlign: 'left', padding: reportType === 'compact' ? 4 : 8 }}>Service</th>
                {reportType === 'expanded' && <th style={{ textAlign: 'left', padding: 8 }}>Completed By</th>}
                {reportType === 'expanded' && <th style={{ textAlign: 'left', padding: 8 }}>Notes</th>}
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id}>
                  <td style={reportType === 'compact' ? compactRowStyle : expandedRowStyle}>{it.completedDate}</td>
                  <td style={reportType === 'compact' ? compactRowStyle : expandedRowStyle}>{it.machineName || it.machine}</td>
                  <td style={reportType === 'compact' ? compactRowStyle : expandedRowStyle}>{it.partName || it.part}</td>
                  {reportType === 'expanded' && <td style={expandedRowStyle}>{it.completedBy}</td>}
                  {reportType === 'expanded' && <td style={{ ...expandedRowStyle, whiteSpace: 'pre-wrap' }}>{it.notes}</td>}
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ))}
    </div>
  )
}

export default MaintenanceReportView
