with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

bad_scale = '''                scale_w = 360 / out_w
                scale_h = 640 / out_h'''

good_scale = '''                scale_w = out_w / 360
                scale_h = out_h / 640'''

code = code.replace(bad_scale, good_scale)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Reverted scale')
