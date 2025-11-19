import qrcode

# Your GitHub Pages URL
url = "https://jbrakel.github.io/YogaAdventskalender/"

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
img.save("yoga_advent_calendar_2025.png")

print("✅ QR code saved as 'yoga_advent_calendar_2025.png'")
