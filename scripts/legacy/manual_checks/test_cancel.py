import tkinter as tk
root = tk.Tk()
timer_id = root.after(10, lambda: print("Fired!"))
root.update()
import time
time.sleep(0.05)
root.update()
# Now timer has fired. Try to cancel it:
try:
    root.after_cancel(timer_id)
    print("Cancel ok")
except Exception as e:
    print("Error:", e)
