# =====================================================================
#  HPClusterJobConfigurator
#  Copyright (C) 2014 by Gabriel Nützi <gnuetzi (at) gmail (dot) com>
#
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
# =====================================================================

import ast


class Expression:
    """
        Special string expression which can be evaluated by the evaluate(formatDict) function 
        wich provide the following syntax
        The evaluate function does interpolation till maxInterpolationDepth is reached!
        If you have recursive circles in your formatDict then this limit will be reached!
        
        ${STRF:: ... }$     formats the string ... with the formatDict
        ${ ... }$           abreviation for ${STRF:: ... }$
        ${EVAl:: ... }$     evaluates the string ... as a python expression, and returning it as a string
        
        Example:
            s = r''' ${EVAL:: ${ga[b]}$ + ${ga[a]}$ }$'''
            f={"ga":{"a":123, "b":3}}
            print("Expr:", e)
            e.evaluate(f);
            print("Expr:", e)
    """
    
     
    exprTokens =  {'EVAL', 'STRF', None }
    tokenLength = 4
    tokenDel = "::"
    tokenDelLength = 2
    
    maxDepth = 10               # max nested expression depth
    maxInterpolationDepth = 5   # max interpolation depth when evaluating
    
    
    def __init__(self,expr=None, interpolationDepth = 0):
        """
            expr can be string or Expression
        """
        self.exprToken = None
        self.accum = []
        self.evaluatedStr = None
        
        if expr is None:
            self.interpolationDepth = interpolationDepth 
            return
        
        elif isinstance(expr,str):
            self.interpolationDepth = interpolationDepth 
            
            if( self.interpolationDepth >=  Expression.maxInterpolationDepth):
                raise ValueError("Expression: " + str(expr) + " has reached its interpolation depth of %i" % Expression.maxInterpolationDepth)
        
            # safe expression and split it
            self.splitExpression(expr,self)
            
        elif isinstance(expr,Expression):
            self.interpolationDepth = expr.interpolationDepth
            
        else:
            raise ValueError("Instantiaion of Expression with type: %s " % str(type(exprStr)))
            
        
    
    def __str__(self):
        if self.evaluatedStr is not None:
            return self.evaluatedStr
        else:
            return self.__repr__()
    
    def evaluate(self,formatDict):
        if self.evaluatedStr is None:
            self.evaluatedStr = self._evaluate(formatDict)
            return  self.evaluatedStr
        else:
            return self.evaluatedStr
        
    def __repr__(self):
        return "Expr::"+str(self.exprToken)+str(self.accum)
    
    def __getitem__(self, i):
        return self.accum[i]
    
    def __len__(self):
        return len(self.accum)
    
    
    ## Private methods 
    
    def _evaluate(self,formatDict):
        
        # depth first  
        finalStr = ""
        idx = 0
        
        while idx<len(self.accum):
        
            expr = self.accum[idx] 
            if isinstance(expr, Expression):
                res=expr._evaluate(formatDict)
                
                # in the case where the evaluation is no str, and we only have to concat this
                # expression, return this type as finalStr
                if not isinstance(res,str) and len(self.accum) == 1:
                    finalStr = res
                else:
                    # convert to string
                    res = str(res)
                    # if res contains again ${}$ pattern, replace and evaluate again
                    if r'${' in res:
                        print("making new expr: " , res)
                        self.accum[idx] = Expression(res,expr.interpolationDepth+1)
                        continue

                    finalStr += res
            else:
                finalStr += str(expr)  
            
            idx+=1
            
        # evaluate finalStr with this types expression
        try:
            
            if self.exprToken == 'EVAL':
                # dangerous eval here, cant use literal_eval (since )
                res = eval(finalStr);
#                 if not isinstance(res,str):
#                     res = str(res)
                return res
            elif self.exprToken == 'STRF':
                return ("{" + finalStr +"}").format(**formatDict)
            
            elif self.exprToken is None:
                 return finalStr
            else:
                raise
                
        except Exception as e:
            raise ValueError("Final interpolated string: '%s' can not be evaluated with type: '%s'!"
                             % (str(finalStr),self.exprToken) + " --> " + str(e))
        
        
    def _close(self):
        self.splitToken()
        
    def _append(self,string):
        self.accum.append(string)
        
    def splitToken(self):
        
        tkL = Expression.tokenLength
        tkDL = Expression.tokenDelLength
        
        if not self.accum:
            raise ValueError("Expression is empty!")
        
        t = self.accum[0]
        if len(t) < tkL + tkDL:
            
            self.exprToken = 'STRF'
            
        else:
            t= self.accum[0][ 0 : tkL + tkDL]
            if t[tkL : tkL + tkDL] == Expression.tokenDel  :
                
                self.exprToken = t[0:tkL]
                if self.exprToken not in Expression.exprTokens:
                     raise ValueError("Expression type: %s not supported!" % self.exprToken)
                
                # remove token
                self.accum[0] = self.accum[0][tkL + tkDL:]
                
            else:
                self.exprToken = 'STRF'
                
    def splitExpression(self, text, rootExpr):

        oBs = r'${'
        cBs = r'}$'
        lB = len(oBs)
        oIdx = 0
        escape = '\\'
        
        l = rootExpr
        level = 0
        currlevel = l;
        listStack = [currlevel]
        idx = 0
        try:
            while idx < len(text):
                brackets = text[idx:idx + lB]
                if brackets == oBs:
                    level+=1
                    
                    if level >= Expression.maxDepth:
                        raise ValueError("Expression splitting reached max. depth at text %s" % text )
                    
                    # push so far read to this level
                    if idx > oIdx:
                        currlevel._append( text[oIdx:idx] )
                    # skip tag
                    idx += lB
                    oIdx = idx # open index
                    currlevel._append( Expression(self) )
                    listStack.append(currlevel[-1])
                    currlevel = currlevel[-1]
                elif brackets == cBs:
                    level-=1
                    # finish level 
                    if idx > oIdx:
                        currlevel._append( text[oIdx:idx] )
                    
                    currlevel._close()
                    
                    # skip tag
                    idx +=lB
                    oIdx=idx # set new open index
                    listStack.pop()
                    currlevel = listStack[-1]


                elif text[idx] == escape:

                    #escape interval begins, check if we skip!
                    if text[idx+1:idx+1 + lB] in [oBs,cBs]:
                        #replace string
                        text = text[:idx] + text[idx+1:]
                        #ignore -> skip
                        idx +=lB
                    idx+=1
                else:
                    idx+=1

            # push last
            if idx > oIdx:
                currlevel._append( text[oIdx:idx] )

            if not level == 0:
                raise ValueError("Wrong bracketing!")

        except:
            raise ValueError("Parsing error at index: %i , string: '%s', stack: %s" % ( idx, text[idx:], str(listStack)) )

        return l   