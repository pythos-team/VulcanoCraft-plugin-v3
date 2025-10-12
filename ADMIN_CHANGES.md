# Admin Panel Changes

## Features Added

### 1. Role-Based Permission System
- Implemented 3-tier role system: Admin, Co-Admin, User
- Role field added to user data structure
- Permission checks on all admin endpoints

### 2. Admin Panel Enhancements
- **User Management**:
  - View all users with role badges
  - Promote/demote users (Admin only)
  - Delete users (Admin only)
  - Display plugin count per user
  - Removed email field from user cards

- **Plugin Management**:
  - View all plugins in the system
  - Delete any plugin (Admin/Co-Admin)
  - Display plugin owner information
  - Visual plugin cards with icons

- **Settings Management**:
  - Toggle registration on/off
  - Accessible to Admin and Co-Admin

### 3. Role-Based UI
- Buttons show/hide based on user role
- Admin sees all controls
- Co-Admin sees plugin/settings controls only
- Role badge displayed in panel header

### 4. Bug Fixes
- Fixed plugin deletion: Admins/Co-Admins can now delete any plugin
- Added `delete_any_plugin()` function for admin deletion
- Updated `delete_plugin()` endpoint to check user role

### 5. Cron Updates
- Modified `cron.py` to preserve owner field during updates
- Parse JSON output from `launcher.py`
- Merge updated data with existing owner information
- Save updated plugins back to `plugins.json`

## Files Modified

1. **webserver.py**
   - Added `require_co_admin()` decorator
   - Added `get_current_user()` helper function
   - Added `/admin/users/<username>/role` endpoint
   - Added `/admin/plugins` and `/admin/plugins/<url>` endpoints
   - Updated `delete_plugin()` to support admin deletion
   - Removed email field from user responses

2. **create_admin.py**
   - Added role field to admin user creation
   - Removed email field

3. **cron.py**
   - Modified `update_plugin()` to return plugin data
   - Added `save_plugins()` function
   - Updated main loop to preserve owner field

4. **users.json**
   - Added role field to existing users
   - Removed email field

5. **components/admin/admin.html**
   - Complete redesign with role-based UI
   - Added user role management dropdown
   - Added plugin management section
   - Dynamic button visibility based on role

## API Endpoints

### New Endpoints
- `POST /admin/users/<username>/role` - Change user role (Admin only)
- `GET /admin/plugins` - Get all plugins (Admin/Co-Admin)
- `DELETE /admin/plugins/<url>` - Delete any plugin (Admin/Co-Admin)

### Modified Endpoints
- `POST /admin/login` - Now returns role information
- `GET /admin/check-session` - Returns role and username
- `GET /admin/users` - Removed email, added role field
- `POST /delete_plugin` - Now checks role for admin deletion

## Usage

### Creating Admin User
```bash
python create_admin.py
```

### Accessing Admin Panel
1. Navigate to `/admin`
2. Login with admin credentials
3. Manage users, plugins, and settings based on role

### Promoting Users
1. Login as Admin
2. Go to Users section
3. Select role from dropdown for any user
4. Changes apply immediately
