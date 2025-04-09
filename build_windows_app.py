"""
Self-Contained Windows Desktop Application Builder for AMRS Maintenance System
This script builds a fully standalone Windows executable that never requires a web browser
and bundles all necessary dependencies inside the executable.
"""
import os
import sys
import subprocess
import shutil
import time
import tempfile
import platform
from pathlib import Path

# Configuration
APP_NAME = "AMRS Maintenance Tracker"
APP_VERSION = "1.0.0"
SERVER_URL = "https://amrs-preventative-maintenance.onrender.com"
OUTPUT_DIR = "dist"
BUILD_DIR = "build"
MAIN_SCRIPT = "amrs_standalone.py"
ICON_FILE = "amrs_icon.ico"
SPLASH_FILE = "splash.png"

print(f"Building {APP_NAME} v{APP_VERSION}")
print(f"This application will connect to: {SERVER_URL}")
print("-" * 60)

# Create output directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(BUILD_DIR, exist_ok=True)

# Create simple icon file if it doesn't exist
if not os.path.exists(ICON_FILE):
    try:
        from PIL import Image, ImageDraw
        
        # Create a simple orange square icon
        img = Image.new('RGB', (256, 256), color = (254, 121, 0))
        d = ImageDraw.Draw(img)
        d.rectangle((50, 50, 206, 206), fill=(255, 255, 255))
        d.text((70, 120), "AMRS", fill=(254, 121, 0), font_size=48)
        
        # Save in multiple formats
        img.save(ICON_FILE)
        img.save(SPLASH_FILE)
        print(f"Created icon file: {ICON_FILE}")
    except Exception as e:
        print(f"Could not create icon: {str(e)} - continuing without icon")

# Create a standalone application with embedded browser
print(f"Creating standalone application: {MAIN_SCRIPT}")

# First define the content as a template
template = """
import os
import sys
import time
import json
import sqlite3
import threading
import datetime
import uuid
import tempfile
import base64
import io
import re
import traceback
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from http.client import HTTPResponse

# Try to import UI libraries
try:
    # First try PyQt5
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWebEngineWidgets import *
    USING_QT5 = True
    USING_QT6 = False
    USING_TKINTER = False
except ImportError:
    try:
        # Next try PyQt6
        from PyQt6.QtWidgets import *
        from PyQt6.QtCore import *
        from PyQt6.QtGui import *
        from PyQt6.QtWebEngineWidgets import *
        from PyQt6.QtWebEngineCore import *
        USING_QT5 = False
        USING_QT6 = True
        USING_TKINTER = False
    except ImportError:
        # Last resort, fall back to tkinter
        import tkinter as tk
        from tkinter import ttk, messagebox, font
        from tkinter.scrolledtext import ScrolledText
        USING_QT5 = False
        USING_QT6 = False
        USING_TKINTER = True

# Application configuration
APP_NAME = "{APP_NAME}"
APP_VERSION = "{APP_VERSION}"
SERVER_URL = "{SERVER_URL}"
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".amrs-maintenance")
DB_PATH = os.path.join(CACHE_DIR, "offline_data.db")

# Create cache directory
os.makedirs(CACHE_DIR, exist_ok=True)

# Set up logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(CACHE_DIR, 'app.log')),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ===== OFFLINE DATABASE MANAGER =====
class OfflineManager:
    """Manages local data storage and server synchronization"""
    
    def __init__(self):
        self.server_url = SERVER_URL
        self.init_db()
        
    def init_db(self):
        """Initialize SQLite database tables"""
        try:
            log.info(f"Initializing offline database at {{DB_PATH}}")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Table for cached pages
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS cached_pages (
                url TEXT PRIMARY KEY,
                content TEXT,
                content_type TEXT,
                timestamp INTEGER
            )''')
            
            # Table for offline maintenance records
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS maintenance_records (
                id TEXT PRIMARY KEY,
                part_id TEXT,
                machine_id TEXT,
                site_id TEXT,
                date TEXT,
                comments TEXT,
                synced INTEGER DEFAULT 0
            )''')
            
            # Table for sites
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sites (
                id INTEGER PRIMARY KEY,
                name TEXT,
                location TEXT
            )''')
            
            # Table for machines
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS machines (
                id INTEGER PRIMARY KEY,
                name TEXT,
                site_id INTEGER,
                model TEXT,
                FOREIGN KEY (site_id) REFERENCES sites (id)
            )''')
            
            # Table for parts
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS parts (
                id INTEGER PRIMARY KEY,
                name TEXT,
                machine_id INTEGER,
                description TEXT,
                last_maintenance TEXT,
                next_maintenance TEXT,
                FOREIGN KEY (machine_id) REFERENCES machines (id)
            )''')
            
            conn.commit()
            conn.close()
            log.info("Database initialization complete")
        except Exception as e:
            log.error(f"Database initialization error: {{e}}")
            log.error(traceback.format_exc())
    
    def cache_page(self, url, content, content_type="text/html"):
        """Store a page in the cache"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            timestamp = int(time.time())
            
            cursor.execute(
                "INSERT OR REPLACE INTO cached_pages (url, content, content_type, timestamp) VALUES (?, ?, ?, ?)",
                (url, content, content_type, timestamp)
            )
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            log.error(f"Error caching page {{url}}: {{e}}")
            return False
    
    def get_cached_page(self, url):
        """Retrieve a page from cache"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute("SELECT content, content_type, timestamp FROM cached_pages WHERE url = ?", (url,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                content, content_type, timestamp = result
                age_hours = (int(time.time()) - timestamp) / 3600
                log.info(f"Found cached page for {{url}}, age: {{age_hours:.1f}} hours")
                return content, content_type
            
            return None, None
        except Exception as e:
            log.error(f"Error retrieving cached page {{url}}: {{e}}")
            return None, None
    
    def is_online(self, timeout=3):
        """Check if server is reachable"""
        try:
            with urlopen(f"{{self.server_url}}/health", timeout=timeout) as response:
                return response.getcode() == 200
        except:
            return False
    
    def fetch_url(self, url, timeout=5):
        """Fetch data from URL with appropriate error handling"""
        try:
            headers = {{
                'User-Agent': f'{{APP_NAME}}/{{APP_VERSION}}',
                'Accept': 'text/html,application/json,*/*'
            }}
            req = Request(url, headers=headers)
            
            with urlopen(req, timeout=timeout) as response:
                content = response.read()
                content_type = response.getheader('Content-Type', 'text/html')
                
                # Handle different content types
                if content_type.startswith('text/') or 'json' in content_type or 'javascript' in content_type or 'css' in content_type:
                    try:
                        # Try to decode as text
                        content_str = content.decode('utf-8')
                        
                        # Cache the content
                        self.cache_page(url, content_str, content_type)
                        return content_str, content_type, None
                    except UnicodeDecodeError:
                        # Handle binary data
                        return content, content_type, None
                else:
                    # Binary data (images, etc.)
                    return content, content_type, None
                    
        except HTTPError as e:
            log.error(f"HTTP Error {{e.code}} for {{url}}: {{e.reason}}")
            return None, None, str(e)
        except URLError as e:
            log.error(f"URL Error for {{url}}: {{e.reason}}")
            return None, None, str(e)
        except Exception as e:
            log.error(f"Error fetching {{url}}: {{str(e)}}")
            return None, None, str(e)

# ===== QT APPLICATION (PYQT5/6) =====
class StandaloneQtApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.offline_manager = OfflineManager()
        
        # Set application details
        if USING_QT5:
            self.app.setApplicationName(APP_NAME)
            self.app.setApplicationVersion(APP_VERSION)
            self.app.setWindowIcon(QIcon("{ICON_FILE}") if os.path.exists("{ICON_FILE}") else QIcon())
        elif USING_QT6:
            self.app.setApplicationName(APP_NAME)
            self.app.setApplicationVersion(APP_VERSION)
            self.app.setWindowIcon(QIcon("{ICON_FILE}") if os.path.exists("{ICON_FILE}") else QIcon())
        
        # Create splash screen if file exists
        self.show_splash_screen()
        
        # Create main window after small delay
        if USING_QT5:
            QTimer.singleShot(1500, self.create_main_window)
        else:
            # For Qt6
            timer = QTimer()
            timer.singleShot(1500, self.create_main_window)
            
        # Start the application event loop
        sys.exit(self.app.exec_() if USING_QT5 else self.app.exec())
    
    def show_splash_screen(self):
        """Show splash screen while app is loading"""
        try:
            if os.path.exists("{SPLASH_FILE}"):
                # Create pixmap from file
                splash_pix = QPixmap("{SPLASH_FILE}")
                
                # Scale if needed
                if splash_pix.width() > 400:
                    splash_pix = splash_pix.scaledToWidth(400, Qt.SmoothTransformation if USING_QT5 else Qt.TransformationMode.SmoothTransformation)
                    
                # Create and show splash screen
                self.splash = QSplashScreen(splash_pix)
                self.splash.show()
                
                # Process events to ensure splash is displayed
                self.app.processEvents()
        except Exception as e:
            log.error(f"Error showing splash screen: {{e}}")
    
    def create_main_window(self):
        """Create the main application window"""
        # Close splash screen if it exists
        if hasattr(self, 'splash'):
            self.splash.close()
        
        # Create main window
        self.main_window = MainWindow(self.offline_manager)
        self.main_window.show()

# Main application window
class MainWindow(QMainWindow):
    def __init__(self, offline_manager):
        super().__init__()
        self.offline_manager = offline_manager
        
        # Window properties
        self.setWindowTitle(APP_NAME)
        self.resize(1024, 768)
        self.setMinimumSize(800, 600)
        
        # Set window icon
        if os.path.exists("{ICON_FILE}"):
            self.setWindowIcon(QIcon("{ICON_FILE}"))
            
        # Create actions and menus
        self.create_actions()
        self.create_menus()
        
        # Create status bar
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Starting application...")
        
        # Create toolbar
        self.create_toolbar()
        
        # Central widget with web view
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Create web view
        self.create_web_view()
        
        # Connection status timer
        self.connection_timer = QTimer(self)
        self.connection_timer.timeout.connect(self.check_connection)
        self.connection_timer.start(30000)  # Check every 30 seconds
        
        # Load initial page
        self.check_connection()
        self.web_view.load(QUrl(SERVER_URL))
        
    def create_actions(self):
        """Create all menu and toolbar actions"""
        if USING_QT5:
            # Qt5 action creation
            self.home_action = QAction("Home", self)
            self.home_action.triggered.connect(lambda: self.web_view.load(QUrl(SERVER_URL)))
            self.home_action.setShortcut("Ctrl+H")
            
            self.refresh_action = QAction("Refresh", self)
            self.refresh_action.triggered.connect(self.web_view.reload)
            self.refresh_action.setShortcut("F5")
            
            self.back_action = QAction("Back", self)
            self.back_action.triggered.connect(self.web_view.back)
            self.back_action.setShortcut("Alt+Left")
            
            self.forward_action = QAction("Forward", self)
            self.forward_action.triggered.connect(self.web_view.forward)
            self.forward_action.setShortcut("Alt+Right")
            
            self.exit_action = QAction("Exit", self)
            self.exit_action.triggered.connect(self.close)
            self.exit_action.setShortcut("Alt+F4")
            
            self.dashboard_action = QAction("Dashboard", self)
            self.dashboard_action.triggered.connect(lambda: self.web_view.load(QUrl(f"{{SERVER_URL}}/dashboard")))
            
            self.sites_action = QAction("Sites", self)
            self.sites_action.triggered.connect(lambda: self.web_view.load(QUrl(f"{{SERVER_URL}}/sites")))
            
            self.machines_action = QAction("Machines", self)
            self.machines_action.triggered.connect(lambda: self.web_view.load(QUrl(f"{{SERVER_URL}}/machines")))
            
            self.maintenance_action = QAction("Maintenance", self)
            self.maintenance_action.triggered.connect(lambda: self.web_view.load(QUrl(f"{{SERVER_URL}}/maintenance")))
            
            self.cache_action = QAction("Cache Current Page", self)
            self.cache_action.triggered.connect(self.cache_current_page)
            
            self.clear_cache_action = QAction("Clear Cache", self)
            self.clear_cache_action.triggered.connect(self.clear_cache)
            
            self.about_action = QAction("About", self)
            self.about_action.triggered.connect(self.show_about)
            
        else:
            # Qt6 action creation
            self.home_action = QAction("Home")
            self.home_action.triggered.connect(lambda: self.web_view.load(QUrl(SERVER_URL)))
            self.home_action.setShortcut("Ctrl+H")
            
            self.refresh_action = QAction("Refresh")
            self.refresh_action.triggered.connect(self.web_view.reload)
            self.refresh_action.setShortcut("F5")
            
            self.back_action = QAction("Back")
            self.back_action.triggered.connect(self.web_view.back)
            self.back_action.setShortcut("Alt+Left")
            
            self.forward_action = QAction("Forward")
            self.forward_action.triggered.connect(self.web_view.forward)
            self.forward_action.setShortcut("Alt+Right")
            
            self.exit_action = QAction("Exit")
            self.exit_action.triggered.connect(self.close)
            self.exit_action.setShortcut("Alt+F4")
            
            self.dashboard_action = QAction("Dashboard")
            self.dashboard_action.triggered.connect(lambda: self.web_view.load(QUrl(f"{{SERVER_URL}}/dashboard")))
            
            self.sites_action = QAction("Sites")
            self.sites_action.triggered.connect(lambda: self.web_view.load(QUrl(f"{{SERVER_URL}}/sites")))
            
            self.machines_action = QAction("Machines")
            self.machines_action.triggered.connect(lambda: self.web_view.load(QUrl(f"{{SERVER_URL}}/machines")))
            
            self.maintenance_action = QAction("Maintenance")
            self.maintenance_action.triggered.connect(lambda: self.web_view.load(QUrl(f"{{SERVER_URL}}/maintenance")))
            
            self.cache_action = QAction("Cache Current Page")
            self.cache_action.triggered.connect(self.cache_current_page)
            
            self.clear_cache_action = QAction("Clear Cache")
            self.clear_cache_action.triggered.connect(self.clear_cache)
            
            self.about_action = QAction("About")
            self.about_action.triggered.connect(self.show_about)
    
    def create_menus(self):
        """Create application menu structure"""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(self.home_action)
        file_menu.addAction(self.refresh_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        # View menu
        view_menu = self.menuBar().addMenu("&View")
        view_menu.addAction(self.back_action)
        view_menu.addAction(self.forward_action)
        view_menu.addSeparator()
        view_menu.addAction(self.dashboard_action)
        view_menu.addAction(self.sites_action)
        view_menu.addAction(self.machines_action)
        view_menu.addAction(self.maintenance_action)
        
        # Tools menu
        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.addAction(self.cache_action)
        tools_menu.addAction(self.clear_cache_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.addAction(self.about_action)
    
    def create_toolbar(self):
        """Create main toolbar with navigation controls"""
        self.toolbar = self.addToolBar("Navigation")
        self.toolbar.setMovable(False)
        
        # Add navigation actions
        self.toolbar.addAction(self.back_action)
        self.toolbar.addAction(self.forward_action)
        self.toolbar.addAction(self.home_action)
        self.toolbar.addAction(self.refresh_action)
        
        # Add URL field
        self.url_edit = QLineEdit()
        self.url_edit.returnPressed.connect(self.navigate_to_url)
        self.toolbar.addWidget(self.url_edit)
        
        # Add spacer to push connection status to right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.toolbar.addWidget(spacer)
        
        # Add connection status widget
        self.connection_status = QLabel("Offline")
        self.connection_status.setStyleSheet("color: red; padding: 2px 8px;")
        self.toolbar.addWidget(self.connection_status)
    
    def create_web_view(self):
        """Create web view component"""
        if USING_QT5:
            # Create profile for custom user agent and cache handling
            self.web_profile = QWebEngineProfile(APP_NAME.lower().replace(" ", "-"), self)
            self.web_profile.setHttpUserAgent(f"{APP_NAME}/{APP_VERSION} QtWebEngine")
            
            # Create page with custom profile
            self.web_page = QWebEnginePage(self.web_profile, self)
            
            # Create view
            self.web_view = QWebEngineView(self)
            self.web_view.setPage(self.web_page)
            
            # Connect signals
            self.web_view.loadStarted.connect(lambda: self.statusBar.showMessage("Loading..."))
            self.web_view.loadFinished.connect(lambda ok: self.handle_page_load(ok))
            self.web_view.urlChanged.connect(self.url_changed)
            
        elif USING_QT6:
            # For Qt6
            # Create profile for custom user agent and cache handling
            self.web_profile = QWebEngineProfile(APP_NAME.lower().replace(" ", "-"), self)
            self.web_profile.setHttpUserAgent(f"{APP_NAME}/{APP_VERSION} QtWebEngine")
            
            # Create page with custom profile
            self.web_page = QWebEnginePage(self.web_profile, self)
            
            # Create view
            self.web_view = QWebEngineView(self)
            self.web_view.setPage(self.web_page)
            
            # Connect signals
            self.web_view.loadStarted.connect(lambda: self.statusBar.showMessage("Loading..."))
            self.web_view.loadFinished.connect(lambda ok: self.handle_page_load(ok))
            self.web_view.urlChanged.connect(self.url_changed)
            
        # Add web view to layout
        self.layout.addWidget(self.web_view)
    
    def check_connection(self):
        """Check connection status and update UI"""
        # Check connection in a separate thread to avoid UI freezing
        threading.Thread(target=self.check_connection_thread, daemon=True).start()
    
    def check_connection_thread(self):
        """Thread function to check connection"""
        is_online = self.offline_manager.is_online()
        
        # Update UI in the main thread
        if USING_QT5:
            # For PyQt5
            QMetaObject.invokeMethod(
                self, 
                "update_connection_status", 
                Qt.QueuedConnection,
                Q_ARG(bool, is_online)
            )
        elif USING_QT6:
            # For PyQt6
            self.update_connection_status_qt6(is_online)
    
    # For PyQt5
    @pyqtSlot(bool)
    def update_connection_status(self, is_online):
        """Update connection status UI elements"""
        if is_online:
            self.connection_status.setText("Online")
            self.connection_status.setStyleSheet("color: green; font-weight: bold; padding: 2px 8px;")
        else:
            self.connection_status.setText("Offline")
            self.connection_status.setStyleSheet("color: red; font-weight: bold; padding: 2px 8px;")
    
    # For PyQt6
    def update_connection_status_qt6(self, is_online):
        """Update connection status for Qt6"""
        if is_online:
            self.connection_status.setText("Online")
            self.connection_status.setStyleSheet("color: green; font-weight: bold; padding: 2px 8px;")
        else:
            self.connection_status.setText("Offline")
            self.connection_status.setStyleSheet("color: red; font-weight: bold; padding: 2px 8px;")
    
    def handle_page_load(self, ok):
        """Handle page load completion"""
        if ok:
            self.statusBar.showMessage("Page loaded", 3000)
            
            # Get the current URL
            current_url = self.web_view.url().toString()
            
            # Update URL field
            self.url_edit.setText(current_url)
            
            # Auto-cache successful pages for offline use
            threading.Thread(
                target=self.cache_page_thread,
                args=(current_url,),
                daemon=True
            ).start()
        else:
            self.statusBar.showMessage("Page failed to load", 3000)
            
            # Try to load from cache
            self.try_load_from_cache(self.web_view.url().toString())
    
    def url_changed(self, url):
        """Handle URL changes"""
        url_str = url.toString()
        self.url_edit.setText(url_str)
    
    def navigate_to_url(self):
        """Navigate to URL from the URL bar"""
        url_text = self.url_edit.text().strip()
        
        # Add protocol if missing
        if not url_text.startswith(('http://', 'https://')):
            # If it's a relative URL for our server
            if not url_text.startswith('/') and '.' not in url_text:
                url_text = f"{SERVER_URL}/{url_text}"
            elif url_text.startswith('/'):
                url_text = f"{SERVER_URL}{url_text}"
            else:
                url_text = f"https://{url_text}"
                
        self.web_view.load(QUrl(url_text))
    
    def cache_page_thread(self, url):
        """Cache a page in a background thread"""
        try:
            # Get HTML content from the web view
            def get_html(callback):
                if USING_QT5:
                    self.web_view.page().toHtml(callback)
                else:
                    # Qt6 version
                    self.web_view.page().toHtml(callback)
            
            # Callback to store the HTML
            def store_html(html):
                if html:
                    # Store in cache
                    self.offline_manager.cache_page(url, html, "text/html")
            
            # Get and store HTML
            get_html(store_html)
        except Exception as e:
            log.error(f"Error caching page: {{e}}")
    
    def cache_current_page(self):
        """Cache the currently displayed page"""
        current_url = self.web_view.url().toString()
        self.cache_page_thread(current_url)
        self.statusBar.showMessage(f"Page cached for offline use", 3000)
    
    def clear_cache(self):
        """Clear the offline cache"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cached_pages")
            conn.commit()
            conn.close()
            self.statusBar.showMessage("Cache cleared", 3000)
        except Exception as e:
            self.statusBar.showMessage(f"Error clearing cache: {{str(e)}}", 5000)
    
    def try_load_from_cache(self, url):
        """Try to load page from cache when online fetch fails"""
        content, content_type = self.offline_manager.get_cached_page(url)
        
        if content:
            # We have a cached version, display it
            if USING_QT5:
                self.web_view.setHtml(content, QUrl(url))
            else:
                self.web_view.setHtml(content, QUrl(url))
                
            self.statusBar.showMessage("Loaded from cache (offline mode)", 3000)
        else:
            # No cached version, show error page
            error_html = f'''
            <html>
            <head><title>Page not available offline</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; text-align: center; }}
                h1 {{ color: #FE7900; }}
                .btn {{ display: inline-block; background: #FE7900; color: white; padding: 10px 20px; 
                       text-decoration: none; border-radius: 4px; margin-top: 20px; }}
                .error {{ color: #d9534f; }}
            </style>
            </head>
            <body>
                <div class="container">
                    <h1>{APP_NAME}</h1>
                    <h2>Page Not Available Offline</h2>
                    <p class="error">The requested page is not available offline:</p>
                    <p><strong>{{url}}</strong></p>
                    <p>Please check your internet connection and try again.</p>
                    <p><a href="{SERVER_URL}/dashboard" class="btn">Go to Dashboard</a></p>
                </div>
            </body>
            </html>
            '''
            
            if USING_QT5:
                self.web_view.setHtml(error_html, QUrl(url))
            else:
                self.web_view.setHtml(error_html, QUrl(url))
    
    def show_about(self):
        """Show about dialog"""
        about_text = f'''
        <h1>{APP_NAME}</h1>
        <p>Version: {APP_VERSION}</p>
        <p>A standalone application for the AMRS Preventative Maintenance System.</p>
        <p>Server URL: {SERVER_URL}</p>
        '''
        
        if USING_QT5:
            QMessageBox.about(self, f"About {APP_NAME}", about_text)
        else:
            about_box = QMessageBox()
            about_box.setWindowTitle(f"About {APP_NAME}")
            about_box.setText(about_text)
            about_box.exec()

# ===== TKINTER APPLICATION =====
class StandaloneTkApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)
        
        # Set window icon if available
        try:
            if os.path.exists("{ICON_FILE}"):
                self.root.iconbitmap("{ICON_FILE}")
        except:
            pass
            
        self.offline_manager = OfflineManager()
        
        # Create UI elements
        self.create_menus()
        self.create_toolbar()
        self.create_status_bar()
        self.create_main_frame()
        
        # Load initial URL
        self.load_url(SERVER_URL)
        
        # Check connection periodically
        self.check_connection()
        self.root.after(30000, self.periodic_connection_check)
        
        # Start the application
        self.root.mainloop()
    
    def create_menus(self):
        """Create application menus"""
        menubar = tk.Menu(self.root)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Home", command=lambda: self.load_url(SERVER_URL))
        file_menu.add_command(label="Refresh", command=self.refresh)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Navigate menu
        nav_menu = tk.Menu(menubar, tearoff=0)
        nav_menu.add_command(label="Dashboard", command=lambda: self.load_url(f"{SERVER_URL}/dashboard"))
        nav_menu.add_command(label="Sites", command=lambda: self.load_url(f"{SERVER_URL}/sites"))
        nav_menu.add_command(label="Machines", command=lambda: self.load_url(f"{SERVER_URL}/machines"))
        nav_menu.add_command(label="Maintenance", command=lambda: self.load_url(f"{SERVER_URL}/maintenance"))
        menubar.add_cascade(label="Navigate", menu=nav_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        tools_menu.add_command(label="Cache Current Page", command=self.cache_current_page)
        tools_menu.add_command(label="Clear Cache", command=self.clear_cache)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        # Set the menu
        self.root.config(menu=menubar)
    
    def create_toolbar(self):
        """Create navigation toolbar"""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Back button
        back_btn = ttk.Button(toolbar, text="←", width=2, command=self.go_back)
        back_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Forward button
        forward_btn = ttk.Button(toolbar, text="→", width=2, command=self.go_forward)
        forward_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Home button
        home_btn = ttk.Button(toolbar, text="Home", command=lambda: self.load_url(SERVER_URL))
        home_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Refresh button
        refresh_btn = ttk.Button(toolbar, text="Refresh", command=self.refresh)
        refresh_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # URL entry
        self.url_var = tk.StringVar(value=SERVER_URL)
        url_entry = ttk.Entry(toolbar, textvariable=self.url_var, width=50)
        url_entry.pack(side=tk.LEFT, padx=4, pady=2, fill=tk.X, expand=True)
        url_entry.bind("<Return>", self.on_url_enter)
        
        # Go button
        go_btn = ttk.Button(toolbar, text="Go", command=self.navigate_to_url)
        go_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Connection status
        self.conn_status_var = tk.StringVar(value="Offline")
        self.conn_status = ttk.Label(toolbar, textvariable=self.conn_status_var, width=10, 
                                   foreground="red", font=("Arial", 9, "bold"))
        self.conn_status.pack(side=tk.RIGHT, padx=4, pady=2)
    
    def create_status_bar(self):
        """Create status bar"""
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                                  relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_main_frame(self):
        """Create main content frame"""
        # Create main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Create HTML display widget
        self.content_view = ScrolledText(self.main_frame, wrap=tk.WORD)
        self.content_view.pack(fill=tk.BOTH, expand=True)
        
        # Configure tags for styling
        self.content_view.tag_configure("heading1", font=("Arial", 18, "bold"))
        self.content_view.tag_configure("heading2", font=("Arial", 16, "bold"))
        self.content_view.tag_configure("heading3", font=("Arial", 14, "bold"))
        self.content_view.tag_configure("normal", font=("Arial", 12))
        self.content_view.tag_configure("error", foreground="red")
        self.content_view.tag_configure("warning", foreground="orange")
        self.content_view.tag_configure("success", foreground="green")
        self.content_view.tag_configure("link", foreground="blue", underline=1)
        
        # Navigation history
        self.history = []
        self.current_position = -1
        self.current_url = None
    
    def on_url_enter(self, event):
        """Handle URL entry keypress"""
        self.navigate_to_url()
    
    def navigate_to_url(self):
        """Navigate to URL from entry field"""
        url = self.url_var.get().strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            # If it's a relative URL for our server
            if not url.startswith('/') and '.' not in url:
                url = f"{SERVER_URL}/{url}"
            elif url.startswith('/'):
                url = f"{SERVER_URL}{url}"
            else:
                url = f"https://{url}"
        
        self.load_url(url)
    
    def load_url(self, url):
        """Load content from URL"""
        self.status_var.set(f"Loading {url}...")
        self.url_var.set(url)
        self.current_url = url
        
        # Update history
        if self.current_position >= 0 and self.history[self.current_position] != url:
            # Remove forward history
            self.history = self.history[:self.current_position + 1]
            self.history.append(url)
            self.current_position = len(self.history) - 1
        elif self.current_position < 0:
            self.history.append(url)
            self.current_position = 0
        
        # Check if offline cache has the content
        content, content_type = self.offline_manager.get_cached_page(url)
        
        # Try to fetch online if not in cache
        if not content and self.offline_manager.is_online():
            threading.Thread(target=self.fetch_url_thread, args=(url,), daemon=True).start()
        else:
            # Use cached content or show offline message
            if content:
                self.display_content(content, content_type, url)
                self.status_var.set(f"Loaded from cache: {url}")
            else:
                self.display_offline_message(url)
                self.status_var.set(f"Unable to load: {url}")
    
    def fetch_url_thread(self, url):
        """Fetch URL content in background thread"""
        content, content_type, error = self.offline_manager.fetch_url(url)
        
        if content:
            # Update UI in main thread
            self.root.after(0, lambda: self.display_content(content, content_type, url))
            self.root.after(0, lambda: self.status_var.set(f"Loaded: {url}"))
        else:
            # Try to get from cache as fallback
            cached_content, cached_type = self.offline_manager.get_cached_page(url)
            
            if cached_content:
                self.root.after(0, lambda: self.display_content(cached_content, cached_type, url))
                self.root.after(0, lambda: self.status_var.set(f"Loaded from cache: {url}"))
            else:
                # Show error
                self.root.after(0, lambda: self.display_offline_message(url, error))
                self.root.after(0, lambda: self.status_var.set(f"Error loading {url}: {error}"))
    
    def display_content(self, content, content_type, url):
        """Display content in the view"""
        # Clear current content
        self.content_view.delete(1.0, tk.END)
        
        if isinstance(content, bytes):
            # Binary content - try to decode
            try:
                content = content.decode('utf-8')
            except UnicodeDecodeError:
                # Can't display binary content
                self.content_view.insert(tk.END, f"Binary content cannot be displayed: {content_type}\\n", "error")
                return
        
        # Simple HTML parsing - extract title and body
        title = url.split('/')[-1] if url else "Unknown"
        body = content
        
        # Try to extract title
        title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE|re.DOTALL)
        if title_match:
            title = title_match.group(1)
        
        # Extract body if possible
        body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.IGNORECASE|re.DOTALL)
        if body_match:
            body = body_match.group(1)
        
        # Insert title
        self.content_view.insert(tk.END, f"{title}\\n\\n", "heading1")
        
        # Basic HTML cleaning - remove tags
        body = re.sub(r'<[^>]*>', ' ', body)
        body = re.sub(r'\\s+', ' ', body)
        
        # Insert body
        self.content_view.insert(tk.END, body, "normal")
        
        # Make links clickable
        self.bind_links(url)
    
    def bind_links(self, base_url):
        """Make links in the content clickable"""
        pass  # In a real implementation, would identify links and make them clickable
    
    def display_offline_message(self, url, error=None):
        """Display offline error message"""
        self.content_view.delete(1.0, tk.END)
        
        # Insert page title
        self.content_view.insert(tk.END, f"{APP_NAME}\\n\\n", "heading1")
        
        # Insert error heading
        self.content_view.insert(tk.END, "Page Not Available Offline\\n\\n", "heading2")
        
        # Insert URL
        self.content_view.insert(tk.END, f"The requested page is not available offline:\\n", "normal")
        self.content_view.insert(tk.END, f"{url}\\n\\n", "error")
        
        # Insert error details if available
        if error:
            self.content_view.insert(tk.END, f"Error: {error}\\n\\n", "error")
            
        self.content_view.insert(tk.END, "Please check your internet connection and try again.\\n\\n", "normal")
        
        # Add some quick links
        self.content_view.insert(tk.END, "Quick Links:\\n", "heading3")
        self.content_view.insert(tk.END, "• Dashboard\\n", "link")
        self.content_view.insert(tk.END, "• Sites\\n", "link")
        self.content_view.insert(tk.END, "• Machines\\n", "link")
        self.content_view.insert(tk.END, "• Maintenance\\n", "link")
    
    def go_back(self):
        """Navigate backwards in history"""
        if self.current_position > 0:
            self.current_position -= 1
            self.load_url(self.history[self.current_position])
    
    def go_forward(self):
        """Navigate forwards in history"""
        if self.current_position < len(self.history) - 1:
            self.current_position += 1
            self.load_url(self.history[self.current_position])
    
    def refresh(self):
        """Refresh current page"""
        if self.current_url:
            self.load_url(self.current_url)
    
    def check_connection(self):
        """Check server connection status"""
        threading.Thread(target=self.check_connection_thread, daemon=True).start()
    
    def check_connection_thread(self):
        """Thread function to check connection"""
        is_online = self.offline_manager.is_online()
        
        # Update UI in main thread
        self.root.after(0, lambda: self.update_connection_status(is_online))
    
    def update_connection_status(self, is_online):
        """Update connection status UI elements"""
        if is_online:
            self.conn_status_var.set("Online")
            self.conn_status.configure(foreground="green")
        else:
            self.conn_status_var.set("Offline")
            self.conn_status.configure(foreground="red")
    
    def periodic_connection_check(self):
        """Periodically check connection status"""
        self.check_connection()
        self.root.after(30000, self.periodic_connection_check)
    
    def cache_current_page(self):
        """Cache the current page for offline use"""
        if not self.current_url:
            return
        
        threading.Thread(
            target=lambda: self.offline_manager.fetch_url(self.current_url), 
            daemon=True
        ).start()
        
        self.status_var.set(f"Caching {self.current_url} for offline use")
    
    def clear_cache(self):
        """Clear the offline cache"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cached_pages")
            conn.commit()
            conn.close()
            self.status_var.set("Cache cleared")
        except Exception as e:
            self.status_var.set(f"Error clearing cache: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo(
            f"About {APP_NAME}",
            f"{APP_NAME} v{APP_VERSION}\\n\\n" +
            f"A standalone application for the AMRS Preventative Maintenance System.\\n\\n" +
            f"Server URL: {SERVER_URL}"
        )

# Main entry point
if __name__ == "__main__":
    try:
        # Start the appropriate UI
        if USING_QT5 or USING_QT6:
            # Use Qt interface
            log.info("Starting Qt application")
            StandaloneQtApp()
        elif USING_TKINTER:
            # Use Tkinter fallback
            log.info("Starting Tkinter application")
            StandaloneTkApp()
        else:
            # If this happens, we've hit an impossible state (imports would have failed earlier)
            raise RuntimeError("No suitable UI framework available")
    except Exception as e:
        # Get error details
        error_details = traceback.format_exc()
        log.critical(f"Fatal application error: {{e}}\\n{{error_details}}")
        
        # Show error message
        if USING_TKINTER:
            messagebox.showerror(
                f"Error Starting {{APP_NAME}}",
                f"An error occurred while starting the application:\\n\\n{{str(e)}}\\n\\n" +
                f"Please check the log file at:\\n{{os.path.join(CACHE_DIR, 'app.log')}}"
            )
        else:
            # Try to use system dialog
            if sys.platform.startswith("win"):
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0,
                    f"An error occurred while starting the application:\\n\\n{{str(e)}}\\n\\n" +
                    f"Please check the log file at:\\n{{os.path.join(CACHE_DIR, 'app.log')}}",
                    f"Error Starting {{APP_NAME}}",
                    0x10  # MB_ICONERROR
                )
            else:
                print(f"ERROR: {{str(e)}}")
                print(f"See log file: {{os.path.join(CACHE_DIR, 'app.log')}}")
"""

# Format the template with our variables
formatted_content = template.format(
    APP_NAME=APP_NAME,
    APP_VERSION=APP_VERSION,
    SERVER_URL=SERVER_URL,
    ICON_FILE=ICON_FILE,
    SPLASH_FILE=SPLASH_FILE
)

# Write the formatted content to file
with open(MAIN_SCRIPT, "w", encoding="utf-8") as f:
    f.write(formatted_content)

print(f"Created {MAIN_SCRIPT}")

# Try to install necessary dependencies for build
print("Installing required dependencies for build...")
try:
    # Install PyInstaller if not already installed
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Try installing PyQt5 for better UI
    try:
        print("Installing PyQt5...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "PyQt5", "PyQtWebEngine"],
            check=True
        )
        print("Successfully installed PyQt5")
    except:
        print("Could not install PyQt5")
        
    # Install Pillow for icon creation
    try:
        print("Installing Pillow for icon creation...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "Pillow"],
            check=True
        )
        print("Successfully installed Pillow")
    except:
        print("Could not install Pillow - continuing without custom icon")
        
except Exception as e:
    print(f"Error installing dependencies: {e}")
    print("Continuing with available packages...")

# Build with PyInstaller
print("\nBuilding executable with PyInstaller...")
try:
    # Create spec file with all dependencies
    spec_file = f"{os.path.splitext(MAIN_SCRIPT)[0]}.spec"
    
    with open(spec_file, "w") as f:
        f.write(f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{MAIN_SCRIPT}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtWebEngineWidgets',
                  'PyQt6', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'PyQt6.QtWebEngineWidgets',
                  'tkinter', 'sqlite3', 'logging', 'urllib', 'http.client'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Add icon and splash image
if os.path.exists('{ICON_FILE}'):
    a.datas += [('{ICON_FILE}', '{ICON_FILE}', 'DATA')]
    
if os.path.exists('{SPLASH_FILE}'):
    a.datas += [('{SPLASH_FILE}', '{SPLASH_FILE}', 'DATA')]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME.replace(" ", "")}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='{ICON_FILE}' if os.path.exists('{ICON_FILE}') else None,
    version='file_version_info.txt',
)
""")
    
    # Create version info file
    with open("file_version_info.txt", "w") as f:
        f.write(f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({APP_VERSION.replace('.', ', ')}, 0),
    prodvers=({APP_VERSION.replace('.', ', ')}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'AMRS'),
        StringStruct(u'FileDescription', u'{APP_NAME}'),
        StringStruct(u'FileVersion', u'{APP_VERSION}'),
        StringStruct(u'InternalName', u'{APP_NAME}'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2023 AMRS'),
        StringStruct(u'OriginalFilename', u'{APP_NAME.replace(" ", "")}.exe'),
        StringStruct(u'ProductName', u'{APP_NAME}'),
        StringStruct(u'ProductVersion', u'{APP_VERSION}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
""")
    
    # Run PyInstaller with the spec file
    subprocess.run(
        [sys.executable, "-m", "PyInstaller", "--clean", spec_file],
        check=True
    )
    
    # Check if executable was created
    exe_path = os.path.join("dist", f"{APP_NAME.replace(' ', '')}.exe")
    if os.path.exists(exe_path):
        print(f"\n✅ Successfully built {exe_path}")
        
        # Copy to output directory if different
        if OUTPUT_DIR != "dist":
            shutil.copy(exe_path, os.path.join(OUTPUT_DIR, os.path.basename(exe_path)))
            print(f"Copied to {os.path.join(OUTPUT_DIR, os.path.basename(exe_path))}")
    else:
        print(f"\n❌ Failed to create executable at {exe_path}")
        
except Exception as e:
    print(f"\n❌ PyInstaller build failed: {e}")
    print("Check logs for details.")

print("\n" + "=" * 60)
print(f"Build process complete for {APP_NAME} v{APP_VERSION}")
print(f"The application will connect to: {SERVER_URL}")
print(f"Executable should be located in: {os.path.abspath(OUTPUT_DIR)}")
print("=" * 60)