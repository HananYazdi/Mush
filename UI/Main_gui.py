import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget,
                             QPushButton, QMessageBox, QLabel, QFileDialog, QHBoxLayout,
                             QFrame, QComboBox, QRadioButton, QButtonGroup, QStackedWidget,
                             QScrollArea, QSizePolicy, QGraphicsDropShadowEffect)
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
from PyQt5.QtCore import Qt, QSettings, QTranslator, QLocale
from firebase_admin import db, credentials, initialize_app
from Order_gui import OrderGUI
from Growing_bed_gui import GrowingBedGUI
from Customer_gui import CustomerGUI
from AnalyticsApp import AnalyticsApp
from FarmVisualGUI import FarmVisualGUI
from WarehouseGUI import WarehouseGUI
from AdminDashboard import AdminDashboard

# Initialize Firebase
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Current file location
PARENT_DIR = os.path.dirname(BASE_DIR)  # Parent directory
SERVICE_ACCOUNT_FILE = os.path.join(
    PARENT_DIR, "db", "farm-management-FireBase_credentials.json")
DATABASE_URL = "https://farm-management-86035-default-rtdb.europe-west1.firebasedatabase.app/"

# Check if the file exists
if not os.path.exists(SERVICE_ACCOUNT_FILE):
    raise FileNotFoundError(
        f"Could not find the Firebase credentials file at: {SERVICE_ACCOUNT_FILE}")

# Initialize Firebase
cred = credentials.Certificate(SERVICE_ACCOUNT_FILE)
initialize_app(cred, {"databaseURL": DATABASE_URL})

# Translation dictionaries for different languages
TRANSLATIONS = {
    'en': {
        'settings': 'Settings',
        'profile': 'Profile',
        'admin_name': 'Admin Name',
        'theme': 'Theme',
        'language': 'Language',
        'dark_mode': 'Dark Mode',
        'light_mode': 'Light Mode',
        'orders': 'Orders',
        'customers': 'Customers',
        'growing_beds': 'Growing Beds',
        'farm_visual': 'Farm Visual',
        'warehouse': 'Warehouse',
        'upload_excel': 'Upload Excel',
        'title': 'Mushroom Farm Management System'
    },
    'he': {
        'settings': 'הגדרות',
        'profile': 'פרופיל',
        'admin_name': 'שם מנהל',
        'theme': 'ערכת נושא',
        'language': 'שפה',
        'dark_mode': 'מצב כהה',
        'light_mode': 'מצב בהיר',
        'orders': 'הזמנות',
        'customers': 'לקוחות',
        'growing_beds': 'מצעי גידול',
        'farm_visual': 'תצוגת חווה',
        'warehouse': 'מחסן',
        'upload_excel': 'העלאת אקסל',
        'title': 'מערכת ניהול חוות פטריות'
    },
    'ar': {
        'settings': 'إعدادات',
        'profile': 'الملف الشخصي',
        'admin_name': 'اسم المشرف',
        'theme': 'المظهر',
        'language': 'اللغة',
        'dark_mode': 'الوضع الداكن',
        'light_mode': 'الوضع الفاتح',
        'orders': 'الطلبات',
        'customers': 'العملاء',
        'growing_beds': 'أسرّة النمو',
        'farm_visual': 'عرض المزرعة',
        'warehouse': 'المستودع',
        'upload_excel': 'تحميل إكسل',
        'title': 'نظام إدارة مزرعة الفطر'
    }
}


class Main_gui(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initialize window attributes
        self.order_gui = None
        self.customer_gui = None
        self.growing_bed_gui = None
        self.warehouse_gui = None
        self.farm_visual = None
        self.analytics_gui = None

        self.settings = QSettings('MushroomFarm', 'Main_gui')
        self.translator = QTranslator()
        self.current_language = self.settings.value('language', 'he')
        self.current_theme = self.settings.value('theme', 'light')

        # Initialize translations before creating UI
        self.current_translations = TRANSLATIONS[self.current_language]

        self.init_ui()
        self.apply_theme(self.current_theme)

        # Make window fullscreen
        self.showMaximized()

    def init_ui(self):
        # Set window properties with RTL support for Arabic and Hebrew
        self.setWindowTitle(self.tr('title'))

        # Set layout direction based on language
        if self.current_language in ['he', 'ar']:
            self.setLayoutDirection(Qt.RightToLeft)
        else:
            self.setLayoutDirection(Qt.LeftToRight)

        # Main layout
        self.main_layout = QHBoxLayout()
        self.main_layout.setSpacing(20)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        # Create settings panel
        settings_panel = self.create_settings_panel()
        self.main_layout.addWidget(settings_panel)

        # Create main content area
        content_layout = QVBoxLayout()
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)

        # Title with shadow
        title_label = QLabel("🍄 " + self.tr('title'))
        title_label.setObjectName("title_label")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 32px;
                color: #2c3e50;
                padding: 20px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #f5f5f5, stop:1 transparent);
                border-radius: 15px;
            }
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 2)
        title_label.setGraphicsEffect(shadow)

        content_layout.addWidget(title_label)

        # Create button grid layout
        button_grid = QVBoxLayout()
        button_grid.setSpacing(15)

        # Buttons with icons and improved styling
        buttons = [
            ('📊 ' + 'Admin Dashboard', self.open_admin_dashboard, "#E91E63"),
            ('🏡 ' + self.tr('farm_visual'), self.open_farm_visual, "#4CAF50"),
            ('📦 ' + self.tr('orders'), self.open_order_gui, "#2196F3"),
            ('🛏️ ' + self.tr('growing_beds'), self.open_growing_bed_gui, "#9C27B0"),
            ('🏭 ' + self.tr('warehouse'), self.open_warehouse_gui, "#FF9800"),
            ('📊 View Analytics', self.open_analytics_gui, "#795548"),
            ('👤 ' + self.tr('customers'), self.open_customer_gui, "#607D8B"),
            ('📤 ' + self.tr('upload_excel'), self.upload_excel_logs, "#009688"),
            ('🚪 Logout', self.handle_logout, "#E57373")
        ]

        for text, callback, color in buttons:
            button = QPushButton(text)
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    font-size: 18px;
                    min-height: 60px;
                    border-radius: 10px;
                    padding: 10px 20px;
                }}
                QPushButton:hover {{
                    background-color: {color};
                    opacity: 0.9;
                }}
            """)
            button.clicked.connect(callback)
            button_grid.addWidget(button)

        content_layout.addLayout(button_grid)
        content_layout.addStretch()
        self.main_layout.addLayout(content_layout, stretch=2)

        # Central Widget
        container = QWidget()
        container.setLayout(self.main_layout)
        self.setCentralWidget(container)

    def create_settings_panel(self):
        panel = QFrame()
        panel.setObjectName("settingsPanel")
        panel.setFixedWidth(300)  # Set fixed width for settings panel
        panel.setStyleSheet("""
            QFrame#settingsPanel {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 10px;
                margin: 10px;
                padding: 20px;
            }
            QLabel {
                color: #2c3e50;
            font-size: 16px;
                margin-top: 15px;
                font-weight: bold;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                background: white;
                min-width: 200px;
                font-size: 14px;
                margin: 5px 0;
            }
            QComboBox:hover {
                border-color: #80bdff;
            }
            QRadioButton {
                font-size: 14px;
                padding: 8px;
                margin: 5px 0;
            }
            QRadioButton:hover {
                color: #2196F3;
            }
        """)

        layout = QVBoxLayout(panel)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Settings title with larger font and icon
        settings_label = QLabel("⚙️ " + self.tr('settings'))
        settings_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            padding-bottom: 15px;
            border-bottom: 2px solid #e0e0e0;
        """)
        layout.addWidget(settings_label)

        # Profile section with enhanced styling
        profile_label = QLabel("👤 " + self.tr('profile'))
        profile_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 20px;
        """)
        layout.addWidget(profile_label)

        admin_name_label = QLabel(self.tr('admin_name') + ": Itay")
        admin_name_label.setStyleSheet("""
            font-size: 16px;
            color: #34495e;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        """)
        layout.addWidget(admin_name_label)

        # Theme selection with improved visibility
        theme_label = QLabel("🎨 " + self.tr('theme'))
        theme_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 20px;
        """)
        layout.addWidget(theme_label)

        theme_group = QButtonGroup(self)
        light_theme = QRadioButton(self.tr('light_mode'))
        dark_theme = QRadioButton(self.tr('dark_mode'))

        radio_style = """
            QRadioButton {
                font-size: 14px;
                padding: 8px;
                margin: 5px 0;
                color: #34495e;
            }
            QRadioButton:hover {
                color: #2196F3;
            }
        """
        light_theme.setStyleSheet(radio_style)
        dark_theme.setStyleSheet(radio_style)

        if self.current_theme == 'dark':
            dark_theme.setChecked(True)
        else:
            light_theme.setChecked(True)

        theme_group.addButton(light_theme)
        theme_group.addButton(dark_theme)

        light_theme.toggled.connect(lambda: self.change_theme('light'))
        dark_theme.toggled.connect(lambda: self.change_theme('dark'))

        layout.addWidget(light_theme)
        layout.addWidget(dark_theme)

        # Language selection with enhanced styling
        language_label = QLabel("🌐 " + self.tr('language'))
        language_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-top: 20px;
        """)
        layout.addWidget(language_label)

        language_combo = QComboBox()
        language_combo.addItems(['עברית', 'English', 'العربية'])
        language_combo.setCurrentText({
            'he': 'עברית',
            'en': 'English',
            'ar': 'العربية'
        }[self.current_language])

        language_combo.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 2px solid #ced4da;
                border-radius: 6px;
                background: white;
                min-width: 200px;
                font-size: 14px;
                margin: 5px 0;
            }
            QComboBox:hover {
                border-color: #80bdff;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 10px;
            }
        """)

        language_combo.currentTextChanged.connect(self.change_language)
        layout.addWidget(language_combo)

        layout.addStretch()
        return panel

    def change_theme(self, theme):
        self.current_theme = theme
        self.settings.setValue('theme', theme)
        self.apply_theme(theme)

    def apply_theme(self, theme):
        if theme == 'dark':
            dark_style = """
                QMainWindow, QWidget {
                    background-color: #1a1a1a;
                    color: #ffffff;
                }
                QLabel {
                    color: #ffffff;
                }
                QPushButton {
                    color: white;
                    border: none;
                }
                QFrame#settingsPanel {
                    background-color: #2d2d2d;
                    border: 1px solid #404040;
                    border-radius: 10px;
                }
                QComboBox, QRadioButton {
                    background-color: #333333;
                    color: #ffffff;
                    border: 1px solid #404040;
                    padding: 8px;
                }
                QComboBox:hover, QRadioButton:hover {
                    border-color: #666666;
                    background-color: #404040;
                }
                QTableView {
                    background-color: #2d2d2d;
                    alternate-background-color: #333333;
                    color: #ffffff;
                    gridline-color: #404040;
                    border: 1px solid #404040;
                    selection-background-color: #2980b9;
                    selection-color: #ffffff;
                }
                QTableView::item {
                    padding: 8px;
                    border-bottom: 1px solid #404040;
                }
                QTableView::item:selected {
                    background-color: #2980b9;
                    color: #ffffff;
                }
                QTableView::item:hover {
                    background-color: #34495e;
                }
                QHeaderView::section {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    padding: 10px;
                    border: 1px solid #404040;
                    font-weight: bold;
                }
                QScrollBar:vertical {
                    background-color: #2d2d2d;
                    width: 14px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #404040;
                    min-height: 30px;
                    border-radius: 7px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #4a4a4a;
                }
                QScrollBar:horizontal {
                    background-color: #2d2d2d;
                    height: 14px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background-color: #404040;
                    min-width: 30px;
                    border-radius: 7px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #4a4a4a;
                }
                QLineEdit {
                    background-color: #333333;
                    color: #ffffff;
                    border: 1px solid #404040;
                    padding: 8px;
                    border-radius: 5px;
                }
                QLineEdit:focus {
                    border-color: #2980b9;
                }
            """
            self.setStyleSheet(dark_style)

            # Update the title label style for dark mode
            title_label = self.findChild(QLabel, "title_label")
            if title_label:
                title_label.setStyleSheet("""
                    QLabel {
                        font-size: 32px;
                        color: #ffffff;
                        padding: 20px;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #2d2d2d, stop:1 transparent);
                        border-radius: 15px;
                    }
                """)

            # Apply dark theme to child windows if they exist
            if hasattr(self, 'order_gui') and self.order_gui is not None:
                self.order_gui.setStyleSheet(dark_style)
            if hasattr(self, 'customer_gui') and self.customer_gui is not None:
                self.customer_gui.setStyleSheet(dark_style)
            if hasattr(self, 'growing_bed_gui') and self.growing_bed_gui is not None:
                self.growing_bed_gui.setStyleSheet(dark_style)
            if hasattr(self, 'warehouse_gui') and self.warehouse_gui is not None:
                self.warehouse_gui.setStyleSheet(dark_style)
            if hasattr(self, 'farm_visual') and self.farm_visual is not None:
                self.farm_visual.setStyleSheet(dark_style)
            if hasattr(self, 'analytics_gui') and self.analytics_gui is not None:
                self.analytics_gui.setStyleSheet(dark_style)
        else:
            # Light theme
            light_style = """
                QMainWindow, QWidget {
                    background-color: #f5f5f5;
                    color: #333333;
                }
                QLabel {
                    color: #333333;
                }
                QPushButton {
                    color: white;
                    border: none;
                }
                QFrame#settingsPanel {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 10px;
                }
                QComboBox, QRadioButton {
                    background-color: white;
                    color: #333333;
                    border: 1px solid #ced4da;
                    padding: 8px;
                }
                QComboBox:hover, QRadioButton:hover {
                    border-color: #80bdff;
                }
                QTableView {
                    background-color: #ffffff;
                    alternate-background-color: #f8f9fa;
                    color: #333333;
                    gridline-color: #dee2e6;
                    border: 1px solid #dee2e6;
                    selection-background-color: #007bff;
                    selection-color: #ffffff;
                }
                QTableView::item {
                    padding: 8px;
                    border-bottom: 1px solid #dee2e6;
                }
                QTableView::item:selected {
                    background-color: #007bff;
                    color: #ffffff;
                }
                QTableView::item:hover {
                    background-color: #e9ecef;
                }
                QHeaderView::section {
                    background-color: #f8f9fa;
                    color: #333333;
            padding: 10px;
                    border: 1px solid #dee2e6;
                    font-weight: bold;
                }
                QScrollBar:vertical {
                    background-color: #f8f9fa;
                    width: 14px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background-color: #dee2e6;
                    min-height: 30px;
                    border-radius: 7px;
                }
                QScrollBar::handle:vertical:hover {
                    background-color: #ced4da;
                }
                QScrollBar:horizontal {
                    background-color: #f8f9fa;
                    height: 14px;
                    margin: 0px;
                }
                QScrollBar::handle:horizontal {
                    background-color: #dee2e6;
                    min-width: 30px;
                    border-radius: 7px;
                }
                QScrollBar::handle:horizontal:hover {
                    background-color: #ced4da;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #ced4da;
                    padding: 8px;
                    border-radius: 5px;
                }
                QLineEdit:focus {
                    border-color: #80bdff;
                }
            """
            self.setStyleSheet(light_style)

            # Update the title label style for light mode
            title_label = self.findChild(QLabel, "title_label")
            if title_label:
                title_label.setStyleSheet("""
                    QLabel {
                        font-size: 32px;
                        color: #2c3e50;
                        padding: 20px;
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #f5f5f5, stop:1 transparent);
                        border-radius: 15px;
                    }
                """)

    def change_language(self, language_text):
        language_map = {
            'עברית': 'he',
            'English': 'en',
            'العربية': 'ar'
        }
        language_code = language_map[language_text]

        if language_code != self.current_language:
            self.current_language = language_code
            self.settings.setValue('language', language_code)
            self.current_translations = TRANSLATIONS[language_code]

            # Rebuild the entire UI with new translations
            self.init_ui()

    def tr(self, text):
        """Translate text using current language"""
        return self.current_translations.get(text.lower(), text)

    def open_farm_visual(self):
        try:
            self.farm_visual = FarmVisualGUI()
            self.farm_visual.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Farm Visual: {str(e)}")
            print(f"Error opening Farm Visual: {str(e)}")

    def open_order_gui(self):
        try:
            self.order_gui = OrderGUI()
            self.order_gui.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Order Management: {str(e)}")
            print(f"Error opening Order Management: {str(e)}")

    def open_growing_bed_gui(self):
        try:
            self.growing_bed_gui = GrowingBedGUI()
            self.growing_bed_gui.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Growing Beds: {str(e)}")
            print(f"Error opening Growing Beds: {str(e)}")

    def open_warehouse_gui(self):
        try:
            self.warehouse_gui = WarehouseGUI()
            self.warehouse_gui.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Warehouse: {str(e)}")
            print(f"Error opening Warehouse: {str(e)}")

    def open_customer_gui(self):
        try:
            self.customer_gui = CustomerGUI()
            self.customer_gui.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Customer Management: {str(e)}")
            print(f"Error opening Customer Management: {str(e)}")

    def open_analytics_gui(self):
        try:
            self.analytics_gui = AnalyticsApp()
            self.analytics_gui.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Analytics: {str(e)}")
            print(f"Error opening Analytics: {str(e)}")

    def open_admin_dashboard(self):
        try:
            self.admin_dashboard = AdminDashboard()
            self.admin_dashboard.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Admin Dashboard: {str(e)}")
            print(f"Error opening Admin Dashboard: {str(e)}")

    def upload_excel_logs(self):
        try:
            file_name, _ = QFileDialog.getOpenFileName(self, "Select Excel File", "", "Excel Files (*.xlsx *.xls)")
            if file_name:
                # TODO: Implement Excel upload logic
                QMessageBox.informsation(self, "Success", "Excel file uploaded successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to upload Excel file: {str(e)}")
            print(f"Error uploading Excel file: {str(e)}")

    def handle_logout(self):
        reply = QMessageBox.question(self, 'Logout', 'Are you sure you want to logout?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()

    @staticmethod
    def delete_table(table_name):
        ref = db.reference(table_name)  # Reference to the table (node)
        ref.delete()  # Deletes the node

    # delete_table("Batches")
    # delete_table("Logs")

    # Deletes the "Logs" table
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Create Main Window
    main_window = Main_gui()
    main_window.show()

    sys.exit(app.exec_())
