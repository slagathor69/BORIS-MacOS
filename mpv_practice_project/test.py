# vulkan_window.py
from PySide6.QtGui import QGuiApplication, QVulkanInstance
from PySide6.QtGui import QSurfaceFormat
from PySide6.QtGui import QWindow
from PySide6.QtGui import QVulkanInstance
from PySide6.QtGui import QVulkanWindow
from PySide6.QtCore import QTimer
import sys

class ClearRenderer(QVulkanWindow.Renderer):
    def __init__(self, w):
        super().__init__()
        self.w = w
        self.hue = 0

    def initResources(self):
        pass  # allocate per-device resources if needed

    def releaseResources(self):
        pass  # free per-device resources

    def startNextFrame(self):
        # Just clear to a varying color; QVulkanWindow handles swapchain/begin/end
        # The clear color is configured via QVulkanWindow::setClearColor
        self.hue = (self.hue + 1) % 360
        self.w.setClearColor(self.w.clearColor().fromHsv(self.hue, 64, 64))
        self.w.frameReady()       # trigger present
        self.w.requestUpdate()    # continuous animation

class VulkanWindow(QVulkanWindow):
    def __init__(self):
        super().__init__()
        self.setTitle("PySide6 QVulkanWindow")
        self.setClearColor(self.clearColor().fromRgbF(0.05, 0.05, 0.1))

    def createRenderer(self):
        return ClearRenderer(self)

def main():
    app = QGuiApplication(sys.argv)
    inst = QVulkanInstance()
    ok = inst.create()
    if not ok:
        raise SystemExit("Failed to create QVulkanInstance (install Vulkan runtime/SDK).")
    w = VulkanWindow()
    w.setVulkanInstance(inst)
    w.resize(1280, 720)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
