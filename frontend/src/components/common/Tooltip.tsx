import React from 'react'
import { Tooltip as AntTooltip } from 'antd'

interface TooltipProps {
  shortcut?: string
  title?: React.ReactNode
  children?: React.ReactNode
  placement?: 'top' | 'bottom' | 'left' | 'right'
  [key: string]: any
}

/**
 * Enhanced tooltip component with keyboard shortcut support
 * Phase 2.8 - Tooltip & Onboarding System
 */
const Tooltip: React.FC<TooltipProps> = ({ shortcut, title, children, ...props }) => {
  const enhancedTitle = shortcut ? (
    <span>
      {title}
      <span style={{ marginLeft: 8, opacity: 0.7, fontSize: '11px' }}>
        ({shortcut})
      </span>
    </span>
  ) : title

  return (
    <AntTooltip
      {...props}
      title={enhancedTitle}
      mouseEnterDelay={0.3}
      placement={props.placement || 'top'}
    >
      {children}
    </AntTooltip>
  )
}

export default Tooltip
