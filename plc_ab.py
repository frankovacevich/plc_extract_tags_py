"""
This is an simple, extremely inefficient code
that extracts tags from a Allen Bradley PLC program
and returns a python script that can be used
with the pycomm library to read the PLC tags.

To use it, print the PLC project as a PDF and then
use a PDF to TXT converter online to get a TXT file. 
This file will be completely unreadable but will 
have information of which tags are used in the project.

Sometimes there is a list of all the memory blocks
at the end of the txt file. That part should be deleted
manually. (We call this part the "tail")

The resulting python code is printed on the console.
"""

# ======================================================
# Open PLC program (TXT file)
# ======================================================
txt_file = open("../plc_tinas.txt", "r", encoding="utf-8")
content = txt_file.read()
txt_file.close()

# Get a long list from the file content
content = content.replace(" ","\n").split("\n")

# ======================================================
# Find the tags in the list
# ======================================================
tags = []
lett = ["I", "O", "B", "F", "N", "T", "C", "S"]
for l in lett:
    for i in range(0, 200):
        tags.append(l + ":" + str(i))
        for j in range(0, 200):
            tags.append(l + str(i) + ":" + str(j))        

tag_count = {}
i = 0
for c in content:
    i += 1
    if ":" not in c: continue
    if c[0] not in lett: continue

    if c in tags: 
        if c not in tag_count: tag_count[c] = 0
        tag_count[c] += 1


# ======================================================
# Remove tags that appear too few times
# ======================================================
tags = [t for t in tags if t in tag_count and tag_count[t] > 2]
tags.sort()


# Optional: use the tail to get which tags are separated
# into bits (insted of reading the whole byte or word)
"""
tail = open("plc_tinas_tail.txt")
tail_content = tail.read()
tail.close()
tail_content = tail_content.replace(" ", "\n").split("\n")
tags = [x for x in tags if x in tail_content]

n_tags = []
for t in tags:
    add = True
    for i in range(0, 16):
        w = t + "/" + str(i)
        if w in tail_content:
            add = False
            n_tags.append(w)
            
    if add: n_tags.append(t)
        
tags = n_tags
"""

# ======================================================
# Sort tags
# ======================================================
def tag_to_tuple(t):
    l = t[0]
    t = t[1:]
    t = t.split("/")[0]
    t = t.split(":")
    if t[0] == "": t[0] = 0
    return (l, int(t[0]), int(t[1]))

tags.sort(key=tag_to_tuple)


# ======================================================
# Create the script
# ======================================================
b = ""
c = ""
tgroup = ""
sgroup = ""

for t in tags:
    tg = t.split(":")[0]
    if tg != tgroup: 
        c = [x for x in tags if x.startswith(tg)][-1].split("/")[0].split(":")[1]
        print()
        print(f'tag = conn.read_tag("{tg}:0", {c})')
    tgroup = tg 
    
    if "/" in t:
        sg = t.split("/")[0].split(":")[1]
        if sgroup != sg: print(f"tag_ = int2bits(tag[{sg}])")
        sgroup = sg
        
        rg = t.split("/")[1]
        print(f'result["{t}"] = tag_[{rg}]')
    
    else:
        rg = t.split(":")[1]
        print(f'result["{t}"] = tag[{rg}]')
    
    