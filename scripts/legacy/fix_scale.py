with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_scale = '''                scale_w = out_w / 360
                scale_h = out_h / 640'''

new_scale = '''                scale_w = 360 / out_w
                scale_h = 640 / out_h'''

code = code.replace(old_scale, new_scale)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Fixed scale')
