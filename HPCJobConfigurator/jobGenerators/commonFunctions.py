# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import os, subprocess, shutil, stat, ctypes,glob2
import hashlib
import jsonpickle
import jsonpickle.ext.numpy
import re
import glob2
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
from attrdict import AttrMap,AttrDict
import collections

from HPCJobConfigurator.jobGenerators import configuratorExceptions as CE


def flatten(l, ltypes=collections.Sequence):
    l = list(l)
    while l:
        while l and isinstance(l[0], ltypes) and not isinstance(l[0],str):
            l[0:1] = l[0]
        if l: yield l.pop(0)

def toBool(s, optionHint=None):
        """Safe converting to a boolean value, raises exception if s has wrong type or does not have the appropriate value"""
        if isinstance(s,str):
            try:
                if ['true','yes','on','false','no','off'].index(s.lower()) <= 2:
                    return True
                else:
                    return False
            except:
                raise CE.MyValueError("Value: %s %s !" % (s, "at option: %s" % optionHint if optionHint else ""))
        elif isinstance(s,bool):
            return
        else:
            raise CE.MyValueError("Converting type: %s with value: %s to bool is deliberately not supported!" % (type(s),s))

def expandEnvVar(string, envVarRegex = "ENV::(\w*)", errorIfNotFullyExpanded=True): 
    """Expands all environment variables in the string"""
    def expandVar(s):
      s = os.path.expandvars(s)
      if "$" in s and errorIfNotFullyExpanded:
        raise CE.MyNameError("Could not fully expand string with env. variables: %s , are all env. variables defined?" % s)
      return s
      
    return re.sub( envVarRegex ,  
                   lambda matchObj : expandVar("$"+matchObj.group(1)), string = string )
                            

def makeLinks(fileGlobPattern, filePathRegex, subTemplate, outputFolder, 
              counters = None , hardLink=False):
    """ Globs all files with the pattern  fileGlobPattern
        and builds for each found file a new symlink where the
        file name is determined by match/substituting the filePath 
        with the regex: filePathRegex and substitution pattern: subTemplate which produces the new file name
        counter is a list of tuples each consisting of (start, key lambda) which defines the start of a 
        counter and a sort lambda which takes a filepath and returns a sort key for the sort function.
        all associated counters are then replaced (formatted) in the new file name , substituted by the subTemplate.
        
        Then, it saves a new symlink in the outputFolder for each of these new file names.
        Example:
        makeSymlinkSequence( "./*.xml",   r".*?/Data-(\d*)-(\d*).jpg",    "NewFileLink-\1-\2",       "./output/files")
    """
    reg = re.compile(filePathRegex)
    files = glob2.glob(fileGlobPattern);
    def matchAndRepl(f):
      m=reg.match(f)
      if m:
        return (f, m.expand(subTemplate),m.groups())
      else:
        return None
    files = [ matchAndRepl(f)  for f in files]
    files = filter(lambda f: f is not None, files)
    

    
    # standart counter (sort paths)
    if counters is None:
       counters = [(0,lambda path,regexG: os.path.basename(path))]
    
    for counter in counters:
        count = counter[0] # the start of this counter
        # sort files according to counter sort lambda
        files = sorted(files, key = lambda f: counter[1]( f[0] , f[2]) ) 
        # assign counter
        for i,f in enumerate(files):
            files[i] = f + (count,)
            count += 1
    
    os.makedirs(outputFolder,exist_ok=True);
    print("Make symlinks in folder: ", outputFolder)
    # make symlinks to all files in outputFolder
    for tu in files:   #list [ (file,newfile, regexGroups, counter1, counter1,..., counterN) , .... ]
        f = tu[0]
        newf = tu[1]
        if newf is None:
          continue # skip this file as regex did not match!

        simLinkFile = newf.format(*tu[3:]);
        simLinkPath = os.path.join(outputFolder,simLinkFile) 
        CE.printInfo("Link: " + f + " --- to ---> " + simLinkPath)
        try:
            if hardLink:
                os.link(os.path.abspath(f), simLinkPath );
            else:
                os.symlink(os.path.abspath(f), simLinkPath );
        except FileExistsError:
            CE.printInfo("file exists, continue")
    


def makeDirectory(path,interact=True, name="Directory", defaultCreate=True, defaultMakeEmpty=False):
       
     
     if not os.path.exists(path) :
         print("%s : %s" % (name,path) + " does not exist!")
         default = 'y' if defaultCreate else 'n'
         r=''
         if interact:
             r = input(CE.makePrompt("Do you want to create directory [y|n, default(%s)]: " % default)).strip()
        
         r = r or default
         
         if r == 'n':
             raise CE.MyValueError("Aborted due to not created directory!")
         else:
             os.makedirs(path)
             CE.printInfo("Created %s : %s" %  (name,path))
     else:
        print("%s : %s" % (name,path) + " does already exist!") 
        # dir exists
        default='y' if  defaultMakeEmpty else 'n'
        r=''
        if interact:
            r = input(CE.makePrompt("Do you want to remove and recreate the directory [y|n, default(%s)]: " % default) ).strip()
        
        r = r or default
        if r == 'y':
             shutil.rmtree(path)
             os.makedirs(path)
             CE.printInfo("Removed and created %s : %s" %  (name,path))


def checkNotExisting(path, interact=True, name="Directory"):
    if os.path.exists(path):
         mess = "%s : %s" % (name,path) + " does already exist!"
         if interact :
            print(mess)
            r = input(CE.makePrompt("Do you want to remove the directory: [y|n|c, default(c), c=no and continue]")).strip()
            if not r:
                r="c"
            if r == 'n':
                raise CE.MyValueError("Aborted due to not removed directory!")
            elif r == 'y':
                 shutil.rmtree(path)
            elif r == 'c':
                pass
            else:
                 raise CE.MyValueError("Aborted due to not removed directory!")
         else:
             raise CE.MyValueError(mess)
    
def callProcess( command, *args,**kargs ):
    if( command ):
        if isinstance(command,str):
            subprocess.check_call(command.strip().split(" "),*args,**kargs)
        elif isinstance(command,list):
            subprocess.check_call(command,*args,**kargs)
        else:
            raise CE.MyValueError("Command %s is not list or string!" % command)
        

def makeExecutable(path):
    """ Make file path executable """       
    #make executable
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def checkExecutable(exe):
    """Check if executable exists and return the correct path"""
    # split exe into first command
    cmds=exe.split(" ")
    if not cmds:
        raise CE.MyValueError("Wrong executable: %s" % exe)
    app = shutil.which(cmds[0]);
    if not app:
        raise CE.MyValueError("Executable %s does not exist!" % cmds[0])
    cmds[0]= app
    return " ".join(cmds);
    

def prettifyXML(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")
    
    
def makeUUID(s,length=32):
    if length <= 32:
        return hashlib.md5(s.encode()).hexdigest()[0:length]
    return hashlib.md5(s.encode()).hexdigest()


def _flattenDictRec(out,dic, formatter=str,seperator=":",currentLevel=""):

      for k,v in dic.items():
          keyS = str(k)
          if isinstance(v,dict) or isinstance(v,AttrMap) or isinstance(v,AttrDict):
              _flattenDictRec(out,v,formatter,currentLevel=currentLevel+keyS+":")
          else:
              # format value v and make entry 
              out[ currentLevel+keyS ] = formatter(v)
        
def flattenDict(dic,formatter=str, seperator=":"):
    out={}
    _flattenDictRec(out,dic,formatter,seperator)
    return out
    

def formatAll(it,formatDic,exceptKeys={}, formatter = None):

    """ Formats nested iterables of types dicts and lists but without the exceptKeys:
        This function does not do any interpolation ! (non-recursive)
        Example:
        a={  "a":"{r}",    
             "b":  ["{r}",
                    ["{r}+{n}", "{n}"] ,
                    "{n}*{n}"
                   ],      
             "c":  {"cc":"{r}","d":"{n}"} 
          }
        f={"r":"3", "n":10}
        b=formatAll(a,f,exceptKeys={ "c":{"d"} ,"a":None, "b":{0:None,1:{0} } } )
        prints : {  "a":"{r}",    "b":  ["{r}",["{r}+{n}", "10"] ,"10*10"] ,      "c":  {"cc":"3","d":"{n}"} }
        
        None stands for "exclude all subelements"
    """
    #print("it:", it,"except:", exceptKeys)
    if isinstance(it, dict):
        for k in it.keys():
            #print("k:",k)
            if k in exceptKeys:
              try:
                e = exceptKeys[k]
                if e:
                    it[k] = formatAll(it[k],formatDic,exceptKeys[k],formatter)
              except:
                  pass
            else:
                  it[k] = formatAll(it[k],formatDic,{},formatter)
                    
    elif isinstance(it, list):
        for i in range(len(it)):
            #print("i:",i)
            if i in exceptKeys:
                try:
                    e = exceptKeys[i]
                    if e:
                        it[i] = formatAll(it[i],formatDic,exceptKeys[i],formatter)
                except:
                    pass
            else:
                it[i] = formatAll(it[i],formatDic,{},formatter)
    elif isinstance(it,str):
        if formatter is not None:
            it = formatter(it).evaluate(formatDic)
        else:
            it = it.format(**formatDic)
        
    return it
   
# register common extension and backend demjson
import jsonpickle.ext.numpy
import demjson
jsonBackend = "demjson"
jsonpickle.ext.numpy.register_handlers()
jsonpickle.load_backend(jsonBackend,"encode","decode",CE.MyValueError)
jsonpickle.set_preferred_backend(jsonBackend)
jsonpickle.set_decoder_options(jsonBackend,decode_float=float)

def jsonDump(obj,file,compact=False,*args,**kargs):
    global jsonBackend
    jsonpickle.set_encoder_options(jsonBackend,compactly=compact,*args,**kargs)
    file.write(jsonpickle.encode(obj))
    
def jsonParse(s):
    return jsonpickle.decode(s)
    
def jsonLoad(filePath):
    f = open(filePath)
    return jsonParse(f.read())
        
