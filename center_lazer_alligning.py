# import tkinter as tk
# import screeninfo

# # Get all 
# screens = screeninfo.get_monitors()
# current_screen = 0

# # Convert cm to pixels (approximately)
# CM_TO_PIXELS = 37.8
# DISTANCE_CM = 2  # Distance in cm
# DISTANCE_PIXELS = int(DISTANCE_CM * CM_TO_PIXELS)

# # Dot sizes
# RED_DOT_SIZE = 10
# BLUE_DOT_SIZE = 10

# def create_blue_dot():
#     # Create the blue dot window
#     blue_dot = tk.Toplevel(root)
#     blue_dot.overrideredirect(True)
#     blue_dot.configure(bg='blue')
#     blue_dot.attributes('-topmost', True)
#     return blue_dot

# def create_arrow_and_text():
#     # Create separate windows for arrow and text
#     arrow_window = tk.Toplevel(root)
#     arrow_window.overrideredirect(True)
#     arrow_window.attributes('-topmost', True)
    
#     # Use canvas for drawing the arrow
#     canvas = tk.Canvas(arrow_window, bg='white', highlightthickness=0)
#     canvas.pack(fill=tk.BOTH, expand=True)
    
#     # Create a separate window for text to ensure visibility
#     text_window = tk.Toplevel(root)
#     text_window.overrideredirect(True)
#     text_window.attributes('-topmost', True)
    
#     # Label for text
#     text_label = tk.Label(text_window, text=f"{DISTANCE_CM+0.5} cm", bg='white', font=("Arial", 10, "bold"))
#     text_label.pack()
    
#     return arrow_window, canvas, text_window

# def move_to_next_screen():
#     global current_screen, blue_dot, arrow_window, text_window
#     current_screen = (current_screen + 1) % len(screens)
#     screen = screens[current_screen]
    
#     # Position the red dot exactly at center
#     center_x = screen.x + screen.width // 2
#     center_y = screen.y + screen.height // 2
#     root.geometry(f"{RED_DOT_SIZE}x{RED_DOT_SIZE}+{center_x - RED_DOT_SIZE // 2}+{center_y - RED_DOT_SIZE // 2}")
    
#     # Position blue dot above
#     blue_dot.geometry(f"{BLUE_DOT_SIZE}x{BLUE_DOT_SIZE}+{center_x - BLUE_DOT_SIZE // 2}+{center_y - DISTANCE_PIXELS - BLUE_DOT_SIZE // 2}")
    
#     # Position and configure arrow window
#     arrow_width = 4  # Narrower arrow window
#     arrow_height = DISTANCE_PIXELS
#     arrow_window.geometry(f"{arrow_width}x{arrow_height}+{center_x - arrow_width // 2}+{center_y - arrow_height}")
    
#     # Draw arrow (two-way)
#     canvas.delete("all")
#     canvas.configure(width=arrow_width, height=arrow_height)
#     canvas.create_line(arrow_width // 2, 0, arrow_width // 2, arrow_height, arrow="both", width=2)
    
#     # Position text window to the right of the arrow
#     text_window.update_idletasks()  # Update to get accurate text size
#     text_width = text_window.winfo_width()
#     text_height = text_window.winfo_height()
#     text_x = center_x + 15  # Offset to the right of the arrow
#     text_y = center_y - (DISTANCE_PIXELS // 2) - (text_height // 2)  # Centered vertically between dots
#     text_window.geometry(f"+{text_x}+{text_y}")

# # Create the red dot
# root = tk.Tk()
# root.overrideredirect(True)
# root.configure(bg='red')
# root.attributes('-topmost', True)

# # Create the blue dot and arrow/text elements
# blue_dot = create_blue_dot()
# arrow_window, canvas, text_window = create_arrow_and_text()

# # Place on the first screen
# move_to_next_screen()

# # Move to the next screen when clicked on any of the elements
# root.bind("<Button-1>", lambda e: move_to_next_screen())
# blue_dot.bind("<Button-1>", lambda e: move_to_next_screen())
# arrow_window.bind("<Button-1>", lambda e: move_to_next_screen())
# text_window.bind("<Button-1>", lambda e: move_to_next_screen())

# root.mainloop()

import tkinter as tk
import screeninfo

# Get all screens
screens = screeninfo.get_monitors()
current_screen = 0

# Convert cm to pixels (approximately)
CM_TO_PIXELS = 30.5
VERTICAL_DISTANCE_CM = 2  # Distance in cm upward
HORIZONTAL_DISTANCE_CM = 3  # Distance in cm left/right
VERTICAL_DISTANCE_PIXELS = int(VERTICAL_DISTANCE_CM * CM_TO_PIXELS)
HORIZONTAL_DISTANCE_PIXELS = int(HORIZONTAL_DISTANCE_CM * CM_TO_PIXELS)

# Dot sizes
RED_DOT_SIZE = 10
BLUE_DOT_SIZE = 10
LEFT_DOT_SIZE = 10
RIGHT_DOT_SIZE = 10

def create_blue_dot():
    # Create the blue dot window (above center)
    blue_dot = tk.Toplevel(root)
    blue_dot.overrideredirect(True)
    blue_dot.configure(bg='blue')
    blue_dot.attributes('-topmost', True)
    return blue_dot

def create_left_dot():
    # Create the left dot window
    left_dot = tk.Toplevel(root)
    left_dot.overrideredirect(True)
    left_dot.configure(bg='green')  # Using green for left
    left_dot.attributes('-topmost', True)
    return left_dot

def create_right_dot():
    # Create the right dot window
    right_dot = tk.Toplevel(root)
    right_dot.overrideredirect(True)
    right_dot.configure(bg='purple')  # Using purple for right
    right_dot.attributes('-topmost', True)
    return right_dot

def create_arrows_and_text():
    # Create windows for arrows and text
    vertical_arrow_window = tk.Toplevel(root)
    vertical_arrow_window.overrideredirect(True)
    vertical_arrow_window.attributes('-topmost', True)
    vertical_canvas = tk.Canvas(vertical_arrow_window, bg='white', highlightthickness=0)
    vertical_canvas.pack(fill=tk.BOTH, expand=True)
    
    # Vertical text window
    vertical_text_window = tk.Toplevel(root)
    vertical_text_window.overrideredirect(True)
    vertical_text_window.attributes('-topmost', True)
    vertical_text_label = tk.Label(vertical_text_window, text=f"{VERTICAL_DISTANCE_CM} cm", 
                                 bg='white', font=("Arial", 10, "bold"))
    vertical_text_label.pack()
    
    # Left horizontal arrow
    left_arrow_window = tk.Toplevel(root)
    left_arrow_window.overrideredirect(True)
    left_arrow_window.attributes('-topmost', True)
    left_canvas = tk.Canvas(left_arrow_window, bg='white', highlightthickness=0)
    left_canvas.pack(fill=tk.BOTH, expand=True)
    
    # Left text window
    left_text_window = tk.Toplevel(root)
    left_text_window.overrideredirect(True)
    left_text_window.attributes('-topmost', True)
    left_text_label = tk.Label(left_text_window, text=f"{HORIZONTAL_DISTANCE_CM} cm", 
                             bg='white', font=("Arial", 10, "bold"))
    left_text_label.pack()
    
    # Right horizontal arrow
    right_arrow_window = tk.Toplevel(root)
    right_arrow_window.overrideredirect(True)
    right_arrow_window.attributes('-topmost', True)
    right_canvas = tk.Canvas(right_arrow_window, bg='white', highlightthickness=0)
    right_canvas.pack(fill=tk.BOTH, expand=True)
    
    # Right text window
    right_text_window = tk.Toplevel(root)
    right_text_window.overrideredirect(True)
    right_text_window.attributes('-topmost', True)
    right_text_label = tk.Label(right_text_window, text=f"{HORIZONTAL_DISTANCE_CM} cm", 
                              bg='white', font=("Arial", 10, "bold"))
    right_text_label.pack()
    
    return (vertical_arrow_window, vertical_canvas, vertical_text_window,
            left_arrow_window, left_canvas, left_text_window,
            right_arrow_window, right_canvas, right_text_window)

def move_to_next_screen():
    global current_screen
    current_screen = (current_screen + 1) % len(screens)
    screen = screens[current_screen]
    
    # Position the red dot exactly at center
    center_x = screen.x + screen.width // 2
    center_y = screen.y + screen.height // 2
    root.geometry(f"{RED_DOT_SIZE}x{RED_DOT_SIZE}+{center_x - RED_DOT_SIZE // 2}+{center_y - RED_DOT_SIZE // 2}")
    
    # Position blue dot above
    blue_dot.geometry(f"{BLUE_DOT_SIZE}x{BLUE_DOT_SIZE}+{center_x - BLUE_DOT_SIZE // 2}+{center_y - VERTICAL_DISTANCE_PIXELS - BLUE_DOT_SIZE // 2}")
    
    # Position left dot
    left_dot.geometry(f"{LEFT_DOT_SIZE}x{LEFT_DOT_SIZE}+{center_x - HORIZONTAL_DISTANCE_PIXELS - LEFT_DOT_SIZE // 2}+{center_y - LEFT_DOT_SIZE // 2}")
    
    # Position right dot
    right_dot.geometry(f"{RIGHT_DOT_SIZE}x{RIGHT_DOT_SIZE}+{center_x + HORIZONTAL_DISTANCE_PIXELS - RIGHT_DOT_SIZE // 2}+{center_y - RIGHT_DOT_SIZE // 2}")
    
    # Configure vertical arrow
    arrow_width = 4
    arrow_height = VERTICAL_DISTANCE_PIXELS
    vertical_arrow_window.geometry(f"{arrow_width}x{arrow_height}+{center_x - arrow_width // 2}+{center_y - arrow_height}")
    vertical_canvas.delete("all")
    vertical_canvas.configure(width=arrow_width, height=arrow_height)
    vertical_canvas.create_line(arrow_width // 2, 0, arrow_width // 2, arrow_height, arrow="both", width=2)
    
    # Configure left horizontal arrow
    arrow_height = 4
    arrow_width = HORIZONTAL_DISTANCE_PIXELS
    left_arrow_window.geometry(f"{arrow_width}x{arrow_height}+{center_x - arrow_width}+{center_y - arrow_height // 2}")
    left_canvas.delete("all")
    left_canvas.configure(width=arrow_width, height=arrow_height)
    left_canvas.create_line(0, arrow_height // 2, arrow_width, arrow_height // 2, arrow="both", width=2)
    
    # Configure right horizontal arrow
    right_arrow_window.geometry(f"{arrow_width}x{arrow_height}+{center_x}+{center_y - arrow_height // 2}")
    right_canvas.delete("all")
    right_canvas.configure(width=arrow_width, height=arrow_height)
    right_canvas.create_line(0, arrow_height // 2, arrow_width, arrow_height // 2, arrow="both", width=2)
    
    # Position vertical text
    vertical_text_window.update_idletasks()
    text_width = vertical_text_window.winfo_width()
    text_height = vertical_text_window.winfo_height()
    text_x = center_x + 15
    text_y = center_y - (VERTICAL_DISTANCE_PIXELS // 2) - (text_height // 2)
    vertical_text_window.geometry(f"+{text_x}+{text_y}")
    
    # Position left horizontal text
    left_text_window.update_idletasks()
    text_width = left_text_window.winfo_width()
    text_height = left_text_window.winfo_height()
    text_x = center_x - (HORIZONTAL_DISTANCE_PIXELS // 2) - (text_width // 2)
    text_y = center_y + 15
    left_text_window.geometry(f"+{text_x}+{text_y}")
    
    # Position right horizontal text
    right_text_window.update_idletasks()
    text_width = right_text_window.winfo_width()
    text_height = right_text_window.winfo_height()
    text_x = center_x + (HORIZONTAL_DISTANCE_PIXELS // 2) - (text_width // 2)
    text_y = center_y + 15
    right_text_window.geometry(f"+{text_x}+{text_y}")

# Create the red dot (center)
root = tk.Tk()
root.overrideredirect(True)
root.configure(bg='red')
root.attributes('-topmost', True)

# Create all dots
blue_dot = create_blue_dot()    # Top dot
left_dot = create_left_dot()    # Left dot
right_dot = create_right_dot()  # Right dot

# Create arrows and text elements
(vertical_arrow_window, vertical_canvas, vertical_text_window,
 left_arrow_window, left_canvas, left_text_window,
 right_arrow_window, right_canvas, right_text_window) = create_arrows_and_text()

# Place on the first screen
move_to_next_screen()

# Bind click events to all elements
root.bind("<Button-1>", lambda e: move_to_next_screen())
blue_dot.bind("<Button-1>", lambda e: move_to_next_screen())
left_dot.bind("<Button-1>", lambda e: move_to_next_screen())
right_dot.bind("<Button-1>", lambda e: move_to_next_screen())
vertical_arrow_window.bind("<Button-1>", lambda e: move_to_next_screen())
left_arrow_window.bind("<Button-1>", lambda e: move_to_next_screen())
right_arrow_window.bind("<Button-1>", lambda e: move_to_next_screen())
vertical_text_window.bind("<Button-1>", lambda e: move_to_next_screen())
left_text_window.bind("<Button-1>", lambda e: move_to_next_screen())
right_text_window.bind("<Button-1>", lambda e: move_to_next_screen())

root.mainloop()