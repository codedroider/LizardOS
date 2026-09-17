import os
import json
import threading
import pygame
from pygame_gui.elements import UIProgressBar

try:
    import webview
except ImportError:
    os.system('pip install pywebview')
    import webview

CUSTOM_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 "
    "Firefox/128.0 (TorBrowser; MullvadBrowser) "
    "Chrome/125.0.0.0 Chromium/125.0 Beta "
    "LizardBrowser/1.0 (Privacy-First; Don't-Track-Me; No-Fingerprint)"
)

HOME_URL = 'https://codedroider.github.io/codesearch/'

class BrowserAPI:
    def __init__(self):
        self.window = None

    def inject_file_data(self, b64_data, filename):
        js_injector = rf'''
        (function() {{
            var fileInput = document.querySelector('input[type="file"]');
            if (fileInput) {{
                var byteCharacters = atob("{b64_data}");
                var byteNumbers = new Array(byteCharacters.length);
                for (var i = 0; i < byteCharacters.length; i++) {{
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }}
                var byteArray = new Uint8Array(byteNumbers);
                var blob = new Blob([byteArray], {{type: "application/octet-stream"}});
                
                var dataTransfer = new DataTransfer();
                var file = new File([blob], {json.dumps(filename)}, {{type: "application/octet-stream"}});
                dataTransfer.items.add(file);
                fileInput.files = dataTransfer.files;
                
                fileInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }})();
        '''
        if self.window:
            try:
                self.window.evaluate_js(js_injector)
            except Exception:
                pass

    def load_fallback_url(self, file_path):
        if self.window:
            file_url = f"file://{os.path.abspath(file_path)}".replace("\\", "/")
            try:
                self.window.load_url(file_url)
            except Exception:
                pass

def launch_browser(start_url, manager, progress_bar, api_instance):
    webview.settings = {
        'ALLOW_DOWNLOADS': True,
        'ALLOW_FILE_URLS': True
    }
    
    webview.PLATFORM_SETTINGS = {
        'user_agent': CUSTOM_USER_AGENT
    }

    window = webview.create_window(
        title='LizardBrowser', 
        url=start_url,
        width=1024,
        height=720,
        resizable=True,
        js_api=api_instance
    )
    
    api_instance.window = window
    
    def simulate_progress():
        import time
        for i in range(0, 101, 5):
            time.sleep(0.05)
            progress_bar.set_progress(i / 100)
        time.sleep(0.5)
        progress_bar.kill()

    prog_thread = threading.Thread(target=simulate_progress, daemon=True)
    prog_thread.start()
    
    webview.start()

def load(manager, params=None):
    start_url = params if isinstance(params, str) and params.startswith('http') else HOME_URL
    
    screen_w, screen_h = manager.get_window_size()
    progress_bar = UIProgressBar(
        pygame.Rect((screen_w // 2 - 150, screen_h // 2), (300, 20)), 
        manager
    )
    progress_bar.set_progress(0)

    api_instance = BrowserAPI()

    from dnd_fm import DnDFileManager
    file_manager = DnDFileManager(
        pygame.Rect((50, 50), (400, 500)),
        manager,
        api_instance=api_instance
    )

    browser_thread = threading.Thread(
        target=launch_browser, 
        args=(start_url, manager, progress_bar, api_instance), 
        daemon=True
    )
    browser_thread.start()
    print("LizardBrowser started")
