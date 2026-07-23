import customtkinter as ctk

app = ctk.CTk()
app.geometry("200x200")

def my_callback():
    print("Callback executed!")

def schedule_callback(*args):
    print("Scheduling...")
    app.after(500, my_callback)

slider = ctk.CTkSlider(app, from_=0, to=100, command=schedule_callback)
slider.pack(pady=20)

btn = ctk.CTkButton(app, text="Test", command=lambda: slider.set(50))
btn.pack()

# Simula um drag no slider
schedule_callback()
app.after(2000, app.destroy)
app.mainloop()
