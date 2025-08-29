# VulcanoCraft Plugin Repository Tool

This repository contains a **Python-based tool** that automatically **fetches plugin information** and keeps it up to date.  
It includes a small web interface for viewing the collected data, but its main focus is background automation.

---

## 🚀 Features
- 🔄 **Automated Updates** – Fetches plugin information at regular intervals.  
- 📦 **Plugin Data Storage** – All plugins are listed and updated in `plugins.json`.  
- 🕒 **Scheduler Support** – `cron.py` handles automated background updates.  
- 🌐 **Simple Viewer** – Intuitive HTML/CSS/JS frontend to quickly browse plugin info.    

---

## 📂 Repository Structure
```
├── cron.py # Background updater (fetches plugins regularly)
├── fetchers/ # Scripts to fetch plugin data from different sources
├── images/ # Assets & icons
├── index.html # Minimal frontend to view plugin data
├── launcher.py # Starts the tool
├── plugins.json # Stored plugin data
├── style.css # Styling for the viewer
└── webserver.py # Simple webserver for local viewing
```

---

## 🛠️ Installation & Usage
### Requirements
- Python 3.9+
- ```pip install requirements.txt```
- (optional) ```playwright install```

### Run Fetcher / Updater
```python cron.py```

### Start webserver
```python webserver.py```
<br>
<br>
<br>
<br>
<br>
<p align="right">made possible by <code>_.g.a.u.t.a.m._</code> on discord.</p>
