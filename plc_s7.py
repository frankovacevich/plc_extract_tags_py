"""
This is an simple, extremely inefficient code
that extracts tags from a Siemens S7 PLC program
and returns a python script that can be used
with the snap7 library to read the PLC tags.

To use it, print the PLC program in TIA portal
as a PDF and then use a PDF to TXT converter online
to get a TXT file. This file will be completely
unreadable but will have information of which tags
are used in the project.

The resulting python code is printed on the console.
It takes about a minute to run.
"""


# ======================================================
# Open PLC program (TXT file)
# ======================================================
txt_file = open("plc_program_as_txt.txt", "r", encoding="utf-8")
content = txt_file.read()
txt_file.close()

# Split the content into a (huge) list
content = content.replace(" ","\n").split("\n")


# ======================================================
# We will extract only from DB and M memory
# ======================================================

# Get tags
DBs = list(set([x for x in content if x.startswith("%DB")]))
Ms = list(set([x for x in content if x.startswith("%M")]))

# The repp function takes a tag "x" and separates it into
# the memory block, byte and bit (for example M50.5 is
# transformed into [50, 5] amd DB102.DBX5.0 is transformed
# into [102, 5, 0]
def repp(x):
    x_ = x
    for l in "%ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        x = x.replace(l, "")
    if x.endswith("."): x = x[:-1]
    x = x.split(".")
    x = [int(y) for y in x]
    return x

# Sort tags
DBs.sort(key=lambda x: repp(x))
Ms.sort(key=lambda x: repp(x))


# ======================================================
# Count how many times each tag appears in the project
# ======================================================
# We will remove tags that appear once or less

Wd = {x: content.count(x) for x in DBs}
DBs = [d for d in DBs if Wd[d] > 1 and "." in d and not d.endswith(".")]

Wm = {x: content.count(x) for x in Ms}
Ms = [m for m in Ms if Wm[m] > 1]

# This is useful later
DBs_ = [(repp(x), x) for x in DBs]
Ms_ = [(repp(x), x) for x in Ms]


# ======================================================
# Create the script for DBs
# ======================================================
lastd = ""
for dx in DBs_:
    d = dx[0]
    if d[0] != lastd:
        maxd = [x for x in DBs_ if x[0][0] == d[0]]
        maxd = maxd[-1]
        maxdd = maxd[0][1]
        if "DBX" in maxd[1]: maxdd += 1
        elif "DBB" in maxd[1]: maxdd += 2
        elif "DBW" in maxd[1]: maxdd += 2
        elif "DBD" in maxd[1]: maxdd += 4
        
        print()
        print(f'tag = conn.db_read({d[0]}, 0, {maxdd})')
        lastd = d[0]
        
    if len(d) == 3:
        print(f'result["DB{d[0]}_{d[1]}_{d[2]}"] = util.get_bool(tag, {d[1]}, {d[2]})')
    
    elif "DBB" in dx[1]:
        print(f'result["DB{d[0]}_{d[1]}"] = util.get_byte(tag, {d[1]})')
    
    elif "DBW" in dx[1]:
        print(f'result["DB{d[0]}_{d[1]}"] = util.get_int(tag, {d[1]})')
        
    elif "DBD" in dx[1]:
        print(f'result["DB{d[0]}_{d[1]}"] = util.get_real(tag, {d[1]}) # Could be dword!!')


print()
print()
# ======================================================
# Create the script for Ms
# ======================================================
lastm = -100
lastmx = ""
lastm0 = -100

buff = ""
buff0 = ""

for mx in Ms_:
    m = mx[0]
    
    ##############
    if m[0] > lastm + 8:
        if buff0 != "":
            add = 1
            if "MB" in lastmx[1]: add = 2
            elif "MW" in lastmx[1]: add = 2
            elif "MD" in lastmx[1]: add = 4
            
            print(buff0 + f'{lastm + add - lastm0})\n')
            print(buff)
        
        buff  = ""
        buff0 = f'tag = conn.read_area(snap7.types.areas["MK"], 0, {m[0]}, '
        lastm0 = m[0]
        
    lastm = m[0]
    lastmx = mx
    ##############
    
    if len(m) == 2:
        buff += f'result["M{m[0]}_{m[1]}"] = util.get_bool(tag, {m[0] - lastm0}, {m[1]})\n'
        
    elif "MB" in mx[1]:
        buff += f'result["M{m[0]}"] = util.get_byte(tag, {m[0] - lastm0})\n'
        
    elif "MW" in mx[1]:
        buff += f'result["M{m[0]}"] = util.get_int(tag, {m[0] - lastm0})\n'
        
    elif "MD" in mx[1]:
        buff += f'result["M{m[0]}"] = util.get_real(tag, {m[0] - lastm0}) # could be dword!\n'

 
print(buff0)
print(buff)
        
