import React from 'react'
import { Result, Button } from 'antd'

interface State {
  hasError: boolean
  error?: Error | null
}

class ErrorBoundary extends React.Component<{ children: React.ReactNode }, State> {
  constructor(props: { children: React.ReactNode }) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: any) {
    // Log to console for debugging; could be extended to remote logging
    // eslint-disable-next-line no-console
    console.error('[ErrorBoundary] Caught error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 24 }}>
          <Result
            status="error"
            title="Something went wrong"
            subTitle="An unexpected error occurred while loading this page. Check the console for details."
            extra={(
              <Button type="primary" onClick={() => window.location.reload()}>
                Reload
              </Button>
            )}
          />
        </div>
      )
    }

    return this.props.children as React.ReactElement
  }
}

export default ErrorBoundary
