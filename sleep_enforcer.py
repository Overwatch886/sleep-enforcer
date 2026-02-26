import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
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
                #--TODO-- review the functionality of this except block and understand the error message which occurs here 
                # When a previous instance of the program is running.
            except (OSError, ValueError, SystemError) as e:
                print(f"[ERROR] The error {e} occurred")
                pass
        try:
            with open(self.lockfile, 'w') as f:
                f.write(str(os.getpid()))
        except IOError as e:
            print(f"[ERROR] Could not write lock file {e}")

# --- "Page" Frames (Views) ---
# We define each "page" of your application as its own class that inherits from tk.Frame.

class StartupPage(tk.Frame):
    """
    This is the main "dashboard" page. It replaces your 'startup_window'.
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#f5f7fa")
        self.controller = controller

        # Header
        header = tk.Frame(self, bg=self['bg'])
        header.pack(fill='x', pady=(20, 10))
        title = tk.Label(header, text="💤 Healthy Sleep Enforcer", font=("Arial", 18, "bold"), bg=self['bg'], fg="#1e40af")
        title.pack()
        subtitle = tk.Label(header, text="Sleep tracking enabled", font=("Arial", 10), bg=self['bg'], fg="#64748b")
        subtitle.pack()

        # Status card
        card = tk.Frame(self, bg="#ffffff", bd=1, relief='flat', highlightthickness=0)
        card.pack(padx=20, pady=15, fill='x')
        status_text = f"⏰ Warning at {controller.warning_time_str}  •  🛑 Shutdown at {controller.shutdown_time_str}"
        self.status_label = tk.Label(card, text=status_text, font=("Arial", 11), bg="#ffffff", fg="#334155")
        self.status_label.pack(padx=16, pady=14)

        # Actions area
        actions = tk.Frame(self, bg=self['bg'])
        actions.pack(pady=20)
        settings_btn = ttk.Button(actions, text="⚙️ Settings", command=lambda: controller.show_frame("SettingsPage"))
        settings_btn.pack(ipadx=12, ipady=8)
        settings_btn.bind('<Return>', lambda e: controller.show_frame('SettingsPage'))


    # --- NEW: Add this method ---
    def update_status(self):
        """Updates the time labels when called by the controller."""
        status_text = f"⏰ Warning at: {self.controller.warning_time_str}\n🛑 Shutdown check at: {self.controller.shutdown_time_str}"
        self.status_label.config(text=status_text)


class SettingsPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#f5f7fa")
        self.controller = controller

        # Main container - centered
        container = tk.Frame(self, bg="#f5f7fa")
        container.pack(expand=True, pady=10)

        # Title
        title = tk.Label(container, text="⚙️ Settings", font=("Arial", 18, "bold"), bg="#f5f7fa", fg="#1e40af")
        title.pack(pady=(0,20))

        # Create time options
        time_options = [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 15)]
        
        # Warning time
        warning_label = tk.Label(container, text="⏰ Warning Time", bg="#f5f7fa", fg="#1e293b", font=("Arial", 11, "bold"))
        warning_label.pack(pady=(0,6))

        self.warning_combo = ttk.Combobox(container, values=time_options, width=20, state='readonly')
        self.warning_combo.set(controller.warning_time_str)
        self.warning_combo.pack(pady=(0,10))
        # Bind key release for filtering
        self.warning_combo.bind('<KeyRelease>', lambda e: self._filter_options(e, self.warning_combo, time_options))

        # Shutdown time
        shutdown_label = tk.Label(container, text="🌙 Shutdown Time", bg="#f5f7fa", fg="#dc2626", font=("Arial", 11, "bold"))
        shutdown_label.pack(pady=(0,6))

        self.shutdown_combo = ttk.Combobox(container, values=time_options, width=20, state='readonly')
        self.shutdown_combo.set(controller.shutdown_time_str)
        self.shutdown_combo.pack(pady=(0,10))
        # Bind key release for filtering
        self.shutdown_combo.bind('<KeyRelease>', lambda e: self._filter_options(e, self.shutdown_combo, time_options))

        # Checkbox
        self.strict_var = tk.BooleanVar(value=controller.strict_break_mode)
        strict_check = ttk.Checkbutton(container, text="Enable mandatory 5-minute break", variable=self.strict_var)
        strict_check.pack(pady=(10,30))
        # Key Bindings for Easy Navigation
        strict_check.bind('<Return>',lambda e: strict_check.invoke())

        # Buttons
        footer = tk.Frame(container, bg="#f5f7fa")
        footer.pack()
        
        save_btn = ttk.Button(footer, text="💾 Save Settings", command=lambda: controller.save_settings())
        save_btn.pack(side='left', padx=(0,10))
        # Key bindings for easy app navigation
        save_btn.bind('<Return>', lambda e: controller.save_settings())
        
        back_btn = ttk.Button(footer, text="← Back to Home", command=lambda: controller.show_frame("StartupPage"))
        back_btn.pack(side='left')
        # Key bindings for easy app navigation
        back_btn.bind('<Return>', lambda e: controller.show_frame('StartupPage'))

    def _filter_options(self, event, combo, all_options):
        """Filter options using 'starts with' logic and maintain cursor position."""
        val = combo.get()
        # Save current cursor position
        pos = combo.index(tk.INSERT)

        # 1. Logic Fix: Only match from the beginning of the string
        if val == '':
            filtered = all_options
        else:
            filtered = [item for item in all_options 
                        if item.startswith(val) or (len(val) == 1 and item.startswith('0' + val))]
        
        combo['values'] = filtered

        # 2. Focus Fix: Put the cursor back where it was
        combo.icursor(pos)

        # Only trigger the dropdown for actual data input
        if event.keysym not in ('Return', 'Tab', 'Escape', 'Up', 'Down', 'BackSpace', 'Left', 'Right'):
            if filtered:
                combo.event_generate('<Down>')
        
        

class ReasonPage(tk.Frame):
    """
    This is the page that asks for a reason.
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#f5f7fa")
        self.controller = controller

        # Centered card
        card = tk.Frame(self, bg="#ffffff", padx=40, pady=40, relief='flat', highlightthickness=0)
        card.pack(expand=True, fill='both', padx=0, pady=0)

        title = tk.Label(card, text=f"🌙 It's {controller.shutdown_time_str} - Time for Bed!", font=("Arial", 17, "bold"), bg="#ffffff", fg="#1e293b")
        title.pack(pady=(0,16))

        question = tk.Label(card, text="Why do you need to stay up?", font=("Arial", 12), bg="#ffffff", fg="#475569")
        question.pack(pady=(0, 12))

        self.reason_trials_limiter = tk.Label(card, text=f"Attempts remaining: {controller.no_of_reason_trials}", font=("Arial", 10), bg="#ffffff", fg="#dc2626")
        self.reason_trials_limiter.pack(pady=(0, 12))

        self.reason_entry = tk.Entry(card, font=("Arial", 11), width=48, relief='solid', bd=1)
        self.reason_entry.pack(pady=(0, 20))
        self.reason_entry.focus()

        # Setting up the submit and hibernate buttons on the reason page
        btn_row = tk.Frame(card, bg="#ffffff")
        btn_row.pack()
        submit_btn = ttk.Button(btn_row, text="✓ Submit Reason", command=controller.check_reason)
        submit_btn.pack(side='left', padx=(0,10), pady=10)
        hibernate_btn = ttk.Button(btn_row, text="✕ Hibernate", command=controller.show_final_countdown)
        hibernate_btn.pack(side='left', pady=10)
        
        # Key bindings for easy app navigation
        self.reason_entry.bind('<Return>', lambda e: controller.check_reason())

    



class CountdownPage(tk.Frame):
    """
    This is the final countdown page.
    """
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent, bg="#1e1b4b")
        self.controller = controller
        self.remaining_seconds = 0

        # Centered card area with proper fill
        card = tk.Frame(self, bg=self['bg'])
        card.pack(expand=True, fill='both', padx=0, pady=0)

        self.title = tk.Label(
            card,
            text="⚠️ FINAL WARNING",
            font=("Arial", 22, "bold"),
            bg=card['bg'],
            fg="#fca5a5"
        )
        self.title.pack(pady=(48, 24))

        # Main countdown display with wrapping
        self.countdown_label = tk.Label(
            card,
            text="",
            font=("Arial", 24, "bold"),
            bg=card['bg'],
            fg="#fbbf24",
            wraplength=400,
            justify='center'
        )
        self.countdown_label.pack(pady=(0, 32), padx=20)


    def start_countdown(self, countdown_type):
        """Starts or resumes the countdown timer."""
        self.remaining_seconds = self.controller.final_countdown
        self.update_countdown_label(countdown_type)

    def update_countdown_label(self, countdown_type):
        """The recursive function to update the countdown label."""
        # Check the controller's flag to see if we should still be counting
        if not self.controller.final_timer_active:
            self.controller.show_frame("StartupPage")
            return  # Stop the countdown
            
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            if "break" == countdown_type:
                self.countdown_label.config(
                    text=f"Cool down and clear your mind.\nYour break ends in {self.remaining_seconds}s",
                    wraplength=400
                )
            elif "hibernate" == countdown_type:
                self.countdown_label.config(
                    text=f"Shutdown in: {self.remaining_seconds}s",
                    wraplength=400
                )
            else:
                print("[ERROR] countdown text does not contain any known keyword to take action")
                
            print(f"[{datetime.now()}] {self.remaining_seconds} seconds left")
            # Update the countdown every second
            self.after(1000, lambda:self.update_countdown_label(countdown_type))
        else:
            if "break" == countdown_type:
                self.countdown_label.config(text="Break over. You may continue working.", wraplength=400)
                self.controller.final_timer_active = False
                self.after(2000, lambda: self.controller.show_frame("StartupPage"))
            elif "hibernate" == countdown_type:
                self.countdown_label.config(text="Hibernating...", wraplength=400)
                self.after(2000, lambda: self.controller.hibernate_system())
            else:
                print("[ERROR] countdown text does not contain any known keyword to take action")
    

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
        self.current_time = datetime.now()
        self.current_time_str = self.current_time.strftime("%H:%M")

        self.warning_time = self.convert_to_dt_format("21:55")
        self.warning_time_str = self.warning_time.strftime("%H:%M")

        self.shutdown_time = self.convert_to_dt_format("22:00")
        self.shutdown_time_str = self.shutdown_time.strftime("%H:%M")

        self.wake_time = self.convert_to_dt_format("05:00")
        
        self.grace_period = 180
        self.final_countdown = 60
        self.extension_minutes = 30
        self.grace_timer_active = False
        self.final_timer_active = False
        self.valid_reasons = [
            "deadline", "assignment", "due", "emergency", "meeting"
        ]
        self.no_of_reason_trials = 3
        

        # Settings and Configurations
        self.strict_break_mode = True

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
        
    def convert_to_dt_format(self, time_to_convert):
        
        time_to_conv_hour, time_to_conv_minute = map(int, time_to_convert.split(":"))
        # Setting UP the Shutdown time in datetime former to be used for hours to sleep time check
        self.time_in_dt = self.current_time.replace(hour=time_to_conv_hour, minute=time_to_conv_minute, second=0, microsecond=0)
        return self.time_in_dt
        '''
        shutdown_hour, shutdown_minute = map(int, self.shutdown_time.split(":"))
        # Setting UP the Shutdown time in datetime former to be used for hours to sleep time check
        self.existing_shutdown_dt = self.current_time.replace(hour=shutdown_hour, minute=shutdown_minute, second=0, microsecond=0)
        print(self.existing_shutdown_dt)
        print(type(self.existing_shutdown_dt))
        
        wake_hour, wake_minute = map(int, self.wake_time.split(":"))
        # Splitting the shutdown time formerly in str to hour and minutes in int
        self.wake_time_dt = self.current_time.replace(hour=wake_hour, minute=wake_minute, second=0, microsecond=0)
        '''
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
        
        # DISABLE all widgets on hidden frames
        for frame_name, frame in self.frames.items():
            if frame_name != page_name:
                self.disable_all_widgets(frame)
            else:
                self.enable_all_widgets(frame)
        
        # Show the new frame
        frame = self.frames[page_name]
        frame.tkraise()
        frame.focus_set()
        
        # Bringing GUI to foreground
        self.deiconify()
        if self.state() == 'iconic':
            self.state('normal')
        
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(30000, lambda: self.attributes("-topmost", False))

    def disable_all_widgets(self, frame):
        """Recursively disable all widgets in a frame"""
        for widget in frame.winfo_children():
            try:
                # Skip labels and frames, they don't have state
                if isinstance(widget, (tk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                    widget.config(state='disabled')
            except tk.TclError:
                pass
            
            # Recursively disable child frames
            if isinstance(widget, tk.Frame):
                self.disable_all_widgets(widget)

    def enable_all_widgets(self, frame):
        """Recursively enable all widgets in a frame"""
        for widget in frame.winfo_children():
            try:
                if isinstance(widget, (tk.Entry, ttk.Button, ttk.Combobox, ttk.Checkbutton)):
                    widget.config(state='normal')
            except tk.TclError:
                pass
            
            # Recursively enable child frames
            if isinstance(widget, tk.Frame):
                self.enable_all_widgets(widget)

    def save_settings(self):
        """
        Saves the new times from the SettingsPage.
        """
        self.current_time=datetime.now()
        print("[DEBUG] Saving new settings...")
        
        try:
            # 1. Get the SettingsPage object from our frames dictionary
            settings_page = self.frames["SettingsPage"]
            # Updating the warning and shutdown time shown on the startup page immediately after saving settings
            self.warning_time_str = self.warning_time.strftime("%H:%M")
            self.shutdown_time_str = self.shutdown_time.strftime("%H:%M")
            self.frames["StartupPage"].update_status()

            # If the shutdown time (e.g., 1 AM) is earlier than now (e.g., 11 PM), 
            # it means the shutdown is scheduled for tomorrow, so add 1 day.
            if self.shutdown_time < self.current_time:
                self.shutdown_time+=timedelta(days=1)
            # Denying option to change sleep time if shutdown time is in less than 3 hours
            lockout_time = self.shutdown_time - timedelta(hours=3)
            
            # Now Checking Conditions
            if self.current_time >= lockout_time and self.current_time < self.shutdown_time:
                print("[DEBUG] Sleep Time Change Denied")
                messagebox.showerror("Sleep Time Change Denied",
                                      "Sleep Time Changes are not allowed 3 hours close to already set bedtime ", 
                                      parent=self)
                return
            else:
                # 2. Get the new values from its Entry boxes
                new_warning_time = settings_page.warning_combo.get()
                new_shutdown_time = settings_page.shutdown_combo.get()
                
                # 3. Update the CONTROLLER'S variables
                self.warning_time = self.convert_to_dt_format(new_warning_time)
                self.shutdown_time = self.convert_to_dt_format(new_shutdown_time)
                
                self.strict_break_mode = settings_page.strict_var.get()
                print(f"[DEBUG] Strict Mode set to: {self.strict_break_mode}")
                
                print(f"[DEBUG] New Warning Time: {self.warning_time.strftime("%H:%M")}")

                print(f"[DEBUG] New Shutdown Time: {self.shutdown_time.strftime("%H:%M")}")
                
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

        # Code to Unminimize the program for proper visibility
        if self.state() == 'iconic':
            self.state('normal')

        # Code to make the sleep enforcer the major focus window the user
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        self.after(100, lambda: self.attributes("-topmost", False))
    
    def handle_invalid_reasons(self):
        self.no_of_reason_trials -= 1
        print(f"[DEBUG] Invalid reason. Trials left: {self.no_of_reason_trials}")
        reason_page = self.frames["ReasonPage"]
        reason_page.reason_trials_limiter.config(
                text=f"You have {self.no_of_reason_trials} trials left"
                )
        if self.no_of_reason_trials > 0:
            messagebox.showwarning(
                "Invalid Reason", 
                f"That reason is not accepted.\nYou have {self.no_of_reason_trials} attempts left.",
                parent=self
            )
            
        else:
            self.show_final_countdown()

    def on_minimizing_to_background(self):
        """Handle the user clicking the 'X' button."""
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
        # Getting Current Time
        self.current_time = datetime.now()
        # Adding a day to wake time if it seems to be past current time
        if self.wake_time < self.current_time:
                self.wake_time+=timedelta(days=1)
        if not self.grace_timer_active and not self.final_timer_active: # IF grace timer is not active, then go on with the check. 
            if self.current_time.strftime("%H:%M")  == self.warning_time.strftime("%H:%M"):
                print("[DEBUG] WARNING TIME MATCHED! Showing warning...")
                self.show_warning()
            elif self.current_time >= self.shutdown_time:
                print("[DEBUG] SHUTDOWN TIME MATCHED! Showing reason check")
                self.show_reason_prompt()
            elif self.current_time >= self.shutdown_time and self.current_time<=self.wake_time:
                print("[DEBUG] User is awake past the sleep time. Ask the user for a reason")
                self.show_reason_prompt()
            # We are a tk.Tk object, so we can call 'after' on 'self'
            # Check Again if it is sleep time in 60 seconds
            print(self.current_time)
            print(self.warning_time)
            print(self.shutdown_time)
            print(self.wake_time)
            self.after(60000, self.check_time)
        else:
            print(f"[DEBUG] Grace/Final timer is still active, check back in 1 minute")
            self.after(60000, self.check_time)

    def show_warning(self):
        # Bring the Warning Window to user focus
        self.attributes("-topmost", True)
        # This is fine, messagebox is a dialog, not a page.
        messagebox.showwarning(
            "Bedtime Reminder",
            "⏰ 5 minutes until shutdown!\n\nPlease wrap up your work.",
            parent=self
        )
    
    def show_reason_prompt(self):
        # Rsetting number of resaon trials to 3
        self.no_of_reason_trials = 3
        # Bring the Reason Prompt to User focus
        self.attributes("-topmost", True)
        self.grace_timer_active = True
        
        self.show_frame("ReasonPage")

        print("You have 3 mins to respond")
        
        # Focus the entry field on the ReasonPage
        self.frames["ReasonPage"].reason_entry.focus()
        
        # Start the grace period timer
        self.after(self.grace_period * 1000, self.handle_grace_timeout)
        
    def handle_grace_timeout(self):
        if self.grace_timer_active:
            self.grace_timer_active = False
            print("[DEBUG] Grace timer has been put off")
            self.show_final_countdown()
    
    def check_reason(self):
        self.grace_timer_active = False
        
        ### CHANGED: Get text from the 'ReasonPage' frame
        reason_entry = self.frames["ReasonPage"].reason_entry
        reason = reason_entry.get().lower().strip().split()
        print(f"[DEBUG] The given reason contains {reason}")
        
        is_valid = any(valid in reason for valid in self.valid_reasons)
        
        ### Grant extension or show countdown.
        if is_valid:
            #--TODO--Set up a method to ask force user to take 5 minutes break before continuing work

            # THis is to ensure that they are not rushing into the work and believe it is truly essential
            # Make sure too set this up as an optional feature in settings page
            print("[DEBUG] Valid reason provided. Granting extension...")
            self.grant_extension()
        else:
            self.handle_invalid_reasons()
            
        
        # Clear the entry field for next time
        reason_entry.delete(0, 'end')

    def take_5mins_break(self):
        """5-minute break timer """
        print("[DEBUG] 5 mins break activated")
        print(f"[DEBUG] Current time: {self.current_time}")
        print(f"[DEBUG] Break status is {self.final_timer_active}")

        self.show_frame("CountdownPage")
        print("[DEBUG] CountdownPage frame shown")

        countdownpage = self.frames["CountdownPage"]
        print("[DEBUG] CountdownPage method called")

        self.final_timer_active = True
        print(f"[DEBUG] Break status is {self.final_timer_active}")

        # Set 5 minute break duration
        countdownpage.remaining_seconds = 300
        print(f"[DEBUG] Countdown seconds set to: {countdownpage.remaining_seconds}")

        # Show break notification
        messagebox.showinfo(
            "5 Minute Break",
            "Please take a 5 minute break before continuing your work.",
            parent=self
        )
        print("[DEBUG] Break notification messagebox shown")

        # Start the countdown - style for calm break mode
        countdownpage.config(bg="#f5f7fa")
        countdownpage.title.config(text="☕ Take a Break", bg="#f5f7fa", fg="#065f46")
        countdownpage.countdown_label.config(bg="#f5f7fa", fg="#059669", wraplength=400)
        print("[DEBUG] CountdownPage title updated to calm break mode")

        print("[DEBUG] Countdown label update initiated")
        print(f"[DEBUG] take_5mins_break() method completed, timer active: {self.final_timer_active}")
        self.show_frame("CountdownPage")
       
        self.final_timer_active = True
        # We want to use the same final countdown page and timer logic but just with 5 mins instead of 1 min
        countdownpage.remaining_seconds = 300  # 5 minutes
        countdownpage.update_countdown_label(countdown_type="break")
     
    def grant_extension(self):
        self.take_5mins_break()
        if not self.final_timer_active:
            self.current_time = datetime.now()
            new_shutdown = self.current_time + timedelta(minutes=self.extension_minutes)
            self.shutdown_time = new_shutdown
            self.warning_time = new_shutdown - timedelta(minutes=5)
            
            messagebox.showinfo(
                "Extension Granted",
                f"✅ Valid reason accepted!\n\nYou have {self.extension_minutes} more minutes."
            )

            # Updating Time Variables on Startup Page
            self.frames["StartupPage"].update_status()
            ### CHANGED: Show the main StartupPage again.
            self.show_frame("StartupPage")
    
    def show_final_countdown(self):
        # Bring the Final Countdown window to User focus
        self.attributes("-topmost", True)

        self.final_timer_active = True
        print(f"[DEBUG] Final Countdown Started")
        ### CHANGED: Show the frame and tell it to start its countdown.
        self.show_frame("CountdownPage")
        try:
            countdownpage = self.frames["CountdownPage"]
            countdownpage.config(bg="#1e1b4b")
            countdownpage.countdown_label.config(bg="#1e1b4b", fg="#fbbf24", wraplength=400)
            countdownpage.title.config(text="⚠️ FINAL WARNING", bg="#1e1b4b", fg="#fca5a5")
            self.frames["CountdownPage"].start_countdown(countdown_type = 'hibernate')
        except Exception as e:
            print(f"[ERROR] Failed to start countdown: {e}")

    def reopen_reason_prompt(self):
        # Bring the Reason Window to User focus
        self.attributes("-topmost", True)

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
            
        except Exception as e:
            # We can't show a messagebox here, window is gone.
            print(f"Hibernate error: {e}")
    
if __name__ == "__main__":
    # Ensure only one instance is running
    single_instance = SingleInstance()
    
    # Create and run the enforcer
    app = SleepEnforcerApp() # This is our new class
    app.mainloop()