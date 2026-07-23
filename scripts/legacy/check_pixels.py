from PIL import Image
img = Image.open('test_stroke.png')
w, h = img.size
red_y = []
for y in range(h):
    for x in range(w):
        p = img.getpixel((x, y))
        if p[0] > 200 and p[1] < 50 and p[2] < 50:
            red_y.append(y)
print(f'Red pixels Y span: min={min(red_y)}, max={max(red_y)}')
