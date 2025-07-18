import os, sys, psutil, subprocess
import win32gui, win32con, win32process,win32api

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout


class TouchPadApp(App):
    def build(self):
        # --- VENTANA ---
        Window.borderless = True               # Sin título / bordes
        Window.clearcolor = (1, 1, 1, 1)       # Totalmente transparente
        Window.left, Window.top = 800, 0       # Posición
        Window.size = (400, dp(80))            # Altura fija a 80px

        # --- LAYOUT PRINCIPAL ---
        panel = BoxLayout(
            size_hint=(1, None),
            height=dp(80),
            spacing=dp(10),
            padding=[dp(10), dp(10), dp(10), dp(10)],
            orientation="horizontal",
        )

        # Botón SharePoint
        btn_sp = Button(
            text="SharePoint",
            size_hint=(1, 1),
            background_normal="",
            background_color=get_color_from_hex("#1861A5"),
            color=(1,1,1,1),
        )
        btn_sp.bind(on_release=lambda *_: os.startfile(
            "https://trw1.sharepoint.com/sites/PAPERLESSSLT"
        ))
        panel.add_widget(btn_sp)

        # Botón Cerrar Paperless
        btn_close = Button(
            text="Cerrar Paperless",
            size_hint=(1, 1),
            background_normal="",
            background_color=get_color_from_hex("#D32F2F"),
            color=(1,1,1,1),
        )
        btn_close.bind(on_release=self.close_edge_naturally)
        panel.add_widget(btn_close)

        # Siempre encima
        Clock.schedule_interval(self._keep_on_top, 1.0)

        return panel

    def on_start(self):
        # Captura única del HWND de esta ventana
        self.hwnd = win32gui.FindWindow(None, self.title)
        if self.hwnd:
            win32gui.SetWindowPos(
                self.hwnd,
                win32con.HWND_TOPMOST,
                0, 0, 0, 0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )
            # 2) habilitamos estilo LAYERED en la ventana
        ex = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(
            self.hwnd,
            win32con.GWL_EXSTYLE,
            ex | win32con.WS_EX_LAYERED
        )

        # 3) definimos el color‐key (blanco) como transparente
        #    cualquier píxel blanco (255,255,255) se renderizará invisible
        colorkey = win32api.RGB(255, 255, 255)
        win32gui.SetLayeredWindowAttributes(
            self.hwnd,
            colorkey,
            0,
            win32con.LWA_COLORKEY
        )

    def _keep_on_top(self, dt):
        if getattr(self, "hwnd", None):
            win32gui.SetWindowPos(
                self.hwnd,
                win32con.HWND_TOPMOST,
                0,0,0,0,
                win32con.SWP_NOMOVE | win32con.SWP_NOSIZE
            )

    def close_edge_naturally(self, *_):
        # Cierra todas las ventanas de Edge con Alt+F4 (SC_CLOSE)
        # para evitar el diálogo de restauración
        pids = {
            p.info["pid"]
            for p in psutil.process_iter(["name", "pid"])
            if p.info["name"] and p.info["name"].lower() == "msedge.exe"
        }
        if not pids:
            return

        def _cb(hwnd, pid_set):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            _, win_pid = win32process.GetWindowThreadProcessId(hwnd)
            if win_pid in pid_set:
                win32gui.PostMessage(hwnd, win32con.WM_SYSCOMMAND, win32con.SC_CLOSE, 0)
            return True

        win32gui.EnumWindows(_cb, pids)


if __name__ == "__main__":
    TouchPadApp().run()
