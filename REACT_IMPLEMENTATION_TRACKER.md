# React SPA Implementation Tracker
## AMRS Maintenance Tracker - Desktop UI Modernization

**Project Start Date:** November 1, 2025  
**Estimated Timeline:** 4-6 weeks  
**Architecture:** React SPA + Flask REST API + Electron Desktop Wrapper

---

## 📋 Implementation Checklist

### PHASE 1: Core React Setup + Desktop Theme + Splash/Login (Weeks 1-2)

#### 1.1 Project Setup & Configuration
- [ ] Initialize React project with TypeScript
- [ ] Install and configure desktop component library (Ant Design or Fluent UI)
- [ ] Set up React Router for client-side routing
- [ ] Configure Webpack/Vite for optimized bundling
- [ ] Set up state management (Context API or Redux)
- [ ] Configure development environment

**Files to Create/Modify:**
- `frontend/package.json` - React dependencies
- `frontend/webpack.config.js` or `vite.config.js`
- `frontend/tsconfig.json`
- `frontend/src/index.tsx` - React entry point
- `frontend/src/App.tsx` - Main app component

#### 1.2 Splash Screen Modernization
- [ ] Create modern splash screen component
- [ ] Implement real progress tracking (not estimated)
- [ ] Add specific status messages ("Installing dependencies...", "Loading database...", etc.)
- [ ] Add smooth animations and transitions
- [ ] Add cancel button for long operations
- [ ] Update main.js to use new splash screen

**Files to Create/Modify:**
- `frontend/src/components/SplashScreen.tsx`
- `main.js` - Electron splash screen integration
- `splash-preload.js` - Update for new progress tracking

**Status:** ⏸️ Not Started

#### 1.3 Login Page Enhancement
- [ ] Create React login component
- [ ] Implement loading state with animated spinner
- [ ] Add sync indicator with progress bar
- [ ] Implement error states with specific messages:
  - [ ] "Invalid username or password"
  - [ ] "Server connection failed"
  - [ ] "Account locked - contact administrator"
- [ ] Add success state (green checkmark → smooth transition)
- [ ] Make UI non-blocking (can cancel during sync)
- [ ] Integrate with Flask authentication API
- [ ] Add "Remember me" functionality
- [ ] Add "Forgot password" flow

**Files to Create/Modify:**
- `frontend/src/pages/Login.tsx`
- `frontend/src/components/LoginForm.tsx`
- `frontend/src/hooks/useAuth.ts`
- `frontend/src/api/auth.ts`
- `app.py` - Add REST API endpoint for authentication

**Status:** ⏸️ Not Started

#### 1.4 Desktop Window Chrome
- [ ] Configure frameless Electron window
- [ ] Create custom title bar component
- [ ] Add window controls (minimize, maximize, close)
- [ ] Make title bar draggable
- [ ] Add app icon and title
- [ ] Handle window events (maximize, minimize, restore)

**Files to Create/Modify:**
- `frontend/src/components/TitleBar.tsx`
- `main.js` - Configure frameless window
- `frontend/src/styles/titlebar.css`

**Status:** ⏸️ Not Started

#### 1.5 Desktop Menu Bar
- [ ] Create desktop menu bar component (File, Edit, View, Tools, Help)
- [ ] Implement dropdown menus for each section
- [ ] Add keyboard shortcuts
- [ ] Integrate with Electron native menu system
- [ ] Add menu items based on user permissions

**Files to Create/Modify:**
- `frontend/src/components/MenuBar.tsx`
- `main.js` - Native menu integration
- `frontend/src/constants/menus.ts`

**Status:** ⏸️ Not Started

---

### PHASE 2: Main Views + Virtual Scrolling + Modals + Tooltips (Weeks 3-4)

#### 2.1 Dashboard Page
- [ ] Create dashboard React component
- [ ] Implement stats cards (Overdue, Due Soon, Completed, Total)
- [ ] Add recent maintenance tasks table
- [ ] Implement site filter dropdown
- [ ] Add decommissioned machines toggle
- [ ] Implement quick action buttons
- [ ] Add real-time data updates

**Files to Create/Modify:**
- `frontend/src/pages/Dashboard.tsx`
- `frontend/src/components/dashboard/StatsCards.tsx`
- `frontend/src/components/dashboard/RecentTasks.tsx`
- `app.py` - Add dashboard REST API endpoint

**Status:** ⏸️ Not Started

#### 2.2 Machines Page with Virtual Scrolling
- [ ] Create machines list component
- [ ] Implement virtual scrolling (react-window)
- [ ] Add collapsible sections for machine groups
- [ ] Implement filters & search at top
- [ ] Add pagination controls (25/50/100/All)
- [ ] Add summary cards showing totals
- [ ] Implement sticky headers
- [ ] Add machine detail modal

**Files to Create/Modify:**
- `frontend/src/pages/Machines.tsx`
- `frontend/src/components/machines/MachineList.tsx`
- `frontend/src/components/machines/MachineCard.tsx`
- `frontend/src/components/common/VirtualScrollTable.tsx`
- `app.py` - Add machines REST API endpoint

**Status:** ⏸️ Not Started

#### 2.3 Maintenance Page
- [ ] Create maintenance tasks component
- [ ] Implement virtual scrolling for large lists
- [ ] Add task filters (by status, site, date range)
- [ ] Implement task creation modal
- [ ] Add task edit/delete functionality
- [ ] Implement multi-part maintenance modal
- [ ] Add task history view

**Files to Create/Modify:**
- `frontend/src/pages/Maintenance.tsx`
- `frontend/src/components/maintenance/TaskList.tsx`
- `frontend/src/components/maintenance/TaskModal.tsx`
- `frontend/src/components/maintenance/MultiPartModal.tsx`
- `app.py` - Add maintenance REST API endpoints

**Status:** ⏸️ Not Started

#### 2.4 Audits Page with Consolidation
- [ ] Create audits page component
- [ ] Implement virtual scrolling
- [ ] Add collapsible sections for audit groups
- [ ] Implement filters & search
- [ ] Add pagination controls
- [ ] Reduce visual anomalies
- [ ] Add audit detail view
- [ ] Implement audit task assignment

**Files to Create/Modify:**
- `frontend/src/pages/Audits.tsx`
- `frontend/src/components/audits/AuditList.tsx`
- `frontend/src/components/audits/AuditDetail.tsx`
- `app.py` - Add audits REST API endpoints

**Status:** ⏸️ Not Started

#### 2.5 Sites Page
- [ ] Create sites management component
- [ ] Add site list with filters
- [ ] Implement site creation/edit modal
- [ ] Add site detail view with machine counts
- [ ] Implement site threshold settings

**Files to Create/Modify:**
- `frontend/src/pages/Sites.tsx`
- `frontend/src/components/sites/SiteList.tsx`
- `frontend/src/components/sites/SiteModal.tsx`
- `app.py` - Add sites REST API endpoints

**Status:** ⏸️ Not Started

#### 2.6 Users & Roles Page (Admin Only)
- [ ] Create users management component
- [ ] Add user list with role badges
- [ ] Implement user creation/edit modal
- [ ] Add role management
- [ ] Implement permission matrix display
- [ ] Add user activity log

**Files to Create/Modify:**
- `frontend/src/pages/admin/Users.tsx`
- `frontend/src/pages/admin/Roles.tsx`
- `frontend/src/components/admin/UserList.tsx`
- `frontend/src/components/admin/UserModal.tsx`
- `app.py` - Add users/roles REST API endpoints

**Status:** ⏸️ Not Started

#### 2.7 Enhanced Modal System
- [ ] Create base modal component with high-contrast overlays
- [ ] Add backdrop blur effect
- [ ] Implement prominent action buttons with visual hierarchy
- [ ] Add clear focus states
- [ ] Implement keyboard navigation (Tab, Esc)
- [ ] Create multi-part maintenance modal with improved visibility
- [ ] Add modal animations

**Files to Create/Modify:**
- `frontend/src/components/common/Modal.tsx`
- `frontend/src/components/common/ModalOverlay.tsx`
- `frontend/src/styles/modals.css`

**Status:** ⏸️ Not Started

#### 2.8 Tooltip & Onboarding System
- [ ] Integrate tooltip library (React Tooltip or Ant Design)
- [ ] Add hover tooltips to all interactive elements (300ms delay)
- [ ] Add keyboard shortcut indicators in tooltips
- [ ] Create optional first-time user guided tour
- [ ] Add help icon badges for complex features
- [ ] Implement contextual help system

**Files to Create/Modify:**
- `frontend/src/components/common/Tooltip.tsx`
- `frontend/src/components/onboarding/GuidedTour.tsx`
- `frontend/src/constants/tooltips.ts`

**Status:** ⏸️ Not Started

#### 2.9 Sidebar Navigation
- [ ] Create always-visible icon sidebar
- [ ] Add active state highlighting
- [ ] Implement permission-based menu items
- [ ] Add collapse/expand functionality
- [ ] Add keyboard navigation

**Files to Create/Modify:**
- `frontend/src/components/Sidebar.tsx`
- `frontend/src/styles/sidebar.css`

**Status:** ⏸️ Not Started

#### 2.10 Toolbar Component
- [ ] Create icon toolbar with quick actions
- [ ] Add action buttons (New, Edit, Delete, Export, Refresh)
- [ ] Implement context-sensitive toolbar (different per page)
- [ ] Add search bar in toolbar
- [ ] Implement permission-based button visibility

**Files to Create/Modify:**
- `frontend/src/components/Toolbar.tsx`
- `frontend/src/styles/toolbar.css`

**Status:** ⏸️ Not Started

---

### PHASE 3: Reports Redesign + Accessibility Settings (Week 5)

#### 3.1 Maintenance Report Redesign
- [ ] Design professional maintenance report template
- [ ] Implement clean table layouts with clear hierarchy
- [ ] Add color-coded status indicators (print-friendly)
- [ ] Add company branding in header/footer
- [ ] Add QR codes for digital verification
- [ ] Support multiple export formats (PDF, Excel, CSV)
- [ ] Add preview before print/export
- [ ] Implement report filtering and date range selection

**Files to Create/Modify:**
- `frontend/src/components/reports/MaintenanceReport.tsx`
- `frontend/src/components/reports/ReportPreview.tsx`
- `frontend/src/utils/reportGenerator.ts`
- `app.py` - Add report generation REST API endpoints

**Design Options to Present:**
- Option A: Minimalist table layout
- Option B: Card-based layout with visual indicators
- Option C: Timeline-based layout

**Status:** ⏸️ Not Started

#### 3.2 Audit Report Redesign
- [ ] Design professional audit report template
- [ ] Implement professional formatting with summary sections
- [ ] Add audit completion percentage charts
- [ ] Add color-coded task status
- [ ] Add company branding
- [ ] Support multiple export formats
- [ ] Add preview functionality

**Files to Create/Modify:**
- `frontend/src/components/reports/AuditReport.tsx`
- `frontend/src/components/reports/AuditSummary.tsx`
- `frontend/src/utils/auditReportGenerator.ts`

**Design Options to Present:**
- Option A: Detailed checklist format
- Option B: Executive summary format
- Option C: Compliance-focused format

**Status:** ⏸️ Not Started

#### 3.3 Accessibility Settings Panel
- [ ] Create settings page component
- [ ] Implement high contrast mode toggle
- [ ] Add color-blind mode (patterns + text labels)
- [ ] Add font size selector (Small/Medium/Large/Extra Large)
- [ ] Add font family selector (Sans-serif/Serif)
- [ ] Add "Reduce motion" toggle for animations
- [ ] Implement responsive scaling (50% to 200% zoom support)
- [ ] Add keyboard navigation settings
- [ ] Persist user preferences to localStorage/backend
- [ ] Test with screen readers (ARIA labels)

**Files to Create/Modify:**
- `frontend/src/pages/Settings.tsx`
- `frontend/src/components/settings/AccessibilityPanel.tsx`
- `frontend/src/hooks/useAccessibility.ts`
- `frontend/src/contexts/AccessibilityContext.tsx`
- `frontend/src/styles/accessibility.css`

**WCAG 2.1 AA Compliance Checklist:**
- [ ] Color contrast ratios meet minimum 4.5:1
- [ ] All interactive elements keyboard accessible
- [ ] Focus indicators visible on all elements
- [ ] Screen reader compatible with proper ARIA labels
- [ ] Text resizable up to 200% without loss of content
- [ ] No content relies solely on color
- [ ] Motion can be disabled

**Status:** ⏸️ Not Started

#### 3.4 User Profile & Preferences
- [ ] Create user profile page
- [ ] Add preference management
- [ ] Add notification settings
- [ ] Add theme preferences
- [ ] Implement password change functionality

**Files to Create/Modify:**
- `frontend/src/pages/Profile.tsx`
- `frontend/src/components/profile/PreferencesForm.tsx`

**Status:** ⏸️ Not Started

---

### PHASE 4: Testing, Refinement & Packaging (Week 6)

#### 4.1 Role-Based Access Control (RBAC) Implementation
- [ ] Create authentication context
- [ ] Implement permission checking hook
- [ ] Add route guards for protected pages
- [ ] Implement conditional rendering based on roles
- [ ] Test with different user roles:
  - [ ] Technician (limited access)
  - [ ] Manager (moderate access)
  - [ ] Admin (full access)
- [ ] Ensure backend authorization preserved

**Files to Create/Modify:**
- `frontend/src/contexts/AuthContext.tsx`
- `frontend/src/hooks/usePermissions.ts`
- `frontend/src/components/auth/ProtectedRoute.tsx`
- `frontend/src/utils/permissions.ts`

**Status:** ⏸️ Not Started

#### 4.2 Performance Optimization
- [ ] Implement React.memo for expensive components
- [ ] Add React.lazy for code splitting
- [ ] Configure service workers for offline caching
- [ ] Implement IndexedDB for client-side data caching
- [ ] Add web workers for background data processing
- [ ] Optimize bundle size
- [ ] Implement debounced search
- [ ] Add loading skeletons for better perceived performance

**Files to Create/Modify:**
- `frontend/src/utils/performance.ts`
- `frontend/src/workers/dataProcessor.worker.ts`
- `frontend/public/service-worker.js`

**Status:** ⏸️ Not Started

#### 4.3 Flask REST API Development
- [ ] Convert Flask routes to REST API endpoints
- [ ] Add API versioning (/api/v1/)
- [ ] Implement JWT authentication
- [ ] Add API rate limiting
- [ ] Implement error handling and standardized responses
- [ ] Add API documentation (Swagger/OpenAPI)
- [ ] Preserve existing authorization decorators

**API Endpoints to Create:**
- [ ] `POST /api/v1/auth/login` - Login
- [ ] `POST /api/v1/auth/logout` - Logout
- [ ] `GET /api/v1/auth/me` - Get current user
- [ ] `GET /api/v1/dashboard` - Dashboard data
- [ ] `GET /api/v1/machines` - List machines
- [ ] `POST /api/v1/machines` - Create machine
- [ ] `PUT /api/v1/machines/:id` - Update machine
- [ ] `DELETE /api/v1/machines/:id` - Delete machine
- [ ] `GET /api/v1/maintenance` - List maintenance tasks
- [ ] `POST /api/v1/maintenance` - Create task
- [ ] `GET /api/v1/audits` - List audits
- [ ] `GET /api/v1/sites` - List sites
- [ ] `GET /api/v1/users` - List users (admin)
- [ ] `GET /api/v1/reports/maintenance` - Generate maintenance report
- [ ] `GET /api/v1/reports/audit` - Generate audit report

**Files to Create/Modify:**
- `app.py` - Add REST API routes
- `api_endpoints.py` - API endpoint definitions
- `api_utils.py` - Update for REST API
- `modules/api/` - New API module structure

**Status:** ⏸️ Not Started

#### 4.4 Build System & Packaging Updates
- [ ] Update package.json with React dependencies
- [ ] Create build scripts for React bundle
- [ ] Update electron-builder-win10.js config
- [ ] Update electron-builder-macos.js config
- [ ] Update electron-builder-linux.js config
- [ ] Configure Webpack/Vite for production builds
- [ ] Update bundle-python.py if needed
- [ ] Test builds on all platforms

**Dependencies to Add:**
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "antd": "^5.11.0" or "@fluentui/react": "^9.0.0",
    "react-window": "^1.8.10",
    "axios": "^1.6.0",
    "@tanstack/react-query": "^5.8.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "typescript": "^5.2.0",
    "webpack": "^5.89.0" or "vite": "^5.0.0",
    "webpack-dev-server": "^4.15.0"
  }
}
```

**Files to Create/Modify:**
- `package.json`
- `electron-builder-win10.js`
- `electron-builder-macos.js`
- `electron-builder-linux.js`
- `bundle-python.py`
- `webpack.config.js` or `vite.config.js`

**Status:** ⏸️ Not Started

#### 4.5 Testing
- [ ] Set up testing framework (Jest + React Testing Library)
- [ ] Write unit tests for components
- [ ] Write integration tests for API calls
- [ ] Write E2E tests with Playwright
- [ ] Test on Windows 10/11
- [ ] Test on macOS (latest 2 versions)
- [ ] Test on Linux (Ubuntu/Debian)
- [ ] Test with different screen sizes
- [ ] Test with different user roles
- [ ] Test accessibility with screen readers
- [ ] Performance testing with large datasets

**Files to Create:**
- `frontend/src/__tests__/` - Test files
- `frontend/jest.config.js`
- `frontend/playwright.config.ts`

**Status:** ⏸️ Not Started

#### 4.6 Documentation Updates
- [ ] Update README.md with React architecture
- [ ] Create developer setup guide
- [ ] Document API endpoints
- [ ] Create user guide for new UI
- [ ] Document accessibility features
- [ ] Create deployment guide

**Files to Create/Modify:**
- `README.md`
- `DEVELOPER_SETUP.md`
- `API_DOCUMENTATION.md`
- `USER_GUIDE.md`
- `ACCESSIBILITY_GUIDE.md`

**Status:** ⏸️ Not Started

---

## 🎨 Design Decisions Pending User Input

### Maintenance Report Layout Options
**Status:** Awaiting user decision

**Option A: Minimalist Table Layout**
- Clean, professional table format
- Focus on data density
- Black and white print-friendly
- Best for: Technical users, detailed records

**Option B: Card-Based Layout**
- Visual cards with status indicators
- More whitespace, easier to scan
- Color-coded sections
- Best for: Executives, quick overview

**Option C: Timeline-Based Layout**
- Chronological timeline view
- Visual progress indicators
- Shows maintenance history flow
- Best for: Historical analysis, trends

### Audit Report Layout Options
**Status:** Awaiting user decision

**Option A: Detailed Checklist Format**
- Item-by-item checklist
- Pass/fail indicators
- Comments for each item
- Best for: Compliance, detailed audits

**Option B: Executive Summary Format**
- High-level overview
- Key metrics and graphs
- Action items highlighted
- Best for: Management reports

**Option C: Compliance-Focused Format**
- Organized by compliance categories
- Risk indicators
- Corrective actions section
- Best for: Regulatory audits

---

## 📊 Progress Tracking

### Overall Progress: 0% Complete

**Phase 1 (Weeks 1-2):** ⏸️ 0% - Not Started  
**Phase 2 (Weeks 3-4):** ⏸️ 0% - Not Started  
**Phase 3 (Week 5):** ⏸️ 0% - Not Started  
**Phase 4 (Week 6):** ⏸️ 0% - Not Started

### Completed Tasks: 0 / 150+

---

## 🚀 Current Focus

**Active Task:** Phase 1.1 - Project Setup & Configuration  
**Next Up:** Initialize React project with TypeScript  
**Blocked By:** None  

---

## 📝 Notes & Decisions

### Key Architectural Decisions
1. **Frontend Framework:** React with TypeScript
2. **Component Library:** TBD (Ant Design or Fluent UI) - User preference?
3. **State Management:** Context API initially, Redux if complexity increases
4. **Routing:** React Router v6
5. **API Communication:** Axios with React Query
6. **Build Tool:** TBD (Webpack or Vite) - Vite recommended for faster builds
7. **Testing:** Jest + React Testing Library + Playwright

### Important Constraints
- Backend (Flask, SQLAlchemy) remains unchanged
- All existing permissions and RBAC must be preserved
- Web hosting capability must be maintained (Flask can serve React build)
- Cross-platform support (Windows, macOS, Linux) required
- Offline functionality must be preserved

### Performance Targets
- 60fps animations
- <100ms page switches
- Handle 10,000+ row tables smoothly
- Initial load time <3 seconds
- Bundle size <2MB (gzipped)

---

## 🔗 Related Documents

- `UI_MODERNIZATION_FEASIBILITY_ANALYSIS.md` - Complete technical analysis
- `UI_MODERNIZATION_QUICK_SUMMARY.md` - Executive summary
- `UI_TRANSFORMATION_VISUAL_GUIDE.md` - Visual mockups and comparisons
- `README_UI_MODERNIZATION.md` - Entry point for all UI modernization docs

---

## 💬 Session Continuity Notes

**Last Updated:** November 1, 2025  
**Last Session:** Initial planning and approval  
**Next Session Start Point:** Begin Phase 1.1 - Initialize React project

**Key Points for Next Session:**
- User approved Option A (Full React implementation)
- User wants autonomous implementation with progress tracking
- User wants mockup options for reports (maintenance & audit)
- All existing permissions/roles must be preserved
- Implementation should be done incrementally with commits

---

## ✅ Pre-Implementation Checklist

Before starting each phase, ensure:
- [ ] Previous phase fully complete and tested
- [ ] No blocking dependencies
- [ ] User feedback incorporated (if applicable)
- [ ] Documentation updated
- [ ] Git commits pushed
- [ ] Progress tracker updated

---

**Document Version:** 1.0  
**Last Modified:** November 1, 2025  
**Maintained By:** GitHub Copilot Coding Agent
