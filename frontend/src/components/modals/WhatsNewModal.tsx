import React from 'react';
import { Button, Typography, List, Tag, Divider } from 'antd';
import BaseModal from './BaseModal';
import changelogData from '../../data/changelog.json';

const { Title, Text, Paragraph } = Typography;

interface WhatsNewModalProps {
  visible: boolean;
  onClose: () => void;
  currentVersion: string;
}

// Helper to render text with bold markdown (**text**)
const renderItemText = (text: string) => {
  const parts = text.split('**');
  return (
    <span>
      {parts.map((part, index) => 
        index % 2 === 1 ? <strong key={index}>{part}</strong> : part
      )}
    </span>
  );
};

const WhatsNewModal: React.FC<WhatsNewModalProps> = ({ visible, onClose, currentVersion }) => {
  // Find the changelog entry for the current version
  const currentRelease = changelogData.find(entry => entry.version === currentVersion);
  
  // If no specific entry for this version, show the latest one or a generic message
  const releaseToShow = currentRelease || changelogData[0];

  // Helper to render content based on structure (sections vs flat list)
  const renderContent = () => {
    if (!releaseToShow) return null;

    // New structure with sections
    if ('sections' in releaseToShow && Array.isArray((releaseToShow as any).sections)) {
      return (
        <div style={{ maxHeight: '60vh', overflowY: 'auto', paddingRight: '8px' }}>
          {(releaseToShow as any).sections.map((section: any, index: number) => (
            <div key={index} style={{ marginBottom: '24px' }}>
              <Title level={5} style={{ marginBottom: '8px', color: '#1890ff' }}>
                {section.title}
              </Title>
              <List
                size="small"
                dataSource={section.items}
                renderItem={(item: string) => (
                  <List.Item style={{ padding: '4px 0', border: 'none' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px' }}>
                      <span style={{ marginTop: '4px', fontSize: '6px' }}>●</span>
                      <Text>{renderItemText(item)}</Text>
                    </div>
                  </List.Item>
                )}
              />
            </div>
          ))}
        </div>
      );
    }

    // Legacy structure (flat list)
    if ('changes' in releaseToShow && Array.isArray((releaseToShow as any).changes)) {
      return (
        <List
          dataSource={(releaseToShow as any).changes}
          renderItem={(item: string) => (
            <List.Item style={{ padding: '8px 0' }}>
              <Text>• {item}</Text>
            </List.Item>
          )}
        />
      );
    }

    return null;
  };

  return (
    <BaseModal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span>What's New</span>
          <Tag color="blue">v{releaseToShow?.version || currentVersion}</Tag>
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button key="close" type="primary" onClick={onClose}>
          Got it!
        </Button>,
      ]}
      width={700}
    >
      {releaseToShow ? (
        <div>
          <div style={{ marginBottom: '16px' }}>
            <Title level={4} style={{ margin: 0 }}>{releaseToShow.title}</Title>
            <Text type="secondary">Released on {releaseToShow.date}</Text>
          </div>
          
          <Divider style={{ margin: '12px 0' }} />
          
          {renderContent()}
          
          <div style={{ marginTop: '24px', backgroundColor: '#f5f5f5', padding: '12px', borderRadius: '6px' }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              We're constantly improving AMRS Maintenance Tracker. 
              Thank you for your feedback and support!
            </Text>
          </div>
        </div>
      ) : (
        <Paragraph>
          Welcome to version {currentVersion}! We've made some under-the-hood improvements to make your experience better.
        </Paragraph>
      )}
    </BaseModal>
  );
};

export default WhatsNewModal;
