import ttkbootstrap as tb
from ttkbootstrap.constants import *
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from fpdf import FPDF
import json
import os
import subprocess
import atexit

# ------------------ Global Data & Stock Management ------------------
stock_file = "stock.json"
products = {
    "Idli Batter": {"price": 35, "stock": 100},
    "Masala Items": {"price": 200, "stock": 50},
    "Oil": {"price": 240, "stock": 75},
    "Ice Creams": {"price": 50, "stock": 200}
}

bill_items = []
total = 0
stock_entries = {}
stock_window = None
last_generated_bill = None

def load_stock():
    """Loads stock data from a JSON file."""
    global products
    try:
        with open(stock_file, "r") as f:
            products = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        save_stock()
        messagebox.showinfo("Stock", "Default stock data created.")

def save_stock():
    """Saves the current stock data to a JSON file."""
    with open(stock_file, "w") as f:
        json.dump(products, f, indent=4)

# ------------------ Helper Functions ------------------
def add_item_to_bill(product_name):
    """Adds a selected product to the bill, checking stock availability."""
    global total
    try:
        qty = int(qty_var.get())
        if qty <= 0:
            messagebox.showerror("Invalid Quantity", "Quantity must be a positive number.")
            return
    except ValueError:
        messagebox.showerror("Invalid Quantity", "Quantity must be a number.")
        return

    if products[product_name]["stock"] < qty:
        messagebox.showerror("Out of Stock", f"Only {products[product_name]['stock']} of {product_name} in stock.")
        return

    price = products[product_name]["price"]
    item_total = price * qty
    bill_items.append((product_name, qty, price, item_total))
    total += item_total
    
    products[product_name]["stock"] -= qty

    total_label.config(text=f"Total: ₹{total}")
    bill_text.insert(tk.END, f"{product_name:15} {qty} x ₹{price} = ₹{item_total}\n")

def select_product_and_add(product_name):
    """Sets the product name in the UI and adds the item."""
    product_var.set(product_name)
    add_item_to_bill(product_name)

def generate_bill():
    """Generates the final bill and saves it as a PDF."""
    global last_generated_bill
    if not bill_items:
        messagebox.showwarning("Empty Bill", "Add items before generating a bill.")
        return

    bill_text.insert(tk.END, "\n" + "-"*35 + "\n")
    bill_text.insert(tk.END, f"Grand Total: ₹{total}\n", "highlight")
    bill_text.insert(tk.END, "Date: " + datetime.now().strftime("%d-%m-%Y %H:%M:%S"))
    
    save_stock()

    pdf = FPDF()
    pdf.add_page()
    
    # Updated: Removed the deprecated 'uni=True' parameter
    pdf.add_font("DejaVuSans", "", "DejaVuSans.ttf")
    pdf.add_font("DejaVuSans", "B", "DejaVuSans-Bold.ttf")

    pdf.set_font("DejaVuSans", size=12)

    pdf.cell(200, 10, text="VAZHGA VALAMUDAN STORES", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.cell(200, 10, text="-------------------------------------", new_x="LMARGIN", new_y="NEXT", align='C')
    
    for item in bill_items:
        product, qty, price, item_total = item
        bill_line = f"{product:15} {qty} x ₹{price} = ₹{item_total}"
        pdf.cell(200, 10, text=bill_line, new_x="LMARGIN", new_y="NEXT")

    pdf.cell(200, 10, text="-------------------------------------", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVuSans", 'B', 14)
    pdf.cell(200, 10, text=f"Grand Total: ₹{total}", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVuSans", size=10)
    pdf.cell(200, 10, text=f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT")

    pdf_filename = f"bill_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf.output(pdf_filename)
    last_generated_bill = pdf_filename
    
    messagebox.showinfo("Bill Generated", f"Bill saved as {pdf_filename}. You can now view and print it.")

def print_bill():
    """Opens the generated PDF file for viewing."""
    if not last_generated_bill:
        messagebox.showwarning("No Bill to Print", "Please generate a bill first.")
        return

    try:
        # Opens the PDF file for viewing
        if os.name == 'nt':
            os.startfile(last_generated_bill)
        elif os.name == 'posix':
            subprocess.run(['open', last_generated_bill])
        else:
            messagebox.showinfo("View", "Viewing is not supported on this OS.")
    except Exception as e:
        messagebox.showerror("Error", f"Could not open the file: {e}")

def refresh_bill():
    """Clears the current bill and resets the application state."""
    global total, bill_items, last_generated_bill
    total = 0
    bill_items = []
    total_label.config(text=f"Total: ₹{total}")
    bill_text.delete("1.0", tk.END)
    qty_var.set("1")
    last_generated_bill = None
    messagebox.showinfo("Refreshed", "Bill has been cleared.")

# ------------------ Stock Management Window ------------------
def update_stock_in_gui(stock_frame):
    """Refreshes the stock display in the stock window."""
    for widget in stock_frame.winfo_children():
        widget.destroy()
    
    row = 0
    for item, data in products.items():
        tb.Label(stock_frame, text=item, font=("Segoe UI", 12)).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        tb.Label(stock_frame, text="Stock:", font=("Segoe UI", 12)).grid(row=row, column=1, padx=10, pady=5, sticky="e")
        
        entry = tb.Entry(stock_frame, width=10, font=("Segoe UI", 12))
        entry.insert(0, str(data["stock"]))
        entry.grid(row=row, column=2, padx=10, pady=5)
        stock_entries[item] = entry
        row += 1

def save_and_close_stock():
    """Saves the updated stock and closes the window."""
    global products
    try:
        for item, entry in stock_entries.items():
            new_stock = int(entry.get())
            if new_stock < 0:
                messagebox.showerror("Error", "Stock cannot be a negative number.")
                return
            products[item]["stock"] = new_stock
        save_stock()
        messagebox.showinfo("Success", "Stock updated successfully!")
        stock_window.destroy()
    except ValueError:
        messagebox.showerror("Error", "Stock must be a valid number.")

def open_stock_window():
    """Opens a new window to manage product stock."""
    global stock_window, stock_entries
    if stock_window and stock_window.winfo_exists():
        stock_window.lift()
        return

    stock_window = tb.Toplevel(root)
    stock_window.title("Manage Stock")
    stock_window.geometry("400x400")
    stock_window.grab_set()

    tb.Label(stock_window, text="Update Stock", font=("Segoe UI", 16, "bold"), bootstyle="inverse").pack(fill="x", pady=10)

    stock_entries = {}
    stock_frame = tb.Frame(stock_window, padding=10)
    stock_frame.pack(fill="both", expand=True)

    update_stock_in_gui(stock_frame)

    save_button = tb.Button(stock_window, text="Save Changes", command=save_and_close_stock, bootstyle="success")
    save_button.pack(pady=10)

# ------------------ Main GUI Window ------------------
root = tb.Window(themename="darkly") 
root.title("Shop Bill Generator")
root.geometry("1000x700")

# Heading
tb.Label(root, text="🛒 VAZHGA VALAMUDAN STORES",
         font=("Segoe UI", 28, "bold"),
         bootstyle="inverse").pack(fill="x", pady=10)

# Frames
main_frame = tb.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

left_frame = tb.Frame(main_frame, padding=20, bootstyle="secondary")
left_frame.pack(side="left", fill="both", expand=True)

right_frame = tb.Frame(main_frame, padding=20, bootstyle="light")
right_frame.pack(side="right", fill="both", expand=True)

# ---- Left Frame (Product Selection) ----
tb.Label(left_frame, text="Select Product", font=("Segoe UI", 18, "bold"), bootstyle="inverse").pack(pady=10)
products_frame = tb.Frame(left_frame)
products_frame.pack(pady=10)

row, col = 0, 0
for product_name in products.keys():
    product_tile = tb.Button(products_frame, text=product_name,
                             command=lambda p=product_name: select_product_and_add(p),
                             bootstyle="info-outline", width=15)
    product_tile.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
    col += 1
    if col > 1:
        col = 0
        row += 1

# ---- Quantity and Actions ----
qty_frame = tb.Frame(left_frame)
qty_frame.pack(pady=20)
tb.Label(qty_frame, text="Quantity:", font=("Segoe UI", 12, "bold")).pack(side="left", padx=10)
qty_var = tk.StringVar(value="1")
qty_spinbox = tb.Spinbox(qty_frame, from_=1, to=100, textvariable=qty_var, width=5, font=("Segoe UI", 12))
qty_spinbox.pack(side="left")

# Action Buttons
action_frame = tb.Frame(left_frame)
action_frame.pack(pady=10, fill="x")

tb.Button(action_frame, text="Generate Bill", command=generate_bill, bootstyle="success", width=18).pack(pady=5, padx=5, fill="x")
tb.Button(action_frame, text="Print Bill", command=print_bill, bootstyle="primary", width=18).pack(pady=5, padx=5, fill="x")
tb.Button(action_frame, text="Clear Bill", command=refresh_bill, bootstyle="warning", width=18).pack(pady=5, padx=5, fill="x")
tb.Button(action_frame, text="Update Stock", command=open_stock_window, bootstyle="info", width=18).pack(pady=5, padx=5, fill="x")

product_var = tk.StringVar()

# ---- Right Frame (Bill Display) ----
tb.Label(right_frame, text="Customer Bill", font=("Segoe UI", 18, "bold"), bootstyle="inverse").pack(pady=10)
bill_display_frame = tb.Frame(right_frame)
bill_display_frame.pack(fill="both", expand=True)

bill_text = tk.Text(bill_display_frame, height=18, font=("Courier New", 12),
                    bg="#FAFAFA", relief="flat", bd=0)
bill_text.pack(side="left", fill="both", expand=True)

scrollbar = tb.Scrollbar(bill_display_frame, command=bill_text.yview)
scrollbar.pack(side="right", fill="y")
bill_text.config(yscrollcommand=scrollbar.set)

bill_text.tag_configure("highlight", foreground="#28a745", font=("Courier New", 14, "bold"))
bill_text.insert(tk.END, " " * 6 + "VAZHGA VALAMUDAN STORES\n", "center")
bill_text.insert(tk.END, "-" * 35 + "\n")

total_label = tb.Label(right_frame, text="Total: ₹0", font=("Segoe UI", 18, "bold"), bootstyle="success")
total_label.pack(pady=10)

# Footer
footer = tb.Label(root, text="Developed by VAZHGA VALAMUDAN STORES",
                 font=("Segoe UI", 10, "italic"), bootstyle="secondary")
footer.pack(side="bottom", fill="x", pady=5)

load_stock()

root.mainloop()