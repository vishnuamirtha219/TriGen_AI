import sys
import os

def get_base_path():
    """Return the base path for bundled data files.
    When frozen by PyInstaller, files are extracted to sys._MEIPASS.
    Otherwise, use the directory containing this script.
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

# Set the base path before importing the app so config.py can use it
BASE_PATH = get_base_path()
os.environ['TRIGEN_BASE_PATH'] = BASE_PATH

from app import create_app

app = create_app()

def start_desktop():
    import webview
    import threading
    import time
    
    def run_flask():
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    time.sleep(1)
     
    webview.create_window('TriGen-AI', 'http://127.0.0.1:5000', width=1280, height=800, resizable=True)
    webview.start()

if __name__ == '__main__':
    if getattr(sys, 'frozen', False):
        # When running as an EXE, always start in desktop mode
        print("Starting in Desktop Mode (EXE)...")
        start_desktop()
    elif len(sys.argv) > 1 and sys.argv[1] == 'desktop':
        print("Starting in Desktop Mode...")
        start_desktop()
    else:
        print("Starting in Server Mode...")
        app.run(debug=True, port=5000)
