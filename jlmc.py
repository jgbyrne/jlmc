from enum import Enum
import re
import sys


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
                try:
                    self.acc, _ = curtail(int(input()))
                except EOFError:
                    return False
            elif xx == 2:
                print(self.acc)

        elif op == Op.HLT:
            return False

        return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        a1 = sys.argv[1]
        if a1 == "--":
            inp = sys.stdin.read()
            print(inp)
            sys.stdin = open("/dev/tty")
            ex = Exec(Assembler(inp).mem)
        else:
            with open(sys.argv[1]) as prog:
                ex = Exec(Assembler(prog.read()).mem)
    while ex.cycle():
        pass
