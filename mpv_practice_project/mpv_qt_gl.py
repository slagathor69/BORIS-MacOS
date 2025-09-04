# mpv_qt_gl.py
import sys
import ctypes
from ctypes import *
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QAction, QOpenGLContext
from PySide6.QtCore import QMetaObject, Qt, QTimer, Slot
from ctypes.util import find_library

# Load libmpv
libmpv_path = find_library("mpv") or "/opt/homebrew/lib/libmpv.dylib"
#libmpv_path = "/opt/homebrew/lib/libmpv.dylib"
mpv = ctypes.CDLL(libmpv_path)

# mpv setup
mpv.mpv_create.restype = c_void_p
mpv.mpv_initialize.argtypes = [c_void_p]
mpv.mpv_initialize.restype = c_int
mpv.mpv_set_option_string.argtypes = [c_void_p, c_char_p, c_char_p]
mpv.mpv_command_async.argtypes = [c_void_p, c_ulonglong, POINTER(c_char_p)]
mpv.mpv_render_context_create.argtypes = [POINTER(c_void_p), c_void_p, POINTER(c_void_p)]
mpv.mpv_render_context_render.argtypes = [c_void_p, POINTER(c_void_p)]
mpv.mpv_render_context_set_update_callback.argtypes = [c_void_p, CFUNCTYPE(None, c_void_p), c_void_p]
mpv.mpv_set_wakeup_callback.argtypes = [c_void_p, CFUNCTYPE(None, c_void_p), c_void_p]
mpv.mpv_wait_event.argtypes = [c_void_p, c_double]
mpv.mpv_wait_event.restype = c_void_p

# Constants
MPV_RENDER_API_TYPE = 1
MPV_RENDER_PARAM_API_TYPE = 1
MPV_RENDER_PARAM_OPENGL_INIT_PARAMS = 3
MPV_RENDER_PARAM_OPENGL_FBO = 4
MPV_RENDER_PARAM_FLIP_Y = 8
MPV_RENDER_PARAM_INVALID = 0

class mpv_opengl_fbo(Structure):
    _fields_ = [("fbo", c_int),
                ("w", c_int),
                ("h", c_int),
                ("internal_format", c_int)]

class mpv_render_param(Structure):
    _fields_ = [("type", c_int), ("data", c_void_p)]

class MpvWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._mpv = c_void_p(mpv.mpv_create())
        if not self._mpv:
            raise RuntimeError("mpv_create failed")

        # set options BEFORE initialize
        mpv.mpv_set_option_string(self._mpv, b"vo", b"libmpv")
        mpv.mpv_set_option_string(self._mpv, b"gpu-api", b"opengl")
        mpv.mpv_set_option_string(self._mpv, b"gpu-context", b"mac")

        # now initialize
        mpv.mpv_initialize(self._mpv)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(30)   # 30 ms = ~33 fps

        # 🔽 Add this after mpv_initialize
        WAKEUP_CB = CFUNCTYPE(None, c_void_p)
        def _on_wakeup(_):
            QTimer.singleShot(0, self.processMpvEvents)

        self._wakeup_cb = WAKEUP_CB(_on_wakeup)  # keep a reference
        mpv.mpv_set_wakeup_callback(self._mpv, self._wakeup_cb, None)

        self._rc = c_void_p()
        
    @Slot()
    def processMpvEvents(self):
        while True:
            ev = mpv.mpv_wait_event(self._mpv, 0.0)
            if not ev:
                break
            event_id = c_int.from_address(ev).value
            if event_id == 0:  # MPV_EVENT_NONE
                break
            print("mpv event id:", event_id)
            self.update()

    def initializeGL(self):
        qt_ctx = QOpenGLContext.currentContext()

        # trampoline to Qt's getProcAddress
        GETPROC = CFUNCTYPE(c_void_p, c_void_p, c_char_p)
        def _get_proc(_, name):
            addr = qt_ctx.getProcAddress(name.decode("utf-8"))
            if not addr:
                print("Missing GL proc:", name)
            return int(addr) if addr else 0

        self._getproc = GETPROC(_get_proc)

        class mpv_opengl_init_params(Structure):
            _fields_ = [("get_proc_address", c_void_p),
                        ("get_proc_address_ctx", c_void_p)]

        gl_init = mpv_opengl_init_params()
        gl_init.get_proc_address = cast(self._getproc, c_void_p)
        gl_init.get_proc_address_ctx = None

        params = (mpv_render_param * 3)(
            mpv_render_param(MPV_RENDER_PARAM_API_TYPE, cast(c_char_p(b"opengl"), c_void_p)),
            mpv_render_param(MPV_RENDER_PARAM_OPENGL_INIT_PARAMS, byref(gl_init)),
            mpv_render_param(MPV_RENDER_PARAM_INVALID, None),
        )

        r = mpv.mpv_render_context_create(byref(self._rc), self._mpv, params)
        if r < 0:
            raise RuntimeError("mpv_render_context_create failed")

        UPDATE_CB = CFUNCTYPE(None, c_void_p)
        def _on_update(_):
            QMetaObject.invokeMethod(self, "update", Qt.QueuedConnection)

        self._update_cb = UPDATE_CB(_on_update)
        mpv.mpv_render_context_set_update_callback(self._rc, self._update_cb, None)
        
    def paintGL(self):
        if not self._rc:
            return
        from OpenGL import GL
        GL.glClearColor(0.2, 0.2, 0.2, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)

        dpr = self.devicePixelRatioF()
        fbo = mpv_opengl_fbo(
            int(self.defaultFramebufferObject()),
            int(self.width() * dpr),
            int(self.height() * dpr),
            0
        )
        flip = c_int(0)
        params = (mpv_render_param * 3)(
            mpv_render_param(MPV_RENDER_PARAM_OPENGL_FBO, cast(pointer(fbo), c_void_p)),
            mpv_render_param(MPV_RENDER_PARAM_FLIP_Y, cast(pointer(flip), c_void_p)),
            mpv_render_param(MPV_RENDER_PARAM_INVALID, None),
        )
        mpv.mpv_render_context_render(self._rc, params)
        print("paintGL called, size:", self.width(), self.height())
        
    def openFile(self, path: str):
        b = path.encode("utf-8")
        argv = (c_char_p * 3)(b"loadfile", b, None)
        mpv.mpv_command_async(self._mpv, 0, argv)
        self.update()

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 + mpv (OpenGL)")
        self.player = MpvWidget(self)
        self.setCentralWidget(self.player)

        menu = self.menuBar().addMenu("&File")
        open_action = QAction("&Open…", self)
        open_action.triggered.connect(self._open)
        menu.addAction(open_action)

    def _open(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open media")
        if f:
            self.player.openFile(f)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Main()
    win.resize(1280, 720)
    win.show()
    sys.exit(app.exec())
