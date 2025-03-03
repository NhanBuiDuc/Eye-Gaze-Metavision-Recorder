import tkinter as tk
import screeninfo

# Get all screens
screens = screeninfo.get_monitors()
current_screen = 0

def move_to_next_screen():
    global current_screen
    current_screen = (current_screen + 1) % len(screens)
    screen = screens[current_screen]
    root.geometry(f"10x10+{screen.x + screen.width // 2 - 5}+{screen.y + screen.height // 2 - 5}")

# Create the red dot
root = tk.Tk()
root.overrideredirect(True)
root.configure(bg='red')
root.attributes('-topmost', True)

# Place on the first screen
move_to_next_screen()

# Move to the next screen when clicked
root.bind("<Button-1>", lambda e: move_to_next_screen())
root.mainloop()
