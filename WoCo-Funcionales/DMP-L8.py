

from kivy.config import Config
# Quita la decoración (borde y título)
Config.set('graphics', 'borderless', '1')
Config.set('graphics', 'resizable', '0')

#Imports
import subprocess
import os,sys
from time import time
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from typing import Tuple
import win32gui, win32con , win32api
from kivy.clock import Clock
from kivy.metrics import dp

# Ruta de Edge
#EDGE_EXECUTABLE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
def resource_path(rel_path: str) -> str:
    """Obtiene la ruta absoluta al recurso:
       - En desarrollo: junto al .py
       - En exe PyInstaller: dentro de _MEIPASS"""
    base = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
    return os.path.join(base, rel_path)

class TouchPad(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Coordenadas del último movimiento
        self.prev_x = None
        self.prev_y = None
        # Coordenadas y tiempo de inicio del toque
        self.touch_start_x = None
        self.touch_start_y = None
        self.touch_down_time = 0
        # Momento del último tap registrado
        self.last_tap_time = 0
        # ahora guardamos tuplas (process, perfil_temporal)
        self.edge_processes: list[Tuple[subprocess.Popen, str]] = []

    def close_everything(self):
        targets = [
        "ZF Digital Manufacturing Platform",
        "PAPERLESS - Inicio",
        ]
        # 1) Cerrar Edge buscando la ventana por título
        def _try_close_edge(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                print(hwnd, win32gui.GetWindowText(hwnd))
                title = win32gui.GetWindowText(hwnd) or ""
                # Ajusta esto al texto real en la barra de título de tu pestaña
                if any(keyword in title for keyword in targets):   
                    print(f"[DEBUG] Cerrando Edge HWND={hwnd} Título={title}")
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        
        win32gui.EnumWindows(_try_close_edge, None)

        # 2) Parar la app de Kivy
        print("[DEBUG] Cerrando aplicación Kivy")
        #App.get_running_app().stop()

    #Metodo para abrir DMP en DAP
    def open_documents(self):
        """Abre la URL de Documents usando tu perfil de Edge."""
        #url = "https://rar.dmp.azure.zf.com/production/worker-cockpit/hourly-countboard/4f13ce12-7aa0-40c7-a2ee-711b8efbf0ed/shift/41d3d1ae-1113-40b3-1091-08dda944266e"
        url = "https://rar.dmp.azure.zf.com/production/worker-cockpit/order-management/1151c8b7-e6e6-4a14-a204-934e3c2cdc6b/"
        print(f"[DEBUG] open_documents -> {url}")
        try:
            os.startfile(url)
        except Exception as e:
            print(f"[ERROR] No pude abrir Documents: {e}")

    #Metodo para abrir el Sharepoint de Paperless
    def open_sharepoint(self):
        """Abre la URL de SharePoint usando tu perfil de Edge."""
        url = "https://trw1.sharepoint.com/sites/PAPERLESSSLT"
        print(f"[DEBUG] open_sharepoint -> {url}")
        try:
            os.startfile(url)
        except Exception as e:
            print(f"[ERROR] No pude abrir SharePoint: {e}")

# Cada entrada es un botón:   
#  - type: ToggleButton o Button  
#  - images: rutas relativas (dentro de /images)  
#  - text: texto a mostrar (puede omitirse si usa solo icono)  
#  - size: tamaño fijo (None para usar size_hint)  
#  - callback: nombre del método de TouchPad  
BUTTONS = [
    
    {
        "id": "open_documents",
        #"type": "image_button",
        "type": "button",
        "text": "DMP",
        "images": "images/DMP LOGO.png",
        "color": (1,1,1,1),
        "bg_color": "#3CB371",
        "callback": "open_documents"
    },
    {
        "id": "close_all",
        "type": "button",
        "text": "Cerrar",
        "images": None,
        "color": (1,1,1,1),
        "bg_color": (0.7,0.1,0.1,1),
        "callback": "close_everything"
    },
]

class TouchPadApp(App):
    title = "TouchPad"
    def build(self):
        
        # Posición y tamaño inicial
        Window.clearcolor = (0,0,0,0)
        Window.size = (250, dp(50))
        Window.borderless = True               
        Window.resizable  = False 

        touch_area = TouchPad()
        root = FloatLayout()
        #root = AnchorLayout()
    
        # Panel de control (abajo)
        control_panel = BoxLayout(
            size_hint=(1, 1),
            orientation='horizontal',
            height=dp(50),
            pos_hint={'center_x': 0.5, 'top': 1},  
            spacing=5,
            padding=5
        )

        # 1) Toggle fijo a la izquierda
        for cfg in BUTTONS:
            btn = None
            if cfg["type"] == "toggle":
                print("toggle")
                """
                btn = ToggleButton(
                    size_hint=(None, None),
                    size=cfg["size"],
                    background_normal=resource_path(cfg["images"]["normal"]),
                    background_down=  resource_path(cfg["images"]["down"]),
                    border=(0,0,0,0)
                )
                btn.bind(on_release=self.toggle_collapse)
                """
            else:
                # crea botón normal (incluye texto desde cfg["text"])
                btn = Button(
                    text=cfg["text"],
                    size_hint=(0.5, 1),
                    background_normal="",
                    background_color=cfg["bg_color"],
                    color=cfg["color"],
                    halign="center",
                    valign="middle",
                )
                # para que haga wrap si es necesario
                btn.text_size = (btn.width, None)
                btn.bind(width=lambda inst, w: inst.setter('text_size')(inst, (w, None)))
                # link al método de TouchPad

                method = getattr(touch_area, cfg["callback"])
                btn.bind(on_release=lambda inst, fn=method: fn())

            control_panel.add_widget(btn)

        root.add_widget(control_panel)
        Clock.schedule_once(self._strip_and_raise, 0.1)
        Clock.schedule_interval(self.keep_on_top, 1.0)
        return root


    #Funcionalidad para fijar el touchpad como primer plano
    def keep_on_top(self, dt):
        if hasattr(self, 'hwnd') and self.hwnd:
            win32gui.SetWindowPos(
                self.hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )

    def on_start(self):
        # Esto fuerza tu ventana a top-most
        # Sólo una vez, capturamos el HWND de nuestra ventana
        self.hwnd = win32gui.FindWindow(None, self.title)
        if self.hwnd:
            # lo ponemos top-most inmediatamente
            win32gui.SetWindowPos(
                self.hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )

    def _strip_and_raise(self, dt):
        """
        1) Quita caption, sysmenu, min/max boxes
        2) Lo vuelve TOPMOST inmediatamente
        """
        if not hasattr(self, 'hwnd') or not self.hwnd:
            return

        # 1) Stripping estilo
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_STYLE)
        style &= ~(
            win32con.WS_CAPTION |
            win32con.WS_THICKFRAME |
            win32con.WS_MINIMIZEBOX |
            win32con.WS_MAXIMIZEBOX |
            win32con.WS_SYSMENU
        )
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_STYLE, style)

        # 2) Forzar refresco de estilo
        win32gui.SetWindowPos(
            self.hwnd, None, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_FRAMECHANGED
        )

         # 3) Calculamos centro‐arriba usando Win32
        screen_w = win32api.GetSystemMetrics(0)
        win_w    = Window.width
        x = int((screen_w - win_w) / 2)
        y = 0   # 0 píxeles desde arriba

        # 4) Movemos la ventana y la ponemos topmost de una sola vez
        win32gui.SetWindowPos(
            self.hwnd,
            win32con.HWND_TOPMOST,
            x, y, 0, 0,
            win32con.SWP_NOSIZE
        )


    def _strip_win_style(self, _):
        """Quita caption, sysmenu, minimizar/maximizar en Win32."""
        hwnd = win32gui.FindWindow(None, self.title)
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
        # apagar caption, thickframe, min/max boxes, sysmenu
        style &= ~(win32con.WS_CAPTION 
                 | win32con.WS_THICKFRAME
                 | win32con.WS_MINIMIZEBOX
                 | win32con.WS_MAXIMIZEBOX
                 | win32con.WS_SYSMENU)
        win32gui.SetWindowLong(hwnd, win32con.GWL_STYLE, style)
        # forzar refresco de estilos
        win32gui.SetWindowPos(
            hwnd, None, 0, 0, 0, 0,
            win32con.SWP_NOMOVE
          | win32con.SWP_NOSIZE
          | win32con.SWP_FRAMECHANGED
        )

if __name__ == "__main__":
    TouchPadApp().run()

