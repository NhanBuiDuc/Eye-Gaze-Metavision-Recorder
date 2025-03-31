import tkinter as tk
import math
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class TriangleCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Triangle Calculator")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize variables
        self.side_a = tk.DoubleVar()
        self.side_b = tk.DoubleVar()
        self.side_c = tk.DoubleVar()
        self.angle_A = tk.DoubleVar()
        self.angle_B = tk.DoubleVar()
        self.angle_C = tk.DoubleVar()
        
        # Setting default values
        self.side_a.set("")
        self.side_b.set("")
        self.side_c.set("")
        self.angle_A.set("")
        self.angle_B.set("")
        self.angle_C.set("")
        
        # Create the main frame
        main_frame = tk.Frame(root, bg="#f0f0f0")
        main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
        
        # Create the input frame
        input_frame = tk.LabelFrame(main_frame, text="Triangle Parameters", bg="#f0f0f0", font=("Arial", 12, "bold"))
        input_frame.pack(padx=10, pady=10, fill=tk.X)
        
        # Side inputs
        sides_frame = tk.Frame(input_frame, bg="#f0f0f0")
        sides_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Label(sides_frame, text="Side a:", bg="#f0f0f0", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(sides_frame, textvariable=self.side_a, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(sides_frame, text="Side b:", bg="#f0f0f0", font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        tk.Entry(sides_frame, textvariable=self.side_b, width=10).grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(sides_frame, text="Side c:", bg="#f0f0f0", font=("Arial", 10)).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        tk.Entry(sides_frame, textvariable=self.side_c, width=10).grid(row=0, column=5, padx=5, pady=5)
        
        # Angle inputs
        angles_frame = tk.Frame(input_frame, bg="#f0f0f0")
        angles_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Label(angles_frame, text="Angle A (°):", bg="#f0f0f0", font=("Arial", 10)).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        tk.Entry(angles_frame, textvariable=self.angle_A, width=10).grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(angles_frame, text="Angle B (°):", bg="#f0f0f0", font=("Arial", 10)).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        tk.Entry(angles_frame, textvariable=self.angle_B, width=10).grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(angles_frame, text="Angle C (°):", bg="#f0f0f0", font=("Arial", 10)).grid(row=0, column=4, padx=5, pady=5, sticky="w")
        tk.Entry(angles_frame, textvariable=self.angle_C, width=10).grid(row=0, column=5, padx=5, pady=5)
        
        # Buttons
        buttons_frame = tk.Frame(input_frame, bg="#f0f0f0")
        buttons_frame.pack(padx=10, pady=10, fill=tk.X)
        
        tk.Button(buttons_frame, text="Calculate", command=self.calculate, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(buttons_frame, text="Reset", command=self.reset, bg="#f44336", fg="white", font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Result display
        self.result_frame = tk.LabelFrame(main_frame, text="Results", bg="#f0f0f0", font=("Arial", 12, "bold"))
        self.result_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.result_text = tk.Text(self.result_frame, height=10, width=60, bg="white", font=("Courier", 10))
        self.result_text.pack(padx=10, pady=10, fill=tk.X)
        
        # Triangle visualization
        self.visualization_frame = tk.LabelFrame(main_frame, text="Triangle Visualization", bg="#f0f0f0", font=("Arial", 12, "bold"))
        self.visualization_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        self.figure, self.ax = plt.subplots(figsize=(6, 4))
        self.canvas = FigureCanvasTkAgg(self.figure, self.visualization_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Draw default
        self.reset_visualization()
    
    def reset_visualization(self):
        """Reset the visualization to show a placeholder triangle"""
        self.ax.clear()
        # Draw a standard triangle with side c at the bottom
        # A at the top, B at right, C at left
        self.ax.plot([0, 1, 0.5, 0], [0, 0, 0.866, 0], 'b-')
        
        # Label the vertices
        self.ax.text(0.5, 0.866+0.05, "A", ha='center', va='center', fontsize=12, fontweight='bold')
        self.ax.text(1+0.05, 0, "B", ha='center', va='center', fontsize=12, fontweight='bold')
        self.ax.text(0-0.05, 0, "C", ha='center', va='center', fontsize=12, fontweight='bold')
        
        # Label the sides
        self.ax.text(0.75, 0.433, "b", ha='center', va='center', fontsize=12)
        self.ax.text(0.25, 0.433, "a", ha='center', va='center', fontsize=12)
        self.ax.text(0.5, -0.05, "c", ha='center', va='center', fontsize=12)
        
        # Label the angles
        self.ax.text(0.5, 0.766, "A", ha='center', va='center', color='red', fontsize=10)
        self.ax.text(0.9, 0.1, "B", ha='center', va='center', color='red', fontsize=10)
        self.ax.text(0.1, 0.1, "C", ha='center', va='center', color='red', fontsize=10)
        
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        self.ax.set_xlim(-0.2, 1.2)
        self.ax.set_ylim(-0.2, 1.2)
        self.canvas.draw()
    
    def reset(self):
        """Reset all inputs"""
        self.side_a.set("")
        self.side_b.set("")
        self.side_c.set("")
        self.angle_A.set("")
        self.angle_B.set("")
        self.angle_C.set("")
        self.result_text.delete(1.0, tk.END)
        self.reset_visualization()
    
    def validate_inputs(self):
        """Count and validate the inputs provided by the user"""
        inputs = {
            'side_a': self.try_get_value(self.side_a),
            'side_b': self.try_get_value(self.side_b),
            'side_c': self.try_get_value(self.side_c),
            'angle_A': self.try_get_value(self.angle_A),
            'angle_B': self.try_get_value(self.angle_B),
            'angle_C': self.try_get_value(self.angle_C)
        }
        
        # Count valid inputs
        valid_sides = sum(1 for side in [inputs['side_a'], inputs['side_b'], inputs['side_c']] if side is not None)
        valid_angles = sum(1 for angle in [inputs['angle_A'], inputs['angle_B'], inputs['angle_C']] if angle is not None)
        
        # Check if we have any inputs
        if valid_sides + valid_angles == 0:
            messagebox.showerror("No Data", "Please provide at least one value.")
            return None
            
        # Check if we have enough inputs for a complete triangle calculation
        # But we'll still proceed even with fewer inputs to calculate what we can
        if valid_sides + valid_angles < 3:
            messagebox.showinfo("Partial Data", "You've provided fewer than 3 values. The calculator will determine what's possible with the given information.")
            # Still proceed with calculation
        
        # Check if we have all three angles
        if valid_angles == 3:
            angle_sum = inputs['angle_A'] + inputs['angle_B'] + inputs['angle_C']
            if abs(angle_sum - 180) > 0.01:
                messagebox.showerror("Invalid Angles", "The sum of all three angles must be 180 degrees.")
                return None
        
        # Check if values are positive
        for key, value in inputs.items():
            if value is not None and value <= 0:
                messagebox.showerror("Invalid Input", f"{key} must be positive.")
                return None
        
        # Validate potential triangle by the triangle inequality
        if valid_sides == 3:
            a, b, c = inputs['side_a'], inputs['side_b'], inputs['side_c']
            if a + b <= c or a + c <= b or b + c <= a:
                messagebox.showerror("Invalid Triangle", "The sides do not satisfy the triangle inequality (sum of two sides must be greater than the third side).")
                return None
                
        return inputs
    
    def try_get_value(self, var):
        """Try to get a numeric value from a tkinter variable"""
        try:
            value = var.get()
            if value == "" or math.isnan(value):
                return None
            return float(value)
        except (ValueError, tk.TclError):
            return None
    
    def calculate(self):
        """Calculate the unknown sides and angles based on available information"""
        # Clear previous results
        self.result_text.delete(1.0, tk.END)
        
        # Validate inputs
        inputs = self.validate_inputs()
        if inputs is None:
            return
        
        # Extract the inputs
        a = inputs['side_a']
        b = inputs['side_b']
        c = inputs['side_c']
        A = inputs['angle_A']
        B = inputs['angle_B']
        C = inputs['angle_C']
        
        # Check if we have enough information for standard triangle cases
        valid_sides = sum(1 for side in [a, b, c] if side is not None)
        valid_angles = sum(1 for angle in [A, B, C] if angle is not None)
        
        # Handle cases with minimal information
        if valid_sides + valid_angles < 3:
            self.calculate_partial(a, b, c, A, B, C)
            return
        
        # Convert angles to radians for calculations
        if A is not None:
            A_rad = math.radians(A)
        if B is not None:
            B_rad = math.radians(B)
        if C is not None:
            C_rad = math.radians(C)
        
        # Case 1: All sides known (SSS)
        if a is not None and b is not None and c is not None:
            # Law of cosines for angles
            A_rad = math.acos((b**2 + c**2 - a**2) / (2 * b * c))
            B_rad = math.acos((a**2 + c**2 - b**2) / (2 * a * c))
            C_rad = math.acos((a**2 + b**2 - c**2) / (2 * a * b))
            
            A = math.degrees(A_rad)
            B = math.degrees(B_rad)
            C = math.degrees(C_rad)
        
        # Case 2: Two sides and the included angle (SAS)
        elif a is not None and b is not None and C is not None:
            # Law of cosines for the third side
            c = math.sqrt(a**2 + b**2 - 2 * a * b * math.cos(math.radians(C)))
            
            # Law of sines for the other angles
            A_rad = math.asin(a * math.sin(math.radians(C)) / c)
            B_rad = math.asin(b * math.sin(math.radians(C)) / c)
            
            A = math.degrees(A_rad)
            B = math.degrees(B_rad)
        
        elif a is not None and c is not None and B is not None:
            # Law of cosines for the third side
            b = math.sqrt(a**2 + c**2 - 2 * a * c * math.cos(math.radians(B)))
            
            # Law of sines for the other angles
            A_rad = math.asin(a * math.sin(math.radians(B)) / b)
            C_rad = math.asin(c * math.sin(math.radians(B)) / b)
            
            A = math.degrees(A_rad)
            C = math.degrees(C_rad)
        
        elif b is not None and c is not None and A is not None:
            # Law of cosines for the third side
            a = math.sqrt(b**2 + c**2 - 2 * b * c * math.cos(math.radians(A)))
            
            # Law of sines for the other angles
            B_rad = math.asin(b * math.sin(math.radians(A)) / a)
            C_rad = math.asin(c * math.sin(math.radians(A)) / a)
            
            B = math.degrees(B_rad)
            C = math.degrees(C_rad)
        
        # Case 3: Two angles and the included side (ASA)
        elif A is not None and B is not None and c is not None:
            # The third angle
            C = 180 - A - B
            C_rad = math.radians(C)
            
            # Law of sines for the other sides
            a = c * math.sin(math.radians(A)) / math.sin(C_rad)
            b = c * math.sin(math.radians(B)) / math.sin(C_rad)
        
        elif A is not None and C is not None and b is not None:
            # The third angle
            B = 180 - A - C
            B_rad = math.radians(B)
            
            # Law of sines for the other sides
            a = b * math.sin(math.radians(A)) / math.sin(B_rad)
            c = b * math.sin(math.radians(C)) / math.sin(B_rad)
        
        elif B is not None and C is not None and a is not None:
            # The third angle
            A = 180 - B - C
            A_rad = math.radians(A)
            
            # Law of sines for the other sides
            b = a * math.sin(math.radians(B)) / math.sin(A_rad)
            c = a * math.sin(math.radians(C)) / math.sin(A_rad)
        
        # Case 4: One side and two non-included angles (AAS)
        elif a is not None and A is not None and B is not None:
            # The third angle
            C = 180 - A - B
            C_rad = math.radians(C)
            
            # Law of sines for the other sides
            b = a * math.sin(math.radians(B)) / math.sin(math.radians(A))
            c = a * math.sin(C_rad) / math.sin(math.radians(A))
        
        elif b is not None and A is not None and B is not None:
            # The third angle
            C = 180 - A - B
            C_rad = math.radians(C)
            
            # Law of sines for the other sides
            a = b * math.sin(math.radians(A)) / math.sin(math.radians(B))
            c = b * math.sin(C_rad) / math.sin(math.radians(B))
        
        elif c is not None and A is not None and B is not None:
            # The third angle
            C = 180 - A - B
            C_rad = math.radians(C)
            
            # Law of sines for the other sides
            a = c * math.sin(math.radians(A)) / math.sin(C_rad)
            b = c * math.sin(math.radians(B)) / math.sin(C_rad)
            
        # Case 5: Two sides and a non-included angle (SSA)
        # This case can have 0, 1, or 2 solutions - we'll implement the single solution case
        elif a is not None and b is not None and A is not None:
            # Law of sines for angle B
            sin_B = b * math.sin(math.radians(A)) / a
            
            # Check if there's a solution
            if abs(sin_B) > 1:
                messagebox.showerror("No Solution", "There is no triangle that satisfies these conditions.")
                return
            
            B_rad = math.asin(sin_B)
            B = math.degrees(B_rad)
            
            # The third angle
            C = 180 - A - B
            C_rad = math.radians(C)
            
            # Law of sines for the third side
            c = a * math.sin(C_rad) / math.sin(math.radians(A))
        
        elif a is not None and c is not None and A is not None:
            # Law of sines for angle C
            sin_C = c * math.sin(math.radians(A)) / a
            
            # Check if there's a solution
            if abs(sin_C) > 1:
                messagebox.showerror("No Solution", "There is no triangle that satisfies these conditions.")
                return
            
            C_rad = math.asin(sin_C)
            C = math.degrees(C_rad)
            
            # The third angle
            B = 180 - A - C
            B_rad = math.radians(B)
            
            # Law of sines for the third side
            b = a * math.sin(B_rad) / math.sin(math.radians(A))
        
        elif b is not None and c is not None and B is not None:
            # Law of sines for angle C
            sin_C = c * math.sin(math.radians(B)) / b
            
            # Check if there's a solution
            if abs(sin_C) > 1:
                messagebox.showerror("No Solution", "There is no triangle that satisfies these conditions.")
                return
            
            C_rad = math.asin(sin_C)
            C = math.degrees(C_rad)
            
            # The third angle
            A = 180 - B - C
            A_rad = math.radians(A)
            
            # Law of sines for the third side
            a = b * math.sin(A_rad) / math.sin(math.radians(B))
        
        # Calculate area using Heron's formula
        s = (a + b + c) / 2  # Semi-perimeter
        area = math.sqrt(s * (s - a) * (s - b) * (s - c))
        
        # Display results
        self.display_results(a, b, c, A, B, C, area)
        
        # Draw the triangle
        self.draw_triangle(a, b, c, A, B, C)
        
    def calculate_partial(self, a, b, c, A, B, C):
        """Calculate what's possible with limited input data"""
        
        # Case: Two sides given
        if a is not None and b is not None and c is None and A is None and B is None and C is None:
            # We can calculate the range of possible values for the third side
            min_side_c = abs(a - b)
            max_side_c = a + b
            
            self.result_text.insert(tk.END, "Partial Triangle Calculation Results:\n")
            self.result_text.insert(tk.END, "===================================\n\n")
            self.result_text.insert(tk.END, f"Side a: {a:.2f}\n")
            self.result_text.insert(tk.END, f"Side b: {b:.2f}\n")
            self.result_text.insert(tk.END, f"Side c: Unknown (must be between {min_side_c:.2f} and {max_side_c:.2f})\n\n")
            self.result_text.insert(tk.END, "For a unique triangle, you need at least 3 values.\n")
            self.result_text.insert(tk.END, "Consider adding another side length or an angle.\n")
            
            # Draw a sample triangle with the maximum possible third side
            c_sample = (a + b) * 0.9  # A bit less than max for visibility
            # Calculate the angles for this sample triangle
            A_sample = math.degrees(math.acos((b**2 + c_sample**2 - a**2) / (2 * b * c_sample)))
            B_sample = math.degrees(math.acos((a**2 + c_sample**2 - b**2) / (2 * a * c_sample)))
            C_sample = 180 - A_sample - B_sample
            
            # Draw the sample triangle
            self.draw_partial_triangle(a, b, c_sample, A_sample, B_sample, C_sample, "Sample possible triangle")
            
        elif a is not None and c is not None and b is None and A is None and B is None and C is None:
            # We can calculate the range of possible values for the third side
            min_side_b = abs(a - c)
            max_side_b = a + c
            
            self.result_text.insert(tk.END, "Partial Triangle Calculation Results:\n")
            self.result_text.insert(tk.END, "===================================\n\n")
            self.result_text.insert(tk.END, f"Side a: {a:.2f}\n")
            self.result_text.insert(tk.END, f"Side b: Unknown (must be between {min_side_b:.2f} and {max_side_b:.2f})\n")
            self.result_text.insert(tk.END, f"Side c: {c:.2f}\n\n")
            self.result_text.insert(tk.END, "For a unique triangle, you need at least 3 values.\n")
            self.result_text.insert(tk.END, "Consider adding another side length or an angle.\n")
            
            # Draw a sample triangle with the maximum possible third side
            b_sample = (a + c) * 0.9  # A bit less than max for visibility
            # Calculate the angles for this sample triangle
            A_sample = math.degrees(math.acos((b_sample**2 + c**2 - a**2) / (2 * b_sample * c)))
            C_sample = math.degrees(math.acos((a**2 + b_sample**2 - c**2) / (2 * a * b_sample)))
            B_sample = 180 - A_sample - C_sample
            
            # Draw the sample triangle
            self.draw_partial_triangle(a, b_sample, c, A_sample, B_sample, C_sample, "Sample possible triangle")
            
        elif b is not None and c is not None and a is None and A is None and B is None and C is None:
            # We can calculate the range of possible values for the third side
            min_side_a = abs(b - c)
            max_side_a = b + c
            
            self.result_text.insert(tk.END, "Partial Triangle Calculation Results:\n")
            self.result_text.insert(tk.END, "===================================\n\n")
            self.result_text.insert(tk.END, f"Side a: Unknown (must be between {min_side_a:.2f} and {max_side_a:.2f})\n")
            self.result_text.insert(tk.END, f"Side b: {b:.2f}\n")
            self.result_text.insert(tk.END, f"Side c: {c:.2f}\n\n")
            self.result_text.insert(tk.END, "For a unique triangle, you need at least 3 values.\n")
            self.result_text.insert(tk.END, "Consider adding another side length or an angle.\n")
            
            # Draw a sample triangle with the maximum possible third side
            a_sample = (b + c) * 0.9  # A bit less than max for visibility
            # Calculate the angles for this sample triangle
            B_sample = math.degrees(math.acos((a_sample**2 + c**2 - b**2) / (2 * a_sample * c)))
            C_sample = math.degrees(math.acos((a_sample**2 + b**2 - c**2) / (2 * a_sample * b)))
            A_sample = 180 - B_sample - C_sample
            
            # Draw the sample triangle
            self.draw_partial_triangle(a_sample, b, c, A_sample, B_sample, C_sample, "Sample possible triangle")
            
        # Case: One side and one angle
        elif a is not None and A is not None and b is None and c is None and B is None and C is None:
            self.result_text.insert(tk.END, "Partial Triangle Calculation Results:\n")
            self.result_text.insert(tk.END, "===================================\n\n")
            self.result_text.insert(tk.END, f"Side a: {a:.2f}\n")
            self.result_text.insert(tk.END, f"Side b: Unknown\n")
            self.result_text.insert(tk.END, f"Side c: Unknown\n\n")
            self.result_text.insert(tk.END, f"Angle A: {A:.2f}°\n")
            self.result_text.insert(tk.END, f"Angle B: Unknown\n")
            self.result_text.insert(tk.END, f"Angle C: Unknown\n\n")
            self.result_text.insert(tk.END, "With one side and its opposite angle, infinite triangles are possible.\n")
            self.result_text.insert(tk.END, "For a unique triangle, you need at least 3 values.\n")
            
            # Draw a sample triangle with other angles = (180-A)/2
            B_sample = (180 - A) / 2
            C_sample = B_sample
            
            # Use law of sines to find the other sides
            b_sample = a * math.sin(math.radians(B_sample)) / math.sin(math.radians(A))
            c_sample = a * math.sin(math.radians(C_sample)) / math.sin(math.radians(A))
            
            # Draw the sample triangle
            self.draw_partial_triangle(a, b_sample, c_sample, A, B_sample, C_sample, "Sample possible triangle")
            
        # Add many more cases here for different combinations of inputs
        elif a is not None and b is not None and C is not None and c is None and A is None and B is None:
            # SAS case - we can fully determine the triangle
            # Law of cosines for the third side
            c = math.sqrt(a**2 + b**2 - 2 * a * b * math.cos(math.radians(C)))
            
            # Law of sines for the other angles
            A_rad = math.asin(a * math.sin(math.radians(C)) / c)
            B_rad = math.asin(b * math.sin(math.radians(C)) / c)
            
            A = math.degrees(A_rad)
            B = math.degrees(B_rad)
            
            # Calculate area using Heron's formula
            s = (a + b + c) / 2  # Semi-perimeter
            area = math.sqrt(s * (s - a) * (s - b) * (s - c))
            
            # Display results
            self.display_results(a, b, c, A, B, C, area)
            
            # Draw the triangle
            self.draw_triangle(a, b, c, A, B, C)
            
        else:
            self.result_text.insert(tk.END, "Insufficient or Ambiguous Data:\n")
            self.result_text.insert(tk.END, "============================\n\n")
            self.result_text.insert(tk.END, "Given values:\n")
            if a is not None: self.result_text.insert(tk.END, f"Side a: {a:.2f}\n")
            if b is not None: self.result_text.insert(tk.END, f"Side b: {b:.2f}\n")
            if c is not None: self.result_text.insert(tk.END, f"Side c: {c:.2f}\n")
            if A is not None: self.result_text.insert(tk.END, f"Angle A: {A:.2f}°\n")
            if B is not None: self.result_text.insert(tk.END, f"Angle B: {B:.2f}°\n")
            if C is not None: self.result_text.insert(tk.END, f"Angle C: {C:.2f}°\n\n")
            
            self.result_text.insert(tk.END, "For a complete triangle calculation, please provide at least 3 values\n")
            self.result_text.insert(tk.END, "that determine a unique triangle. Common combinations include:\n\n")
            self.result_text.insert(tk.END, "- Three sides (SSS)\n")
            self.result_text.insert(tk.END, "- Two sides and the included angle (SAS)\n")
            self.result_text.insert(tk.END, "- Two angles and any side (AAS or ASA)\n\n")
            
            # Reset visualization to default
            self.reset_visualization()
            
    def draw_partial_triangle(self, a, b, c, A, B, C, title_text="Sample Triangle"):
        """Draw a sample triangle with the given parameters using the same fixed orientation"""
        # Use the main drawing function for consistency
        self.draw_triangle(a, b, c, A, B, C)
        
        # Just update the title to reflect this is a sample/partial triangle
        self.ax.set_title(title_text)
    
    def display_results(self, a, b, c, A, B, C, area):
        """Display the calculated results"""
        self.result_text.insert(tk.END, "Triangle Calculation Results:\n")
        self.result_text.insert(tk.END, "===========================\n\n")
        self.result_text.insert(tk.END, f"Side a: {a:.2f}\n")
        self.result_text.insert(tk.END, f"Side b: {b:.2f}\n")
        self.result_text.insert(tk.END, f"Side c: {c:.2f}\n\n")
        self.result_text.insert(tk.END, f"Angle A: {A:.2f}°\n")
        self.result_text.insert(tk.END, f"Angle B: {B:.2f}°\n")
        self.result_text.insert(tk.END, f"Angle C: {C:.2f}°\n\n")
        self.result_text.insert(tk.END, f"Area: {area:.2f} square units\n")
        self.result_text.insert(tk.END, f"Perimeter: {a + b + c:.2f} units\n\n")
        
        # Additional trigonometric formulas used
        self.result_text.insert(tk.END, "Formulas Used:\n")
        self.result_text.insert(tk.END, "- Law of Sines: a/sin(A) = b/sin(B) = c/sin(C)\n")
        self.result_text.insert(tk.END, "- Law of Cosines: a² = b² + c² - 2bc·cos(A)\n")
        self.result_text.insert(tk.END, "- Angle Sum: A + B + C = 180°\n")
        self.result_text.insert(tk.END, "- Heron's Formula: Area = √(s(s-a)(s-b)(s-c))\n")
        self.result_text.insert(tk.END, "  where s = (a + b + c)/2\n")
    
    def draw_triangle(self, a, b, c, A, B, C):
        """Draw the triangle using matplotlib with A at top left, B at top right, C below"""
        self.ax.clear()
        
        # Fixed positions for the vertices
        # A at top left, B at top right, C below in the middle
        A_x, A_y = -0.4, 0.4   # Top left point
        B_x, B_y = 0.4, 0.4    # Top right point
        C_x, C_y = 0, -0.2     # Bottom middle point
        
        # Calculate the scale to adjust the triangle dimensions to match the actual proportions
        # First, calculate what the sides would be with these coordinates
        current_c = math.sqrt((B_x - A_x)**2 + (B_y - A_y)**2)  # Side c (AB)
        current_b = math.sqrt((A_x - C_x)**2 + (A_y - C_y)**2)  # Side b (AC)
        current_a = math.sqrt((B_x - C_x)**2 + (B_y - C_y)**2)  # Side a (BC)
        
        # Calculate scaling factors for each side
        scale_c = c / current_c
        scale_b = b / current_b
        scale_a = a / current_a
        
        # Use the average scale to preserve triangle shape
        avg_scale = (scale_a + scale_b + scale_c) / 3
        
        # Make the triangle a bit wider by adjusting the width scale
        width_scale = avg_scale * 1.3  # 30% wider
        height_scale = avg_scale
        
        # Apply different scales to x and y coordinates
        A_x *= width_scale
        B_x *= width_scale
        C_x *= width_scale
        
        A_y *= height_scale
        B_y *= height_scale
        C_y *= height_scale
        
        # Draw the triangle
        self.ax.plot([A_x, B_x, C_x, A_x], [A_y, B_y, C_y, A_y], 'b-', linewidth=2)
        
        # Add labels for vertices with better spacing
        vertex_offset = 0.05
        self.ax.text(A_x - vertex_offset, A_y + vertex_offset, "A", ha='right', va='center', fontsize=12, fontweight='bold')
        self.ax.text(B_x + vertex_offset, B_y + vertex_offset, "B", ha='left', va='center', fontsize=12, fontweight='bold')
        self.ax.text(C_x, C_y - vertex_offset, "C", ha='center', va='top', fontsize=12, fontweight='bold')
        
        # Add labels for sides with better spacing
        side_offset = 0.03
        self.ax.text((B_x + C_x) / 2 + side_offset, (B_y + C_y) / 2, f"a = {a:.2f}", ha='left', va='center')
        self.ax.text((A_x + C_x) / 2 - side_offset, (A_y + C_y) / 2, f"b = {b:.2f}", ha='right', va='center')
        self.ax.text((A_x + B_x) / 2, (A_y + B_y) / 2 + side_offset, f"c = {c:.2f}", ha='center', va='bottom')
        
        # Add angle labels with arcs using Greek letters
        radius = 0.08
        
        # Angle A (alpha)
        start_angle_A = math.degrees(math.atan2(C_y - A_y, C_x - A_x))
        end_angle_A = math.degrees(math.atan2(B_y - A_y, B_x - A_x))
        if start_angle_A < 0: start_angle_A += 360
        if end_angle_A < 0: end_angle_A += 360
        if start_angle_A > end_angle_A: start_angle_A, end_angle_A = end_angle_A, start_angle_A
        
        self.ax.add_patch(plt.matplotlib.patches.Arc((A_x, A_y), radius, radius, 
                                                theta1=start_angle_A, theta2=end_angle_A,
                                                color='red'))
        angle_pos_A = math.radians((start_angle_A + end_angle_A) / 2)
        self.ax.text(A_x + radius * 0.7 * math.cos(angle_pos_A), 
                    A_y + radius * 0.7 * math.sin(angle_pos_A), 
                    f"α = {A:.1f}°", ha='center', va='center', color='red', fontsize=10)
        
        # Angle B (beta)
        start_angle_B = math.degrees(math.atan2(C_y - B_y, C_x - B_x))
        end_angle_B = math.degrees(math.atan2(A_y - B_y, A_x - B_x))
        if start_angle_B < 0: start_angle_B += 360
        if end_angle_B < 0: end_angle_B += 360
        if start_angle_B > end_angle_B: start_angle_B, end_angle_B = end_angle_B, start_angle_B
        
        self.ax.add_patch(plt.matplotlib.patches.Arc((B_x, B_y), radius, radius, 
                                                theta1=start_angle_B, theta2=end_angle_B,
                                                color='red'))
        angle_pos_B = math.radians((start_angle_B + end_angle_B) / 2)
        self.ax.text(B_x + radius * 0.7 * math.cos(angle_pos_B), 
                    B_y + radius * 0.7 * math.sin(angle_pos_B), 
                    f"β = {B:.1f}°", ha='center', va='center', color='red', fontsize=10)
        
        # Angle C (gamma)
        start_angle_C = math.degrees(math.atan2(A_y - C_y, A_x - C_x))
        end_angle_C = math.degrees(math.atan2(B_y - C_y, B_x - C_x))
        if start_angle_C < 0: start_angle_C += 360
        if end_angle_C < 0: end_angle_C += 360
        if start_angle_C > end_angle_C: start_angle_C, end_angle_C = end_angle_C, start_angle_C
        
        self.ax.add_patch(plt.matplotlib.patches.Arc((C_x, C_y), radius, radius, 
                                                theta1=start_angle_C, theta2=end_angle_C,
                                                color='red'))
        angle_pos_C = math.radians((start_angle_C + end_angle_C) / 2)
        self.ax.text(C_x + radius * 0.7 * math.cos(angle_pos_C), 
                    C_y + radius * 0.7 * math.sin(angle_pos_C), 
                    f"γ = {C:.1f}°", ha='center', va='center', color='red', fontsize=10)
        
        # Set equal aspect ratio and margins
        margin = 0.2
        self.ax.set_xlim(min(A_x, C_x) - margin, max(B_x, C_x) + margin)
        self.ax.set_ylim(C_y - margin, max(A_y, B_y) + margin)
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        
        # Add title with measurements
        self.ax.set_title(f"Triangle (a={a:.2f}, b={b:.2f}, c={c:.2f})")
        
        # Draw the canvas
        self.canvas.draw()

if __name__ == "__main__":
    root = tk.Tk()
    app = TriangleCalculator(root)
    root.mainloop()