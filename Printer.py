import platform
import subprocess

class Printer:

    colorDic = {
        "Color": "",
        "Blanco/negro": ""
    }

    def __init__(self, printer_name):
        self.printer_name = printer_name
        self.__checkIfLinux()

    """ 
        1 --> Black and white
        2 --> Color
    """
    def setPrintColor(self, color):
        color = Printer.colorDic[color]
        out = subprocess.Popen([], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()

    def print(self, path):
        out = subprocess.Popen([], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout,stderr = out.communicate()

    def __checkIfLinux(self):
        if platform.system() != "Linux":
            raise Exception("This application is not running on Linux")
