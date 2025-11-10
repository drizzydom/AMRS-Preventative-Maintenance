# Dashboard and Maintenance Loading Fix

**Date:** November 6, 2025  
**Issues Fixed:** Dashboard and Maintenance Tasks unable to load

---

## Problem Analysis

### Root Cause

The **Dashboard** page was calling API endpoints that didn't properly support the query parameters it was using:

1. **Dashboard Stats**: Called `/api/v1/dashboard` ✅ (working)
2. **Overdue Items**: Called `/api/v1/maintenance?status=overdue` ❌ (status parameter not supported)
3. **Due Soon Items**: Called `/api/v1/maintenance?status=due_soon` ❌ (status parameter not supported)

The `/api/v1/maintenance` endpoint existed but didn't handle the `status` query parameter, so it was returning ALL maintenance tasks instead of filtered results.

### Impact

- Dashboard couldn't load overdue and due soon items lists
- Maintenance page worked for showing all tasks, but couldn't be filtered
- No error messages were shown to help diagnose the issue

---

## Changes Made

### 1. Enhanced `/api/v1/maintenance` Endpoint

**File:** `api_v1.py`

**Added Support For:**
- ✅ **Status filtering** - Query parameter `?status=overdue|due_soon|pending`
- ✅ **Site filtering** - Query parameter `?site_id=X` or `?site_id=all`
- ✅ **Additional data fields** for Dashboard compatibility:
  - `part_name` - Name of the part needing maintenance
  - `machine_name` and `machine_id` - Machine details
  - `site_name` and `site_id` - Site details
  - `days_overdue` - For overdue items (absolute value)
  - `days_until` - For upcoming items

**Key Changes:**
```python
# Changed status format from 'due-soon' to 'due_soon' to match frontend
status = 'due_soon'  # Instead of 'due-soon'

# Added filtering logic
if status_filter and status != status_filter:
    continue  # Skip items that don't match the filter

# Added calculated fields
if status == 'overdue':
    task_dict['days_overdue'] = abs(days_diff)
else:
    task_dict['days_until'] = days_diff
```

### 2. Enhanced Dashboard Endpoint Logging

**File:** `api_v1.py`

**Added:**
- Debug logging for date filters
- Counts for each metric (machines, overdue, due soon, completed)
- Cache status logging
- Full exception traces for errors

**Log Output Example:**
```
Dashboard date filters: today=2025-11-06, due_soon_date=2025-11-13
Total machines (not decommissioned): 25
Overdue parts: 8
Due soon parts: 12
Completed maintenance this month: 45
Dashboard cache updated: {'total_machines': 25, 'overdue': 8, 'due_soon': 12, 'completed': 45}
```

### 3. Enhanced Frontend Dashboard Logging

**File:** `frontend/src/pages/Dashboard.tsx`

**Added:**
- Console logging for each API call
- Response data logging
- Count of loaded items
- Detailed error information

**Console Output Example:**
```
[Dashboard] Fetching dashboard data...
[Dashboard] Fetching stats from /api/v1/dashboard
[Dashboard] Stats response: { data: {...} }
[Dashboard] Fetching overdue items from /api/v1/maintenance?status=overdue
[Dashboard] Overdue items response: { data: [...] }
[Dashboard] Loaded 8 overdue items
[Dashboard] Fetching due soon items from /api/v1/maintenance?status=due_soon
[Dashboard] Due soon items response: { data: [...] }
[Dashboard] Loaded 12 due soon items
[Dashboard] All data loaded successfully
```

---

## API Endpoint Reference

### Dashboard Stats
```
GET /api/v1/dashboard
```

**Response:**
```json
{
  "data": {
    "total_machines": 25,
    "overdue": 8,
    "due_soon": 12,
    "completed": 45
  }
}
```

### Maintenance Tasks (All)
```
GET /api/v1/maintenance
```

### Maintenance Tasks (Filtered by Status)
```
GET /api/v1/maintenance?status=overdue
GET /api/v1/maintenance?status=due_soon
GET /api/v1/maintenance?status=pending
```

### Maintenance Tasks (Filtered by Site)
```
GET /api/v1/maintenance?site_id=5
GET /api/v1/maintenance?site_id=all
```

### Maintenance Tasks (Multiple Filters)
```
GET /api/v1/maintenance?status=overdue&site_id=5
```

**Response Format:**
```json
{
  "data": [
    {
      "id": 123,
      "part_name": "Hydraulic Pump",
      "machine": "CNC Machine A",
      "machine_name": "CNC Machine A",
      "machine_id": 5,
      "task": "Hydraulic Pump - Replace seals",
      "dueDate": "2025-11-01",
      "next_maintenance": "2025-11-01",
      "status": "overdue",
      "site": "Main Plant",
      "site_name": "Main Plant",
      "site_id": 2,
      "days_overdue": 5,
      "priority": "high",
      "lastMaintenance": "2025-10-01",
      "frequency": "30 days"
    }
  ]
}
```

---

## Testing Steps

### 1. Start the Application

Check the logs as the app starts for any errors.

### 2. Test Dashboard Loading

1. Navigate to Dashboard page
2. **Open Browser Console** (F12)
3. Watch for console logs:
   ```
   [Dashboard] Fetching dashboard data...
   [Dashboard] Stats response: ...
   [Dashboard] Loaded X overdue items
   [Dashboard] Loaded X due soon items
   [Dashboard] All data loaded successfully
   ```

4. **Check Application Logs** (backend):
   ```
   Fetching fresh dashboard data...
   Dashboard date filters: ...
   Total machines: X
   Overdue parts: X
   Due soon parts: X
   Dashboard cache updated: {...}
   ```

### 3. Verify Dashboard Displays

The Dashboard should show:
- ✅ **Stats Cards**: Total Machines, Overdue, Due Soon, Completed
- ✅ **Overdue Items Table**: List of overdue maintenance tasks
- ✅ **Due Soon Table**: List of upcoming maintenance tasks

### 4. Test Maintenance Page

1. Navigate to Maintenance page
2. Should show all maintenance tasks (overdue + due soon + pending)
3. Console should show:
   ```
   Maintenance API response: { data: [...] }
   Loaded X maintenance tasks
   ```

### 5. If Pages Are Empty

**This is expected if:**
- No machines exist in database
- No parts have been added to machines
- No parts have maintenance schedules set

**To populate data:**
1. Go to Machines page
2. Add a machine (if none exist)
3. Add parts to that machine
4. Set maintenance schedules for parts:
   - Maintenance Frequency: e.g., "30"
   - Maintenance Unit: e.g., "days"
   - Last Maintenance: Recent date
5. Return to Dashboard/Maintenance - tasks should appear

---

## Common Issues & Solutions

### Issue: "Failed to load dashboard data"

**Possible Causes:**
1. Backend server not running
2. Database connection error
3. Authentication issue

**Solution:**
- Check backend logs for errors
- Verify database file exists
- Check if user is logged in

### Issue: Dashboard shows 0 for all stats

**Cause:** No data in database

**Solution:**
- Add machines, parts, and maintenance schedules
- See "If Pages Are Empty" section above

### Issue: Console shows API errors

**Solution:**
- Check browser console for exact error message
- Check backend logs for detailed error
- Verify API endpoint is accessible: `http://localhost:5000/api/v1/dashboard`

---

## Technical Details

### Status Value Mapping

| Frontend Request | Backend Filter | Description |
|-----------------|----------------|-------------|
| `status=overdue` | `status == 'overdue'` | Tasks past due date |
| `status=due_soon` | `status == 'due_soon'` | Tasks due within 7 days |
| `status=pending` | `status == 'pending'` | Tasks due after 7 days |

### Date Logic

```python
today = datetime.now().date()
due_soon_date = today + timedelta(days=7)

if next_maintenance < today:
    status = 'overdue'
elif next_maintenance <= due_soon_date:
    status = 'due_soon'
else:
    status = 'pending'
```

### Caching

Dashboard stats are cached for **5 minutes** (300 seconds) to improve performance:
- First request: Fetch from database, cache result
- Subsequent requests: Return cached data if < 5 minutes old
- After 5 minutes: Fetch fresh data, update cache

---

## Files Modified

1. ✅ `api_v1.py`:
   - Enhanced `/api/v1/maintenance` endpoint with status and site filtering
   - Added detailed logging to `/api/v1/dashboard` endpoint
   - Fixed status value from 'due-soon' to 'due_soon'

2. ✅ `frontend/src/pages/Dashboard.tsx`:
   - Added detailed console logging for all API calls
   - Added error details logging
   - Added success confirmation logs

3. ✅ `frontend/src/pages/Maintenance.tsx`:
   - Already had logging from previous fix
   - Now compatible with updated API response format

---

## Build Status

```
✓ TypeScript compilation: PASSED
✓ Vite build: PASSED (658.37 kB)
✓ All changes compiled successfully
✓ No errors
```

---

## Next Steps

1. **Start the application**
2. **Check logs** for startup errors
3. **Navigate to Dashboard** and check browser console
4. **Verify data loads** or see empty state
5. **If empty**: Add machines → parts → schedules
6. **Report results**: What do the logs show?

---

**End of Report**
