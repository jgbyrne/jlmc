import subprocess
with open("tests") as tsts:
    for line in tsts:
        proc = subprocess.Popen(['python3', './jlmc.py', '../summative/bconvn.comp2.lmc'], stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        parts = line.split(";")[1].split(",")
        print(proc.communicate(bytes("\n".join(parts[0:1]), "utf8")))
        if response == parts[2]:
            print("Passed")
        else:
            print("Failed: {} ({})", line, response)
