import threading
import webview

def launch_browser():
    window = webview.create_window(
        title='LizardBrowser', 
        url='https://codedroider.github.io/codesearch',
        width=900,
        height=650,
        resizable=True
    )
    webview.start()

def load(manager, params):
    browser_thread = threading.Thread(target=launch_browser, daemon=True)
    browser_thread.start()
    
    print("browser started")
