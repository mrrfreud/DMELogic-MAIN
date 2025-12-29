from PIL import Image

# Convert the logo to ICO format with multiple sizes
img = Image.open("DMELogic_Logo.png")  # Or .jpg - whatever your file is
img.save("assets/app_icon.ico", format="ICO", sizes=[(256,256), (128,128), (64,64), (32,32), (16,16)])

print("✅ Icon created: assets/app_icon.ico")
