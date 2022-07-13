from neko.viewer import Application

# The duration keyword represents the time in seconds that an image will be displayed when slideshow is enabled.
app = Application(paths=['/path/to/image/dir'], duration=2, width=720, height=720)
app.run()