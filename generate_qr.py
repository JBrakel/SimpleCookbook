import qrcode

# Your GitHub Pages URL
url = "https://simplecookbook.streamlit.app"

# Generate the QR code
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,
    box_size=10,
    border=4,
)

qr.add_data(url)
qr.make(fit=True)

# Create an image
img = qr.make_image(fill_color="black", back_color="white")

# Save the QR code
img.save("SimpleCookbook.png")

print("✅ QR code saved as 'SimpleCookbook.png'")
