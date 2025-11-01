# Manual Steps Required for UI/UX Overhaul Completion

This document outlines the manual steps that need to be taken to complete the UI/UX overhaul project. These items require human intervention, testing, or platform-specific configurations that cannot be fully automated.

**Last Updated:** November 1, 2025  
**Current Progress:** 45% Complete

---

## 🔧 Priority 1: Critical Integration Steps

### 1.1 Electron Main Process Integration
**Phase:** 1.2, 1.4, 1.5  
**Difficulty:** Medium  
**Time Estimate:** 2-3 hours

**What:** Integrate React frontend with Electron window controls and splash screen.

**Steps:**

1. **Update main.js for frameless window:**
   ```javascript
   // In main.js, update createWindow function
   mainWindow = new BrowserWindow({
     width: 1400,
     height: 900,
     frame: false,  // Add this line
     titleBarStyle: 'hidden',
     webPreferences: {
       nodeIntegration: false,
       contextIsolation: true,
       preload: path.join(__dirname, 'main-preload.js')
     }
   })
   ```

2. **Add IPC handlers for window controls:**
   ```javascript
   // Add to main.js
   const { ipcMain } = require('electron')
   
   ipcMain.on('minimize-window', () => {
     if (mainWindow) mainWindow.minimize()
   })
   
   ipcMain.on('maximize-window', () => {
     if (mainWindow) {
       if (mainWindow.isMaximized()) {
         mainWindow.unmaximize()
       } else {
         mainWindow.maximize()
       }
     }
   })
   
   ipcMain.on('close-window', () => {
     if (mainWindow) mainWindow.close()
   })
   ```

3. **Update main-preload.js to expose IPC:**
   ```javascript
   // Add to main-preload.js
   const { contextBridge, ipcRenderer } = require('electron')
   
   contextBridge.exposeInMainWorld('electronAPI', {
     minimize: () => ipcRenderer.send('minimize-window'),
     maximize: () => ipcRenderer.send('maximize-window'),
     close: () => ipcRenderer.send('close-window'),
   })
   ```

4. **Integrate splash screen progress tracking:**
   ```javascript
   // In main.js, send progress updates
   function updateSplashProgress(message, progress) {
     if (splashWindow && !splashWindow.isDestroyed()) {
       splashWindow.webContents.send('splash-progress', { message, progress })
     }
   }
   
   // Use throughout startup process
   updateSplashProgress('Loading configuration...', 10)
   updateSplashProgress('Initializing database...', 30)
   // etc.
   ```

5. **Update splash-preload.js:**
   ```javascript
   // Add to splash-preload.js
   contextBridge.exposeInMainWorld('electronAPI', {
     onProgressUpdate: (callback) => {
       ipcRenderer.on('splash-progress', (event, data) => {
         callback(data.progress, data.message)
       })
     },
     removeProgressListener: () => {
       ipcRenderer.removeAllListeners('splash-progress')
     }
   })
   ```

**Files to modify:**
- `main.js`
- `main-preload.js`
- `splash-preload.js`

**Testing:**
- Build the application and verify window controls work
- Verify splash screen shows progress
- Test on all platforms (Windows, macOS, Linux)

---

### 1.2 React Frontend Production Build
**Phase:** 4.4  
**Difficulty:** Medium  
**Time Estimate:** 1-2 hours

**What:** Configure production builds to serve React frontend.

**Steps:**

1. **Build React frontend:**
   ```bash
   cd frontend
   npm run build
   ```

2. **Update main.js to serve React build in production:**
   ```javascript
   // In main.js, update loadURL
   if (process.env.NODE_ENV === 'development') {
     mainWindow.loadURL('http://localhost:3000')
   } else {
     // Serve the built React app
     mainWindow.loadFile(path.join(__dirname, 'frontend', 'dist', 'index.html'))
   }
   ```

3. **Update electron-builder configs to include React build:**
   ```javascript
   // In electron-builder-win10.js, electron-builder-macos.js, electron-builder-linux.js
   module.exports = {
     files: [
       'main.js',
       'main-preload.js',
       'frontend/dist/**/*',  // Add this line
       // ... other files
     ]
   }
   ```

4. **Test production build:**
   ```bash
   npm run build:win10  # or build:mac, build:linux
   ```

**Files to modify:**
- `main.js`
- `electron-builder-win10.js`
- `electron-builder-macos.js`
- `electron-builder-linux.js`

**Testing:**
- Build application for each platform
- Verify React app loads in production
- Test all features in built application

---

### 1.3 Flask API Integration Testing
**Phase:** 4.3  
**Difficulty:** Medium  
**Time Estimate:** 3-4 hours

**What:** Test and validate REST API endpoints with real database.

**Steps:**

1. **Start Flask development server:**
   ```bash
   python app.py
   ```

2. **Start React development server:**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test authentication flow:**
   - Navigate to http://localhost:3000/login
   - Try logging in with test credentials
   - Verify token/session is set
   - Check that protected routes work

4. **Test each API endpoint:**
   - GET /api/v1/dashboard
   - GET /api/v1/machines
   - GET /api/v1/maintenance
   - GET /api/v1/sites
   - GET /api/v1/auth/me

5. **Check browser console for errors:**
   - Open DevTools (F12)
   - Check Console tab for errors
   - Check Network tab for failed requests

6. **Verify data transformations:**
   - Ensure API responses match frontend expectations
   - Check date formats
   - Verify relationships (site names, etc.)

7. **Test error handling:**
   - Try invalid login credentials
   - Test with missing data
   - Verify error messages display correctly

**Common Issues to Fix:**
- Model attribute names might not match (e.g., `serial_number` vs `serial`)
- Date formatting differences
- Null/undefined handling
- Missing relationships

**Files to potentially modify:**
- `api_v1.py` - Adjust data transformations
- Frontend API calls - Adjust expected data structure

---

## 🧪 Priority 2: Testing & Validation

### 2.1 Accessibility Testing with Screen Readers
**Phase:** 3.3  
**Difficulty:** Medium  
**Time Estimate:** 2-3 hours

**What:** Verify WCAG 2.1 AA compliance using screen readers.

**Steps:**

1. **Windows - NVDA:**
   - Download NVDA: https://www.nvaccess.org/download/
   - Launch application
   - Navigate through all pages using Tab key
   - Verify all elements are announced
   - Test form inputs and buttons

2. **macOS - VoiceOver:**
   - Enable VoiceOver: Cmd+F5
   - Navigate with VoiceOver commands
   - Test all interactive elements
   - Verify proper announcements

3. **Check for issues:**
   - Missing alt text on images
   - Buttons without labels
   - Form inputs without labels
   - Missing ARIA roles
   - Improper heading structure

4. **Verify keyboard navigation:**
   - Tab through all interactive elements
   - Verify focus indicators are visible
   - Test Esc to close modals
   - Test Enter/Space to activate buttons

5. **Color contrast testing:**
   - Use browser DevTools Accessibility panel
   - Check all text meets 4.5:1 contrast ratio
   - Verify in high-contrast mode

**Files to potentially modify:**
- Add `aria-label` attributes where needed
- Add proper heading hierarchy
- Ensure all buttons have accessible names

---

### 2.2 Cross-Platform Build Testing
**Phase:** 4.4  
**Difficulty:** High  
**Time Estimate:** 4-6 hours

**What:** Build and test application on all supported platforms.

**Steps:**

1. **Windows 10/11 Build:**
   ```bash
   npm run build:win10
   ```
   - Install on Windows machine
   - Test all features
   - Verify window controls work
   - Check file paths are correct
   - Test auto-update if enabled

2. **macOS Build:**
   ```bash
   npm run build:mac
   ```
   - Install on macOS machine
   - Test application signing
   - Verify Gatekeeper compatibility
   - Test all features
   - Check menu bar integration

3. **Linux Build:**
   ```bash
   npm run build:linux
   ```
   - Test on Ubuntu/Debian
   - Verify desktop file integration
   - Test all features
   - Check permissions

4. **Common issues to watch for:**
   - Path separators (Windows vs Unix)
   - File permissions
   - SQLite database access
   - Python interpreter location
   - Resource file paths

**Documentation to update:**
- Build instructions in README
- Platform-specific notes
- Known issues

---

## 🔄 Priority 3: Feature Completion

### 3.1 Implement Remaining API Endpoints
**Phase:** 4.3  
**Difficulty:** Medium  
**Time Estimate:** 4-5 hours

**What:** Add POST/PUT/DELETE endpoints for all resources.

**Location:** `api_v1.py`

**Endpoints to implement:**

```python
# Machines
@api_v1.route('/machines', methods=['POST'])
@api_login_required
def api_create_machine():
    # Implement machine creation
    pass

@api_v1.route('/machines/<int:id>', methods=['PUT'])
@api_login_required
def api_update_machine(id):
    # Implement machine update
    pass

@api_v1.route('/machines/<int:id>', methods=['DELETE'])
@api_login_required
def api_delete_machine(id):
    # Implement machine deletion
    pass

# Maintenance
@api_v1.route('/maintenance', methods=['POST'])
@api_login_required
def api_create_maintenance():
    pass

@api_v1.route('/maintenance/<int:id>', methods=['PUT'])
@api_login_required
def api_update_maintenance(id):
    pass

# Audits
@api_v1.route('/audits', methods=['GET'])
@api_login_required
def api_get_audits():
    pass

# Users (Admin only)
@api_v1.route('/users', methods=['GET'])
@api_login_required
def api_get_users():
    # Check if user is admin
    pass
```

**Testing:**
- Use Postman or curl to test each endpoint
- Verify data validation
- Check error handling
- Test permissions

---

### 3.2 Integrate Modals into Existing Pages
**Phase:** 2.7  
**Difficulty:** Low  
**Time Estimate:** 2-3 hours

**What:** Connect modal components to Machines and Maintenance pages.

**Steps:**

1. **Update Machines.tsx:**
   ```typescript
   import MachineModal from '../components/modals/MachineModal'
   
   const [modalVisible, setModalVisible] = useState(false)
   const [selectedMachine, setSelectedMachine] = useState(undefined)
   
   const handleCreate = () => {
     setSelectedMachine(undefined)
     setModalVisible(true)
   }
   
   const handleEdit = (machine) => {
     setSelectedMachine(machine)
     setModalVisible(true)
   }
   
   const handleSubmit = async (values) => {
     // Call API to create/update machine
     await axios.post('/api/v1/machines', values)
     // Refresh data
   }
   
   // In render:
   <MachineModal
     visible={modalVisible}
     machine={selectedMachine}
     onCancel={() => setModalVisible(false)}
     onSubmit={handleSubmit}
   />
   ```

2. **Update Maintenance.tsx similarly**

3. **Test functionality:**
   - Create new items
   - Edit existing items
   - Validate form fields
   - Test error handling

**Files to modify:**
- `frontend/src/pages/Machines.tsx`
- `frontend/src/pages/Maintenance.tsx`
- `frontend/src/pages/Audits.tsx` (if needed)
- `frontend/src/pages/Sites.tsx` (if needed)

---

### 3.3 Implement Report Generation
**Phase:** 3.1, 3.2  
**Difficulty:** High  
**Time Estimate:** 6-8 hours

**What:** Create report generation components and PDF export.

**Steps:**

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install jspdf jspdf-autotable
   npm install xlsx  # For Excel export
   ```

2. **Create report components:**
   - `frontend/src/components/reports/MaintenanceReport.tsx`
   - `frontend/src/components/reports/AuditReport.tsx`
   - `frontend/src/utils/reportGenerator.ts`

3. **Implement PDF generation:**
   ```typescript
   import jsPDF from 'jspdf'
   import autoTable from 'jspdf-autotable'
   
   export const generateMaintenanceReport = (data) => {
     const doc = new jsPDF()
     // Add company branding
     // Add report title
     // Generate table
     autoTable(doc, {
       head: [['Machine', 'Task', 'Due Date', 'Status']],
       body: data.map(item => [item.machine, item.task, item.dueDate, item.status])
     })
     doc.save('maintenance-report.pdf')
   }
   ```

4. **Add report buttons to pages:**
   - Dashboard
   - Maintenance page
   - Audits page

5. **Implement preview functionality**

6. **Add export options:**
   - PDF
   - Excel (xlsx)
   - CSV

**Design consideration:**
- Present 3 design options to user (Table, Card, Timeline)
- Get user feedback before finalizing

---

## 🎨 Priority 4: Polish & Enhancement

### 4.1 Add Keyboard Shortcuts
**Phase:** 1.5, 2.8  
**Difficulty:** Medium  
**Time Estimate:** 2-3 hours

**What:** Implement global keyboard shortcuts.

**Steps:**

1. **Create keyboard shortcut handler:**
   ```typescript
   // frontend/src/hooks/useKeyboardShortcuts.ts
   useEffect(() => {
     const handleKeyPress = (e: KeyboardEvent) => {
       // Ctrl/Cmd + K: Search
       if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
         e.preventDefault()
         // Focus search bar
       }
       // Ctrl/Cmd + N: New item
       if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
         e.preventDefault()
         // Open create modal
       }
       // etc.
     }
     
     window.addEventListener('keydown', handleKeyPress)
     return () => window.removeEventListener('keydown', handleKeyPress)
   }, [])
   ```

2. **Common shortcuts to implement:**
   - Ctrl/Cmd + K: Search
   - Ctrl/Cmd + N: New item
   - Ctrl/Cmd + S: Save
   - Ctrl/Cmd + R: Refresh
   - Ctrl/Cmd + ,: Settings
   - Esc: Close modal/clear search

3. **Update tooltips to show shortcuts**

4. **Create shortcuts help page/modal**

---

### 4.2 Performance Optimization
**Phase:** 4.2  
**Difficulty:** Medium  
**Time Estimate:** 3-4 hours

**What:** Optimize React application performance.

**Steps:**

1. **Implement code splitting:**
   ```typescript
   // In App.tsx
   import { lazy, Suspense } from 'react'
   
   const Dashboard = lazy(() => import('./pages/Dashboard'))
   const Machines = lazy(() => import('./pages/Machines'))
   // etc.
   
   // Wrap routes with Suspense
   <Suspense fallback={<Loading />}>
     <Routes>
       <Route path="/dashboard" element={<Dashboard />} />
     </Routes>
   </Suspense>
   ```

2. **Add React.memo to expensive components:**
   ```typescript
   export default React.memo(MachineCard)
   ```

3. **Implement virtual scrolling for large tables:**
   ```bash
   npm install react-window
   ```

4. **Add debounced search:**
   ```typescript
   import { debounce } from 'lodash'
   
   const debouncedSearch = debounce((term) => {
     // Perform search
   }, 300)
   ```

5. **Optimize bundle size:**
   - Check bundle with: `npm run build -- --report`
   - Remove unused dependencies
   - Use production builds

---

### 4.3 Add Testing Infrastructure
**Phase:** 4.5  
**Difficulty:** High  
**Time Estimate:** 8-10 hours

**What:** Set up testing frameworks and write tests.

**Steps:**

1. **Configure Jest:**
   ```bash
   cd frontend
   npm install --save-dev @testing-library/react @testing-library/jest-dom jest-environment-jsdom
   ```

2. **Create jest.config.js:**
   ```javascript
   module.exports = {
     testEnvironment: 'jsdom',
     setupFilesAfterEnv: ['<rootDir>/src/setupTests.ts'],
     moduleNameMapper: {
       '\\.(css|less|scss)$': 'identity-obj-proxy',
     },
   }
   ```

3. **Write component tests:**
   ```typescript
   // __tests__/Login.test.tsx
   import { render, screen, fireEvent } from '@testing-library/react'
   import Login from '../pages/Login'
   
   test('renders login form', () => {
     render(<Login />)
     expect(screen.getByPlaceholderText('Username')).toBeInTheDocument()
   })
   ```

4. **Set up E2E testing with Playwright:**
   ```bash
   npm init playwright@latest
   ```

5. **Write E2E tests for critical flows:**
   - Login flow
   - Creating a machine
   - Completing a maintenance task

---

## 📚 Priority 5: Documentation

### 5.1 Update Documentation
**Phase:** 4.6  
**Difficulty:** Low  
**Time Estimate:** 2-3 hours

**What:** Update all documentation for new React frontend.

**Files to update:**

1. **README.md:**
   - Add React development setup
   - Update build instructions
   - Document new features

2. **DEVELOPER_SETUP.md:**
   - Frontend development setup
   - API development and testing
   - Electron development mode

3. **API_DOCUMENTATION.md:**
   - Document all REST API endpoints
   - Include request/response examples
   - Authentication requirements

4. **USER_GUIDE.md:**
   - Screenshot new UI
   - Document new features
   - Accessibility features
   - Keyboard shortcuts

---

## ✅ Checklist for Completion

Use this checklist to track progress:

### Phase 1 Completion
- [ ] Electron frameless window working
- [ ] Window controls functional (minimize, maximize, close)
- [ ] Splash screen shows progress
- [ ] Menu bar keyboard shortcuts work
- [ ] Login API integration tested

### Phase 2 Completion
- [ ] All pages load correctly
- [ ] Modals integrated and functional
- [ ] Tooltips showing on all actions
- [ ] Sidebar navigation complete
- [ ] Users page functional

### Phase 3 Completion
- [ ] Accessibility settings working
- [ ] High contrast mode tested
- [ ] Screen reader compatibility verified
- [ ] Report generation functional
- [ ] PDF/Excel export working

### Phase 4 Completion
- [ ] RBAC permissions enforced
- [ ] All API endpoints implemented
- [ ] Performance optimized
- [ ] Tests written and passing
- [ ] Cross-platform builds working
- [ ] Documentation updated

---

## 🆘 Getting Help

If you encounter issues:

1. **Check browser console** for JavaScript errors
2. **Check Flask logs** for API errors
3. **Review REACT_IMPLEMENTATION_TRACKER.md** for status
4. **Test in isolation** - start with simplest components first
5. **Use git** to revert changes if needed

---

## 📞 Support Resources

- **React Documentation:** https://react.dev
- **Ant Design Components:** https://ant.design/components/overview
- **Electron Documentation:** https://www.electronjs.org/docs
- **Flask REST API:** https://flask-restful.readthedocs.io
- **WCAG Guidelines:** https://www.w3.org/WAI/WCAG21/quickref

---

**Document Version:** 1.0  
**Last Updated:** November 1, 2025  
**Next Review:** After manual steps completion
