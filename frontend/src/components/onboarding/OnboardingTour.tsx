import React, { useState, useEffect } from 'react'
import { Modal, Steps, Button, Typography, Card, Space, Row, Col, Divider } from 'antd'
import {
  DashboardOutlined,
  ToolOutlined,
  CalendarOutlined,
  SettingOutlined,
  AuditOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  RocketOutlined,
  BulbOutlined,
} from '@ant-design/icons'
import '../../styles/onboarding.css'

const { Title, Text, Paragraph } = Typography
const { Step } = Steps

interface OnboardingTourProps {
  open: boolean
  onClose: () => void
  onComplete: () => void
}

interface TourStep {
  title: string
  icon: React.ReactNode
  description: string
  tips: string[]
  image?: string
}

const tourSteps: TourStep[] = [
  {
    title: 'Welcome to AMRS Maintenance Tracker',
    icon: <RocketOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
    description: 'Your comprehensive solution for preventative maintenance management. Let\'s take a quick tour of the key features.',
    tips: [
      'Track maintenance schedules for all your machines',
      'Never miss an overdue service with automatic alerts',
      'Generate compliance reports with a single click',
    ],
  },
  {
    title: 'Dashboard Overview',
    icon: <DashboardOutlined style={{ fontSize: 48, color: '#1890ff' }} />,
    description: 'The Dashboard provides an at-a-glance view of your maintenance status across all sites and machines.',
    tips: [
      'View overdue and upcoming maintenance tasks',
      'Filter by site to focus on specific locations',
      'Quick access to emergency maintenance logging',
    ],
  },
  {
    title: 'Managing Machines',
    icon: <ToolOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
    description: 'Add and manage your equipment with detailed service schedules and maintenance history.',
    tips: [
      'Organize machines by site and type',
      'Define custom services for each machine',
      'Track services and maintenance intervals automatically',
    ],
  },
  {
    title: 'Recording Maintenance',
    icon: <CalendarOutlined style={{ fontSize: 48, color: '#faad14' }} />,
    description: 'Log maintenance activities quickly with our streamlined recording process.',
    tips: [
      'Record scheduled maintenance completions',
      'Add emergency repairs with detailed notes',
      'Attach work orders and P.O. numbers for tracking',
    ],
  },
  {
    title: 'Audit & Compliance',
    icon: <AuditOutlined style={{ fontSize: 48, color: '#722ed1' }} />,
    description: 'Stay compliant with comprehensive audit checklists and automated tracking.',
    tips: [
      'Create custom audit checklists for your needs',
      'Track audit completion status and scores',
      'Generate audit reports for regulatory compliance',
    ],
  },
  {
    title: 'Reports & Analytics',
    icon: <FileTextOutlined style={{ fontSize: 48, color: '#13c2c2' }} />,
    description: 'Generate detailed reports for management reviews and compliance documentation.',
    tips: [
      'Choose between Compact and Detailed report formats',
      'Export reports to PDF for sharing',
      'Print reports directly from the application',
    ],
  },
  {
    title: 'You\'re All Set!',
    icon: <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />,
    description: 'You\'re ready to start managing your maintenance operations efficiently.',
    tips: [
      'Visit Settings to customize your preferences',
      'Check the Help section for detailed guides',
      'Contact support if you need assistance',
    ],
  },
]

const OnboardingTour: React.FC<OnboardingTourProps> = ({ open, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [animating, setAnimating] = useState(false)

  const handleNext = () => {
    if (currentStep < tourSteps.length - 1) {
      setAnimating(true)
      setTimeout(() => {
        setCurrentStep(currentStep + 1)
        setAnimating(false)
      }, 200)
    } else {
      handleComplete()
    }
  }

  const handlePrev = () => {
    if (currentStep > 0) {
      setAnimating(true)
      setTimeout(() => {
        setCurrentStep(currentStep - 1)
        setAnimating(false)
      }, 200)
    }
  }

  const handleComplete = () => {
    localStorage.setItem('amrs_onboarding_complete', 'true')
    onComplete()
    onClose()
  }

  const handleSkip = () => {
    localStorage.setItem('amrs_onboarding_complete', 'true')
    onClose()
  }

  const currentTourStep = tourSteps[currentStep]

  return (
    <Modal
      open={open}
      onCancel={handleSkip}
      footer={null}
      width={700}
      centered
      className="onboarding-modal"
      closable={true}
      maskClosable={false}
    >
      <div className="onboarding-content">
        {/* Progress Steps */}
        <Steps current={currentStep} size="small" className="onboarding-steps">
          {tourSteps.map((step, index) => (
            <Step key={index} />
          ))}
        </Steps>

        <Divider />

        {/* Step Content */}
        <div className={`step-content ${animating ? 'animating' : ''}`}>
          <div className="step-icon-wrapper">
            {currentTourStep.icon}
          </div>

          <Title level={3} className="step-title">
            {currentTourStep.title}
          </Title>

          <Paragraph className="step-description">
            {currentTourStep.description}
          </Paragraph>

          <Card className="tips-card" size="small">
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Text strong>
                <BulbOutlined style={{ marginRight: 8, color: '#faad14' }} />
                Quick Tips
              </Text>
              <ul className="tips-list">
                {currentTourStep.tips.map((tip, index) => (
                  <li key={index}>
                    <Text>{tip}</Text>
                  </li>
                ))}
              </ul>
            </Space>
          </Card>
        </div>

        <Divider />

        {/* Navigation Buttons */}
        <Row justify="space-between" align="middle">
          <Col>
            <Button onClick={handleSkip} type="text">
              Skip Tour
            </Button>
          </Col>
          <Col>
            <Space>
              <Button 
                onClick={handlePrev} 
                disabled={currentStep === 0}
              >
                Previous
              </Button>
              <Button 
                type="primary" 
                onClick={handleNext}
                icon={currentStep === tourSteps.length - 1 ? <CheckCircleOutlined /> : undefined}
              >
                {currentStep === tourSteps.length - 1 ? 'Get Started' : 'Next'}
              </Button>
            </Space>
          </Col>
        </Row>
      </div>
    </Modal>
  )
}

export default OnboardingTour
