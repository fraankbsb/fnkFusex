import tkinter as tk
from unittest.mock import patch
from editor_automacao import EditorAutomaDarkApp
import os
from pathlib import Path

def run_test():
    app = EditorAutomaDarkApp()
    
    # Simulate clicking "Enviar para Editar Frases"
    app.videos_carregados = [Path("C:/fake/video1.mp4")]
    app.enviar_para_frases()
    
    # Now simulate clicking "Sincronizar de .txt"
    with patch('editor_automacao.filedialog.askopenfilename') as mock_ask:
        with patch('builtins.open', create=True) as mock_open:
            mock_ask.return_value = 'C:/fake/frases.txt'
            # Mock the file content
            mock_open.return_value.__enter__.return_value.readlines.return_value = ['frase1\n', 'frase2\n']
            
            try:
                app.sincronizar_frases_txt()
                print("Sync was successful!")
            except Exception as e:
                print(f"Error during sync: {type(e).__name__} - {e}")
                
    app.destroy()

if __name__ == '__main__':
    run_test()
