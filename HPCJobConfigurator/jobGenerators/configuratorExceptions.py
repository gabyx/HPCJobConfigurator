import colorama
from colorama import Fore, Back, Style


""" Some terminal exceptions """
class TValueError(ValueError):
    def __init__(self, message):
        super(TValueError, self).__init__(Fore.RED + Back.BLACK + Style.BRIGHT + message + Style.RESET_ALL)
class TNameError(NameError):
    def __init__(self, message):
        super(TNameError, self).__init__(Fore.RED + Back.BLACK + Style.BRIGHT + message + Style.RESET_ALL)


def makeWarningT(m):
  return Fore.RED + Back.BLACK + Style.BRIGHT + m + Style.RESET_ALL
  
def makeInfoT(m):
  return  m
  
def makeHeaderT(m):
  return Style.BRIGHT + m + Style.RESET_ALL
  
def makeKeyMessageT(k,m):
  return Fore.GREEN + Back.BLACK + Style.BRIGHT + "-> " + k + ": " + Style.RESET_ALL + m

def makePromptT(m):
  return Fore.BLUE + Back.BLACK + Style.BRIGHT + "::: " + m + Style.RESET_ALL


def makeWarningN(m):
  return m
def makeInfoN(m):
  return m
def makeKeyMessageN(k,m):
  return  "-> " + k + ": " + m
def makePromptN(m):
  return "::: " + m
def makeHeaderN(m):
  return  m 


""" Switch color on/off """
MyNameError  = NameError
MyValueError = ValueError

makeWarning      = makeWarningN
makeInfo         = makeInfoN
makeHeader       = makeHeaderN
makeKeyMessage   = makeKeyMessageN
makePrompt       = makePromptN

def printWarning(m):
    print(makeWarning(m))
def printHeader(m):
    print(makeHeader(m))
def printInfo(m):
    print(makeInfo(m))
def printKeyMessage(k,m):
    print(makeKeyMessage(k,m))


def doColoredOutput():
  global MyNameError, MyValueError, makeWarning, makeInfo, makeKeyMessage,makePrompt,makeHeader
  colorama.init()
  MyNameError  = TNameError
  MyValueError = TValueError
  
  makeWarning      = makeWarningT
  makeInfo         = makeInfoT
  makeKeyMessage   = makeKeyMessageT
  makePrompt       = makePromptT
  makeHeader       = makeHeaderT
  
def undoColoredOutput():
  global MyNameError, MyValueError, makeWarning, makeInfo, makeKeyMessage,makePrompt,makeHeader
  colorama.deinit()
  MyNameError  = NameError
  MyValueError = ValueError
  
  makeWarning      = makeWarningN
  makeInfo         = makeInfoN
  makeKeyMessage   = makeKeyMessageN
  makePrompt       = makePromptN
  makeHeader       = makeHeaderN