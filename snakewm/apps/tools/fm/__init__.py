import os
import shutil
import subprocess
import sys
import base64
import json
import pygame
import pygame_gui
from pygame_gui.elements import UIWindow, UISelectionList

class DnDFileManager(UIWindow):
    def __init__(self, rect, manager, api_instance=None):
        super().__init__(rect, manager, window_display_title="File Manager (root@kali:~)", object_id="#kali_mint_fm")
        self.current_path = os.path.abspath(os.sep)
        self.items_data = []
        self.browser_api = api_instance
        
        self.file_list = UISelectionList(
            relative_rect=pygame.Rect((10, 10), (rect.width - 40, rect.height - 60)),
            item_list=[],
            manager=self.ui_manager,
            container=self
        )
        self.update_list()

    def update_list(self):
        self.items_data = []
        display_items = []
        try:
            for item in sorted(os.listdir(self.current_path)):
                full_path = os.path.join(self.current_path, item)
                is_dir = os.path.isdir(full_path)
                marker = "[FOLDER]" if is_dir else "[FILE]"
                display_items.append(f"{marker} {item}")
                self.items_data.append({"path": full_path, "is_dir": is_dir, "name": item})
            self.file_list.set_item_list(display_items)
        except Exception:
            self.file_list.set_item_list(["[Access Denied]"])

    def process_event(self, event):
        super().process_event(event)
        
        if event.type == pygame.DROPFILE:
            dropped_path = os.path.abspath(event.file)
            mouse_pos = pygame.mouse.get_pos()
            
            if self.browser_api and not self.rect.collidepoint(mouse_pos):
                if os.path.isfile(dropped_path):
                    try:
                        filename = os.path.basename(dropped_path)
                        with open(dropped_path, "rb") as f:
                            b64_data = base64.b64encode(f.read()).decode('utf-8')
                        self.browser_api.inject_file_data(b64_data, filename)
                    except Exception:
                        self.browser_api.load_fallback_url(dropped_path)
                else:
                    self.browser_api.load_fallback_url(dropped_path)
                    
            elif self.rect.collidepoint(mouse_pos):
                try:
                    dest = os.path.join(self.current_path, os.path.basename(dropped_path))
                    if os.path.isdir(dropped_path):
                        shutil.copytree(dropped_path, dest)
                    else:
                        shutil.copy2(dropped_path, dest)
                    self.update_list()
                except Exception:
                    pass
                    
        if event.type == pygame_gui.UI_SELECTION_LIST_DOUBLE_CLICKED_SELECTION and event.ui_element == self.file_list:
            try:
                idx = self.file_list.item_list.index(next(item for item in self.file_list.item_list if item['text'] == event.text))
                target = self.items_data[idx]
                if target["is_dir"]:
                    self.current_path = target["path"]
                    self.update_list()
                else:
                    if target["path"].endswith(".py"):
                        subprocess.Popen([sys.executable, target["path"]])
                    elif target["path"].endswith(".sh"):
                        subprocess.Popen(["bash", target["path"]])
            except Exception:
                pass
