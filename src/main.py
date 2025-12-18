"""Application entry point."""

import sys
from PyQt6.QtWidgets import QApplication

from src.models.database import Database
from src.ui.main_window import MainWindow


def main():
    """Main application entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Payment Tracker")
    app.setOrganizationName("Personal")
    
    # Initialize database
    database = Database()
    database.connect()
    
    try:
        # Create and show main window
        main_window = MainWindow(database)
        main_window.show()
        
        # Run application event loop
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error: {e}")
        database.close()
        sys.exit(1)


if __name__ == "__main__":
    main()

