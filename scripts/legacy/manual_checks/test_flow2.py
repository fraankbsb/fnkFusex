import tkinter as tk
from unittest.mock import patch
from editor_automacao import EditorAutomaDarkApp

def run_test():
    app = EditorAutomaDarkApp()
    
    # Mock askopenfilenames
    with patch('editor_automacao.filedialog.askopenfilenames') as mock_ask:
        # Mock returning some fake video files
        mock_ask.return_value = ('C:/fake/video1.mp4', 'C:/fake/video2.mp4')
        
        # Trigger the action
        app.selecionar_entrada()
        
        print("Videos carregados:", len(app.videos_carregados))
        print("Thumb labels:", len(app.labels_thumb_indiv))
        print("Grid widgets:", len(app.grid_frame.winfo_children()))
        
    app.destroy()

if __name__ == '__main__':
    run_test()
