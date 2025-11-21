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
import pystray
from pystray import MenuItem as item

# Relative File Resolver to HElp Find OTher NON python resources

# TODO study this function
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# --- No changes to this class ---
class SingleInstance:
    def __init__(self):
        self.lockfile = os.path.join(tempfile.gettempdir(), 'sleep_enforcer.lock')
        
        if os.path.exists(self.lockfile):
            try:
                with open(self.lockfile, 'r') as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)
                print("Sleep Enforcer is already running!")
                sys.exit(1)
            except OSError:
                pass
        
        with open(self.lockfile, 'w') as f:
            f.write(str(os.getpid()))

# --- "Page" Frames (Views) ---
# We define each "page" of your application as its own class that inherits from tk.Frame.

class StartupPage(tk.Frame):
    """
    This is the main "dashboard" page. It replaces your 'startup_window'.
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#2090b9")
        self.controller = controller

        # Add content for the startup page
        label = tk.Label(self, 
                         text="💤 Healthy Sleep Enforcer is Active", 
                         font=("Arial", 14),
                           bg="#cecfcf",
                           fg= "black")
        label.pack(pady=20, padx=20)
        
        status_text = f"⏰ Warning at: {controller.warning_time}\n🛑 Shutdown check at: {controller.shutdown_time}"
        
        # We save the status_label as 'self.status_label'
        # so we can access it in 'update_status'
        self.status_label = tk.Label(self, text=status_text, font=("Arial", 11), bg="#f0f0f0")
        self.status_label.pack(pady=10)


        # Button to go to the Settings page
        # It calls the controller's 'show_frame' method
        settings_btn = tk.Button(
            self,
            text="Settings",
            bg = "#ddf63b",
            fg = "#000000",
            image=controller.settings_icon, # Get icon from controller
            compound="left",
            font=("Arial", 11),
            cursor="hand2",
            command=lambda: controller.show_frame("SettingsPage")
        )
        settings_btn.pack(pady=50)

        

    # --- NEW: Add this method ---
    def update_status(self):
        """Updates the time labels when called by the controller."""
        status_text = f"⏰ Warning at: {self.controller.warning_time}\n🛑 Shutdown check at: {self.controller.shutdown_time}"
        self.status_label.config(text=status_text)
                                 
class SettingsPage(tk.Frame):
    """
    This is the settings page. It replaces your 'setting_window'.
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#f0f0f0")
        self.controller = controller

        label = tk.Label(self, text="Settings Page", font=("Arial", 16, "bold"), bg="#f0f0f0")
        label.pack(pady=20, padx=20)

        # --- TODO: Add your settings widgets here ---
        # For example, you could have Entry fields to change
        # controller.warning_time and controller.shutdown_time
        
        warning_label = tk.Label(self, text="Warning Time (HH:MM):", bg="#f0f0f0")
        warning_label.pack()
        self.warning_entry = tk.Entry(self)
        self.warning_entry.insert(0, controller.warning_time)
        print(f"This is the new warning time time {controller.warning_time}")
        self.warning_entry.pack(pady=5)

        # Entry Fields and Logic to Change Shutdown Time
        shutdown_label = tk.Label(self, text="Shutdown Time (HH:MM):", bg="#f0f0f0", fg = "red")
        shutdown_label.pack()
        self.shutdown_entry = tk.Entry(self)
        self.shutdown_entry.insert(0, controller.shutdown_time)
        print(f"This is the new shutdown time {controller.shutdown_time}")
        self.shutdown_entry.pack(pady=5)
        
        # --- (Add save button and logic) ---
        # --- NEW: The "Save" button ---
        save_btn = tk.Button(
            self,
            text="Save Settings",
            font=("Arial", 11, "bold"),
            bg="#3b82f6", # Blue
            fg="white",
            cursor="hand2",
            # This calls the controller's "save_settings" method
            command=lambda: controller.save_settings()
        )
        save_btn.pack(pady=20)

        # Button to navigate back to the Startup page
        back_btn = tk.Button(
            self,
            text="Back to Home",
            font=("Arial", 11),
            cursor="hand2",
            command=lambda: controller.show_frame("StartupPage")
        )
        back_btn.pack(pady=5)


class ReasonPage(tk.Frame):
    """
    This is the page that asks for a reason. It replaces 'reason_window'.
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#1e293b")
        self.controller = controller

        # We move all the widget creation from 'show_reason_prompt' here
        # Note that 'self' is now the frame, not a 'Toplevel' window

        title = tk.Label(
            self,
            text=f"🌙 It's {controller.shutdown_time} - Time for Bed!",
            font=("Arial", 16, "bold"),
            bg="#1e293b",
            fg="white"
        )
        title.pack(pady=(40, 20))
        
        question = tk.Label(
            self,
            text="Why do you need to stay up?",
            font=("Arial", 12),
            bg="#1e293b",
            fg="#cbd5e1"
        )
        question.pack(pady=(0, 10))
        
        self.reason_entry = tk.Entry(
            self,
            font=("Arial", 11),
            width=40
        )
        self.reason_entry.pack(pady=(0, 20))
        
        submit_btn = tk.Button(
            self,
            text="Submit Reason",
            font=("Arial", 11, "bold"),
            bg="#3b82f6",
            fg="white",
            padx=20,
            pady=10,
            # This button now calls the controller's check_reason method
            command=controller.check_reason,
            cursor="hand2"
        )
        submit_btn.pack()
        
        # Bind Enter key to the controller's method
        self.reason_entry.bind('<Return>', lambda e: controller.check_reason())


class CountdownPage(tk.Frame):
    """
    This is the final countdown page. It replaces 'countdown_window'.
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#991b1b")
        self.controller = controller
        self.remaining_seconds = 0

        # Move all widgets from 'show_final_countdown' here
        title = tk.Label(
            self,
            text="⚠️ FINAL WARNING",
            font=("Arial", 18, "bold"),
            bg="#991b1b",
            fg="white"
        )
        title.pack(pady=(40, 15))
        
        self.countdown_label = tk.Label(
            self,
            text="", # Will be set by start_countdown
            font=("Arial", 14),
            bg="#991b1b",
            fg="white"
        )
        self.countdown_label.pack(pady=(0, 20))
        
        hibernate_btn = tk.Button(
            self,
            text="💾 Hibernate Now",
            font=("Arial", 12, "bold"),
            bg="#10b981",
            fg="white",
            padx=25,
            pady=12,
            # Call controller's method
            command=controller.hibernate_system,
            cursor="hand2"
        )
        hibernate_btn.pack(pady=(0, 10))
        
        reason_btn = tk.Button(
            self,
            text="⏱️ I Have a Valid Reason",
            font=("Arial", 11),
            bg="#3b82f6",
            fg="white",
            padx=25,
            pady=10,
            # Call controller's method
            command=controller.reopen_reason_prompt,
            cursor="hand2"
        )
        reason_btn.pack()

    def start_countdown(self):
        """Starts or resumes the countdown timer."""
        self.remaining_seconds = self.controller.final_countdown
        self.update_countdown_label()

    def update_countdown_label(self):
        """The recursive function to update the countdown label."""
        # Check the controller's flag to see if we should still be counting
        if not self.controller.final_timer_active:
            return  # Stop the countdown
            
        if self.remaining_seconds > 0:
            self.countdown_label.config(
                text=f"System will hibernate in: {self.remaining_seconds}s"
            )
            self.remaining_seconds -= 1
            # Use 'self.after' (since this class is a widget)
            self.after(1000, self.update_countdown_label)
        else:
            self.countdown_label.config(text="Hibernating...")
            self.controller.hibernate_system()

# --- Main Application (Controller) ---
###
### This class is now the MAIN window. It inherits from tk.Tk.
### It holds all the logic and controls which frame (page) is visible.
###
class SleepEnforcerApp(tk.Tk):
    
    def __init__(self):
        super().__init__() # Initialize tk.Tk
        # App Windows Icon
        try:
            # We use the *same* .ico file
            icon_path = resource_path("icons\\app_icon.ico") 
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Warning: Could not load window icon. {e}")
        ###
        ### 1. CONFIGURE THE MAIN WINDOW
        ### Instead of self.root = tk.Tk() and self.root.withdraw(),
        ### 'self' IS the root window. We give it a title and size.
        ###
        self.title("Sleep Enforcer")
        self.geometry("500x300")
        self.protocol("WM_DELETE_WINDOW", self.on_minimizing_to_background) # Handle user closing window(this minimizes it to background)

        # --- Copy all your logic variables ---
        self.warning_time = "21:55"
        self.shutdown_time = "22:00"
        self.grace_period = 180
        self.final_countdown = 60
        self.extension_minutes = 30
        self.grace_timer_active = False
        self.final_timer_active = False
        self.valid_reasons = [
            "client deadline", "assignment due", "emergency", "meeting"
        ]

        # --- 3. Load Assets ---
        self.load_assets()
        self.setup_tray() # Creating Notification Tray 
        ###
        ### 2. CREATE THE FRAME CONTAINER
        ### This one frame will hold all our pages.
        ###
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        ###
        ### 3. CREATE AND STACK ALL PAGES
        ### We create all our page-frames and store them in a dictionary.
        ### They are all placed in the *same grid cell* (0,0) in the container.
        ###
        self.frames = {}
        # Loop through a tuple of all our page classes
        for F in (StartupPage, SettingsPage, ReasonPage, CountdownPage):
            page_name = F.__name__
            # Create an instance of the page
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            
            # Place the frame in the grid. All frames are in the same spot!
            frame.grid(row=0, column=0, sticky="nsew")

        ###
        ### 4. START THE APP
        ###
       
        self.center_window(self, 500, 300) # Center the main window
        self.show_frame("StartupPage")  # Show the first page
        self.check_time() # Start your time-checking logic
        

    def load_assets(self):
            """Loads and stores required assets like icons."""
            settings_icon_path = resource_path("icons/settings_icon.png")
            try:
                settings_icon_image = Image.open(settings_icon_path)
                settings_icon_image = settings_icon_image.resize((16, 16), Image.LANCZOS)
                self.settings_icon = ImageTk.PhotoImage(settings_icon_image)
            except Exception as e:
                print(f"Warning: Could not load settings icon. {e}")
                # Create a fallback blank image to prevent errors
                self.settings_icon = ImageTk.PhotoImage(Image.new('RGBA', (16, 16), (0,0,0,0)))

    # --- This is the most important new method ---
    def show_frame(self, page_name):
        """
        Brings the requested frame to the top of the stack.
        """
        print(f"[DEBUG] Showing frame: {page_name}")
        frame = self.frames[page_name]
        frame.tkraise() # This is the magic command!

    def save_settings(self):
        """
        Saves the new times from the SettingsPage.
        """
        print("[DEBUG] Saving new settings...")
        
        try:
            # 1. Get the SettingsPage object from our frames dictionary
            settings_page = self.frames["SettingsPage"]
            
            # 2. Get the new values from its Entry boxes
            new_warning_time = settings_page.warning_entry.get()
            new_shutdown_time = settings_page.shutdown_entry.get()
            
            # 3. Update the CONTROLLER'S variables
            self.warning_time = new_warning_time
            self.shutdown_time = new_shutdown_time
            
            print(f"[DEBUG] New Warning Time: {self.warning_time}")
            print(f"[DEBUG] New Shutdown Time: {self.shutdown_time}")
            
            # 4. (IMPORTANT) Update the StartupPage status label
            self.frames["StartupPage"].update_status()

            messagebox.showinfo("Settings Saved",
                                "Your new times have been saved.",
                                parent=self)
                                
        except Exception as e:
            print(f"[ERROR] Could not save settings: {e}")
            messagebox.showerror("Error",
                                 f"Could not save settings:\n{e}",
                                 parent=self)
    def setup_tray(self):
        # Creating the System Tray for Background Running Notification

        # Creating the notification menu
        try:
            notification_menu =( 
                item('Open Sleep Enforcer', self.show_window),
                    )
            print("[DEBUG] Notification Menu Created")

            # Loading Icons
            try:
                icon_path = resource_path('icons\\app_icon.ico')
                notification_icon_image = Image.open(icon_path)
                print("[DEBUG] Icon Successfully Loaded")
            except Exception as e:
                print(f"[ERROR] Tray Icon error {e}")
                image = Image.new('RGB', (64,64), color = 'red')
                print("[DEBUG] Using fallback square red icon")
            
            # Creating the Tray icon object and adding to notification menu
            print("[DEBUG] Creating pystray.Icon object...")
            self.tray_icon = pystray.Icon("SleepEnforcer", notification_icon_image, f"Sleep Enforcer \nSleep Time is by {self.shutdown_time}", notification_menu)
            print("[DEBUG] pystray.Icon object successfully created")

            # Running A Separate Notification Thread to avoid affecting GUI
            threading.Thread(target = self.tray_icon.run, daemon=True).start()
            print("[DEBUG] Tray thread started.")
        except Exception as e:
            print(f"[ERROR] Tray object created failed because of {e}")

        

    def show_window(self, icon=None, item=None):
        # Bringing back the GUI to Run In the Foreground
        self.deiconify() 
        self.lift()
        self.attributes("-topmost", True)

    def on_minimizing_to_background(self):
        """Handle the user clicking the 'X' button."""
        # TODO set up notification showing that sleep enforcer running in the background even when closed
        # In the notification centre
        self.withdraw()
   
        # Displaying Notification of Background running
        if hasattr(self, 'tray_icon'):
            print("[DEBUG] Tray Icon Exists, Displaying Notification")
            try:
                self.tray_icon.notify(
                "Sleep Enforcer is running in the background. \nCheck Notification Tray To Find Me",
                "Nice try! I'm still here. 👀" 
                )
                print("[DEBUG] Background Run Notification Displayed")
            except Exception as e:
                    print(f"[ERROR] Notification failed: {e}")
        else:
            print("[ERROR] Tray Icon Not Found")

        
            
  
    # Windows positioning and centering
    def center_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
    

    def check_time(self):
        current_time = datetime.now().strftime("%H:%M")
        
        if current_time == self.warning_time:
            print("[DEBUG] WARNING TIME MATCHED! Showing warning...")
            self.show_warning()
        elif current_time == self.shutdown_time:
            print("[DEBUG] SHUTDOWN TIME MATCHED! Showing reason check")
            self.show_reason_prompt()
        
        # We are a tk.Tk object, so we can call 'after' on 'self'
        # Check Again it is sleep time in 30 seconds
        self.after(30000, self.check_time) 

    def show_warning(self):
        # This is fine, messagebox is a dialog, not a page.
        messagebox.showwarning(
            "Bedtime Reminder",
            "⏰ 5 minutes until shutdown!\n\nPlease wrap up your work.",
            parent=self
        )
    
    def show_reason_prompt(self):
        ### CHANGED: No Toplevel, just show the frame.
        self.grace_timer_active = True
        print("You have 3 mins to respond")
        
        self.show_frame("ReasonPage")
        # Focus the entry field on the ReasonPage
        self.frames["ReasonPage"].reason_entry.focus()
        
        # Start the grace period timer
        self.after(self.grace_period * 1000, self.handle_grace_timeout)
        
        ### No 'protocol' or 'grab_set' needed, as it's not a separate window.
        
    def handle_grace_timeout(self):
        if self.grace_timer_active:
            ### CHANGED: No 'destroy', just show the next frame.
            self.grace_timer_active = False
            self.show_final_countdown()
    
    def check_reason(self):
        self.grace_timer_active = False
        
        ### CHANGED: Get text from the 'ReasonPage' frame
        reason_entry = self.frames["ReasonPage"].reason_entry
        reason = reason_entry.get().lower().strip()
        
        is_valid = any(valid in reason for valid in self.valid_reasons)
        
        ### CHANGED: No 'destroy'. Just grant extension or show countdown.
        if is_valid:
            self.grant_extension()
        else:
            self.show_final_countdown()
        
        # Clear the entry field for next time
        reason_entry.delete(0, 'end')

    def grant_extension(self):
        current_time = datetime.now()
        new_shutdown = current_time + timedelta(minutes=self.extension_minutes)
        self.shutdown_time = new_shutdown.strftime("%H:%M")
        self.warning_time = (new_shutdown - timedelta(minutes=5)).strftime("%H:%M")
        
        messagebox.showinfo(
            "Extension Granted",
            f"✅ Valid reason accepted!\n\nYou have {self.extension_minutes} more minutes."
        )
        ### CHANGED: Show the main StartupPage again.
        self.show_frame("StartupPage")
    
    def show_final_countdown(self):
        self.final_timer_active = True
        
        ### CHANGED: Show the frame and tell it to start its countdown.
        self.show_frame("CountdownPage")
        self.frames["CountdownPage"].start_countdown()

    def reopen_reason_prompt(self):
        self.final_timer_active = False  # Stop the countdown
        
        ### CHANGED: No 'destroy', just show the ReasonPage.
        self.show_frame("ReasonPage")
    
    def hibernate_system(self):
        print("[DEBUG] Hibernating system...")
        # Stop all timers
        self.final_timer_active = False
        self.grace_timer_active = False
        self.show_frame('StartupPage')
        # Give windows some time
        time.sleep(0.3)
        
        # Hibernate
        try:
            subprocess.Popen(["cmd", "/c", "timeout /t 2 && shutdown /h && exit"], 
                             creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)
        except Exception as e:
            # We can't show a messagebox here, window is gone.
            print(f"Hibernate error: {e}")


if __name__ == "__main__":
    # Ensure only one instance is running
    single_instance = SingleInstance()
    
    # Create and run the enforcer
    app = SleepEnforcerApp() # This is our new class
    app.mainloop()