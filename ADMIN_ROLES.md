# Admin Role System Documentation

## Role Hierarchy

### 1. Admin
- **Full Control**: Complete access to all system features
- **Permissions**:
  - Promote/demote users between all roles (User, Co-Admin, Admin)
  - Delete any user (except the main admin account)
  - Delete any plugin regardless of owner
  - Manage system settings (enable/disable registration)
  - View all users and plugins

### 2. Co-Admin
- **Plugin & Settings Management**: Can manage plugins and settings but not user roles
- **Permissions**:
  - Delete any plugin regardless of owner
  - Manage system settings (enable/disable registration)
  - View all users and plugins
  - **Cannot**: Promote/demote users

### 3. User
- **Basic Access**: Standard user with limited permissions
- **Permissions**:
  - Add plugins to the repository
  - Delete only their own plugins
  - View all public plugins

## Access Control

### Admin Panel Access
- URL: `/admin`
- Only Admin and Co-Admin roles can access
- Regular users are denied access

### Plugin Deletion
- **Admin/Co-Admin**: Can delete any plugin
- **User**: Can only delete plugins they own

### User Management
- **Admin**: Full control over user roles and deletion
- **Co-Admin**: View-only access to user list
- **User**: No access to user management

## Default Credentials
- Username: `admin`
- Password: `admin123`
- Role: `admin`

**Important**: Change the default password after first login!
