# **Sleep Enforcer - Developer & Agent Guide**

Welcome, Developer/Agent! This guide contains the architecture details, coding practices, environment instructions, testing guidelines, and release workflows for the Sleep Enforcer application.

> [!IMPORTANT]
> **CRITICAL CODE ISOLATION RULE**:
> All agent development, experimental feature additions, and tests MUST be executed on the **`agent-dev`** branch (or another user-specified sandbox branch). **DO NOT push directly to the `main` branch.** The user retains control of all merges into the production `main` branch.

---

## **1. Design & Architecture Overview**

The Sleep Enforcer is a single-instance Python Tkinter desktop application that tracks bedtime hours, enforces sleep breaks, and hibernates the computer if no valid reason to stay awake is provided.

```mermaid
graph TD
    A[sleep_enforcer.py] --> B[SingleInstance Lock]
    A --> C[DualLogger System]
    A --> D[SleepEnforcerApp (Tkinter Main)]
    D --> E[StartupPage (Frame)]
    D --> F[ReasonPage (Frame)]
    D --> G[CountdownPage (Frame)]
    D --> H[System Tray Icon (pystray)]
```

### **Core Components**
* **`SingleInstance`**: Prevents multiple enforcer instances from running concurrently by utilizing a temp file lock (`%TEMP%\sleep_enforcer.lock`).
* **`DualLogger`**: Automatically captures all `stdout` and `stderr` streams, writing them concurrently to both the interactive terminal console and a persistent local log file at `%LOCALAPPDATA%\SleepEnforcer\sleep_enforcer.log`.
* **GUI Structure**:
  * **`StartupPage`**: Allows configuring bedtime, warning times, wake-up times, break enforcement, and shows a digital countdown clock.
  * **`ReasonPage`**: Intercepts focus when bedtime arrives. Prompt-driven window requiring input to grant an extension or begin the shutdown timer.
  * **`CountdownPage`**: Visual final countdown clock (default 60 seconds before hibernation, or 5 minutes during strict break modes).
* **`System Tray Integration`**: Runs a background `pystray` tray thread so the application can be safely minimized to system tray and run in the background.

---

## **2. Development Guidelines for Agents**

### **Mandatory Conda Environment**
All scripts (running the app, testing, and compiling) **must** run inside the dedicated Conda environment. Do not use global python environments.
* **Env Name**: `sleep_enforcer_windows_env`
* **Activation**:
  ```powershell
  conda activate sleep_enforcer_windows_env
  ```

### **Avoid Thread Blocking with Modals**
* **Rule**: Never use default blocking OS dialogue popups (like standard `tkinter.messagebox`) during state checks or warning windows. They block the Tkinter event loop, causing countdowns to freeze and timer handlers to miss scheduled events.
* **Practice**: Always use the modern, non-blocking custom warning modal defined in the app:
  ```python
  self.show_custom_warning("Title", "Your custom alert message goes here.")
  ```

### **Local Persistent Log Tracking**
If you need to diagnose state transitions, timers, or sleep triggers, inspect:
📁 `%LOCALAPPDATA%\SleepEnforcer\sleep_enforcer.log`

---

## **3. Headless Unit Testing**

Before pushing code or compiling binaries, you **must** run and verify the test suite:
```powershell
conda run -n sleep_enforcer_windows_env python test_sleep_enforcer.py
```
This headless suite instantiates the enforcer with no GUI layout (`.withdraw()`) and validates core scheduling routines, daytime transitions, bedtime triggers, and after-midnight transitions.

---

## **4. Compilation & Release Process**

When a new version is ready, follow these exact compile and release steps:

### **Step 4.1: Bump Version Numbers**
Update the version string (e.g., from `1.3.1` to `1.3.2`) in the following files:
1. `sleep_enforcer.spec` (line: `version = "X.Y.Z"`)
2. `sleep_enforcer_installer.iss` (line: `#define AppVersion "X.Y.Z"`)

### **Step 4.2: Build the Standalone Executable**
Run PyInstaller inside the environment:
```powershell
conda run -n sleep_enforcer_windows_env pyinstaller sleep_enforcer.spec
```
This output is written to: `dist\sleep_enforcer-vX.Y.Z.exe`

### **Step 4.3: Compile the Windows Setup Installer**
Run the Inno Setup compiler using `ISCC.exe` (typically located in Inno Setup installation paths):
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" sleep_enforcer_installer.iss
```
This output is compiled to: `installer_output\Sleep-Enforcer-vX.Y.Z-Setup.exe`

### **Step 4.4: Local Git Commit & Tagging**
Commit your updates to `agent-dev`, create a Git tag, and push:
```powershell
git commit -am "bump: release vX.Y.Z updates"
git push
git tag vX.Y.Z
git push origin vX.Y.Z
```

### **Step 4.5: Automating the GitHub Release**
To publish the release and upload the portable binary and setup installer:
1. Retrieve a Personal Access Token from the **Git Credential Manager** (or GITHUB_TOKEN environment variable).
2. Execute the python release automation script:
   ```powershell
   python -u "C:\Users\israelolawuyi.OVERWATCH886\.gemini\antigravity-ide\brain\48afa492-d739-4f45-93a3-5ca24b9efe60\scratch\create_release.py"
   ```
   *(Note: The release script will automatically clean up duplicate old files on re-runs to prevent upload failures)*

---

## **5. Traceability and Sandbox Commit Authorship**

To ensure changes made by AI agents are easily auditable, the local repository has been configured to use the following Git developer credentials for all operations on the `agent-dev` branch:
* **Username**: `Antigravity Agent`
* **Email**: `agent@healthy-sleep-enforcer.local`

This ensures that agent work is never mixed up with the user's manual commits, leaving a clean trail of agent contribution.
