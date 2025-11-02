import React from 'react'
import { 
  PlusOutlined, 
  ReloadOutlined, 
  ExportOutlined, 
  PrinterOutlined,
  FilterOutlined,
  SearchOutlined,
  SettingOutlined
} from '@ant-design/icons'
import { Button, Space, Tooltip } from 'antd'
import '../styles/toolbar.css'

interface ToolbarProps {
  onAdd?: () => void
  onRefresh?: () => void
  onExport?: () => void
  onPrint?: () => void
  onFilter?: () => void
  onSearch?: () => void
  onSettings?: () => void
  showAdd?: boolean
  showRefresh?: boolean
  showExport?: boolean
  showPrint?: boolean
  showFilter?: boolean
  showSearch?: boolean
  showSettings?: boolean
  title?: string
  customActions?: React.ReactNode
}

const Toolbar: React.FC<ToolbarProps> = ({
  onAdd,
  onRefresh,
  onExport,
  onPrint,
  onFilter,
  onSearch,
  onSettings,
  showAdd = true,
  showRefresh = true,
  showExport = false,
  showPrint = false,
  showFilter = false,
  showSearch = false,
  showSettings = false,
  title,
  customActions
}) => {
  return (
    <div className="toolbar">
      <div className="toolbar-left">
        {title && <h2 className="toolbar-title">{title}</h2>}
      </div>
      <div className="toolbar-right">
        <Space size="small">
          {showSearch && onSearch && (
            <Tooltip title="Search (Ctrl+F)">
              <Button 
                icon={<SearchOutlined />} 
                onClick={onSearch}
                className="toolbar-button"
              >
                Search
              </Button>
            </Tooltip>
          )}
          
          {showFilter && onFilter && (
            <Tooltip title="Filter">
              <Button 
                icon={<FilterOutlined />} 
                onClick={onFilter}
                className="toolbar-button"
              >
                Filter
              </Button>
            </Tooltip>
          )}
          
          {showAdd && onAdd && (
            <Tooltip title="Add New (Ctrl+N)">
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={onAdd}
                className="toolbar-button toolbar-button-primary"
              >
                Add New
              </Button>
            </Tooltip>
          )}
          
          {showRefresh && onRefresh && (
            <Tooltip title="Refresh (F5)">
              <Button 
                icon={<ReloadOutlined />} 
                onClick={onRefresh}
                className="toolbar-button"
              >
                Refresh
              </Button>
            </Tooltip>
          )}
          
          {showExport && onExport && (
            <Tooltip title="Export">
              <Button 
                icon={<ExportOutlined />} 
                onClick={onExport}
                className="toolbar-button"
              >
                Export
              </Button>
            </Tooltip>
          )}
          
          {showPrint && onPrint && (
            <Tooltip title="Print (Ctrl+P)">
              <Button 
                icon={<PrinterOutlined />} 
                onClick={onPrint}
                className="toolbar-button"
              >
                Print
              </Button>
            </Tooltip>
          )}
          
          {showSettings && onSettings && (
            <Tooltip title="Settings">
              <Button 
                icon={<SettingOutlined />} 
                onClick={onSettings}
                className="toolbar-button"
              />
            </Tooltip>
          )}
          
          {customActions}
        </Space>
      </div>
    </div>
  )
}

export default Toolbar
