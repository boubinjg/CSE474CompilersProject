import sys
import argparse
import MLparser
import NameGenerator as ng

class ParserError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


count = 1
GEN = ng.NameGenerator("dummy")
labelGen = ng.NameGenerator("Label")

def compiler(source, tokens, output):
    tree, symbolTable, intLitTable = MLparser.parser(source, tokens)
    print(tree)
    print(symbolTable)
    print(intLitTable)
    PROGRAM(tree, symbolTable, intLitTable, output)

def PROGRAM(tree, symbolTable, intLitTable, output):
    outputFile = BEGIN(tree, symbolTable, output)
    STATEMENT_LIST(tree.children[1], symbolTable, intLitTable, output, outputFile)
    return;

def BEGIN(tree, symbolTable, output):
    outputFile = open(output, 'w+')
    outputFile.write(".data\n")
    outputFile.write("True: .asciiz \"True\"\n")
    outputFile.write("False: .asciiz \"False\"\n")
   
    for i in symbolTable:
	#bools and literals
        if (i[3] != "string"):
            outputFile.write(i[0] + ": .word 0\n")
	#strings:
	#outputFile.write(i[0] + ": .space 32\n")
    outputFile.write(".text\n")
    outputFile.flush()
    return outputFile
    
def STATEMENT_LIST(tree, symbolTable, intLitTable, output, outputFile):
    JG = ng.NameGenerator("jump")
    for child in tree.children:
        STATEMENT(child, symbolTable, intLitTable, output, outputFile, JG)
    return

def STATEMENT(tree, symbolTable, intLitTable, output, outputFile, JG):
    global count
    global GEN
    global labelGen
    NG = ng.NameGenerator("dummy")
    index = 0
    if (tree.children[0].label == "READ"):
        for readID in tree.children[1].children:
            i = 0
            while (i < len(symbolTable)):
                if (count in symbolTable[i][1]):
                    index = i
                    break
                i = i + 1 
            READ(tree, symbolTable, output, symbolTable[index][0])
            symbolTable[index][2] = True
            count = count + 1
########################################################################################################
    elif (tree.children[0].label == "WRITE"):
        for writeID in tree.children[1].children:
            v, op, parentOp, done, name = exploreChild(tree, writeID, symbolTable, intLitTable, output, None, "0", None, True, NG, None, outputFile)
            index = 0
            c = 0
            while(c<len(intLitTable)):
                if(count == intLitTable[c][0]):
                    index = c
                    break;
                c = c+1
            if(intLitTable[index-1][2] == "int"):
      	        if (v.isdigit()):
                    if (not op == None):
                        WRITEVal(tree, symbolTable, output, name) 
                    else:
                        WRITEInt(tree, symbolTable, output, v)
                else:
                    if (not op == None):
                        WRITEVal(tree, symbolTable, output, name)
                    else:
                        WRITEVal(tree, symbolTable, output, v)
            elif(intLitTable[index-1][2] == "string"):
                WRITEstring(tree, symbolTable, output, v)
            elif(intLitTable[index-1][2] == "bool"): 
                printBoolLit(tree, symbolTable, output, v, next(labelGen), next(labelGen))           
########################################################################################################
    elif (tree.children[0].label == "ASSIGNMENT"):
        tree = tree.children[0]
        idStr = None
        v = None
        typeOfVar = None
        val = None
        name = next(NG)
        for child in tree.children:
            if (child.label == "EXPR"):
                jumpName = next(JG)
                jumpName2 = next(JG)
                val = EXPRESSION(child, symbolTable, intLitTable, output, idStr,i, False, typeOfVar, name, NG, JG, jumpName, jumpName2)
            elif child.label == "IDENT":
                idStr, i, typeOfVar = IDENT(child, symbolTable, intLitTable, output, False)
                symbolTable[i][2] = True
            elif child.label == "INIT":
                typeOfVar, idStr, i = INIT(child, symbolTable, intLitTable, output, outputFile)
                
                
        if (val != None):
             if(typeOfVar == "int"):
                 if (val.isdigit()):
                     assignIntLit(tree, symbolTable, output, idStr, val)
                 else:
                     assignVariable(tree, symbolTable, output, idStr, val)
             elif(typeOfVar == "bool"):
                 if (val == "True" or val == "False"):
                     assignBoolLit(tree, symbolTable, output, idStr, val)
                 else:
                     assignBoolVar(tree, symbolTable, output, idStr, val)
             elif (typeOfVar == "string"):
                 if(val[0] == "\""): # need to fix this
                    # redeclare idStr -> from explore to add into .data
                 # idStr: . 64 -> want size of largest possible string
                     assignStringLit(tree, symbolTable, output, idStr, val)
                 else:
                     assignStringVar(tree, symbolTable, output, idStr, val)

                 outputFile = open(output, 'r')
                 contents = outputFile.readlines()
                 outputFile.close()
                 contents.insert(1, idStr+": .space 64\n")
                 outputFile = open(output, 'w+')
                 contents = "".join(contents)

                 outputFile.write(contents)
             else:
                 assignVariable(tree, symbolTable, output, idStr, val)
             symbolTable[i][2] = True

def EXPRESSION(tree, symbolTable, intLitTable, output, idStr, i, write, typeOfVar, name, NG, JG, jumpName, jumpName2):
    global count
    op = None
    val = None
    val2 = None
    valType = None
    idStrType = typeOfVar
    j = 0
    for child in tree.children:
 
        if (child.label == "STRINGLIT"):
            j = 0
            v = None
            typeOfVar = "string"
            while (j < len(intLitTable)):
                if (count == intLitTable[j][0]):
                    v = intLitTable[j][1]
                    count = count + 1
                    break
                j = j + 1
            return v
        elif (child.label == "PRIMARY"):
            val2, idStr, j, op, typeOfVar = PRIMARY(child, symbolTable, intLitTable, output, idStr, i, write, typeOfVar, op, name, NG)
            if (op != None):
                if (op == "PLUS"):
                    if (idStrType != "int"):
                        raise ParserError("Semantic Error: Can't assign result of logical expression to " + idStrType + "type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't use PLUS on variable of " +typeOfVar + " type")
                    infixAdd(tree, symbolTable, output, idStr, val, val2)
                elif (op == "MINUS"):
                    if (idStrType != "int"):
                        raise ParserError("Semantic Error: Can't assign result of logical expression to " + idStrType + "type") 
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't use MINUS on variable of " +typeOfVar + " type")
                    infixSub(tree, symbolTable, output, idStr, val, val2)
                elif (op == "MULTI"):
                    if (idStrType != "int"):
                        raise ParserError("Semantic Error: Can't assign result of logical expression to " + idStrType + "type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't use MULTI on variable of " +typeOfVar + " type")
                    infixMul(tree, symbolTable, output, idStr, val, val2)
                elif (op == "DIV"):
                    if (idStrType != "int"):
                        raise ParserError("Semantic Error: Can't assign result of logical expression to " + idStrType + "type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't use DIV on variable of " +typeOfVar + " type")
                    infixDiv(tree, symbolTable, output, idStr, val, val2)
                elif (op == "MOD"):
                    if (idStrType != "int"):
                        raise ParserError("Semantic Error: Can't assign result of logical expression to " + idStrType + "type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't use MOD on variable of " +typeOfVar + " type")
                    infixMod(tree, symbolTable, output, idStr, val, val2)
                # add rest of ops...
                elif (op == "LESSEQUAL"):
                    # find idStr's type because it must be  bool; bool = these expressions; val and val2 must be ints.. 
                    if (idStrType != "bool"):
                        raise ParserError("Semantic Error: Can't assign result of boolean expression to " + idStrType + " type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't perform Boolean operation on " + typeOfVar + " type")
                    lessThanEqual(tree, symbolTable, output, val, val2, idStr, jumpName, jumpName2) 
                    jumpName = next(JG)
                    jumpName2 = next(JG)
                elif (op == "GREATEQUAL"):
                    if (idStrType != "bool"):
                        raise ParserError("Semantic Error: Can't assign result of boolean expression to " + idStrType + " type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't perform Boolean operation on " + typeOfVar + " type")
                    greaterThanEqual(tree, symbolTable, output, val, val2, idStr, jumpName, jumpName2)
                    jumpName = next(JG)
                    jumpName2 = next(JG)
                elif (op == "EQUAL"):
                    if (idStrType != "bool"):
                        raise ParserError("Semantic Error: Can't assign result of boolean expression to " + idStrType + " type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't perform Boolean operation on " + typeOfVar + " type")
                    equal(tree, symbolTable, output, val, val2, idStr, jumpName, jumpName2)
                    jumpName = next(JG)
                    jumpName2 = next(JG)
                elif (op == "NOTEQUAL"):
                    if (idStrType != "bool"):
                        raise ParserError("Semantic Error: Can't assign result of boolean expression to " + idStrType + " type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't perform Boolean operation on " + typeOfVar + " type")
                    notEqual(tree, symbolTable, output, val, val2, idStr, jumpName, jumpName2)
                    jumpName = next(JG)
                    jumpName2 = next(JG)
                elif (op == "LESS"):
                    if (idStrType != "bool"):
                        raise ParserError("Semantic Error: Can't assign result of boolean expression to " + idStrType + " type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't perform Boolean operation on " + typeOfVar + " type")
                    lessThan(tree, symbolTable, output, val, val2, idStr, jumpName, jumpName2)
                    jumpName = next(JG)
                    jumpName2 = next(JG)
                elif (op == "GREAT"):
                    if (idStrType != "bool"):
                        raise ParserError("Semantic Error: Can't assign result of boolean expression to " + idStrType + " type")
                    if (typeOfVar != "int"):
                        raise ParserError("Semantic Error: Can't perform Boolean operation on " + typeOfVar + " type")
                    greaterThan(tree, symbolTable, output, val, val2, idStr, jumpName, jumpName2) 
                    jumpName = next(JG)
                    jumpName2 = next(JG)
                elif (op == "AND"):
                    if (idStrType != "bool"):
                        raise ParserError("Semantic Error: Can't assign result of boolean expression to " + idStrType + "type")
                    if (typeOfVar != "bool"):
                        raise ParserError("Semantic Error: Can't use AND on variable of " + typeOfVar + " type")
                    if ((val == "True" or val == "False") and (val2 == "True" or val2 == "False")):
                        andTwoLit(tree, symbolTable, output, val, val2, idStr)
                    elif((val == "True" or val == "False" or val2 == "True" or val2 == "False")):
                        if (val == "True" or val == "False"):
                            andOneVar(tree, symbolTable, output, val2, val, idStr)
                        else:
                            andOneVar(tree, symbolTable, output, val, val2, idStr)
                    else:
                        andTwoVar(tree, symbolTable, output, val, val2, idStr)
                        
                elif (op == "OR"):
                    if (idStrType != "bool"):
                        raise ParserError("Semantic Error: Can't assign result of boolean expression to " + idStrType + "type")
                    if (typeOfVar != "bool"):
                        raise ParserError("Semantic Error: Can't use OR on variable of " + typeOfVar + " type")
                    if ((val == "True" or val == "False") and (val2 == "True" or val2 == "False")):
                        orTwoLit(tree, symbolTable, output, val, val2, idStr)
                    elif((val == "True" or val == "False" or val2 == "True" or val2 == "False")):
                        if (val == "True" or val == "False"):
                            orOneVar(tree, symbolTable, output, val2, val, idStr)
                        else:
                            orOneVar(tree, symbolTable, output, val, val2, idStr)
                    else:
                        orTwoVar(tree, symbolTable, output, val, val2, idStr)
                
                if (write):
                    val = "dummy"
                else:
                    val = idStr
                    valType = idStrType
                    op = None
                    val2 = None
            else:
                val = val2
                valType = typeOfVar
        elif (child.label in {'PLUS', 'MINUS', 'MULTI', 'DIV', 'MOD', 'GREATEQUAL', 'LESSEQUAL', 'EQUAL', 'NOTEQUAL', 'GREAT', 'LESS', 'AND', 'OR', 'NOT'}):
            op = child.label
    return val

def PRIMARY(tree, symbolTable, intLitTable, output, idStr, i, write, typeOfVar, op, name, NG):
    global count
    val = None
    v = None
    j = 0
    for child in tree.children:
        if (child.label == "EXPR"):
            idStr = name
            name = next(NG)
            val = EXPRESSION(child, symbolTable, intLitTable, output, idStr, i, write, typeOfVar, name, NG, JG, jumpName, jumpName2)
        elif (child.label == "IDENT"):
            idStr, i, typeOfVar = IDENT(child, symbolTable, intLitTable, output, None)
            print(symbolTable)
            print(i)
            print(symbolTable[i][2])
            if (symbolTable[i][2] != True):
                raise ParserError("Semantic Error: Unitialized variable");
            val = symbolTable[i][3]
        elif (child.label == "INTLIT"):
            j = 0
            typeOfVar = "int"
            while (j < len(intLitTable)):
                if (count == intLitTable[j][0]):
                    v = intLitTable[j][1]
                    count = count + 1
                    break
                j = j + 1
            return v, idStr, j, op, typeOfVar
        elif (child.label == "BOOLLIT"):
            i = 0
            typeOfVar = "bool"
            while (i < len(intLitTable)):
                if (count == intLitTable[i][0]):
                    v = intLitTable[i][1]
                    count = count + 1
                    break
                i = i + 1
            return v, idStr, j, op, typeOfVar
        elif (child.label == "MINUS"):
            op = "-"
        elif (child.label == "NOT"):
            op = "not"
    return val, idStr, i, op, typeOfVar

def IDENT(tree, symbolTable, intLitTable, output, isDeclared):
    global count
    idStr = None
    i = 0
    while (i < len(symbolTable)):
        if (count in symbolTable[i][1]):
            idStr = symbolTable[i][0]
            count = count + 1
            if symbolTable[i][4] != True:
                raise ParserError("variable not declared")
            break
        i = i + 1

    return idStr, i, symbolTable[i][3]

def INIT(tree, symbolTable, intLitTable, output, outputFile):
    typeOfVar = None
    idStr = None
    isDeclared = False
    for child in tree.children:
        print(child.label)
        if child.label == "INTTYPE":
            typeOfVar = "int"
        elif child.label == "BOOLTYPE":
            typeOfVar = "bool"
        elif child.label == "STRTYPE":
            typeOfVar = "string"
        if child.label == "IDENT":
            idStr, i, typeOfVar = IDENT(tree, symbolTable, intLitTable, output, isDeclared)
    return typeOfVar, idStr, i

def exploreChild(tree, writeID, symbolTable, intLitTable, output, parentOp, value, op, done, NG, name, outputFile):
    global count
    global gen
    v = 0
    if (writeID.label == "EXPR"):
        # explore each child..
        for child in writeID.children:
            v, op, parentOp, done, name = exploreChild(tree, child, symbolTable, intLitTable, output, parentOp, value, op, False, NG, name, outputFile)
            if(child.label == "STRINGLIT"):
                v,i = findValue(symbolTable, intLitTable)
                var = next(GEN)
                outputFile = open(output, 'r')
                contents = outputFile.readlines()
                outputFile.close()
                c = 0
                index = 0
                while(c<len(intLitTable)):
                    if(count-1 == intLitTable[c][0]):
                        index = c
                        break
                    c = c+1
                contents.insert(1,var+": .asciiz "+intLitTable[index][1] + "\n")
                outputFile = open(output, 'w+')
                contents = "".join(contents)
                outputFile.write(contents)
                v = var
                return v, op, parentOp, done, name
            elif ((not op == None)):
                if op == "PLUS":
                    if not (v == "0" or value == "0"):
                        infixAdd(tree, symbolTable, output, name, v, value)
                        value = name
                elif op == "MINUS":
                    if not (v == "0" or value == "0"):
                        infixSub(tree, symbolTable, output, name, value, v)
                        value = name
            else:
                 value = v
           
    elif (writeID.label == "PRIMARY"):
        # explore each child
        for child in writeID.children:
            if (child.label == "INTLIT"):
                v, i = findValue(symbolTable, intLitTable)
                return v, op, parentOp, done, name
            elif (child.label == "IDENT"):
                v, i = findValue(symbolTable, intLitTable)
                return v, op, parentOp, done, name
            elif (child.label == "BOOLLIT"):
                v, i = findValue(symbolTable, intLitTable)
                return v, op, parentOp, done, name
            else:
                v, op, parentOp, done, name = exploreChild(tree, child, symbolTable, intLitTable, output, op, 0, None, False, NG, name, outputFile)
                op = parentOp
                v = name
                return v, op, parentOp, done, name
    elif (writeID.label in {"PLUS", "MINUS"}):
        name = next(NG)
        outputFile = open(output, 'r')
        contents = outputFile.readlines()
        outputFile.close()
        
        contents.insert(1, name+": .word 0\n")
        outputFile = open(output, 'w+')
        contents = "".join(contents)

        outputFile.write(contents)
        
        return "0", writeID.label, parentOp, False, name
    return value, op, parentOp, done, name 

def findValue(symbolTable, intLitTable):
    global count
    i = 0
    v = None
    while(i < len(symbolTable)):
        if (count in symbolTable[i][1]):
            if (symbolTable[i][2] == False):
                raise ParserError("Semantic Error: use of variable before declaration")
            v = symbolTable[i][0]
            symbolTable[i][2] = True
            break
        i = i + 1
    if v == None:
        i = 0
        while (i < len(intLitTable)):
             if (count == intLitTable[i][0]):
                 v = intLitTable[i][1]
                 break
             i = i + 1
    count = count + 1
    return v, i

def findLHS(symbolTable, intLitTable):
    global count
    i2 = 0
    v = None
    while (i2 < len(symbolTable)):
        if (count in symbolTable[i2][1]):
            # check to see if init
            if (symbolTable[i2][2] == False):
                raise ParserError("Semantic Error: Use of variable before declaration")
            v = symbolTable[i2][0]
            break
        i2 = i2 + 1
    i2 = 0
    if v == None:
        while (i2 < len(intLitTable)):
            if (count == intLitTable[i2][0]):
                v = intLitTable[i2][1]
                break
            i2 = i2 + 1
    count = count + 1
    return v, i2

def extend(tree, symbolTable, intLitTable, output, ident, v, write):
    global count
    op = 1
    while ((op < len(tree.children)) & (tree.children[op].label in {"PLUS", "MINUS"})):
        i = 0
        v2 = None
        if (tree.label == "EXPR"):
            pass
        else: 
            while (i < len(symbolTable)):
                if (count in symbolTable[i][1]):
                    if (symbolTable[i][2] == False):
                        raise ParserError("Semantic Error: use of variable before declaration")
                    v2 = symbolTable[i][0]
                    break
                i = i + 1
            if v2 == None: 
                i = 0
                while (i < len(intLitTable)):
                    if (count == intLitTable[i][0]):
                        v2 = intLitTable[i][1]
                        break
                    i = i + 1
            count = count + 1
            if (tree.children[op].label == "PLUS"):
                infixAdd(tree, symbolTable, output, ident, v, v2)
            else:
                infixSub(tree, symbolTable, output, ident, v, v2)
            if (write):
                v = "dummy"
            else:
                v = ident
            op = op + 2
            if (op >= len(tree.children)):
                break
        return

def READ(tree, symbolTable, output, readID):
    with open(output, "a") as outputFile:
        outputFile.write("\nli $v0, 5\nsyscall\nla $t0, " + readID + "\nsw $v0, 0($t0)\n")

def WRITEVal(tree, symbolTable, output, writeId):
    with open(output,"a") as outputFile:
        outputFile.write("\nli $v0,1\nlw $a0," + writeId + "\nsyscall\n")

def WRITEInt(tree, symbolTable, output, writeId):
     with open(output,"a") as outputFile:
        outputFile.write("\nli $v0,1\nli $a0," + writeId + "\nsyscall\n")

def WRITEstring(tree, symbolTable, output, writeId):
     with open(output,"a") as outputFile:
        outputFile.write("\nla $t0 "+writeId+"\nmove $a0, $t0\nli $v0,4\nsyscall\n")

def assignIntLit(tree, symbolTable, output, ident, value):
    with open(output,"a") as outputFile:
        outputFile.write("\nli $t0,"+value+"\nla $t1,"+ident+"\nsw $t0, 0($t1)\n")

def assignVariable(tree, symbolTable, output, ident1, ident2):
    with open(output,"a") as outputFile:
        outputFile.write("\nla $t0,"+ident2+"\nla $t1,"+ident1+"\nlw $t2, 0($t0)\nsw $t2, 0($t1)\n")

def assignBoolLit(tree, symbolTable, output, ident, value):
    if(value == "False"):
        value = "0"
    else:
        value = "1"
    with open(output,"a") as outputFile:
        outputFile.write("\nli $t0,"+value+"\nla $t1,"+ident+"\nsw $t0, 0($t1)\n")

def assignBoolVar(tree, symbolTable, output, ident1, ident2):
    with open(output,"a") as outputFile:
        outputFile.write("\nla $t0,"+ident2+"\nla $t1,"+ident1+"\nlw $t2, 0($t0)\nsw $t2, 0($t1)\n")

def assignStringLit(tree, symbolTable, output, variableName, value):
    with open(output,"a") as outputFile:
        outputFile.write("\nla $s0, "+variableName+"\n")
        print(value)
        for char in value:
             outputFile.write("\nli $t0, '" + char + "'\nsb $t0, ($s0)\naddi $s0, $s0, 1\n")
   
def assignStringVar(tree, symbolTable, output, ident1, ident2):
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $s0, "+ident1+"\nsw $s0 "+ident2+"\n")

#logical operators
def andTwoVar(tree, symbolTable, output, varOne, varTwo, result):
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $t1, "+varOne+"\nlw $t2, "+varTwo+"\nand $t0, $t1, $t2\nsw $t0, "+result+"\n")

def andOneVar(tree, symbolTable, output, varOne, lit, result):
    if(lit == "True"):
        value = "1"
    else:
        value = "0"
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $t1, "+varOne+"\nli $t2, "+value+"\nand $t0, $t1, $t2\nsw $t0, "+result+"\n")

def andTwoLit(tree, symbolTable, output, lit1, lit2, result):
    if(lit1 == "True"):
        value1 = "1"
    else:
        value1 = "0"
    if(lit2 == "True"):
        value2 = "1"
    else:
        value2 = "0"
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $t1, "+value1+"\nli $t2, "+value2+"\nand $t0, $t1, $t2\nsw $t0, "+result+"\n")

def orTwoVar(tree, symbolTable, output, varOne, varTwo, result):
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $t1, "+varOne+"\nlw $t2, "+varTwo+"\nor $t0, $t1, $t2\nsw $t0, "+result+"\n")

def orOneVar(tree, symbolTable, output, varOne, lit, result):
    if(lit == "True"):
        value = "1"
    else:
        value = "0"
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $t1, "+varOne+"\nli $t2, "+value+"\nor $t0, $t1, $t2\nsw $t0, "+result+"\n")

def orTwoLit(tree, symbolTable, output, lit1, lit2, result):
    if(lit1 == "True"):
        value1 = "1"
    else:
        value1 = "0"
    if(lit2 == "True"):
        value2 = "1"
    else:
        value2 = "0"
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $t1, "+value1+"\nli $t2, "+value2+"\nor $t0, $t1, $t2\nsw $t0, "+result+"\n")

def notLit(tree, sumbolTable, output, lit, result):
    if(lit == "True"):
        value = "1"
    else:
        value = "0"
    with open(output,"a") as outputFile:
        outputFile.write("\nli $t1, "+value+"\nli $t2, 1\nxor $t0, $t1, $t2\nsw $t0, "+result+"\n")

def notVar(tree, sumbolTable, output, var, result):
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $t1, "+var+"\nli $t2, 1\nxor $t0, $t1, $t2\nsw $t0, "+result+"\n")

#Math
def infixAdd(tree, symbolTable, output, ident1, ident2, ident3):
    with open(output,"a") as outputFile:
        if(ident2.isdigit()):
            outputFile.write("\nli $s0, "+ident2+"\nla $t1, 0($s0)\n")
        else:
            outputFile.write("\nla $s0, "+ident2+"\nlw $t1, 0($s0)\n")
        if(ident3.isdigit()):
            outputFile.write("li $s0, "+ident3+"\nla $t2, 0($s0)\n")
        else:
            outputFile.write("la $s0, "+ident3+"\nlw $t2, 0($s0)\n")

        outputFile.write("add $t0, $t1, $t2\nla $s0,"+ident1+"\nsw $t0, 0($s0)\n")
    
def infixSub(tree, symbolTable, output, ident1, ident2, ident3):
    with open(output,"a") as outputFile:
        if(ident2.isdigit()):
            outputFile.write("\nli $s0, "+ident2+"\nla $t1, 0($s0)\n")
        else:
            outputFile.write("\nla $s0, "+ident2+"\nlw $t1, 0($s0)\n")
        if(ident3.isdigit()):
            outputFile.write("li $s0, "+ident3+"\nla $t0, 0($s0)\n")
        else:
            outputFile.write("la $s0, "+ident3+"\nlw $t0, 0($s0)\n")

        outputFile.write("sub $t0, $t1, $t0\nla $s0,"+ident1+"\nsw $t0, 0($s0)\n")	

def infixMul(tree, symbolTable, output, ident1, ident2, ident3):
    with open(output,"a") as outputFile:
        if(ident2.isdigit()):
            outputFile.write("\nli $s0, "+ident2+"\nla $t1, 0($s0)\n")
        else:
            outputFile.write("\nla $s0, "+ident2+"\nlw $t1, 0($s0)\n")
        if(ident3.isdigit()):
            outputFile.write("li $s0, "+ident3+"\nla $t0, 0($s0)\n")
        else:
            outputFile.write("la $s0, "+ident3+"\nlw $t0, 0($s0)\n")

        outputFile.write("mul $t0, $t1, $t0\nla $s0,"+ident1+"\nsw $t0, 0($s0)\n")	

def infixDiv(tree, symbolTable, output, ident1, ident2, ident3):
    with open(output,"a") as outputFile:
        if(ident2.isdigit()):
            outputFile.write("\nli $s0, "+ident2+"\nla $t1, 0($s0)\n")
        else:
            outputFile.write("\nla $s0, "+ident2+"\nlw $t1, 0($s0)\n")
        if(ident3.isdigit()):
            outputFile.write("li $s0, "+ident3+"\nla $t0, 0($s0)\n")
        else:
            outputFile.write("la $s0, "+ident3+"\nlw $t0, 0($s0)\n")

        outputFile.write("div $t0, $t1, $t0\nla $s0,"+ident1+"\nsw $t0, 0($s0)\n")	

def infixRem(tree, symbolTable, output, ident1, ident2, ident3):
    with open(output,"a") as outputFile:
        if(ident2.isdigit()):
            outputFile.write("\nli $s0, "+ident2+"\nla $t1, 0($s0)\n")
        else:
            outputFile.write("\nla $s0, "+ident2+"\nlw $t1, 0($s0)\n")
        if(ident3.isdigit()):
            outputFile.write("li $s0, "+ident3+"\nla $t0, 0($s0)\n")
        else:
            outputFile.write("la $s0, "+ident3+"\nlw $t0, 0($s0)\n")

        outputFile.write("rem $t0, $t1, $t0\nla $s0,"+ident1+"\nsw $t0, 0($s0)\n")	

def equal(tree, symbolTable, output, ident1, ident2, ident3,label1, label2):
    with open(output,"a") as outputFile:
        if(ident1.isdigit()):
            outputFile.write("\nli $t0, "+ident1+"\n")
        else:
            outputFile.write("\nla $t0, "+ident1+"\n")
        if(ident2.isdigit()):
            outputFile.write("li $t1, "+ident2+"\n")
        else:
            outputFile.write("la $t1, "+ident2+"\n")
	
        outputFile.write("bne $t0, $t1, "+label1+"\nli $t2, 1\nsw $t2, "+ident3+"\nj "+label2)	
        outputFile.write("\n"+label1+":\nli $t2, 0\nsw $t2, "+ident3+"\n"+label2+":\n")

def notEqual(tree, symbolTable, output, ident1, ident2, ident3,label1, label2):
    with open(output,"a") as outputFile:
        if(ident1.isdigit()):
            outputFile.write("\nli $t0, "+ident1+"\n")
        else:
            outputFile.write("\nla $t0, "+ident1+"\n")
        if(ident2.isdigit()):
            outputFile.write("li $t1, "+ident2+"\n")
        else:
            outputFile.write("la $t1, "+ident2+"\n")
	
        outputFile.write("bne $t0, $t1, "+label1+"\nli $t2, 0\nsw $t2, "+ident3+"\nj "+label2)	
        outputFile.write("\n"+label1+":\nli $t2, 1\nsw $t2, "+ident3+"\n"+label2+":\n")
#ident1 is less than ident2
def lessThan(tree, symbolTable, output, ident1, ident2, ident3,label1, label2):
    with open(output,"a") as outputFile:
        if(ident1.isdigit()):
            outputFile.write("\nli $t0, "+ident1+"\n")
        else:
            outputFile.write("\nla $t0, "+ident1+"\n")
        if(ident2.isdigit()):
            outputFile.write("li $t1, "+ident2+"\n")
        else:
            outputFile.write("la $t1, "+ident2+"\n")
	
        outputFile.write("bgt $t0, $t1, "+label1+"\nli $t2, 1\nsw $t2, "+ident3+"\nj "+label2)	
        outputFile.write("\n"+label1+":\nli $t2, 0\nsw $t2, "+ident3+"\n"+label2+":\n")

def lessThanEqual(tree, symbolTable, output, ident1, ident2, ident3,label1, label2):
    with open(output,"a") as outputFile:
        if(ident1.isdigit()):
            outputFile.write("\nli $t0, "+ident1+"\n")
        else:
            outputFile.write("\nla $t0, "+ident1+"\n")
        if(ident2.isdigit()):
            outputFile.write("li $t1, "+ident2+"\n")
        else:
            outputFile.write("la $t1, "+ident2+"\n")
	 
        outputFile.write("bge $t1, $t0, "+label1+"\nli $t2, 0\nsw $t2, "+ident3+"\nj "+label2)	
        outputFile.write("\n"+label1+":\nli $t2, 1\nsw $t2, "+ident3+"\n"+label2+":\n")

def greaterThan(tree, symbolTable, output, ident1, ident2, ident3,label1, label2):
    with open(output,"a") as outputFile:
        if(ident1.isdigit()):
            outputFile.write("\nli $t0, "+ident1+"\n")
        else:
            outputFile.write("\nla $t0, "+ident1+"\n")
        if(ident2.isdigit()):
            outputFile.write("li $t1, "+ident2+"\n")
        else:
            outputFile.write("la $t1, "+ident2+"\n")
	
        outputFile.write("bgt $t0, $t1, "+label1+"\nli $t2, 0\nsw $t2, "+ident3+"\nj "+label2)	
        outputFile.write("\n"+label1+":\nli $t2, 1\nsw $t2, "+ident3+"\n"+label2+":\n")

def greaterThanEqual(tree, symbolTable, output, ident1, ident2, ident3,label1, label2):
    with open(output,"a") as outputFile:
        if(ident1.isdigit()):
            outputFile.write("\nli $t0, "+ident1+"\n")
        else:
            outputFile.write("\nla $t0, "+ident1+"\n")
        if(ident2.isdigit()):
            outputFile.write("li $t1, "+ident2+"\n")
        else:
            outputFile.write("la $t1, "+ident2+"\n")
	
        outputFile.write("bge $t0, $t1, "+label1+"\nli $t2, 0\nsw $t2, "+ident3+"\nj "+label2)	
        outputFile.write("\n"+label1+":\nli $t2, 1\nsw $t2, "+ident3+"\n"+label2+":\n")

#assumes variables "True" and "False" correspond to the correct values in the .data section
def printBoolVar(tree, symbolTable, output, boolean, label1, label2):
    with open(output,"a") as outputFile:
        outputFile.write("\nlw $t0, "+boolean+"\nli $t1, 1\nbne $t1, $t0, "+label1+"\n")
        outputFile.write("li $v0, 4\nla $a0 True\nsyscall\nj "+label2+"\n"+label1+":\n")
        outputFile.write("li $v0, 4\nla $a0, False\nsyscall\n"+label2+":\n")

def printBoolLit(tree, symbolTable, output, boolean, label1, label2):
    if(boolean == "True"):
        boolean = "1";
    else:
        boolean = "0";
    with open(output,"a") as outputFile:
        outputFile.write("\nli $t0, "+boolean+"\nli $t1, 1\nbne $t1, $t0, "+label1+"\n")
        outputFile.write("li $v0, 4\nla $a0 True\nsyscall\nj "+label2+"\n"+label1+":\n")
        outputFile.write("li $v0, 4\nla $a0, False\nsyscall\n"+label2+":\n")

if __name__ == "__main__":  # Only true if program invoked from the command line

    # Use the argparse library to parse the commandline arguments
    parser = argparse.ArgumentParser(description = "GroupX micro-language compiler")
    parser.add_argument('-t', type = str, dest = 'token_file',
                       help = "Token file", default = 'tokens.txt')
    parser.add_argument('source_file', type = str,
                        help = "Source-code file", default = 'tokens.txt')
    parser.add_argument('output_file', type = str, 
                        help = 'output file name')
    
    args = parser.parse_args()

    # Call the compiler function
    compiler(args.source_file, args.token_file, args.output_file)
