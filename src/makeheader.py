#! /usr/bin/python
import re
import os.path

def run(filename):
    c_lines = []
    for line in open(filename):
        c_lines += [ line.rstrip() ]
    funcs = "";
    for i, line in enumerate(c_lines):
        if line == "{" and i > 2:
            func = c_lines[i-1]
            rets = c_lines[i-2]
            m = re.match(r"^([_\w]+)[(]", func)
            if m:
                funcs += "\n"
                if rets: 
                    funcs += rets + "\n"
                funcs += func + ";\n"
    h_filename = filename[:-1] + "h"
    if h_filename == filename:
        print "H", h_filename
        return
    h_lines = []
    for line in open(h_filename):
        h_lines += [ line.rstrip() ]
    x_endif = -1
    x_generate = -1
    for i, line in enumerate(h_lines):
        if line.startswith("/* from "):
            x_generate = i
        if line.startswith("#endif"):
            x_endif = i
    if x_endif < 0: return
    x_end = x_endif
    if x_generate > 0: x_end = x_generate
    f = open(h_filename, "w")
    for i in xrange(x_end):
        f.write(h_lines[i]+"\n")
    f.write("/* from %s */\n" % os.path.basename(filename))
    f.write(funcs)
    f.write("\n")
    f.write(h_lines[x_endif]+"\n")
    f.close()
    print "written", h_filename

if __name__ == "__main__":
    from optparse import OptionParser
    opts = OptionParser("%prog xy.c")
    opt, args = opts.parse_args()
    for arg in args:
        run(arg)