# CRUD Operations - React to Flask Connection

## ✅ What's Been Connected

### Machines Page - FULLY FUNCTIONAL

The Machines page now has full CRUD operations connected to the existing Flask backend:

#### ✅ Create Machine
- **Button**: "Add Machine" in Machines page
- **Modal**: MachineModal component
- **Backend Endpoint**: `POST /machines`
- **How it works**:
  1. User clicks "Add Machine"
  2. Modal opens with form (Name, Serial Number, Model, Machine Number, Site)
  3. User fills form and clicks "Create"
  4. React sends FormData to `POST /machines`
  5. Flask creates machine in database
  6. React refreshes machine list
  7. Success message displayed

#### ✅ Edit Machine
- **Button**: Edit icon (pencil) in each machine row
- **Modal**: Same MachineModal component
- **Backend Endpoint**: `POST /machine/edit/:id`
- **How it works**:
  1. User clicks edit icon on a machine
  2. Modal opens pre-filled with machine data
  3. User modifies fields and clicks "Update"
  4. React sends FormData to `POST /machine/edit/{id}`
  5. Flask updates machine in database
  6. React refreshes machine list
  7. Success message displayed

#### ✅ Delete Machine
- **Button**: Delete icon (trash) in each machine row
- **Confirmation**: Ant Design Modal confirmation dialog
- **Backend Endpoint**: `POST /machines/delete/:id`
- **How it works**:
  1. User clicks delete icon
  2. Confirmation dialog appears
  3. User confirms deletion
  4. React sends request to `POST /machines/delete/{id}`
  5. Flask deletes machine from database
  6. React refreshes machine list
  7. Success message displayed

#### ✅ View Machines
- **Data Source**: `GET /api/v1/machines`
- **Features**:
  - Real-time data from database
  - Loading states
  - Refresh button
  - Search and filtering (frontend)
  - Pagination
  - Site dropdown (dynamically loaded from `GET /api/v1/sites`)

## 🔧 Technical Implementation Details

### Key Changes Made

1. **API Response Structure**
   - Updated machines API to include `site_id` and `machine_number`
   - React properly parses `response.data.data` (axios wraps API response)

2. **Form Data Submission**
   - React sends FormData instead of JSON
   - Matches Flask's `request.form` expectations
   - Content-Type: `multipart/form-data`

3. **Machine Modal**
   - Added `sites` prop to dynamically populate site dropdown
   - Form fields match Flask backend expectations:
     - `name` → required
     - `model` → optional
     - `serial_number` → optional
     - `machine_number` → optional
     - `site_id` → required (integer)

4. **State Management**
   - Machines page fetches sites on mount
   - Refreshes machine list after create/edit/delete
   - Loading states prevent duplicate operations

### Code Structure

```typescript
// Machines.tsx - Main page component
const handleSubmitMachine = async (values: any) => {
  const formData = new FormData()
  formData.append('name', values.name)
  formData.append('model', values.model || '')
  formData.append('serial_number', values.serial || '')
  formData.append('machine_number', values.machine_number || '')
  formData.append('site_id', values.site_id)

  if (selectedMachine) {
    await apiClient.post(`/machine/edit/${selectedMachine.id}`, formData)
  } else {
    await apiClient.post('/machines', formData)
  }
  
  await fetchMachines() // Refresh list
}
```

## 🚧 Still TODO - Other Pages

The same pattern needs to be applied to other pages:

### Sites Page
**Endpoints Available**:
- `POST /sites` - Create new site
- `POST /site/edit/:id` - Update site
- `POST /sites/delete/:id` - Delete site

**What to do**:
1. Update `SiteModal` to send FormData
2. Connect form submission to Flask endpoints
3. Add delete confirmation with API call
4. Test create/edit/delete operations

### Maintenance Page
**Endpoints Available**:
- `POST /maintenance` - Create maintenance record
- `POST /update-maintenance` - Update maintenance
- Completion/assignment endpoints exist

**What to do**:
1. Update `MaintenanceTaskModal` to send FormData
2. Connect to Flask maintenance endpoints
3. Add complete/assign buttons with API calls
4. Test CRUD operations

### Audits Page
**Endpoints Available**:
- Check `app.py` for audit-related routes
- Likely `/audits` with POST support

**What to do**:
1. Find audit endpoints in app.py
2. Create audit modal if needed
3. Connect CRUD operations
4. Test functionality

### Users Page (Admin Only)
**Endpoints Available**:
- Check `app.py` for user management routes
- Likely `/users` or `/admin/users`

**What to do**:
1. Find user management endpoints
2. Connect user modal to endpoints
3. Add proper admin-only checks
4. Test user CRUD operations

## 📋 Pattern to Follow

For each remaining page, follow this pattern:

1. **Find the Flask endpoint** in `app.py`
   ```python
   @app.route('/resource', methods=['GET', 'POST'])
   def manage_resource():
       if request.method == 'POST':
           # See what form fields it expects
   ```

2. **Update the React modal** to match form fields
   ```typescript
   const formData = new FormData()
   formData.append('field_name', values.field_name)
   ```

3. **Connect the submit handler**
   ```typescript
   if (editing) {
     await apiClient.post(`/resource/edit/${id}`, formData)
   } else {
     await apiClient.post('/resource', formData)
   }
   ```

4. **Add delete handler**
   ```typescript
   await apiClient.post(`/resource/delete/${id}`)
   await fetchResources() // Refresh list
   ```

5. **Test thoroughly**
   - Create new item
   - Edit existing item
   - Delete item
   - Verify data persists after refresh

## 🎯 Testing the Machine CRUD

To test that machines CRUD is working:

1. **Restart the app** (if running): The rebuild is complete
2. **Navigate to Machines page**
3. **Test Create**:
   - Click "Add Machine"
   - Fill in the form
   - Select a site from dropdown
   - Click "Create"
   - Should see success message
   - Machine should appear in list
4. **Test Edit**:
   - Click edit icon on any machine
   - Modify some fields
   - Click "Update"
   - Should see success message
   - Changes should persist after refresh
5. **Test Delete**:
   - Click delete icon
   - Confirm deletion
   - Machine should disappear from list
   - Data should be gone after refresh

## 🐛 Troubleshooting

If operations fail:

1. **Check browser console** for errors
2. **Check Flask terminal** for backend errors
3. **Verify FormData fields** match Flask expectations
4. **Check network tab** to see actual request/response
5. **Ensure site_id is a number** not a string

Common issues:
- **"Field required"** - Check form field names match Flask `request.form['name']`
- **401 Unauthorized** - Session expired, re-login
- **500 Server Error** - Check Flask terminal for stack trace
- **Network error** - Flask backend not running

## 📊 Current Status Summary

| Page | Read | Create | Edit | Delete | Status |
|------|------|--------|------|--------|--------|
| Dashboard | ✅ | N/A | N/A | N/A | Complete |
| **Machines** | ✅ | ✅ | ✅ | ✅ | **COMPLETE** |
| Maintenance | ✅ | ❌ | ❌ | ❌ | Data only |
| Sites | ✅ | ❌ | ❌ | ❌ | Data only |
| Audits | ❌ | ❌ | ❌ | ❌ | Not started |
| Users | ❌ | ❌ | ❌ | ❌ | Not started |

**Next Priority**: Connect Sites page CRUD operations following the same pattern as Machines.
