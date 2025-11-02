import React, { useEffect, useState } from 'react'
import { Progress, Typography, Button, Space } from 'antd'
import { LoadingOutlined, CloseOutlined } from '@ant-design/icons'
import '../styles/splash.css'

const { Title, Text } = Typography

interface SplashScreenProps {
  onComplete?: () => void
}

const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const [progress, setProgress] = useState(0)
  const [message, setMessage] = useState('Initializing...')
  const [canCancel, setCanCancel] = useState(false)

  useEffect(() => {
    // Listen for progress updates from Electron main process
    if (window.electronAPI?.onProgressUpdate) {
      window.electronAPI.onProgressUpdate((newProgress: number, newMessage: string) => {
        setProgress(newProgress)
        setMessage(newMessage)
        
        // Allow cancel after initial setup
        if (newProgress > 10) {
          setCanCancel(true)
        }
        
        // Complete when done
        if (newProgress >= 100) {
          setTimeout(() => {
            onComplete?.()
          }, 500)
        }
      })
    }

    // Fallback simulation if Electron API not available
    if (!window.electronAPI) {
      simulateProgress()
    }

    return () => {
      if (window.electronAPI?.removeProgressListener) {
        window.electronAPI.removeProgressListener()
      }
    }
  }, [onComplete])

  const simulateProgress = () => {
    const steps = [
      { progress: 10, message: 'Loading configuration...', delay: 500 },
      { progress: 25, message: 'Initializing database...', delay: 800 },
      { progress: 40, message: 'Loading modules...', delay: 600 },
      { progress: 60, message: 'Preparing UI components...', delay: 700 },
      { progress: 80, message: 'Finalizing setup...', delay: 500 },
      { progress: 100, message: 'Ready!', delay: 400 },
    ]

    let currentStep = 0
    
    const executeStep = () => {
      if (currentStep < steps.length) {
        const step = steps[currentStep]
        setProgress(step.progress)
        setMessage(step.message)
        setCanCancel(step.progress > 10)
        currentStep++
        setTimeout(executeStep, step.delay)
      } else {
        setTimeout(() => onComplete?.(), 500)
      }
    }

    executeStep()
  }

  const handleCancel = () => {
    if (window.electronAPI?.close) {
      window.electronAPI.close()
    } else {
      window.close()
    }
  }

  return (
    <div className="splash-screen">
      <div className="splash-content">
        <div className="splash-logo">
          <img src="/favicon.ico" alt="AMRS Logo" width="64" height="64" />
        </div>
        
        <Title level={2} className="splash-title">
          AMRS Maintenance Tracker
        </Title>
        
        <div className="splash-progress">
          <Progress
            percent={progress}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
            trailColor="#f0f0f0"
            strokeWidth={8}
            showInfo={false}
          />
        </div>
        
        <Space direction="vertical" align="center" className="splash-status">
          <Space>
            <LoadingOutlined style={{ fontSize: 16 }} spin />
            <Text className="splash-message">{message}</Text>
          </Space>
          <Text type="secondary" className="splash-percent">
            {progress}%
          </Text>
        </Space>

        {canCancel && progress < 100 && (
          <Button
            className="splash-cancel"
            type="text"
            icon={<CloseOutlined />}
            onClick={handleCancel}
          >
            Cancel
          </Button>
        )}

        <div className="splash-footer">
          <Text type="secondary">Version 1.4.6</Text>
        </div>
      </div>
    </div>
  )
}

export default SplashScreen
