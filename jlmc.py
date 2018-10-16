from enum import Enum
import re

class Op(Enum):
    ADD = 1
    SUB = 2
    STA = 3
    LDA = 5
    BRA = 6
    BRZ = 7
    BRP = 8
    IO  = 9
    HLT = 0

def lookup(op):
    if op == "ADD":
        return 100
    if op == "SUB":
        return 200
    if op == "STA":
        return 300
    if op == "LDA":
        return 500
    if op == "BRA":
        return 600
    if op == "BRZ":
        return 700
    if op == "BRP":
        return 800
    if op == "INP":
        return 901
    if op == "OUT":
        return 902
    if op == "HLT":
        return 000
    if op == "COB":
        return 000
    if op == "DAT":
        return 000
    return None

class Assembler:
    comments = re.compile(".*((;|//|#).*)")
    def write_op(self, tok):
        self.mem[self.ptr] += lookup(tok)

    def write_val(self, val):
        try:
            if 0 <= int(val) < (100 if self.mem[self.ptr] else 1000):
                self.mem[self.ptr] += int(val)
            else:
                pass #BORK
        except ValueError:
            if val in self.symbols:
                self.mem[self.ptr] += self.symbols[val]
            else:
                self.links[self.ptr] = val

    def write_label(self, tok):
        if tok in self.symbols:
            return #BORK
        self.symbols[tok] = self.ptr

    def __init__(self, lines):
        self.mem = [000] * 100
        self.symbols = {}
        self.links = {}
        self.ptr = 000
        for line in lines.split("\n"):
            cmatch = Assembler.comments.match(line)
            if cmatch is not None:
                line = line[:cmatch.span(1)[0]]
            toks = line.split()
            tlen = len(toks)
            if tlen == 0:
                continue
            if tlen == 1:
                self.write_op(toks[0])
            elif tlen == 2:
                # first token is instruction
                if lookup(toks[0]) is not None:
                    self.write_op(toks[0])
                    self.write_val(toks[1])
                else:
                    self.write_label(toks[0])
                    self.write_op(toks[1])
            elif tlen == 3:
                self.write_label(toks[0])
                self.write_op(toks[1])
                self.write_val(toks[2])
            self.ptr += 1

        for lnptr, lnval in self.links.items():
            self.mem[lnptr] += self.symbols[lnval]

def curtail(n):
    if n > 999:
        return (999, False)
    elif n < 0:
        return (0, True)
    return (n, False)


class Exec:
    def __init__(self, prog):
        self.memory = [000] * 100
        for i, d in enumerate(prog):
            self.memory[i] = d
        self.outbox = 000
        self.inbox  = 000
        self.pc     = 000
        self.acc    = 000
        self.neg    = False
        #print(self.memory)

    def cycle(self):
        ip = self.pc
        ir = self.memory[ip]
        self.pc += 1
        op = Op(ir // 100)
        xx = ir - (op.value * 100)


        if op == Op.ADD:
            self.neg = False
            self.acc, _ = curtail(self.acc + self.memory[xx])

        elif op == Op.SUB:
            self.acc, self.neg = curtail(self.acc - self.memory[xx])

        elif op == Op.STA:
            self.neg = False
            self.memory[xx] = self.acc

        elif op == Op.LDA:
            self.acc = self.memory[xx]

        elif op == Op.BRA:
            self.pc = xx

        elif op == Op.BRZ:
            if not self.neg:
                if self.acc == 000:
                    self.pc = xx

        elif op == Op.BRP:
            if not self.neg:
                self.pc = xx

        elif op == Op.IO:
            if xx == 1:
                self.neg = False
                self.acc, _ = curtail(int(input()))
            elif xx == 2:
                print(self.acc)

        elif op == Op.HLT:
            return False

        return True

trig = Exec([901, 323, 526, 324, 325, 524, 223, 814, 525, 127, 325, 124, 324, 605, 523, 224, 720, 526, 902, 622, 525, 902, 000, 000, 000, 000, 000, 1])

#while trig.cycle():
#    pass

square = """
START   LDA ZERO     // Initialize for multiple program run
        STA RESULT
        STA COUNT
        INP          // User provided input
        BRZ END      // Branch to program END if input = 0
        STA VALUE    #  Store input as VALUE
LOOP    LDA RESULT   ;  Load the RESULT
        ADD VALUE    // Add VALUE, the user provided input, to RESULT
        STA RESULT   // Store the new RESULT
        LDA COUNT    // Load the COUNT
        ADD ONE      // Add ONE to the COUNT
        STA COUNT    // Store the new COUNT
        SUB VALUE    // Subtract the user provided input VALUE from COUNT
        BRZ ENDLOOP  // If zero (VALUE has been added to RESULT by VALUE times), branch to ENDLOOP
        BRA LOOP     // Branch to LOOP to continue adding VALUE to RESULT
ENDLOOP LDA RESULT   // Load RESULT
        OUT          // Output RESULT
        BRA START    // Branch to the START to initialize and get another input VALUE
END     HLT          // HALT - a zero was entered so done!
RESULT  DAT          // Computed result (defaults to 0)
COUNT   DAT          // Counter (defaults to 0)
ONE     DAT 1        // Constant, value of 1
VALUE   DAT          // User provided input, the value to be squared (defaults to 0)
ZERO    DAT          // Constant, value of 0 (defaults to 0)
"""

#gcse = """
#INP
#STA value1
#while LDA value1
#BRZ endwhile
#SUB count
#STA value1
#LDA nineninenine
#OUT
#BRA while
#endwhile HLT
#value1 DAT
#count DAT 1
#nineninenine DAT 999
#"""

ex = Exec(Assembler(square).mem)

while ex.cycle(): pass

