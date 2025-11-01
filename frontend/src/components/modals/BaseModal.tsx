import React from 'react'
import { Modal } from 'antd'
import type { ModalProps } from 'antd'
import '../../styles/modals.css'

interface BaseModalProps extends ModalProps {
  children: React.ReactNode
}

/**
 * Enhanced base modal component with high-contrast overlay and backdrop blur
 * Follows Phase 2.7 requirements for improved visibility and focus
 */
const BaseModal: React.FC<BaseModalProps> = ({ children, ...props }) => {
  return (
    <Modal
      {...props}
      className={`base-modal ${props.className || ''}`}
      maskStyle={{
        backdropFilter: 'blur(4px)',
        backgroundColor: 'rgba(0, 0, 0, 0.65)',
      }}
      centered
      destroyOnClose
    >
      {children}
    </Modal>
  )
}

export default BaseModal
