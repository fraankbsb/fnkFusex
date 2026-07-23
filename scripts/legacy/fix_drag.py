import re

with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace tags in create_image
code = code.replace('tags=("frase", str(i))', 'tags=("frase", f"frase_idx_{i}")')

# Replace drag and drop methods
old_press = '''    def on_frase_press(self, event):
        item = self.pf_canvas_preview.find_withtag("current")
        if not item: return
        tags = self.pf_canvas_preview.gettags(item[0])
        if "frase" in tags:
            self._drag_frase_idx = int(tags[1])
            self._drag_start_x = event.x
            self._drag_start_y = event.y'''

new_press = '''    def on_frase_press(self, event):
        item = self.pf_canvas_preview.find_withtag("current")
        if not item: return
        tags = self.pf_canvas_preview.gettags(item[0])
        if "frase" in tags:
            for t in tags:
                if t.startswith("frase_idx_"):
                    self._drag_frase_idx = int(t.split("_")[2])
                    break
            self._drag_start_x = event.x
            self._drag_start_y = event.y'''
code = code.replace(old_press, new_press)

old_drag = '''    def on_frase_drag(self, event):
        if hasattr(self, '_drag_frase_idx'):
            dx = event.x - self._drag_start_x
            dy = event.y - self._drag_start_y
            self.pf_canvas_preview.move("current", dx, dy)
            self._drag_start_x = event.x
            self._drag_start_y = event.y'''

new_drag = '''    def on_frase_drag(self, event):
        if hasattr(self, '_drag_frase_idx'):
            dx = event.x - self._drag_start_x
            dy = event.y - self._drag_start_y
            self.pf_canvas_preview.move(f"frase_idx_{self._drag_frase_idx}", dx, dy)
            self._drag_start_x = event.x
            self._drag_start_y = event.y'''
code = code.replace(old_drag, new_drag)

old_release = '''    def on_frase_release(self, event):
        if hasattr(self, '_drag_frase_idx'):
            item = self.pf_canvas_preview.find_withtag("current")
            if not item: return
            coords = self.pf_canvas_preview.coords(item[0])
            if coords:'''

new_release = '''    def on_frase_release(self, event):
        if hasattr(self, '_drag_frase_idx'):
            items = self.pf_canvas_preview.find_withtag(f"frase_idx_{self._drag_frase_idx}")
            if not items: return
            coords = self.pf_canvas_preview.coords(items[0])
            if coords:'''
code = code.replace(old_release, new_release)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Fixed drag and drop bugs')
