from colorama import Fore, Back, Style


""" Some terminal exceptions """
class TValueError(ValueError):
    def __init__(self, message):
        super(TValueError, self).__init__(Fore.RED + Back.BLACK + Style.BRIGHT + message + Style.RESET_ALL)
class TNameError(NameError):
    def __init__(self, message):
        super(TNameError, self).__init__(Fore.RED + Back.BLACK + Style.BRIGHT + message + Style.RESET_ALL)


def printWarningN(message):
    print(message)
def printInfoN(message):
    print(message)
def printKeyValueN(k,value):
    print("-> " + k + ": " + value)

def printWarningT(message):
    print(Fore.RED + Back.BLACK + Style.BRIGHT + message + Style.RESET_ALL)
   
def printInfoT(message):
    print(Fore.Green + Back.BLACK + Style.BRIGHT + message + Style.RESET_ALL)

def printKeyValueT(k,value):
    print(Fore.Green + Back.BLACK + Style.BRIGHT + "-> " + k + ": " + Style.RESET_ALL + value)
    
    

""" Reference to error exception used in the configurator """
MyNameError  = NameError
MyValueError = ValueError

printWarning      = printWarningN
printInfo         = printInfoN
printKeyValue     = printKeyValueN


def setColoredOutput():
  global MyNameError, MyValueError, printWarning, printInfo, printKeyValue
  MyNameError  = TNameError
  MyValueError = TValueError
  
  printWarning      = printWarningT
  printInfo         = printInfoT
  printKeyValue     = printKeyValueT

