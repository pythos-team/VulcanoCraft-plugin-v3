# VulcanoCraft Plugin Repository Tool

This repository contains a **Python-based tool** that automatically **fetches plugin information** and keeps it up to date.  
It includes a small web interface for viewing the collected data, but its main focus is background automation.

---

## 🚀 Features
- 🔄 **Automated Updates** – Background service fetches and updates plugin information hourly
- 👥 **User Management** – Registration, login, and role-based permissions (User, Co-Admin, Admin)
- 🎨 **Modern UI** – Responsive design with animations and filtering capabilities
- 🔍 **Advanced Filtering** – Search by name, version, or platform
- 🛡️ **Admin Panel** – Manage users, plugins, and system settings
- ⚡ **Optimized Scraping** – Fast plugin data fetching with Playwright
- 🖼️ **Smart Icons** – Automatic fallback to letter-based logos for broken images

---

## 📂 Repository Structure
```
├── cron.py                 # Background updater (hourly plugin updates)
├── webserver.py            # Flask web server with API endpoints
├── launcher.py             # Plugin data fetcher
├── create_admin.py         # Admin account creation utility
├── fetchers/               # Platform-specific data scrapers
│   ├── author.py
│   ├── description.py
│   ├── icon.py
│   ├── titles.py
│   └── versions.py
├── components/
│   ├── admin/
│   │   └── admin.html      # Admin panel interface
│   └── user/
│       └── login.html      # User login/registration page
├── images/                 # UI assets and icons
├── index.html              # Main plugin browser interface
├── style.css               # Styling and animations
├── plugins.json            # Plugin database
├── users.json              # User accounts database
├── settings.json           # Application settings
└── requirements.txt        # Python dependencies
```

---

## 🛠️ Installation & Usage

### Requirements
- Python 3.9+
- pip (Python package manager)

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install

# Create admin account
python create_admin.py
```

### Running the Application

**Start the web server:**
```bash
python webserver.py
```
Access at: `http://localhost:5000`

**Start background updater (optional):**
```bash
python cron.py
```
Updates all plugins every hour automatically.

---

## 👥 User Roles

- **User** – Add, view, and delete own plugins
- **Co-Admin** – Manage all plugins and view users
- **Admin** – Full access including user management and settings

---

## 🌐 Supported Platforms

- **SpigotMC** – `spigotmc.org/resources/*`
- **Modrinth** – `modrinth.com/plugin/*`
- **Hangar** – `hangar.papermc.io/*/*`
- **CurseForge** – `curseforge.com/minecraft/*`

---

## 📝 API Endpoints

- `GET /` – Main plugin browser
- `GET /login-page` – User login/registration
- `GET /admin` – Admin panel
- `GET /api/plugins/public` – Get all plugins (public)
- `POST /add_plugin` – Add new plugin (authenticated)
- `POST /delete_plugin` – Delete plugin (authenticated)
- `POST /login` – User login
- `POST /register` – User registration
- `GET /auth-status` – Check authentication status

---
<p align="right">made possible by <code>_.g.a.u.t.a.m._</code> on discord.</p>
<p align="right">made possible by (Swapnanilb)[https://github.com/Swapnanilb]</p>
