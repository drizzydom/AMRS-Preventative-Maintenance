import React from 'react'
import { CloseOutlined, MinusOutlined, BorderOutlined } from '@ant-design/icons'
import '../styles/titlebar.css'

const TitleBar: React.FC = () => {
  const handleMinimize = () => {
    if (window.electronAPI && window.electronAPI.window) {
      window.electronAPI.window.minimize()
    }
  }

  const handleMaximize = () => {
    if (window.electronAPI && window.electronAPI.window) {
      window.electronAPI.window.maximize()
    }
  }

  const handleClose = () => {
    if (window.electronAPI && window.electronAPI.window) {
      window.electronAPI.window.close()
    }
  }

  return (
    <div className="title-bar">
      <div className="title-bar-drag-region">
        <div className="title-bar-icon">
          <img src="/static/img/logo.png" alt="AMRS" width="16" height="16" />
        </div>
        <div className="title-bar-title">AMRS Maintenance Tracker</div>
      </div>
      <div className="title-bar-controls">
        <button className="title-bar-button minimize" onClick={handleMinimize} title="Minimize">
          <MinusOutlined />
        </button>
        <button className="title-bar-button maximize" onClick={handleMaximize} title="Maximize">
          <BorderOutlined />
        </button>
        <button className="title-bar-button close" onClick={handleClose} title="Close">
          <CloseOutlined />
        </button>
      </div>
    </div>
  )
}

export default TitleBar
