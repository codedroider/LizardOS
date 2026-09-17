import threading
import os

try:
    import webview
except ImportError:
    os.system('pip install pywebview')
    import webview

from pygame_gui.elements import UIProgressBar

CUSTOM_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 "
    "Firefox/128.0 (TorBrowser; MullvadBrowser) "
    "Chrome/125.0.0.0 Chromium/125.0 Beta "
    "LizardBrowser/1.0 (Privacy-First; Don't-Track-Me; No-Fingerprint)"
)

HOME_URL = 'https://codedroider.github.io/codesearch/'

def launch_browser(start_url, manager, progress_bar):
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
        resizable=True
    )
    
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

    browser_thread = threading.Thread(
        target=launch_browser, 
        args=(start_url, manager, progress_bar), 
        daemon=True
    )
    browser_thread.start()
    print("LizardBrowser started")
