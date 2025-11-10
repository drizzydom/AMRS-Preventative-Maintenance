import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

/**
 * Global keyboard shortcuts hook
 * Implements common shortcuts for desktop app UX
 */
export const useKeyboardShortcuts = () => {
  const navigate = useNavigate()

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Detect OS for correct modifier key
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0
      const ctrlKey = isMac ? e.metaKey : e.ctrlKey

      // Ctrl/Cmd + N - New item (context-aware)
      if (ctrlKey && e.key === 'n') {
        e.preventDefault()
        console.log('[Keyboard] New item shortcut triggered')
        window.dispatchEvent(new CustomEvent('keyboard-new'))
      }

      // Ctrl/Cmd + F - Focus search bar
      if (ctrlKey && e.key === 'f') {
        e.preventDefault()
        const searchInput = document.querySelector('input[type="search"]') as HTMLInputElement
        if (searchInput) {
          searchInput.focus()
          searchInput.select()
        }
      }

      // Ctrl/Cmd + R - Refresh current page data
      if (ctrlKey && e.key === 'r') {
        e.preventDefault()
        console.log('[Keyboard] Refresh shortcut triggered')
        window.dispatchEvent(new CustomEvent('keyboard-refresh'))
      }

      // Ctrl/Cmd + S - Save (prevent default browser save)
      if (ctrlKey && e.key === 's') {
        e.preventDefault()
        console.log('[Keyboard] Save shortcut triggered')
        window.dispatchEvent(new CustomEvent('keyboard-save'))
      }

      // Ctrl/Cmd + P - Print (already handled by browser, but log it)
      if (ctrlKey && e.key === 'p') {
        console.log('[Keyboard] Print shortcut triggered (browser default)')
        // Let browser handle the print dialog
      }

      // Escape - Close modal/cancel action
      if (e.key === 'Escape') {
        console.log('[Keyboard] Escape pressed')
        window.dispatchEvent(new CustomEvent('keyboard-escape'))
      }

      // Ctrl/Cmd + 1-9 - Navigate to pages
      if (ctrlKey && e.key >= '1' && e.key <= '9') {
        e.preventDefault()
        const pageMap: { [key: string]: string } = {
          '1': '/dashboard',
          '2': '/sites',
          '3': '/machines',
          '4': '/maintenance',
          '5': '/audits',
          '6': '/users',
        }
        const path = pageMap[e.key]
        if (path) {
          console.log(`[Keyboard] Navigate to ${path}`)
          navigate(path)
        }
      }

      // F1 - Help (could open documentation)
      if (e.key === 'F1') {
        e.preventDefault()
        console.log('[Keyboard] Help shortcut triggered')
        window.dispatchEvent(new CustomEvent('keyboard-help'))
      }
    }

    // Attach listener
    window.addEventListener('keydown', handleKeyDown)

    // Cleanup on unmount
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [navigate])
}
