#!/usr/bin/env python
"""
Support Bot Setup Launcher

This script serves as a launcher for various setup utilities in the fresh-setup folder.
It provides a simple menu interface to help users select the appropriate tool.
"""

import os
import sys
import subprocess

def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print the header for the setup menu."""
    print("=" * 60)
    print("               SUPPORT BOT SETUP UTILITIES               ")
    print("=" * 60)
    print("This launcher provides access to various setup utilities.")
    print("Select an option to get started.\n")

def print_menu():
    """Print the main menu options."""
    print("1. Full Setup (for new machines)")
    print("2. Install/Update ngrok")
    print("3. Update ngrok URL")
    print("4. Fix ngrok Issues")
    print("5. Run Tests")
    print("6. Monitor Logs")
    print("7. Exit")
    print("\nEnter your choice (1-7): ", end="")

def run_full_setup():
    """Run the full setup script."""
    clear_screen()
    print("Running full setup...")
    subprocess.run([sys.executable, os.path.join("fresh-setup", "setup.py")])
    input("\nPress Enter to return to the main menu...")

def run_ngrok_installer():
    """Run the ngrok installer script."""
    clear_screen()
    print("Running ngrok installer...")
    subprocess.run([sys.executable, os.path.join("fresh-setup", "ngrok_installer.py")])
    input("\nPress Enter to return to the main menu...")

def run_ngrok_update():
    """Run the ngrok URL update script."""
    clear_screen()
    print("Running ngrok URL update utility...")
    subprocess.run([sys.executable, os.path.join("fresh-setup", "ngrok_update.py")])
    input("\nPress Enter to return to the main menu...")

def run_ngrok_fix():
    """Run the ngrok troubleshooting utility."""
    clear_screen()
    print("Running ngrok troubleshooting utility...")
    subprocess.run([sys.executable, os.path.join("fresh-setup", "fix_ngrok.py")])
    input("\nPress Enter to return to the main menu...")

def run_log_monitor():
    """Run the log monitoring utility."""
    clear_screen()
    print("Running log monitor...")
    print("(Press Ctrl+C to exit back to menu)")
    subprocess.run([sys.executable, os.path.join("fresh-setup", "monitor_logs.py"), "--follow"])
    input("\nPress Enter to return to the main menu...")

def run_test_menu():
    """Show the test menu."""
    while True:
        clear_screen()
        print("=" * 60)
        print("                  TEST UTILITIES                  ")
        print("=" * 60)
        print("1. Test Bot Connection")
        print("2. Set Up Webhook")
        print("3. Delete Webhook")
        print("4. Test WebApp URL")
        print("5. Update Container Webhook")
        print("6. Return to Main Menu")
        print("\nEnter your choice (1-6): ", end="")
        
        choice = input().strip()
        
        if choice == "1":
            subprocess.run([sys.executable, "run_test.py", "bot"])
            input("\nPress Enter to continue...")
        elif choice == "2":
            subprocess.run([sys.executable, "run_test.py", "webhook-set"])
            input("\nPress Enter to continue...")
        elif choice == "3":
            subprocess.run([sys.executable, "run_test.py", "webhook-delete"])
            input("\nPress Enter to continue...")
        elif choice == "4":
            subprocess.run([sys.executable, "run_test.py", "webapp"])
            input("\nPress Enter to continue...")
        elif choice == "5":
            subprocess.run([sys.executable, "run_test.py", "container-webhook"])
            input("\nPress Enter to continue...")
        elif choice == "6":
            break
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")

def show_documentation():
    """Show available documentation."""
    clear_screen()
    print("=" * 60)
    print("               AVAILABLE DOCUMENTATION               ")
    print("=" * 60)
    
    docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
    docs_files = [f for f in os.listdir(docs_path) if f.endswith(".md")]
    
    if not docs_files:
        print("No documentation files found in the docs folder.")
    else:
        print("The following documentation files are available in the docs folder:")
        print("\nSetup and Configuration:")
        for doc in docs_files:
            if doc.startswith("SETUP") or doc.startswith("CONFIG"):
                print(f"- {doc}")
        
        print("\nTesting and Troubleshooting:")
        for doc in docs_files:
            if doc.startswith("TEST") or doc.startswith("TROUBLE"):
                print(f"- {doc}")
        
        print("\nOther Documentation:")
        for doc in docs_files:
            if not (doc.startswith("SETUP") or doc.startswith("CONFIG") or 
                    doc.startswith("TEST") or doc.startswith("TROUBLE")):
                print(f"- {doc}")
                
    print("\nYou can view these files in a text editor or markdown viewer.")
    input("\nPress Enter to return to the main menu...")

def main():
    """Main function to run the launcher."""
    while True:
        clear_screen()
        print_header()
        print_menu()
        
        choice = input().strip()
        
        if choice == "1":
            run_full_setup()
        elif choice == "2":
            run_ngrok_installer()
        elif choice == "3":
            run_ngrok_update()
        elif choice == "4":
            run_ngrok_fix()
        elif choice == "5":
            run_test_menu()
        elif choice == "6":
            run_log_monitor()
        elif choice == "7":
            clear_screen()
            print("Exiting setup utilities. Goodbye!")
            return 0
        else:
            print("Invalid choice. Please try again.")
            input("\nPress Enter to continue...")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 