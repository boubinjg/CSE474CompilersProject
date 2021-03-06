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
# check variables have been assigned..

def compiler(source, tokens, output):
    tree, symbolTable, intLitTable = MLparser.parser(source, tokens)
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
        outputFile.write(i[0] + ": .word 0\n")
	#strings:
	#outputFile.write(i[0] + ": .space 32\n")
    outputFile.write(".text\n")
    outputFile.flush()
    return outputFile
    
def STATEMENT_LIST(tree, symbolTable, intLitTable, output, outputFile):
    for child in tree.children:
        STATEMENT(child, symbolTable, intLitTable, output, outputFile)
    return

def STATEMENT(tree, symbolTable, intLitTable, output, outputFile):
    global count
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
    elif (tree.children[0].label == "WRITE"):
        for writeID in tree.children[1].children:
            v, op, parentOp, done, name, printType, var = exploreChild(tree, writeID, symbolTable, intLitTable, output, None, "0", None, True, NG, None, outputFile)
            print("print type")
	    print(printType)
            if(printType == "INTLIT" or printType == "INTVAR"):
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
	    elif(printType == "STRINGLIT"):
		WRITEstring(tree, symbolTable, output, var)
    elif (tree.children[0].label == "ASSIGNMENT"):
        tree = tree.children[0]
        
        # get RHS variable
        i = 0
        ident = None
        v = None
        while (i < len(symbolTable)):
            if (count in symbolTable[i][1]):
                ident = symbolTable[i][0]
                count = count + 1
                break
            i = i + 1
        # get LHS first variable
        v, i2 = findLHS(symbolTable, intLitTable)
        
        tree = tree.children[1]
        
        if(v.isdigit()):
            if (len(tree.children) > 1):
                extend(tree,symbolTable, intLitTable, output, ident, v, False)
            else:
                assignIntLit(tree, symbolTable, output, ident, v)
        else:
            if (len(tree.children) > 1):
                extend(tree,symbolTable, intLitTable, output, ident, v, False)
            else:
                assignVariable(tree, symbolTable, output, ident, v)
        symbolTable[i][2] = True

def exploreChild(tree, writeID, symbolTable, intLitTable, output, parentOp, value, op, done, NG, name, outputFile):
    global count
    v = 0
    
    if (writeID.label == "EXPR"):
        # explore each child..
        for child in writeID.children:
            v, op, parentOp, done, name, printType, var = exploreChild(tree, child, symbolTable, intLitTable, output, parentOp, value, op, False, NG, name, outputFile)
            if ((not op == None)):
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
                print("CORRECT RETURN")
	        return v, op, parentOp, done, name, "INTLIT", None
            elif (child.label == "IDENT"):
                v, i = findValue(symbolTable, intLitTable)
                return v, op, parentOp, done, name, "INTVAR",None
	    elif (child.label == "STRINGLIT"):
	       v,i = findValue(symbolTable, intLitTable)
	       var = next(NG);
	       outputFile = open(output, 'r')
               contents = outputFile.readlines()
               outputFile.close()
               contents.insert(1,var+ ": .asciiz "+v+"\n");
	       outputFile = open(output, 'w+')
               contents = "".join(contents)
               outputFile.write(contents)
	       return v, op, parentOp, done, name, "STRINGLIT",var
	    elif (child.label == "BOOLLIT"):
	       v,i = findValue(symbolTable, intLitTable)
	       return v, op, parentOp, done, name, "BOOLLIT", None
            else:
                v, op, parentOp, done, name,printType, var = exploreChild(tree, child, symbolTable, intLitTable, output, op, 0, None, False, NG, name, outputFile)
                op = parentOp
                v = name
                return v, op, parentOp, done, name, "", None
    elif (writeID.label in {"PLUS", "MINUS"}):
        name = next(NG)
        outputFile = open(output, 'r')
        contents = outputFile.readlines()
        outputFile.close()
        
        contents.insert(1, name+": .word 0\n")
        outputFile = open(output, 'w+')
        contents = "".join(contents)

        outputFile.write(contents)
        
        return "0", writeID.label, parentOp, False, name, None, None
    print("FinalLabel")
    print(writeID.label)
    return value, op, parentOp, done, name, None, None 

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

def notLit(tree, sumbolTable, output, var, result):
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
	
        outputFile.write("bgt $t0, $t1, "+label1+"\nli $t2, 0\nsw $t2, "+ident3+"\nj "+label2)	
	outputFile.write("\n"+label1+":\nli $t2, 1\nsw $t2, "+ident3+"\n"+label2+":\n")

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
