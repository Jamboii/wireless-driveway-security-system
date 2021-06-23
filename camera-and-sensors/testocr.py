try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
tesseract_cmd = r'/home/pi/.local/bin/pytesseract'
img = Image.open ('/home/pi/1.png')
text = pytesseract.image_to_string(img, config='')
print (text)
