import tkinter as tk
from tkinter import messagebox
import threading
import time
from datetime import datetime, timedelta
import os
import subprocess
import sys
import tempfile
from PIL import Image, ImageTk

class SingleInstance:
    def __init__(self):
        self.lockfile = os.path.join(tempfile.gettempdir(), 'sleep_enforcer.lock')
        
        # Check if the lock file exists
        if os.path.exists(self.lockfile):
            try:
                with open(self.lockfile, 'r') as f:
                    pid = int(f.read().strip())
                # Try to check if process exists
                os.kill(pid, 0)  # This will raise OSError if process doesn't exist
                print("Sleep Enforcer is already running!")
                sys.exit(1)
            except OSError:
                # Process not running, we can take over
                pass
        
        # Create lock file with current process ID
        with open(self.lockfile, 'w') as f:
            f.write(str(os.getpid()))

class SleepEnforcer:
    
    def __init__(self):
        
        # Creating parent UI
        self.root = tk.Tk()
        self.root.withdraw()

        # Initial Window Features and Sizing
        self.title("Sleep Enforcer") 
        self.geometry("500x300")
        
        # Time settings
        self.warning_time = "21:55"
        self.shutdown_time = "10:30"
        self.grace_period = 180
        self.final_countdown = 60
        self.extension_minutes =30
        
        # Timer control flags
        self.grace_timer_active = False
        self.final_timer_active = False
        
        # UI elements (initialized when needed)
        self.reason_window = None
        self.countdown_window = None
        self.reason_entry = None
        self.countdown_label = None

        # Images and Icons
        settings_icon_image = Image.open('icons/settings_icon.png')
        settings_icon_image = settings_icon_image.resize((16, 16), Image.LANCZOS)
        self.settings_icon = ImageTk.PhotoImage(settings_icon_image)

        # Frames Setup
        # Icon Frames
        self.icon_frame = tk.Frame(self.root, width=24, height=24, bg="lightgrey")
        self.icon_frame.pack(expand=True, fill='both')

       

        # Reasons Allowed AN Extension
        self.valid_reasons = [
        "client deadline",
        "assignment due", 
        "emergency",
        "meeting"
    ]
    def center_window(self, window, width, height):
        """Center window on screen"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
    def settings(self):
        self.setting_window = tk.Toplevel(self.root)
        self.setting_window.title("Settings")
        self.center_window(self.setting_window, 400, 300)  
        
    def startup(self):
        self.startup_window = tk.Toplevel(self.root)
        self.startup_window.title("Healthy Sleep Enforcer")
        self.center_window(self.startup_window, 500, 250)
        
    def check_time(self):
        """Continuously check the current time"""
        current_time = datetime.now().strftime("%H:%M")
            
        if current_time == self.warning_time:
            print("[DEBUG] WARNING TIME MATCHED! Showing warning...")
            self.show_warning()  # schedule GUI call in main thread
        elif current_time == self.shutdown_time:
            print("[DEBUG] SHUTDOWN TIME MATCHED! Showing reason check")
            self.show_reason_prompt() # schedule GUI call in main thread
        else:
            print("Error")
                
        self.root.after(60000, self.check_time)  # schedule GUI call in main thread
            
    
    def show_warning(self):
        """Show 5-minute warning at 9:55 PM"""
        messagebox.showwarning(
            "Bedtime Reminder",
            "⏰ 5 minutes until shutdown!\n\nPlease wrap up your work.",
            parent=self.root
        )
    
    def show_reason_prompt(self):
        """Show reason input dialog at 10:00 PM"""
        self.grace_timer_active = True  # ✅ Move here, at the start
        print("You have 3 mins to respond")

        # The reason window interface
        self.reason_window = tk.Toplevel(self.root)
        self.reason_window.title("Sleep Enforcer")
        self.reason_window.geometry("500x250")
        self.reason_window.configure(bg="#1e293b")
        self.center_window(self.reason_window, 500, 250) # Center the window

        #self.reason_window.transient(self.root)  # Make window modal
        #self.reason_window.grab_set()  # Block other windows 
        # the previous 2 lines on code seem to prevent the gui from showing on this environment, so I am removing it to avoid compatibility issues
        
        
        
        # Make window stay on top
        self.reason_window.attributes('-topmost', True)

        # The 
        frame = tk.Frame(self.reason_window, bg="#1e293b")
        frame.pack(expand=True, fill='both')
        
        # Title
        title = tk.Label(
            frame,
            text=f"🌙 It's {self.shutdown_time} PM - Time for Bed!",
            font=("Arial", 16, "bold"),
            bg="#1e293b",
            fg="white"
        )
        title.pack(pady=(0, 20))
        
        # Question
        question = tk.Label(
            frame,
            text="Why do you need to stay up?",
            font=("Arial", 12),
            bg="#1e293b",
            fg="#cbd5e1"
        )
        question.pack(pady=(0, 10))
        
        # Input field
        self.reason_entry = tk.Entry(
            frame,
            font=("Arial", 11),
            width=40
        )
        self.reason_entry.pack(pady=(0, 20))
        self.reason_entry.focus()
        
        # Submit button
        submit_btn = tk.Button(
            frame,
            text="Submit Reason",
            font=("Arial", 11, "bold"),
            bg="#3b82f6",
            fg="white",
            padx=20,
            pady=10,
            command=self.check_reason,
            cursor="hand2"
        )
        submit_btn.pack()
        
        # Bind Enter key to submit
        self.reason_entry.bind('<Return>', lambda e: self.check_reason())

        # Settings Button
        settings_button = tk.Button(
            self.icon_frame,
            image = self.settings_icon,
            bg="white",
            fg="black",
            compound = "bottom",
            command = self.settings
        )
        settings_button.pack(side = "left", pady=(0,10))

        """Wait 3 minutes, then show final countdown"""
        # Schedule UI updates on main thread
        self.reason_window.after(self.grace_period * 1000, self.handle_grace_timeout)
        
        # Disable close button
        self.reason_window.protocol("WM_DELETE_WINDOW", lambda: None)  

    # Countdown Timer Tracking IF I respond to the Sleep TIme Popup

    def handle_grace_timeout(self):
        """Handle grace period timeout"""
        if self.grace_timer_active and self.reason_window.winfo_exists():
            self.reason_window.destroy()
            self.show_final_countdown()
    
    def check_reason(self):
        """Check if the provided reason is valid"""
        self.grace_timer_active = False
        
        reason = self.reason_entry.get().lower().strip()
        
        is_valid = any(valid in reason for valid in self.valid_reasons)
        
        if is_valid:
            self.reason_window.destroy()
            self.grant_extension()
        else:
            self.reason_window.destroy()
            self.show_final_countdown()
    
    def grant_extension(self):
        """Grant 30-minute extension"""
        # Calculate new shutdown time based on current time
        current_time = datetime.now()
        new_shutdown = current_time + timedelta(minutes=self.extension_minutes)
        
        # Update the shutdown and warning times
        self.shutdown_time = new_shutdown.strftime("%H:%M")
        # Set warning 5 minutes before shutdown
        self.warning_time = (new_shutdown - timedelta(minutes=5)).strftime("%H:%M")
        
        messagebox.showinfo(
            "Extension Granted",
            f"✅ Valid reason accepted!\n\nYou have {self.extension_minutes} more minutes.\n\nNext check at {self.get_next_check_time()}"
        )
    
    def get_next_check_time(self):
        """Calculate next check time"""

        next_time = datetime.now() + timedelta(minutes=self.extension_minutes)
        return next_time.strftime("%I:%M %p")
    
    def show_final_countdown(self):
        self.final_timer_active = True # Start the system timer for 1-minute hibernation
        """Show 1-minute final countdown before hibernate"""
        self.countdown_window = tk.Toplevel(self.root)
        #self.countdown_window.transient(self.root) 
        #self.countdown_window.grab_set()
        self.countdown_window.title("Final Warning")
        self.countdown_window.geometry("450x300")
        self.countdown_window.configure(bg="#991b1b")
        
        # Center the window
        self.center_window(self.countdown_window, 450, 300)
        self.countdown_window.attributes('-topmost', True)
        
        # Countdown Window Frame
        frame = tk.Frame(self.countdown_window, bg="#991b1b")
        frame.pack(expand=True, fill='both')
        
        # Warning icon and title
        title = tk.Label(
            frame,
            text="⚠️ FINAL WARNING",
            font=("Arial", 18, "bold"),
            bg="#991b1b",
            fg="white"
        )
        title.pack(pady=(0, 15))
        
        # Countdown label
        self.countdown_label = tk.Label(
            frame,
            text="System will hibernate in: 60s",
            font=("Arial", 14),
            bg="#991b1b",
            fg="white"
        )
        self.countdown_label.pack(pady=(0, 20))
        
        # Hibernate now button
        hibernate_btn = tk.Button(
            frame,
            text="💾 Hibernate Now",
            font=("Arial", 12, "bold"),
            bg="#10b981",
            fg="white",
            padx=25,
            pady=12,
            command=self.hibernate_system,
            cursor="hand2"
        )
        hibernate_btn.pack(pady=(0, 10))
        
        # Give reason button
        reason_btn = tk.Button(
            frame,
            text="⏱️ I Have a Valid Reason",
            font=("Arial", 11),
            bg="#3b82f6",
            fg="white",
            padx=25,
            pady=10,
            command=self.reopen_reason_prompt,
            cursor="hand2"
        )
        reason_btn.pack()
        
        self.countdown_window.protocol("WM_DELETE_WINDOW", lambda: None)
        
        
        

        # Defining Variable for Updating Countdown Timer
        self.remaining_seconds = self.final_countdown
        self.update_countdown()

    
    def update_countdown(self):
        """
        1-minute countdown before auto-hibernate.

        Note: This method is intended to run in a background thread and interacts with the Tkinter UI.
        Updating UI elements from a thread other than the main thread may cause issues in some environments.
        """
        if not self.final_timer_active :
            return
        try:
            if self.countdown_window.winfo_exists() and self.remaining_seconds > 0 :
                self.countdown_label.config(
                    text=f"System will hibernate in: {self.remaining_seconds}s"
                )
                self.remaining_seconds-= 1 # Reducing time left by 1 second
                self.countdown_window.after(1000, self.update_countdown)
            elif self.remaining_seconds <= 0:
                if self.countdown_window.winfo_exists():
                    self.countdown_window.destroy()
                self.hibernate_system()
            else:
                return
        except tk.TclError:
        # Window was destroyed, stop countdown gracefully
            return
        
        
    
    def reopen_reason_prompt(self):
        """Reopen the reason prompt from final countdown"""
        
        self.final_timer_active = False  # ✅ Stop the countdown for the 1-minute hibernation to be continued after wrong response from reason prompt 
        self.countdown_window.destroy()
        self.show_reason_prompt()
    
    def hibernate_system(self):
        """Hibernate the Windows system"""
        # Close all windows first
        try:
            if hasattr(self, 'countdown_window') and self.countdown_window.winfo_exists():
                self.countdown_window.destroy()
            if hasattr(self, 'reason_window') and self.reason_window.winfo_exists():
                self.reason_window.destroy()
        except:
            pass
        
       # clean up lock file
        try:
            lockfile = os.path.join(tempfile.gettempdir(), 'sleep_enforcer.lock')
            if os.path.exists(lockfile):
                os.remove(lockfile)
        except:
            pass

        # Give windows time to close
        time.sleep(0.3)
        
        # Now try to hibernate
        try:
            # Kill this program THEN hibernate
            subprocess.Popen(["cmd", "/c", "timeout /t 2 && shutdown /h && exit"], 
                        creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)  # Kill the Python program immediately
        
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def run(self):
        """Start the sleep enforcer"""
        print("💤 Sleep Enforcer is running...")
        print(f"⏰ Warning at: {self.warning_time}")
        print(f"🛑 Shutdown check at: {self.shutdown_time}")
        print(f"✅ Valid reasons: {', '.join(self.valid_reasons)}")
        print("\nPress Ctrl+C to stop (not recommendeded!)\n") 
        self.check_time()
        self.root.mainloop()
        
        
        # Start check_time in background thread
        


if __name__ == "__main__":
    # Ensure only one instance is running
    single_instance = SingleInstance()
    
    # Create and run the enforcer
    enforcer = SleepEnforcer()
    enforcer.run()