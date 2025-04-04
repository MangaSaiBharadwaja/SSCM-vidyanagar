from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.utils import platform
from kivymd.uix.screen import MDScreen
from kivymd.uix.webview import MDWebView
from kivy.clock import Clock

class MainScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.webview = MDWebView(url="http://localhost:5000")
        self.add_widget(self.webview)

class TemplePOSApp(MDApp):
    def build(self):
        Window.softinput_mode = "below_target"
        return MainScreen()

    def on_start(self):
        # Start Flask server
        from app import app
        import threading
        def run_flask():
            app.run(host='localhost', port=5000)
        threading.Thread(target=run_flask, daemon=True).start()
        # Wait for server to start
        Clock.schedule_once(lambda dt: None, 2)

if __name__ == '__main__':
    TemplePOSApp().run()