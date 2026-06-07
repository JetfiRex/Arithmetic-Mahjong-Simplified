"""Android/Kivy entry point for Buildozer packaging."""

from mobile_app import SuanshuMahjongMobileApp, register_cjk_font


if __name__ == "__main__":
    register_cjk_font()
    SuanshuMahjongMobileApp().run()
