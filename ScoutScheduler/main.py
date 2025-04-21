--- a/ScoutScheduler/main.py
+++ b/ScoutScheduler/main.py
@@
-print("main.py is running")  # Add this line
+print("main.py is running")  # Add this line

-from gui.scheduler import launch_scheduler
+from ScoutScheduler.gui.scheduler import launch_scheduler

 if __name__ == "__main__":
     print("Launching GUI...")
     launch_scheduler()
