import threading
import webview

CUSTOM_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 "
    "Firefox/128.0 (TorBrowser; MullvadBrowser) "
    "Chrome/125.0.0.0 Chromium/125.0 Beta "
    "LizardBrowser/1.0 (Privacy-First; Don't-Track-Me; No-Fingerprint)"
)

HOME_URL = 'https://codedroider.github.io/codesearch/'

def launch_browser(start_url):
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
    
    webview.start()

def load(manager, params=None):
    start_url = params if isinstance(params, str) and params.startswith('http') else HOME_URL
    browser_thread = threading.Thread(target=launch_browser, args=(start_url,), daemon=True)
    browser_thread.start()
    print("LizardBrowser started")
