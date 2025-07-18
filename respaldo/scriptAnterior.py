import subprocess
import os,sys
from time import time
import pyautogui
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from typing import Tuple
import win32gui, win32con, win32process
from kivy.uix.togglebutton import ToggleButton
from kivy.clock import Clock

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
        

    def on_touch_down(self, touch):
        # Guardamos posición y tiempo al iniciar el toque
        self.touch_start_x = touch.x
        self.touch_start_y = touch.y
        self.prev_x = touch.x
        self.prev_y = touch.y
        self.touch_down_time = time()

    def on_touch_move(self, touch):
        dx = touch.x - self.prev_x
        dy = touch.y - self.prev_y

        # Si el desplazamiento vertical es dominante, scroll; si no, muevo el cursor
        if abs(dy) > abs(dx) * 2:
            pyautogui.scroll(int(dy))
        else:
            pyautogui.moveRel(dx, -dy)

         # Actualizamos la posición previa
        self.prev_x = touch.x
        self.prev_y = touch.y

    def on_touch_up(self, touch):
        # si no hay posición de arranque, salimos
        if self.touch_start_x is None or self.touch_start_y is None:
            return super().on_touch_up(touch)
        
        end_time = time()
        dt = end_time - self.touch_down_time
        dx = touch.x - self.touch_start_x
        dy = touch.y - self.touch_start_y

        # Detecto “tap” (poco movimiento + corto tiempo)
        if abs(dx) < 5 and abs(dy) < 5 and dt < 0.5:
            # ¿Double-tap?; Si ocurrió otro tap recientemente, lo tratamos como doble tap
            if end_time - self.last_tap_time < 0.3:
                pyautogui.doubleClick()
                # Reiniciamos para no encadenar múltiples double-click
                self.last_tap_time = 0
            else:
                pyautogui.click()
                self.last_tap_time = end_time

        # Reseteamos todas las variables para el siguiente toque
        self.touch_start_x = self.touch_start_y = None
        self.prev_x = self.prev_y = None

        return super().on_touch_up(touch)

    #Primer metodo para abrir los documentos
    def open_url(self, raw_url: str):
        # URL por defecto si el campo viene vacío
        default_url = "https://rar.dmp.azure.zf.com/administration/digital-asset-portal/documents"
        if not raw_url.strip():
            raw_url = default_url

        # Asegurarnos de que tiene protocolo
        if not raw_url.startswith(("http://", "https://")):
            url = f"https://{raw_url}"
        else:
            url = raw_url

        print(f"[DEBUG] open_url -> {url}")
        try:
            # Esto abre tu URL con el navegador por defecto (Edge) y mantiene tu sesión
            os.startfile(url)
        except Exception as e:
            print(f"[ERROR] No pude abrir la URL: {e}")


    #Primer metodo para cerrar la ventana de Edge
    def close_portal_window(self):
        def _enum(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd) or ""
                # Ajusta este fragmento al título real que veas en la pestaña
                if "ZF Digital Manufacturing Platform" in title:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

        win32gui.EnumWindows(_enum, None)
        print("[DEBUG] Se envió WM_CLOSE a la(s) ventana(s) de Portal")




    def  close_all_processes(self):
        print(f"[DEBUG] close_all_processes: {len(self.edge_processes)} procesos activos")

        """Termina todos los procesos que abrimos."""
        for process  in self.edge_processes:
            try:
                process .terminate()
                print(f"[DEBUG] terminate() enviado a PID {process.pid}")
            except Exception as err:
                print(f"[ERROR] Falló terminate() en PID {process.pid}: {err}")
        self.edge_processes.clear()
        print("[DEBUG] Lista de procesos limpiada")

    


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
        url = "https://rar.dmp.azure.zf.com/administration/digital-asset-portal/documents"
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
        "id": "collapse",
        "type": "toggle",
        "images": {
            "normal": "images/flecha-abajo.png",
            "down":   "images/flecha-arriba.png",
        },
        "size": (40, 40),
        "callback": "toggle_collapse"
    },
    {
        "id": "open_documents",
        "type": "image_button",
        "text": "Paperless DMP",
        "images": "images/DMP LOGO.png",
        "color": (1,1,1,1),
        "bg_color": (0.1,0.5,0.8,1),
        "callback": "open_documents"
    },
    {
        "id": "open_sharepoint",
        "type": "button",
        "text": "SharePoint Paperless",
        "images": None,
        "color": (1,1,1,1),
        "bg_color": (0.8,0.4,0.1,1),
        "callback": "open_sharepoint"
    },
    {
        "id": "close_all",
        "type": "button",
        "text": "Cerrar Paperless",
        "images": None,
        "color": (1,1,1,1),
        "bg_color": (0.7,0.1,0.1,1),
        "callback": "close_everything"
    },
]





class TouchPadApp(App):
    title = "TouchPad"
    def build(self):
        Window.title = self.title
        # Ajusta aquí la posición de tu pantalla táctil:
        Window.left = 1100
        Window.top = 460
        Window.size = (400, 400)
        Window.clearcolor = (1, 1, 1, 1)

        root = FloatLayout()

        # Área touchpad (arriba)
        touch_area = TouchPad(size_hint=(1, 0.75), pos_hint={'x': 0, 'y': 0.25})
        root.add_widget(touch_area)

        control_panel = BoxLayout(
            size_hint=(1, 0.25),
            pos_hint={'x': 0, 'y': 0},
            orientation='horizontal',
            spacing=10,
            padding=10
        )

        for cfg in BUTTONS:
            if cfg["type"] == "toggle":
                button = ToggleButton(
                    size_hint=(None, None),
                    size=cfg["size"] or (40,40),
                    background_normal=resource_path(cfg["images"]["normal"]),
                    background_down=resource_path(cfg["images"]["down"]),
                    border=(0,0,0,0)
                )
            else:  # "button"
                button = Button(
                    text=cfg["text"],
                    size_hint=(None, None),
                    size=cfg.get("size", (100, 40)),
                    background_normal="",
                    background_color=cfg["bg_color"],
                    color=cfg["color"],
                    font_size="16sp"
                )

            if cfg["callback"] == "toggle_collapse":
                button.bind(on_release=self.toggle_collapse)
            else:
                button.bind(on_release=lambda inst, cb=cfg["callback"]: 
                   getattr(touch_area, cb)()
                )

            control_panel.add_widget(button)

        root.add_widget(control_panel)
        Clock.schedule_interval(self.keep_on_top, 1.0)
        
        return root

    """
            # ① Creamos el toggle con iconos (flecha derecha / izquierda)
            collapse_btn = ToggleButton(
                text="⯈",              # flecha “expandir”
                size_hint=(None, None),
                size=(100, 100)
            )


            dmp_button = Button(text="Open Paperless")
            sharepoint_button = Button(text="Open Sharepoint")
            close_button = Button(text="Close All")

            # Los vinculamos a los métodos nuevos
            collapse_btn.bind(on_release=self.toggle_collapse)  #Boton de colapsar
            dmp_button.bind(on_release=lambda *_: touch_area.open_documents())
            sharepoint_button.bind(on_release=lambda *_: touch_area.open_sharepoint())
            close_button.bind(on_release=lambda *_: touch_area.close_everything())

            
            
            control_panel.add_widget(collapse_btn)
            control_panel.add_widget(dmp_button)
            control_panel.add_widget(sharepoint_button)
            control_panel.add_widget(close_button)



            root.add_widget(control_panel)
            Clock.schedule_interval(self.keep_on_top, 1.0)
            return root
    """

            


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

    #Funcionalidad para el boton toggle
    def toggle_collapse(self, btn):
        if btn.state == "down":
            btn.text = "⯇"
            # Colapsar: solo la barra de botones (altura 50px)
            Window.size = (200, 50)
        else:
            btn.text = "⯈"            # flecha “expandir”
            # Expandir: tamaño original
            Window.size = (400, 400)

        # volvemos a forzar always-on-top
        hwnd = win32gui.FindWindow(None, self.title)
        if hwnd:
            win32gui.SetWindowPos(
                hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
        )
            
        

if __name__ == "__main__":
    TouchPadApp().run()

