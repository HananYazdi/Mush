from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from Main_gui import MainGUI
import sys
from PyQt5.QtWidgets import QApplication
from firebase_admin import db
import hashlib
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class LoginGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLabel {
                color: #333;
            }
        """)

        # Main layout
        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(20, 20, 20, 20)

        # Title
        self.title = QLabel("Farm Management System")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont('Arial', 18, QFont.Bold))
        self.layout.addWidget(self.title)

        # Username input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(35)
        self.layout.addWidget(self.username_input)

        # Password input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(35)
        self.layout.addWidget(self.password_input)

        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(40)
        self.login_button.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_button)

        self.setLayout(self.layout)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password.")
            return

        try:
            ref = db.reference("Users")
            users = ref.get()

            if not users:
                QMessageBox.warning(self, "Error", "No users found in the database.")
                return

            # Find the user in the database
            user_found = False
            for user_id, user_data in users.items():
                if (user_data.get("Username") == username and 
                    user_data.get("Password") == self.hash_password(password)):
                    # Update login status
                    ref.child(user_id).update({"LoggedIn": True})
                    user_found = True
                    QMessageBox.information(self, "Success", "Login successful!")
                    self.open_main_gui()
                    return

            if not user_found:
                QMessageBox.warning(self, "Error", "Invalid username or password.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to log in: {str(e)}")

    def open_main_gui(self):
        self.main_window = MainGUI()
        self.main_window.show()
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    login_window = LoginGUI()
    login_window.show()
    sys.exit(app.exec_())


# UserName:Admin Password: 1234