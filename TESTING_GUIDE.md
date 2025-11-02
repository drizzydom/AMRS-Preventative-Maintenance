# Testing Guide - UI/UX Overhaul

**Last Updated:** November 2, 2025  
**Status:** Ready for User Testing  
**Progress:** 52% Complete

This guide will help you test all the new functionality that's been implemented in the UI/UX overhaul.

---

## 🚀 Quick Start

### Prerequisites
```bash
# Install frontend dependencies
cd frontend
npm install

# Start Flask backend (Terminal 1)
cd ..
python app.py

# Start React frontend (Terminal 2)
cd frontend
npm run dev
```

### Access the Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:5000

---

## 🎯 What to Test

### 1. Login Page (`/login`)

**Features to Test:**
- [ ] Enter username and password
- [ ] Click "Remember me" checkbox
- [ ] Click "Login" button
- [ ] See loading spinner during login
- [ ] Try invalid credentials (see error message)
- [ ] Click "Forgot password?" link

**Expected Behavior:**
- Login form validates input
- Loading state shows during authentication
- Error messages display for invalid credentials
- Success redirects to Dashboard

---

### 2. Machines Page (`/machines`)

**Features to Test:**

**Create Machine:**
- [ ] Click "Add Machine" button
- [ ] Fill in machine details (name, serial, model, site)
- [ ] Click "Submit"
- [ ] See new machine appear in table
- [ ] See success message

**Edit Machine:**
- [ ] Click edit icon (pencil) on any machine row
- [ ] Modify machine details
- [ ] Click "Update"
- [ ] See changes reflected in table
- [ ] See success message

**Delete Machine:**
- [ ] Click delete icon (trash) on any machine row
- [ ] See confirmation dialog
- [ ] Click "Delete" to confirm
- [ ] See machine removed from table
- [ ] See success message

**Other Features:**
- [ ] Search for machines by name/serial
- [ ] Filter by site using dropdown
- [ ] Toggle "Show Decommissioned" button
- [ ] Sort columns by clicking headers
- [ ] Change page size (25/50/100)

**Expected Behavior:**
- All buttons open appropriate modals
- Forms validate required fields
- Changes update table immediately
- Success messages display
- Confirmations prevent accidental deletes

---

### 3. Maintenance Page (`/maintenance`)

**Features to Test:**

**Create Task:**
- [ ] Click "New Task" button
- [ ] Fill in task details (machine, description, due date, etc.)
- [ ] Use date picker for due date
- [ ] Select priority (low/medium/high/critical)
- [ ] Click "Submit"
- [ ] See new task appear in table
- [ ] See summary statistics update

**Complete Task:**
- [ ] Click checkmark icon on pending task
- [ ] See confirmation dialog
- [ ] Click "Complete"
- [ ] See task status change to "completed"
- [ ] See summary statistics update

**Cancel Task:**
- [ ] Click X icon on any task
- [ ] See confirmation dialog
- [ ] Click "Cancel Task"
- [ ] See task removed from table
- [ ] See summary statistics update

**Other Features:**
- [ ] Filter by status (pending/overdue/completed)
- [ ] Filter by site
- [ ] Use date range picker
- [ ] Search tasks
- [ ] Sort columns

**Expected Behavior:**
- Task creation validates all fields
- Date picker prevents invalid dates
- Status changes update immediately
- Summary cards show correct counts
- Overdue dates display in red

---

### 4. Dashboard Page (`/dashboard`)

**Features to Test:**
- [ ] View statistics cards (Total Machines, Overdue, Due Soon, Completed)
- [ ] See recent maintenance tasks table
- [ ] Check if stats match reality (when using real data)

**Expected Behavior:**
- Statistics display correctly
- Recent tasks show latest entries
- Cards are color-coded appropriately

---

### 5. Audits Page (`/audits`)

**Features to Test:**
- [ ] View audits list
- [ ] Filter by type (safety/quality/maintenance/compliance)
- [ ] Filter by status
- [ ] See progress bars for task completion
- [ ] Search audits

**Expected Behavior:**
- Filters work correctly
- Progress bars show accurate percentages
- Status tags are color-coded

---

### 6. Sites Page (`/sites`)

**Features to Test:**
- [ ] View sites list
- [ ] See machine counts per site
- [ ] See contact information
- [ ] Search sites

**Expected Behavior:**
- All site information displays
- Statistics are accurate
- Search filters results

---

### 7. Users Page (`/users`)

**Features to Test:**
- [ ] View users list
- [ ] See role badges (Admin/Manager/Technician/Viewer)
- [ ] See user status (Active/Inactive)
- [ ] Filter by role
- [ ] Search users

**Expected Behavior:**
- User list displays correctly
- Role badges are color-coded
- Filters work properly

---

### 8. Settings Page (`/settings`)

**Features to Test:**

**Visual Settings:**
- [ ] Toggle "High Contrast Mode" → See increased contrast
- [ ] Toggle "Color Blind Mode" → See patterns added to colors
- [ ] Change "Font Size" (12-18px) → See text size change
- [ ] Change "Font Family" (Sans-serif/Serif) → See font change
- [ ] Adjust "Zoom Level" (50-200%) → See entire UI scale

**Motion Settings:**
- [ ] Toggle "Reduce Motion" → See animations disabled

**Persistence:**
- [ ] Make changes and click "Save Settings"
- [ ] Refresh page → Settings should persist
- [ ] Click "Reset to Defaults" → All settings return to default

**Expected Behavior:**
- Changes apply immediately
- Settings persist across sessions (localStorage)
- All settings work independently
- Reset button restores defaults

---

### 9. Reports - Maintenance (`/reports`)

**Features to Test:**

**Option A: Minimalist Table**
- [ ] View table layout with all records
- [ ] See summary statistics
- [ ] Check status tags (completed/pending/overdue)

**Option B: Card-Based Visual**
- [ ] View dashboard with metric cards
- [ ] See performance overview with large metrics
- [ ] See completion rate progress bar
- [ ] View individual maintenance record cards

**Option C: Timeline View**
- [ ] View chronological timeline
- [ ] See records grouped by date
- [ ] View statistics panel
- [ ] Check timeline dots match status

**Features:**
- [ ] Switch between tabs to compare designs
- [ ] Use date range picker
- [ ] Select site filter
- [ ] Read decision helper guide
- [ ] Click Preview/Export/Print buttons (UI only)

**Expected Behavior:**
- All 3 options display sample data
- Each has distinct visual style
- Descriptions explain when to use each
- Professional appearance suitable for print

---

### 10. Reports - Audits (`/reports/audits`)

**Features to Test:**

**Option A: Detailed Checklist**
- [ ] View complete checklist table
- [ ] See overall compliance score
- [ ] View findings section (failed items)
- [ ] Check signature blocks

**Option B: Executive Summary**
- [ ] View large KPI circle gauge
- [ ] See colored metric cards
- [ ] View category performance breakdown
- [ ] Read critical findings section
- [ ] View recommendations

**Option C: Compliance-Focused**
- [ ] View compliance header
- [ ] Expand/collapse category sections
- [ ] See non-compliance items with NC numbers
- [ ] Read compliance statement
- [ ] View certification section

**Features:**
- [ ] Switch between tabs
- [ ] Select audit date
- [ ] Select site and audit type
- [ ] Read decision helper
- [ ] Review audit types guide

**Expected Behavior:**
- All 3 options show 15 checkpoints
- 3 failed items highlighted
- 80% compliance score shown
- Each format serves different purpose
- Professional compliance documentation

---

## 🎨 UI/UX Elements to Check

### Desktop UI Components

**Title Bar:**
- [ ] Custom title bar displays at top
- [ ] Window control buttons visible (minimize/maximize/close)
- [ ] Title bar is draggable (future Electron integration)

**Menu Bar:**
- [ ] Desktop menu bar shows below title bar
- [ ] All menus (File/Edit/View/Tools/Help) present
- [ ] Dropdown menus work on hover/click
- [ ] Logout option in menu

**Sidebar:**
- [ ] Sidebar navigation on left
- [ ] All page links present (Dashboard, Machines, Maintenance, etc.)
- [ ] Active page highlighted
- [ ] Collapse/expand button works
- [ ] Icons show when collapsed

### Visual Design

- [ ] Consistent color scheme throughout
- [ ] Professional desktop application appearance
- [ ] Status indicators are color-coded
- [ ] Loading states show for operations
- [ ] Error messages are user-friendly
- [ ] Success notifications appear
- [ ] Tables are sortable and filterable
- [ ] Responsive on different screen sizes

---

## 🐛 Known Limitations

### Currently Using Mock Data
- All pages use sample/mock data
- CRUD operations update local state only (not database)
- Changes don't persist after page refresh
- API integration needed for real data

### Pending Backend Integration
- POST/PUT/DELETE API endpoints not yet implemented
- PDF/Excel export not functional (buttons present)
- Report generation with real data pending
- Database operations need API completion

### Electron Features Pending
- Window controls don't actually minimize/maximize/close
- Needs main.js IPC handler integration
- Splash screen progress not connected
- Native menus not integrated

---

## ✅ Success Criteria

### Functional Tests Pass When:
- [ ] All buttons perform expected actions
- [ ] Forms validate input correctly
- [ ] Modals open and close properly
- [ ] Tables update after operations
- [ ] Filters and search work correctly
- [ ] Navigation between pages is smooth
- [ ] Success/error messages display

### UI/UX Tests Pass When:
- [ ] Design is professional and consistent
- [ ] Desktop application appearance maintained
- [ ] Colors and typography are appropriate
- [ ] Loading states show during operations
- [ ] User feedback is immediate and clear
- [ ] Responsive design works on various screens

---

## 📝 Feedback Checklist

### For Report Mockups

**Maintenance Reports:**
- [ ] Which option do you prefer? (A/B/C)
- [ ] What changes would you like?
- [ ] Any missing information?

**Audit Reports:**
- [ ] Which option do you prefer? (A/B/C)
- [ ] What changes would you like?
- [ ] Any compliance requirements to add?

### General Feedback

- [ ] Any buttons not working as expected?
- [ ] Any confusing UI elements?
- [ ] Any missing features?
- [ ] Performance issues?
- [ ] Design preferences?

---

## 🔧 Troubleshooting

### Frontend Won't Start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.7+

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

### Ports Already in Use
```bash
# Check what's using port 3000
lsof -i :3000

# Kill process if needed
kill -9 <PID>

# Same for port 5000
lsof -i :5000
kill -9 <PID>
```

### Browser Console Errors
- Open DevTools (F12)
- Check Console tab for errors
- Check Network tab for failed requests
- Clear browser cache and reload

---

## 📊 Testing Checklist Summary

**Critical Functionality:**
- [ ] Login works
- [ ] Navigation works
- [ ] Machines CRUD works
- [ ] Maintenance CRUD works
- [ ] All buttons respond
- [ ] Modals open/close
- [ ] Forms validate
- [ ] Tables update

**UI/UX:**
- [ ] Professional appearance
- [ ] Consistent design
- [ ] Desktop UI components
- [ ] Color coding
- [ ] Status indicators
- [ ] Loading states
- [ ] Notifications

**Reports:**
- [ ] All 6 mockups display
- [ ] Sample data shows
- [ ] Design options clear
- [ ] Decision guidance helpful
- [ ] Professional quality

---

## 🎉 Next Steps

After testing:

1. **Provide Feedback** on report designs (which options you prefer)
2. **Report Issues** if any features don't work as expected
3. **Request Changes** if you'd like different designs or features
4. **Backend Integration** can proceed once frontend is approved
5. **PDF/Excel Export** can be implemented for chosen report designs

---

**Questions?** Check MANUAL_STEPS.md for backend integration details or IMPLEMENTATION_COMPLETE_SUMMARY.md for overall project status.

**Ready to Test!** 🚀
