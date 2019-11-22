from fbs_runtime.application_context import ApplicationContext
from PyQt5.QtWidgets import QMainWindow

import sys

from QGameCounter import QGameCounter

class AppContext(ApplicationContext):
    def run(self):
        window = QGameCounter()
        window.appContext = self
        window.version = self.build_settings['version']
        window.show()
        return self.app.exec_()

if __name__ == '__main__':
    appctxt = AppContext()
    exit_code = appctxt.run()
    sys.exit(exit_code)