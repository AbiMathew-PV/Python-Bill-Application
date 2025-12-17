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

    if product_name not in products or products[product_name]["stock"] < qty:
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

    # Define custom page dimensions (approx. 1/3 of A4)
    # A4 is 210mm x 297mm. So 1/3 would be ~70mm x 99mm.
    page_width = 70
    page_height = 99
    
    pdf = FPDF(format=(page_width, page_height))
    pdf.add_page()
    
    # We'll use DejaVuSans to ensure the Rupee symbol (₹) is rendered correctly.
    # Make sure you have DejaVuSans.ttf and DejaVuSans-Bold.ttf in the same folder as this script.
    pdf.add_font("DejaVuSans", "", "DejaVuSans.ttf")
    pdf.add_font("DejaVuSans", "B", "DejaVuSans-Bold.ttf")
    
    # Add a border around the entire page content
    pdf.set_line_width(0.5)
    pdf.rect(5, 5, page_width - 10, page_height - 10) # Adjust rectangle for margins

    # Move current position after the border
    pdf.set_xy(5, 5) # Start content slightly inside the border

    # Generate a unique Bill ID
    bill_id = datetime.now().strftime("%Y%m%d%H%M%S")

    # Center and add the heading
    pdf.set_font("DejaVuSans", 'B', 8)
    pdf.set_x(5)
    pdf.cell(page_width - 10, 5, text="VAZHGA VALAMUDAN STORES", align='C', new_x="LMARGIN", new_y="NEXT")

    # Add the Bill ID
    pdf.set_font("DejaVuSans", '', 7)
    pdf.set_x(5)
    pdf.cell(page_width - 10, 5, text=f"Bill ID: {bill_id}", align='C', new_x="LMARGIN", new_y="NEXT")
    
    # Add the separator line
    pdf.set_x(5)
    pdf.cell(page_width - 10, 5, text="-"*30, align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(2)

    # Add the table headers
    pdf.set_font("DejaVuSans", 'B', 6) # Font for headers
    # Adjust cell widths to fit new page size
    col_width_item = 20
    col_width_qty = 8
    col_width_price = 14
    col_width_total = 18

    pdf.set_x(5)
    pdf.cell(col_width_item, 4, text="Item", border=1, align='C')
    pdf.cell(col_width_qty, 4, text="Qty", border=1, align='C')
    pdf.cell(col_width_price, 4, text="Price", border=1, align='C')
    pdf.cell(col_width_total, 4, text="Total", border=1, align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVuSans", size=6) # Font for data rows
    
    # Add bill items in a tabular format
    for item in bill_items:
        product, qty, price, item_total = item
        pdf.set_x(5)
        pdf.cell(col_width_item, 4, text=product, border=1)
        pdf.cell(col_width_qty, 4, text=str(qty), border=1, align='C')
        pdf.cell(col_width_price, 4, text=f"₹{price}", border=1, align='C')
        pdf.cell(col_width_total, 4, text=f"₹{item_total}", border=1, align='C', new_x="LMARGIN", new_y="NEXT")

    # Add separator and grand total
    pdf.ln(3)
    pdf.set_x(5)
    pdf.cell(page_width - 10, 5, text="-"*30, new_x="LMARGIN", new_y="NEXT", align='C')
    
    # Use bold font for the grand total line and align right
    pdf.set_font("DejaVuSans", 'B', 8) # Slightly larger bold font
    pdf.set_x(5)
    pdf.cell(page_width - 10, 5, text=f"Grand Total: ₹{total}", new_x="LMARGIN", new_y="NEXT", align='R')
    
    # Back to regular font for the date and align right
    pdf.set_font("DejaVuSans", size=6) # Smaller font for date
    pdf.set_x(5)
    pdf.cell(page_width - 10, 5, text=f"Date: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", new_x="LMARGIN", new_y="NEXT", align='R')

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

# ------------------ Add New Product Window ------------------
def save_new_product(window, product_entry, price_entry, stock_entry):
    """Validates and saves a new product to the stock."""
    global products
    name = product_entry.get().strip()
    price = price_entry.get().strip()
    stock = stock_entry.get().strip()

    if not name or not price or not stock:
        messagebox.showerror("Validation Error", "All fields are required.")
        return

    try:
        price = float(price)
        stock = int(stock)
        if price <= 0 or stock < 0:
            messagebox.showerror("Validation Error", "Price must be positive and stock must be non-negative.")
            return
    except ValueError:
        messagebox.showerror("Validation Error", "Price must be a number and stock must be an integer.")
        return

    if name in products:
        messagebox.showerror("Duplicate Product", f"{name} already exists. Use 'Update Stock' to modify it.")
        return

    products[name] = {"price": price, "stock": stock}
    save_stock()
    messagebox.showinfo("Success", f"Product '{name}' added successfully!")
    window.destroy()
    update_product_buttons()

def open_add_product_window():
    """Opens a new window to add a product with a scrollbar."""
    add_product_window = tb.Toplevel(root)
    add_product_window.title("Add New Product")
    add_product_window.geometry("400x300")
    add_product_window.grab_set()
    
    # Create a frame to hold the canvas and scrollbar
    main_scroll_frame = tb.Frame(add_product_window, padding=10)
    main_scroll_frame.pack(fill="both", expand=True)

    # Create a canvas and a scrollbar
    canvas = tk.Canvas(main_scroll_frame, highlightthickness=0)
    scrollbar = tb.Scrollbar(main_scroll_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tb.Frame(canvas, padding=10)

    # Configure the scrollable frame to update the canvas's scroll region
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Place form widgets inside the scrollable frame
    tb.Label(scrollable_frame, text="Product Name:", font=("Segoe UI", 12)).pack(pady=5)
    product_entry = tb.Entry(scrollable_frame, width=30, font=("Segoe UI", 12))
    product_entry.pack(pady=5)

    tb.Label(scrollable_frame, text="Price:", font=("Segoe UI", 12)).pack(pady=5)
    price_entry = tb.Entry(scrollable_frame, width=30, font=("Segoe UI", 12))
    price_entry.pack(pady=5)

    tb.Label(scrollable_frame, text="Initial Stock:", font=("Segoe UI", 12)).pack(pady=5)
    stock_entry = tb.Entry(scrollable_frame, width=30, font=("Segoe UI", 12))
    stock_entry.pack(pady=5)

    add_button = tb.Button(scrollable_frame, text="Add", bootstyle="success",
                            command=lambda: save_new_product(add_product_window, product_entry, price_entry, stock_entry))
    add_button.pack(pady=20)

# ------------------ Main GUI Window ------------------
def update_product_buttons():
    """Clears and re-creates the product selection buttons."""
    for widget in products_frame.winfo_children():
        widget.destroy()

    row, col = 0, 0
    for product_name in products.keys():
        product_tile = tb.Button(products_frame, text=product_name,
                                 command=lambda p=product_name: select_product_and_add(p),
                                 bootstyle="primary-outline", width=15)
        product_tile.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        col += 1
        if col > 1:
            col = 0
            row += 1

root = tb.Window(themename="solar") 
root.title("Shop Bill Generator")
root.geometry("1000x700")

# Heading
tb.Label(root, text="🛒 VAZHGA VALAMUDAN STORES",
         font=("Helvetica", 32, "bold", "italic"),
         bootstyle="inverse").pack(fill="x", pady=10)

# Frames
main_frame = tb.Frame(root, padding=20)
main_frame.pack(fill="both", expand=True)

left_frame = tb.Frame(main_frame, padding=20, bootstyle="dark")
left_frame.pack(side="left", fill="both", expand=True)

right_frame = tb.Frame(main_frame, padding=20, bootstyle="light")
right_frame.pack(side="right", fill="both", expand=True)

# ---- Left Frame (Product Selection) ----
tb.Label(left_frame, text="Select Product", font=("Segoe UI", 18, "bold"), bootstyle="inverse").pack(pady=10)
products_frame = tb.Frame(left_frame)
products_frame.pack(pady=10)

update_product_buttons()

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

tb.Button(action_frame, text="📄 Generate Bill", command=generate_bill, bootstyle="success", width=18).pack(pady=5, padx=5, fill="x")
tb.Button(action_frame, text="🖨️ Print Bill", command=print_bill, bootstyle="primary", width=18).pack(pady=5, padx=5, fill="x")
tb.Button(action_frame, text="🧹 Clear Bill", command=refresh_bill, bootstyle="warning", width=18).pack(pady=5, padx=5, fill="x")
tb.Button(action_frame, text="📦 Update Stock", command=open_stock_window, bootstyle="info", width=18).pack(pady=5, padx=5, fill="x")
tb.Button(action_frame, text="+ Add Product", command=open_add_product_window, bootstyle="success", width=18).pack(pady=5, padx=5, fill="x")

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

# Save stock on program exit to ensure all changes are persistent
atexit.register(save_stock)

root.mainloop()
