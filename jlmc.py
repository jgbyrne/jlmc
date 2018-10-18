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
        val = lookup(tok)
        if val is not None:
            self.mem[self.ptr] += lookup(tok)
        else:
            print("Encountered Bad Token: {}".format(tok))
            sys.exit(1)

    def write_val(self, val):
        try:
            if 0 <= int(val) < (100 if self.mem[self.ptr] else 1000):
                self.mem[self.ptr] += int(val)
            else:
                print("Bad numerical value: {}".format(val))
                sys.exit(1)
        except ValueError:
            if val in self.symbols:
                self.mem[self.ptr] += self.symbols[val]
            else:
                self.links[self.ptr] = val

    def write_label(self, tok):
        if tok in self.symbols:
            print("Encountered same label twice: {}".format(tok))
            sys.exit(1)
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
    HALT    = 0
    SUCCESS = 2
    OUTPUT  = 3
    INPUT   = 4

    def __init__(self, prog, symbols={}):
        self.memory = [000] * 100
        for i, d in enumerate(prog):
            self.memory[i] = d
        self.symbols = symbols
        self.begun   = False
        self.inputs  = []
        self.outputs = []
        self.outbox  = 000
        self.inbox   = 000
        self.pc      = 000
        self.ip      = 000
        self.acc     = 000
        self.neg     = False
        #print(self.memory)

    def __str__(self):
        s = "+-" * 40 + "\n"
        s += " " * 14
        s += "   IP  {:02d}      PC  {:02d}  ACC {:03d}\n".format(self.ip, self.pc, self.acc)
        s += " " * 14
        s += "INBOX {:03d}  OUTBOX {:03d}  NEG {}\n\n ".format(self.inbox, self.outbox, self.neg)
        s += "      0    1    2    3    4    5    6    7    8    9\n"
        op = Op(self.memory[self.ip] // 100)
        if op in (Op.ADD, Op.SUB, Op.STA, Op.LDA, Op.BRA, Op.BRZ, Op.BRP):
            target = self.memory[self.ip] % 100
        else:
            target = 100
        for a in range(10):
            s += "  {}   ".format(a)
            for b in range(10):
                addr = (10 * a) + b
                if addr == self.ip:
                    s = s[:-1]
                    s += "{{{:03d}}} ".format(self.memory[addr])
                elif addr == target:
                    s = s[:-1]
                    s += ">{:03d}< ".format(self.memory[addr])
                else:
                    s += "{:03d}  ".format(self.memory[addr])
            s += "\n"

        if not self.begun:
            s += "\n  Program Loaded\n"
        else:
            s += "\n  Concluded Operation: {:03d} ({})\n".format(self.memory[self.ip],
                                                       Op(self.memory[self.ip] // 100).name)
        s += "-+" * 40
        return s

    def cycle(self, inp = None):
        if not self.begun: self.begun = True
        self.ip = self.pc
        ir = self.memory[self.ip]
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
                self.acc, _ = curtail(inp)
                self.inbox = self.acc
                self.inputs.append(self.acc)
                return Exec.INPUT
            elif xx == 2:
                self.outbox = self.acc
                self.outputs.append(self.outbox)
                return Exec.OUTPUT
        elif op == Op.HLT:
            return Exec.HALT

        return Exec.SUCCESS

    def needs_input(self):
        return self.memory[self.pc] == 901

if __name__ == "__main__":
    if len(sys.argv) > 1:
        a1 = sys.argv[1]
        if a1 == "--":
            inp = sys.stdin.read()
            # Ugly hack to take user input after previously reading stdin
            sys.stdin = open("/dev/tty")
            ex = Exec(Assembler(inp).mem)
        else:
            with open(sys.argv[1]) as prog:
                asm = Assembler(prog.read())
                ex = Exec(asm.mem, symbols=asm.symbols)
    else:
        print("JLMC needs either a program file as an argument, or the argument '--' and a progam on stdin")
        sys.exit(1)

    if "--debug" in sys.argv:
        breaks  = []
        run     = "--run" in sys.argv
        ahdr = ["", " " * 22 + "JLMC Debugger"] + [""] * 3 + ["    Inputs     Outputs", "    ------     -------"]
        inp  = None
        first = True
        while True:
            if not first:
                if ex.needs_input():
                    if inp is None:
                        print("Halting - No Input Given")
                        sys.exit(1)
                    try:
                        code = ex.cycle(inp = int(inp))
                    except (EOFError, ValueError, KeyboardInterrupt):
                        print("Halting - Bad Input Value")
                        sys.exit(1)
                    else:
                        inp = None
                else:
                    code = ex.cycle()
            else:
                first = False
                code  = Exec.SUCCESS
            print()
            appends = [] + ahdr
            for i in range(1, 8):
                ln = []
                ln.append("    {:03d}".format(ex.inputs[-i]) if i <= len(ex.inputs) else "       ")
                if code == Exec.INPUT and i == 1:
                    ln.append(" <      ")
                else:
                    ln.append("        ")
                ln.append("{:03d}".format(ex.outputs[-i]) if i <= len(ex.outputs) else "   ")
                if code == Exec.OUTPUT and i == 1:
                    ln.append(" <  ")
                else:
                    ln.append("    ")
                appends.append("".join(ln))
            if inp is not None:
                appends.append("    Next Input: {}".format(inp))
            else:
                appends.append("")

            notices = []
            if ex.ip in breaks:
                notices.append("Hit Breakpoint (IP is {:02d})".format(ex.ip))
            if ex.needs_input() and inp is None:
                notices.append("Next instruction requires Input")
            appends.append("  " + ", ".join(notices))


            s = str(ex).split("\n")
            for i, a in enumerate(appends):
                s[i] += str(a)
            print("\n".join(s))

            while True:
                try:
                    comargs = []
                    await_inp = ex.needs_input() and inp is None
                    if not run or ex.ip in breaks or await_inp:
                        command = input("$ ")
                        comargs = command.split()
                    if comargs:
                        comargs[0] = comargs[0].lower()
                        if comargs[0] == "breakpoint":
                            if len(comargs) > 1:
                                try:
                                    addr = int(comargs[1])
                                except ValueError:
                                    if comargs[1] in ex.symbols:
                                        addr = ex.symbols[comargs[1]]
                                    else:
                                        print("No such symbol")
                                        continue
                                breaks.append(addr)
                                print("Added Breakpoint")
                        elif comargs[0] == "delpoint":
                            if len(comargs) > 1:
                                try:
                                    addr = int(comargs[1])
                                except ValueError:
                                    if comargs[1] in ex.symbols:
                                        addr = ex.symbols[comargs[1]]
                                    else:
                                        print("No such symbol")
                                        continue
                                if addr in breaks:
                                    breaks.remove(addr)
                                    print("Removed Breakpoint")
                        elif comargs[0] == "listpoints":
                            print(", ".join(str(b) for b in breaks))
                        elif comargs[0] in ("input", "inp", "i"):
                            if len(comargs) > 1:
                                inp = comargs[1]
                        elif comargs[0] == "run":
                            run = True
                        elif comargs[0] == "step":
                            run = False
                    elif not await_inp:
                        break
                except (EOFError, KeyboardInterrupt):
                    print("Halting")
                    sys.exit(1)
            if not code:
                break

    else:
        while True:
            if ex.needs_input():
                try:
                    code = ex.cycle(inp = int(input()))
                except (EOFError, ValueError, KeyboardInterrupt):
                    sys.exit(1)
            else:
                code = ex.cycle()
            if not code: break
            if code == Exec.OUTPUT:
                print(ex.outbox)

