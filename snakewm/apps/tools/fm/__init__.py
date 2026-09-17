import os, shutil, subprocess, sys, base64, json, time, pygame, pygame_gui
from pygame_gui.elements import UIWindow, UISelectionList, UIButton, UITextInputLine, UILabel

class DnDFileManager(UIWindow):
    def __init__(self, rect, manager, api_instance=None):
        super().__init__(rect, manager, window_display_title="LizardFiles", object_id="#fm")
        self.current_path, self.items_data, self.browser_api = os.path.abspath(os.sep), [], api_instance
        self.context_menu = self.selected_item_path = self.clipboard_path = self.active_dialog = None
        w, h = self.get_container().get_size()
        
        self.path_input = UITextInputLine(pygame.Rect((10, 5), (w - 20, 30)), manager, self)
        self.file_list = UISelectionList(pygame.Rect((10, 40), (w - 20, h - 105)), [], manager, self)
        self.space_lbl = UILabel(pygame.Rect((10, h - 35), (w - 20, 25)), "", manager, self)
        self.update_list()

    def update_list(self):
        self.path_input.set_text(self.current_path)
        self.items_data, display_items = [], []
        try:
            for item in sorted(os.listdir(self.current_path), key=lambda x: (not os.path.isdir(os.path.join(self.current_path, x)), x.lower())):
                p = os.path.join(self.current_path, item)
                is_dir = os.path.isdir(p)
                display_items.append(f"[{'FOLDER' if is_dir else 'FILE'}] {item}")
                self.items_data.append({"path": p, "is_dir": is_dir})
            self.file_list.set_item_list(display_items)
            
            total, used, free = shutil.disk_usage(self.current_path)
            self.space_lbl.set_text(f"Free: {free // (2**30)} GB / {total // (2**30)} GB")
        except Exception:
            self.file_list.set_item_list(["[Access Denied]"])

    def show_ctx(self, pos):
        if self.context_menu: self.context_menu.kill()
        sel = self.file_list.get_single_selection()
        if not sel: return
        self.selected_item_path = self.items_data[self.file_list.item_list.index(next(i for i in self.file_list.item_list if i['text'] == sel))]["path"]
        
        self.context_menu = UIWindow(pygame.Rect(pos, (130, 195)), self.ui_manager, window_display_title="")
        btns = ["Open", "Copy", "Paste/Replace", "Rename", "Info", "Delete"]
        for i, name in enumerate(btns):
            b = UIButton(pygame.Rect((5, 5 + i*30), (110, 25)), name, self.ui_manager, self.context_menu)
            if name == "Paste/Replace" and not self.clipboard_path: b.disable()

    def trigger_open(self, p, is_dir):
        if is_dir:
            self.current_path = p
            self.update_list()
        else:
            if p.endswith(".py"): subprocess.Popen([sys.executable, p])
            elif p.endswith(".sh"): subprocess.Popen(["bash", p])

    def show_dialog(self, title, h_size, content, is_input=False):
        c_w, c_h = self.ui_manager.window_resolution
        self.active_dialog = UIWindow(pygame.Rect((c_w//2 - 150, c_h//2 - h_size//2), (300, h_size)), self.ui_manager, window_display_title=title)
        if is_input:
            self.dialog_in = UITextInputLine(pygame.Rect((10, 10), (265, 30)), self.ui_manager, self.active_dialog)
            self.dialog_in.set_text(content)
        else:
            pygame_gui.elements.UITextBox(content, pygame.Rect((10, 10), (265, h_size - 50)), self.ui_manager, self.active_dialog)

    def show_info(self):
        st = os.stat(self.selected_item_path)
        sz = sum(os.path.getsize(os.path.join(r, f)) for r, d, files in os.walk(self.selected_item_path) for f in files) if os.path.isdir(self.selected_item_path) else st.st_size
        t_c = time.strftime('%Y-%m-%d', time.localtime(st.st_ctime))
        t_m = time.strftime('%Y-%m-%d', time.localtime(st.st_mtime))
        self.show_dialog("Properties", 160, f"Name: {os.path.basename(self.selected_item_path)}<br>Size: {sz / (2**20):.2f} MB<br>Created: {t_c}<br>Modified: {t_m}")

    def process_event(self, event):
        super().process_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3 and self.file_list.rect.collidepoint(event.pos): self.show_ctx(event.pos)
            elif event.button == 1 and self.context_menu and not self.context_menu.rect.collidepoint(event.pos): self.context_menu.kill()
            
        if event.type == pygame_gui.UI_TEXT_ENTRY_FINISHED:
            if event.ui_element == self.path_input and os.path.exists(event.text):
                self.current_path = os.path.abspath(event.text)
                self.update_list()
            elif self.active_dialog and event.ui_element == self.dialog_in and event.text:
                try: os.rename(self.selected_item_path, os.path.join(os.path.dirname(self.selected_item_path), event.text)); self.update_list()
                except Exception: pass
                self.active_dialog.kill()

        if event.type == pygame_gui.UI_BUTTON_PRESSED and self.context_menu and event.ui_element.ui_container == self.context_menu.get_container():
            act = event.ui_element.text
            if act == "Open": self.trigger_open(self.selected_item_path, os.path.isdir(self.selected_item_path))
            elif act == "Copy": self.clipboard_path = self.selected_item_path
            elif act == "Paste/Replace":
                dst = os.path.join(self.current_path, os.path.basename(self.clipboard_path))
                if os.path.exists(dst): shutil.rmtree(dst) if os.path.isdir(dst) else os.remove(dst)
                shutil.copytree(self.clipboard_path, dst) if os.path.isdir(self.clipboard_path) else shutil.copy2(self.clipboard_path, dst)
                self.update_list()
            elif act == "Rename": self.show_dialog("Rename", 100, os.path.basename(self.selected_item_path), True)
            elif act == "Info": self.show_info()
            elif act == "Delete":
                try: shutil.rmtree(self.selected_item_path) if os.path.isdir(self.selected_item_path) else os.remove(self.selected_item_path); self.update_list()
                except Exception: pass
            self.context_menu.kill()

        if event.type == pygame.DROPFILE:
            dp = os.path.abspath(event.file)
            if self.browser_api and not self.rect.collidepoint(pygame.mouse.get_pos()):
                if os.path.isfile(dp):
                    try:
                        with open(dp, "rb") as f: b64 = base64.b64encode(f.read()).decode('utf-8')
                        self.browser_api.inject_file_data(b64, os.path.basename(dp))
                    except Exception: self.browser_api.load_fallback_url(dp)
                else: self.browser_api.load_fallback_url(dp)
            elif self.rect.collidepoint(pygame.mouse.get_pos()):
                dst = os.path.join(self.current_path, os.path.basename(dp))
                shutil.copytree(dp, dst) if os.path.isdir(dp) else shutil.copy2(dp, dst)
                self.update_list()
                
        if event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION and event.ui_element == self.file_list:
            sel = self.items_data[self.file_list.item_list.index(next(i for i in self.file_list.item_list if i['text'] == event.text))]
            self.trigger_open(sel["path"], sel["is_dir"])
