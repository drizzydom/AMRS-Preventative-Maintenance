import React, { useState, useEffect } from 'react'
import { Card, Typography, List, Spin, message, Select, DatePicker, Space, Checkbox, Button } from 'antd'
import dayjs from 'dayjs'
import api from '../../utils/api'

const { Title, Paragraph } = Typography
const { RangePicker } = DatePicker

interface Site {
  id: number
  name: string
}

interface Machine {
  id: number
  name: string
  site_id?: number
}

/**
 * Incremental ReportsPreview: diagnostic -> add machines -> add date controls -> add options -> generate
 */
const ReportsPreview: React.FC = () => {
  const [sites, setSites] = useState<Site[]>([])
  const [loading, setLoading] = useState(true)
  const [errorDetail, setErrorDetail] = useState<string | null>(null)

  // Step: machines
  const [machines, setMachines] = useState<Machine[]>([])
  const [machinesLoading, setMachinesLoading] = useState(false)
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(null)
  const [selectedMachineId, setSelectedMachineId] = useState<number | null>(null)

  // Step: date range
  const [dateRange, setDateRange] = useState<[dayjs.Dayjs, dayjs.Dayjs] | null>([
    dayjs().subtract(30, 'day'),
    dayjs(),
  ])

  // Step: grouping & options
  const [groupBy, setGroupBy] = useState<string>('date')
  const [includeNotes, setIncludeNotes] = useState<boolean>(true)
  const [includePO, setIncludePO] = useState<boolean>(true)
  // Report display type: compact (A) or expanded (C)
  const [reportType, setReportType] = useState<string>('compact')

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const res = await api.get('/api/v1/sites')
        const data = res?.data?.data || res?.data || []
        // API uses {status:'success', data: [...]}
        const sitesData = Array.isArray(data) ? data : (data.sites || [])
        setSites(sitesData)
        setErrorDetail(null)
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('[ReportsPreview] Failed to load sites:', err)
        try {
          const axiosErr = err as any
          const status = axiosErr?.response?.status
          const respData = axiosErr?.response?.data
          setErrorDetail(`Status: ${status || 'unknown'} - ${JSON.stringify(respData)}`)
        } catch (e) {
          setErrorDetail(String(err))
        }
        message.error('Failed to load report options; see details below')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  useEffect(() => {
    // When a site is selected, fetch machines for that site
    const loadMachines = async (siteId: number) => {
      try {
        setMachinesLoading(true)
        const res = await api.get('/api/v1/machines', { params: { site_id: siteId } })
        const data = res?.data?.data || res?.data || []
        const machinesData = Array.isArray(data) ? data : (data.machines || [])
        setMachines(machinesData)
      } catch (err) {
        // eslint-disable-next-line no-console
        console.error('[ReportsPreview] Failed to load machines:', err)
        message.error('Failed to load machines for selected site')
        setMachines([])
      } finally {
        setMachinesLoading(false)
      }
    }

    if (selectedSiteId) {
      loadMachines(selectedSiteId)
    } else {
      setMachines([])
      setSelectedMachineId(null)
    }
  }, [selectedSiteId])

  const generateMaintenanceReport = () => {
    const params = new URLSearchParams()
    if (dateRange && dateRange[0]) params.append('date_from', dateRange[0].format('YYYY-MM-DD'))
    if (dateRange && dateRange[1]) params.append('date_to', dateRange[1].format('YYYY-MM-DD'))
    if (selectedSiteId) params.append('site_id', String(selectedSiteId))
    if (selectedMachineId) params.append('machine_id', String(selectedMachineId))
    params.append('group_by', groupBy || 'date')
    params.append('include_notes', includeNotes ? '1' : '0')
    params.append('include_po', includePO ? '1' : '0')
    params.append('report_type', reportType || 'compact')
    // Open the client-side maintenance report view (React) so printing uses the new UI
    const origin = window.location.origin
    window.open(`${origin}/reports/maintenance/view?${params.toString()}`, '_blank')
  }

  const generateAuditReport = () => {
    const params = new URLSearchParams()
    if (selectedSiteId) params.append('site_id', String(selectedSiteId))
    if (selectedMachineId) params.append('machine_id', String(selectedMachineId))
    if (dateRange && dateRange[0]) params.append('date_from', dateRange[0].format('YYYY-MM-DD'))
    if (dateRange && dateRange[1]) params.append('date_to', dateRange[1].format('YYYY-MM-DD'))
    params.append('report_type', reportType || 'compact')
    const origin = window.location.origin
    window.open(`${origin}/reports/audits/view?${params.toString()}`, '_blank')
  }

  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  return (
    <div style={{ padding: 24 }}>
      <Card style={{ marginBottom: 16 }}>
        <Title level={2}>Reports</Title>
        <Paragraph type="secondary">Generate maintenance, audit, and summary reports. This view is being incrementally enabled.</Paragraph>
      </Card>

      <Card style={{ marginBottom: 16 }}>
        <Title level={4}>Filters</Title>
        {errorDetail && <div style={{ color: 'red', whiteSpace: 'pre-wrap', marginBottom: 12 }}>{errorDetail}</div>}

        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div>
            <div style={{ marginBottom: 8, fontWeight: 600 }}>Site</div>
            <Select
              placeholder="Select a site (or leave blank for all)"
              value={selectedSiteId ?? undefined}
              onChange={(val) => setSelectedSiteId(val ?? null)}
              style={{ minWidth: 260 }}
              allowClear
            >
              {sites.map((s) => (
                <Select.Option key={s.id} value={s.id}>{s.name}</Select.Option>
              ))}
            </Select>
          </div>

          <div>
            <div style={{ marginBottom: 8, fontWeight: 600 }}>Machine</div>
            <Select
              placeholder={selectedSiteId ? 'Select a machine' : 'Select a site first'}
              value={selectedMachineId ?? undefined}
              onChange={(val) => setSelectedMachineId(val ?? null)}
              loading={machinesLoading}
              style={{ minWidth: 260 }}
              allowClear
              disabled={!selectedSiteId}
            >
              {machines.map((m) => (
                <Select.Option key={m.id} value={m.id}>{m.name}</Select.Option>
              ))}
            </Select>
          </div>

          <div>
            <div style={{ marginBottom: 8, fontWeight: 600 }}>Date Range</div>
            <RangePicker
              value={dateRange as any}
              onChange={(vals) => setDateRange(vals as any)}
              format="YYYY-MM-DD"
            />
          </div>

          <div>
            <Space>
              <div style={{ fontWeight: 600 }}>Group By</div>
              <Select value={groupBy} onChange={setGroupBy} style={{ minWidth: 160 }}>
                <Select.Option value="date">Date</Select.Option>
                <Select.Option value="machine">Machine</Select.Option>
                <Select.Option value="site">Site</Select.Option>
                <Select.Option value="service">Service/Part</Select.Option>
              </Select>
            </Space>
          </div>

          <div>
            <Space>
              <Checkbox checked={includeNotes} onChange={(e) => setIncludeNotes(e.target.checked)}>Include Notes</Checkbox>
              <Checkbox checked={includePO} onChange={(e) => setIncludePO(e.target.checked)}>Include PO / Work Order</Checkbox>
            </Space>
          </div>

          <div>
            <Space>
              <Button type="primary" onClick={generateMaintenanceReport}>Generate Maintenance Report</Button>
              <Button onClick={generateAuditReport}>Generate Audit Report</Button>
            </Space>
          </div>
        </Space>
      </Card>

      <Card style={{ marginTop: 12, marginBottom: 16 }}>
        <Title level={5}>Report Layout</Title>
        <div style={{ marginTop: 8 }}>
          <Select value={reportType} onChange={(v) => setReportType(v)} style={{ minWidth: 220 }}>
            <Select.Option value="compact">A — Compact (densely packed)</Select.Option>
            <Select.Option value="expanded">C — Expanded (detailed)</Select.Option>
          </Select>
        </div>
      </Card>

      <Card>
        <Title level={4}>Available Sites</Title>
        <List
          dataSource={sites}
          renderItem={(site: Site) => (
            <List.Item key={site.id}>{site.name || `Site ${site.id}`}</List.Item>
          )}
        />
      </Card>
    </div>
  )
}

export default ReportsPreview
