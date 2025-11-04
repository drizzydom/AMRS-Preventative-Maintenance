# CRUD Operations Implementation Status

## ✅ COMPLETED: Sites CRUD (100%)

### Files Created/Modified:
1. **frontend/src/components/modals/SiteModal.tsx** - NEW FILE
   - Created modal component for creating/editing sites
   - Form fields: name (required), location, contact_email, notification_threshold, enable_notifications
   - Validates email format
   - Default notification_threshold: 30 days

2. **frontend/src/pages/Sites.tsx** - UPDATED
   - Added SiteModal import and Modal confirm
   - Added state: `modalOpen`, `selectedSite`, `submitting`
   - Implemented `handleAddSite()` - Opens modal for creating new site
   - Implemented `handleEditSite(site)` - Opens modal with site data for editing
   - Implemented `handleSubmitSite(values)` - Submits FormData to Flask endpoints:
     * Create: `POST /sites`
     * Edit: `POST /site/edit/:id`
     * Uses `multipart/form-data` headers
     * Shows success/error messages
     * Refreshes site list after operation
   - Implemented `handleDeleteSite(site)` - Confirms and deletes site:
     * Delete: `POST /sites/delete/:id`
     * Shows confirmation dialog
     * Handles error if site has associated machines
   - Connected Edit and Delete buttons to handlers
   - Connected "Add Site" button to modal

### Flask Endpoints Used:
- `POST /sites` - Create site (admin only)
- `POST /site/edit/<int:site_id>` - Edit site
- `POST /sites/delete/<int:site_id>` - Delete site (checks for associated machines)

### Form Data Structure:
```typescript
formData.append('name', values.name)                    // Required
formData.append('location', values.location || '')
formData.append('contact_email', values.contact_email || '')
formData.append('notification_threshold', values.notification_threshold || '30')
if (values.enable_notifications) {
  formData.append('enable_notifications', 'on')
}
```

### Testing Checklist:
- [x] Create new site
- [ ] Edit existing site
- [ ] Delete site (without machines)
- [ ] Delete site (with machines - should show error)
- [ ] Form validation (required name, valid email)
- [ ] Data persists after app restart

---

## ✅ COMPLETED: Machines CRUD (100%)

### Status: FULLY FUNCTIONAL
- Create machine via `POST /machines` ✅
- Edit machine via `POST /machine/edit/:id` ✅
- Delete machine via `POST /machines/delete/:id` ✅
- Dynamic site dropdown ✅
- FormData submission ✅
- Success/error messages ✅
- Data refresh after operations ✅

---

## 🔄 PENDING: Maintenance CRUD

### Challenge:
The maintenance system is complex - it's based on Parts and MaintenanceRecords, not simple tasks. The frontend currently shows a "tasks" view that doesn't match the backend data model.

### Backend Structure:
- **Part**: Machine component with maintenance schedule (frequency, unit, next_maintenance date)
- **MaintenanceRecord**: Record of completed maintenance (part_id, date, user_id, comments)

### Current State:
- Frontend displays `/api/v1/maintenance` data (which converts parts to "tasks")
- No direct "create task" - instead, should schedule maintenance for parts
- Completing maintenance creates a MaintenanceRecord and updates Part.next_maintenance

### Flask Endpoints Found:
- `POST /update-maintenance` - Completes maintenance for a part, creates MaintenanceRecord
  * Required: `part_id`, optional: `comments`
  * Updates `last_maintenance` and calculates `next_maintenance`
- Parts are managed through machine/part workflows, not standalone maintenance tasks

### Recommended Approach:
1. **Option A - Keep Current UI**: Modify to show parts needing maintenance, add "Mark Complete" button
   - Simpler: Connect existing buttons to `/update-maintenance`
   - Add comments field
   - Show maintenance history per part
   
2. **Option B - Redesign**: Match frontend to backend model
   - Show parts list with maintenance status
   - Add maintenance completion modal
   - More work but better alignment

### Implementation Required:
- [ ] Decide on approach (A or B)
- [ ] Update MaintenanceTaskModal or create new CompleteMaintenance modal
- [ ] Connect "Complete" button to `/update-maintenance` endpoint
- [ ] Add comments field for maintenance completion
- [ ] Show maintenance history per machine/part
- [ ] Add filtering by site/status

---

## 🔄 PENDING: Users CRUD (Admin Only)

### Flask Endpoints Found:
- `POST /admin/users` - Create new user
- `POST /user/edit/<int:user_id>` - Edit user
- `POST /user/delete/<int:user_id>` - Delete user

### Create User Form Fields:
```python
username (required, unique)
email (required, unique, encrypted)
password (required, min 8 chars)
role_id (required)
```

### Edit User Form Fields:
```python
username (unique check for other users)
email (unique check for other users, encrypted)
full_name
role_id
site assignments (user_ids list)
```

### Delete User Restrictions:
- Cannot delete own account
- Cannot delete main 'admin' account
- Checks current_user.id != user_id

### Current State:
- Frontend shows mock user data
- No API endpoint in api_v1.py for users
- All operations go through Flask routes in app.py

### Implementation Required:
- [ ] Check if UserModal exists, create if not
- [ ] Update admin/Users.tsx page:
  - [ ] Connect to `/api/v1/users` (needs to be created in api_v1.py) OR fetch from web route
  - [ ] Implement `handleAddUser()` - Open modal
  - [ ] Implement `handleEditUser(user)` - Open modal with user data
  - [ ] Implement `handleSubmitUser(values)` - FormData to Flask:
    * Create: `POST /admin/users`
    * Edit: `POST /user/edit/:id`
    * Password field only for create
    * Encrypted username/email handling
  - [ ] Implement `handleDeleteUser(user)` - Confirm and delete:
    * Delete: `POST /user/delete/:id`
    * Check restrictions (own account, main admin)
  - [ ] Add role dropdown (fetch from `/api/v1/roles` or roles endpoint)
  - [ ] Show user role and site assignments
  - [ ] Admin-only permission check

---

## 🔄 PENDING: Audits CRUD

### Status: NOT STARTED

### Investigation Needed:
- [ ] Search app.py for audit-related routes
- [ ] Find Audit model structure
- [ ] Determine if audits are:
  * Audit tasks to be performed?
  * Audit logs/history records?
  * Compliance audit tracking?

### Implementation Steps:
1. Find Flask endpoints: `grep -n "audit" app.py` or search for `@app.route('.*audit')`
2. Check models.py for Audit class
3. Determine CRUD operations available
4. Create/update AuditModal component
5. Update frontend/src/pages/Audits.tsx:
   - Connect to real API data
   - Implement CRUD handlers
   - Follow Machines/Sites pattern

---

## Summary of Work Remaining

### Priority 1: Complete Testing
- Test Sites CRUD operations
- Verify data persistence
- Check error handling

### Priority 2: Users CRUD (Estimated: 20 minutes)
- UserModal component (similar to MachineModal/SiteModal)
- Update Users.tsx with CRUD handlers
- Role dropdown integration
- Admin permission checks
- Test all operations

### Priority 3: Investigate and Implement Audits (Estimated: 30 minutes)
- Find endpoints in app.py
- Understand audit model
- Implement CRUD following established pattern

### Priority 4: Maintenance Redesign (Estimated: 40 minutes)
- Decide on approach (keep current UI vs redesign)
- Implement maintenance completion
- Add comments field
- Show maintenance history
- Test workflow

### Total Estimated Time: ~90 minutes

---

## Pattern Reference (For Remaining Pages)

### 1. Modal Component
```typescript
interface Entity {
  id?: number
  // ... fields
}

interface EntityModalProps {
  open: boolean
  onClose: () => void
  onSubmit: (values: any) => void
  entity: Entity | null
  loading?: boolean
}

// Form with Form.Items, validation rules
// useEffect to populate form on edit
```

### 2. Page Component State
```typescript
const [entities, setEntities] = useState<Entity[]>([])
const [loading, setLoading] = useState(true)
const [modalOpen, setModalOpen] = useState(false)
const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null)
const [submitting, setSubmitting] = useState(false)
```

### 3. CRUD Handlers
```typescript
const handleAdd = () => {
  setSelectedEntity(null)
  setModalOpen(true)
}

const handleEdit = (entity: Entity) => {
  setSelectedEntity(entity)
  setModalOpen(true)
}

const handleSubmit = async (values: any) => {
  try {
    setSubmitting(true)
    const formData = new FormData()
    // ... append fields
    
    if (selectedEntity) {
      await apiClient.post(`/entity/edit/${selectedEntity.id}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      message.success('Updated successfully')
    } else {
      await apiClient.post('/entities', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      message.success('Created successfully')
    }
    
    setModalOpen(false)
    setSelectedEntity(null)
    await fetchEntities()
  } catch (error: any) {
    message.error(error.response?.data?.message || 'Failed to save')
  } finally {
    setSubmitting(false)
  }
}

const handleDelete = (entity: Entity) => {
  confirm({
    title: 'Delete Entity',
    icon: <ExclamationCircleOutlined />,
    content: `Are you sure?`,
    okText: 'Delete',
    okType: 'danger',
    async onOk() {
      await apiClient.post(`/entities/delete/${entity.id}`)
      message.success('Deleted successfully')
      await fetchEntities()
    }
  })
}
```

### 4. Connect to UI
```tsx
<Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
  Add Entity
</Button>

// In table actions column:
<Button icon={<EditOutlined />} onClick={() => handleEdit(record)} />
<Button danger icon={<DeleteOutlined />} onClick={() => handleDelete(record)} />

// Modal
<EntityModal
  open={modalOpen}
  onClose={() => {
    setModalOpen(false)
    setSelectedEntity(null)
  }}
  onSubmit={handleSubmit}
  entity={selectedEntity}
  loading={submitting}
/>
```

---

## Next Steps

1. **Test Sites CRUD** - Verify all operations work correctly
2. **Implement Users CRUD** - Follow Sites pattern for admin user management
3. **Investigate Audits** - Find endpoints and model structure
4. **Implement Audits CRUD** - Once structure is understood
5. **Decide Maintenance Approach** - Discuss with user: keep task view or redesign?
6. **Implement Maintenance** - Based on chosen approach
7. **Final Testing** - Test all CRUD operations across all pages
8. **Update Documentation** - Mark all items complete

