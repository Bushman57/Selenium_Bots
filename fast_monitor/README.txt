Fast.com speed monitor (GUI)
==============================

What you need
-------------
- Windows 10 or later (toast notifications use win10toast).
- Google Chrome installed (the app drives Chrome to run the test on fast.com).
- Internet connection (Selenium may download a matching ChromeDriver once).

How to run the built app
------------------------
1. Unzip the whole "FastMonitor" folder (onedir build).
2. Double-click FastMonitor.exe.
3. Choose browser mode (normal, minimized, or headless), set runs and interval, then Start.
4. Results are appended to speed_readings.txt in the SAME folder as FastMonitor.exe.
5. After all runs finish, a Windows toast shows the average (if enabled).

Build the .exe (for developers)
--------------------------------
From the Flirt_Bot project, install PyInstaller in your venv, then run:

  powershell -ExecutionPolicy Bypass -File fast_monitor\build_exe.ps1

Or from fast_monitor:

  ..\bot_env\Scripts\pyinstaller.exe --clean --noconfirm fast_monitor.spec

Run from Python instead
-----------------------
From the Flirt_Bot folder (parent of fast_monitor):

  python -m fast_monitor

Command line / Task Scheduler
-----------------------------
  python -m fast_monitor.cli --headless
  python -m fast_monitor.cli --minimized --runs 6 --interval-minutes 10

Log file path: next to FastMonitor.exe when using the built app; when running from source, speed_readings.txt is created in the Flirt_Bot project folder (parent of the fast_monitor package).
