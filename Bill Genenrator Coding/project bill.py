from fpdf import FPDF

# Product master data
products = {
    "Idli Batter": 35,
    "Masala": 200,
    "Oil": 240,
    "Ice Cream": 50
}

# Example customer order
order = {
    "Idli Batter": 2,
    "Oil": 1
}

# PDF setup
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

pdf.cell(200, 10, txt="INVOICE / BILL", ln=True, align="C")
pdf.ln(10)

total = 0
pdf.cell(100, 10, "Items", border=1)
pdf.cell(40, 10, "Qty", border=1)
pdf.cell(50, 10, "Amount", border=1)
pdf.ln()

for item, qty in order.items():
    price = products[item]
    amount = price * qty
    total += amount
    pdf.cell(100, 10, item, border=1)
    pdf.cell(40, 10, str(qty), border=1)
    pdf.cell(50, 10, f"₹{amount}", border=1)
    pdf.ln()

gst = total * 0.05
grand_total = total + gst

pdf.ln(5)
pdf.cell(150, 10, "Sub Total", border=0)
pdf.cell(50, 10, f"₹{total}", border=0, ln=True)
pdf.cell(150, 10, "GST (5%)", border=0)
pdf.cell(50, 10, f"₹{gst:.2f}", border=0, ln=True)
pdf.cell(150, 10, "Grand Total", border=0)
pdf.cell(50, 10, f"₹{grand_total:.2f}", border=0, ln=True)

pdf.output("bill.pdf")
print("✅ Bill generated as bill.pdf")
