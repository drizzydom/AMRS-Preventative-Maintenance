import React, { useEffect, useState } from 'react'
import { Modal, Checkbox, Button, message, Space, List, Typography } from 'antd'
import { CheckOutlined } from '@ant-design/icons'
import apiClient from '../../utils/api'

const { Text } = Typography

interface Machine {
  id: number
  name: string
  model: string
  serial_number: string
  completed: boolean
  completed_at?: string
  completed_by?: number
}

interface AuditCompletionModalProps {
  open: boolean
  onClose: () => void
  auditId: number | null
  auditName: string
  onComplete: () => void
}

const AuditCompletionModal: React.FC<AuditCompletionModalProps> = ({
  open,
  onClose,
  auditId,
  auditName,
  onComplete,
}) => {
  const [machines, setMachines] = useState<Machine[]>([])
  const [selectedMachines, setSelectedMachines] = useState<number[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (open && auditId) {
      fetchMachines()
    }
  }, [open, auditId])

  const fetchMachines = async () => {
    if (!auditId) return

    try {
      setLoading(true)
      const response = await apiClient.get(`/api/v1/audits/${auditId}/machines`)
      const machinesData = response.data.data

      setMachines(machinesData)

      // Pre-select completed machines (they can't be unchecked)
      const completedIds = machinesData
        .filter((m: Machine) => m.completed)
        .map((m: Machine) => m.id)
      setSelectedMachines(completedIds)
    } catch (error: any) {
      console.error('Failed to load machines:', error)
      message.error('Failed to load machines for audit task')
    } finally {
      setLoading(false)
    }
  }

  const handleMachineToggle = (machineId: number, isCompleted: boolean) => {
    if (isCompleted) {
      // Can't uncheck completed machines
      return
    }

    setSelectedMachines((prev) =>
      prev.includes(machineId)
        ? prev.filter((id) => id !== machineId)
        : [...prev, machineId]
    )
  }

  const handleSubmit = async () => {
    if (selectedMachines.length === 0) {
      message.warning('Please select at least one machine to complete')
      return
    }

    try {
      setSubmitting(true)

      // Only submit machines that are not already completed
      const machineIdsToComplete = selectedMachines.filter((id) => {
        const machine = machines.find((m) => m.id === id)
        return machine && !machine.completed
      })

      if (machineIdsToComplete.length === 0) {
        message.info('All selected machines are already completed')
        onClose()
        return
      }

      console.log('[AUDIT] Submitting completion for audit:', auditId, 'machines:', machineIdsToComplete)
      
      const response = await apiClient.post(`/api/v1/audits/${auditId}/complete`, {
        machine_ids: machineIdsToComplete,
      })
      
      console.log('[AUDIT] Completion response:', response.data)

      message.success(`Successfully completed ${machineIdsToComplete.length} audit task(s)`)
      
      console.log('[AUDIT] Calling onComplete callback')
      await onComplete()
      
      console.log('[AUDIT] Closing modal')
      onClose()
    } catch (error: any) {
      console.error('[AUDIT] Failed to complete audit:', error)
      console.error('[AUDIT] Error response:', error.response?.data)
      console.error('[AUDIT] Error status:', error.response?.status)
      const errorMsg = error.response?.data?.error || 'Failed to complete audit task'
      message.error(errorMsg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleCancel = () => {
    setSelectedMachines([])
    onClose()
  }

  const incompleteMachines = machines.filter((m) => !m.completed)
  const completedMachines = machines.filter((m) => m.completed)

  return (
    <Modal
      title={`Complete Audit: ${auditName}`}
      open={open}
      onCancel={handleCancel}
      width={600}
      footer={[
        <Button key="cancel" onClick={handleCancel}>
          Cancel
        </Button>,
        <Button
          key="submit"
          type="primary"
          icon={<CheckOutlined />}
          onClick={handleSubmit}
          loading={submitting}
          disabled={loading || incompleteMachines.length === 0}
        >
          Complete Selected
        </Button>,
      ]}
    >
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Text type="secondary">
          Check off the machines you have completed the audit for today.
        </Text>

        {loading ? (
          <Text>Loading machines...</Text>
        ) : (
          <>
            {incompleteMachines.length > 0 && (
              <>
                <Text strong>Machines to Complete:</Text>
                <List
                  size="small"
                  dataSource={incompleteMachines}
                  renderItem={(machine) => (
                    <List.Item>
                      <Checkbox
                        checked={selectedMachines.includes(machine.id)}
                        onChange={() => handleMachineToggle(machine.id, false)}
                      >
                        <Space>
                          <Text>{machine.name}</Text>
                          {machine.model && (
                            <Text type="secondary">({machine.model})</Text>
                          )}
                        </Space>
                      </Checkbox>
                    </List.Item>
                  )}
                />
              </>
            )}

            {completedMachines.length > 0 && (
              <>
                <Text strong style={{ marginTop: 16 }}>
                  Already Completed Today:
                </Text>
                <List
                  size="small"
                  dataSource={completedMachines}
                  renderItem={(machine) => (
                    <List.Item>
                      <Checkbox checked disabled>
                        <Space>
                          <Text delete type="success">
                            {machine.name}
                          </Text>
                          {machine.model && (
                            <Text type="secondary">({machine.model})</Text>
                          )}
                          <CheckOutlined style={{ color: '#52c41a' }} />
                        </Space>
                      </Checkbox>
                    </List.Item>
                  )}
                />
              </>
            )}

            {incompleteMachines.length === 0 && completedMachines.length > 0 && (
              <Text type="success" strong>
                All machines completed for today! ✓
              </Text>
            )}
          </>
        )}
      </Space>
    </Modal>
  )
}

export default AuditCompletionModal
