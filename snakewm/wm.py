"""
Snake Window Manager (LizardWM)
"""

TESTMODE = __name__ == "__main__"

import os
import sys
import importlib
import threading
import time

import pygame, pygame_gui
from pygame_gui.elements import UILabel

if TESTMODE:
    from appmenu.appmenupanel import AppMenuPanel
    from snakebg.bg import SnakeBG
    from snakebg.bgmenu import SnakeBGMenu
else:
    from snakewm.appmenu.appmenupanel import AppMenuPanel
    from snakewm.snakebg.bg import SnakeBG
    from snakewm.snakebg.bgmenu import SnakeBGMenu


class SnakeWM:
    SCREEN = None
    DIMS = None
    BG = None
    MANAGER = None

    BG_COLOR = (0, 128, 128)
    PAINT = False
    PAINT_RADIUS = 10
    PAINT_COLOR = 0
    PAINT_COLOR_LIST = [
        (255, 255, 255), (192, 192, 192), (128, 128, 128), (0, 0, 0),
        (0, 255, 0), (0, 128, 0), (128, 128, 0), (0, 128, 128),
        (255, 0, 0), (128, 0, 0), (128, 0, 128), (255, 0, 255),
        (0, 0, 255), (0, 0, 128), (0, 255, 255), (255, 255, 0),
    ]
    PAINT_SHAPE = 0
    NUM_SHAPES = 3
    DYNBG = None
    DYNBG_MENU = None
    FOCUS = None
    APPS = {}
    APPMENU = None

    def __init__(self):
        apps_path = os.path.dirname(os.path.abspath(__file__)) + "/apps"
        if os.path.exists(apps_path):
            SnakeWM.iter_dir(self.APPS, apps_path)

        pygame.init()
        os.putenv("SDL_FBDEV", "/dev/fb0")
        pygame.display.init()

        self.DIMS = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        self.SCREEN = pygame.display.set_mode(self.DIMS, pygame.FULLSCREEN)
        self.BG = pygame.Surface((self.DIMS))
        self.BG.fill(self.BG_COLOR)
        self.BRUSH_SURF = pygame.Surface((self.DIMS), flags=pygame.SRCALPHA)
        self.BRUSH_SURF.fill((0, 0, 0, 0))
        self.MANAGER = pygame_gui.UIManager(self.DIMS)
        
        self.blur_surf = pygame.Surface(self.DIMS, pygame.SRCALPHA)
        self.is_dragging = False
        self.blur_alpha = 0

        self.toast('Welcome to LizardOS!')
        pygame.mouse.set_visible(True)
        pygame.display.update()

    @staticmethod
    def iter_dir(tree, path):
        for f in os.listdir(path):
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path):
                if os.path.isfile(os.path.join(full_path, "__init__.py")):
                    tree[f] = None
                else:
                    tree[f] = {}
                    SnakeWM.iter_dir(tree[f], full_path)

    def toast(self, text):
        w, h = pygame.display.get_surface().get_size()
        lbl = UILabel(pygame.Rect((w//2 - 200, h - 100), (400, 40)), str(text), self.MANAGER)
        lbl.text_colour = pygame.Color("#FFFFFF")
        lbl.background_colour = pygame.Color("#222222")
        lbl.rebuild()
        def thide():
            time.sleep(3)
            lbl.kill()
        threading.Thread(target=thide, daemon=True).start()

    def loadapp(self, app, params=None):
        if not TESTMODE: app = "snakewm." + app
        _app = importlib.import_module(app)
        try:
            _app.load(self.MANAGER, params)
        except:
            self.toast('App crashed!')

    def appmenu_load(self, app):
        if self.APPMENU is not None:
            self.APPMENU.destroy()
            self.APPMENU = None
        self.loadapp(app)

    def set_bg_color(self, color):
        self.BG_COLOR = color
        self.BG.fill(self.BG_COLOR)

    def set_bg_image(self, file):
        filename, file_extension = os.path.splitext(file)
        if file_extension.lower() in [".jpg", ".png"]:
            self.BG = pygame.transform.scale(pygame.image.load(file), self.DIMS)

    def run(self):
        clock = pygame.time.Clock()
        running = True
        self.menu_alpha = 0

        while running:
            delta = clock.tick(60) / 1000.0
            pressed = pygame.key.get_pressed()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LSUPER:
                        if self.APPMENU is None:
                            self.APPMENU = AppMenuPanel(self.MANAGER, (0, 0), "apps", self.APPS, self.appmenu_load)
                            self.APPMENU.get_container().surface.set_alpha(self.menu_alpha)
                            self.menu_alpha = min(255, self.menu_alpha + 15)
                        else:
                            self.APPMENU.destroy()
                            self.APPMENU = None

                    if pressed[pygame.K_LALT]:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                            pygame.quit()
                            sys.exit()
                        elif event.key == pygame.K_p:
                            self.PAINT = not self.PAINT
                            self.BRUSH_SURF.fill((0, 0, 0, 0))
                        elif event.key == pygame.K_d:
                            if self.DYNBG is None and self.DYNBG_MENU is None:
                                self.DYNBG_MENU = SnakeBGMenu(self.MANAGER)
                            elif self.DYNBG is not None:
                                self.DYNBG = None

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.MANAGER.get_element_at(event.pos):
                        self.is_dragging = True
                    if self.PAINT:
                        if event.button == 4:
                            if pressed[pygame.K_LALT]: self.PAINT_COLOR = (self.PAINT_COLOR + 1) % len(self.PAINT_COLOR_LIST)
                            elif pressed[pygame.K_LCTRL]: self.PAINT_SHAPE = (self.PAINT_SHAPE + 1) % self.NUM_SHAPES
                            else: self.PAINT_RADIUS += 2
                        elif event.button == 5:
                            if pressed[pygame.K_LALT]: self.PAINT_COLOR = (self.PAINT_COLOR - 1) % len(self.PAINT_COLOR_LIST)
                            elif pressed[pygame.K_LCTRL]: self.PAINT_SHAPE = (self.PAINT_SHAPE - 1) % self.NUM_SHAPES
                            else: self.PAINT_RADIUS -= 2
                            if self.PAINT_RADIUS < 2: self.PAINT_RADIUS = 2

                elif event.type == pygame.MOUSEBUTTONUP:
                    self.is_dragging = False

                elif event.type == pygame.USEREVENT:
                    if event.user_type == "window_selected":
                        if self.FOCUS is not None: self.FOCUS.unfocus()
                        self.FOCUS = event.ui_element
                        self.FOCUS.focus()
                    elif event.user_type == pygame_gui.UI_COLOUR_PICKER_COLOUR_PICKED:
                        if event.ui_object_id == "#desktop_colour_picker": self.set_bg_color(event.colour[:-1])
                    elif event.user_type == pygame_gui.UI_FILE_DIALOG_PATH_PICKED:
                        if event.ui_object_id == "#background_picker": self.set_bg_image(event.text)
                    elif event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                        if "#bgmenu" in event.ui_object_id:
                            if "close_button" in event.ui_object_id:
                                self.DYNBG_MENU.kill()
                                self.DYNBG_MENU = None
                            elif "title_bar" not in event.ui_object_id:
                                selected_bg = event.ui_object_id.split(".")[1]
                                self.DYNBG = SnakeBG(selected_bg, TESTMODE)
                                self.DYNBG_MENU.kill()
                                self.DYNBG_MENU = None
                                self.PAINT = False

                self.MANAGER.process_events(event)

            self.MANAGER.update(delta)

            self.SCREEN.blit(self.BG, (0, 0))

            if self.is_dragging:
                self.blur_surf.blit(self.SCREEN, (0, 0))
                self.blur_alpha = max(0, self.blur_alpha - 20)
                self.blur_surf.set_alpha(self.blur_alpha)
                self.SCREEN.blit(self.blur_surf, (0, 0))
                self.blur_alpha = 180

            if self.DYNBG is not None:
                self.DYNBG.draw(self.BRUSH_SURF)
                self.SCREEN.blit(self.BRUSH_SURF, (0, 0))
            elif self.PAINT:
                mpos = pygame.mouse.get_pos()
                draw_surf = self.BG if pygame.mouse.get_pressed()[0] else self.BRUSH_SURF
                if self.PAINT_SHAPE == 0:
                    pygame.draw.circle(draw_surf, self.PAINT_COLOR_LIST[self.PAINT_COLOR], mpos, self.PAINT_RADIUS)
                elif self.PAINT_SHAPE == 1:
                    pygame.draw.rect(draw_surf, self.PAINT_COLOR_LIST[self.PAINT_COLOR], pygame.Rect((mpos[0]-self.PAINT_RADIUS, mpos[1]-self.PAINT_RADIUS), (self.PAINT_RADIUS*2, self.PAINT_RADIUS*2)))
                elif self.PAINT_SHAPE == 2:
                    pygame.draw.polygon(draw_surf, self.PAINT_COLOR_LIST[self.PAINT_COLOR], ((mpos[0]-self.PAINT_RADIUS, mpos[1]+self.PAINT_RADIUS), (mpos[0]+self.PAINT_RADIUS, mpos[1]+self.PAINT_RADIUS), (mpos[0], mpos[1]-self.PAINT_RADIUS)))
                self.SCREEN.blit(self.BRUSH_SURF, (0, 0))
                self.BRUSH_SURF.fill((0, 0, 0, 0))

            self.MANAGER.draw_ui(self.SCREEN)
            pygame.display.update()

if TESTMODE:
    wm = SnakeWM()
    wm.run()

# im so stupiddd
