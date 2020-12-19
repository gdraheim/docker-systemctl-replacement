#! /usr/bin/python3
import re
import logging

DONE = (logging.ERROR + logging.WARNING) // 2

logg = logging.getLogger("FORMAT")
logging.addLevelName(DONE, "DONE")

WRITEBACK=False

def run(filename):
    changes = 0
    lines = []
    linetext = open(filename).read()
    for line in linetext.splitlines():
        newline = line
        if re.match("^\\s*#", line):
            lines.append(line)
            continue
        m = re.match('(^[^"]*)(["][^"]*["])([^"]*)$', line)
        if m:
            prefix, string, suffix = m.groups()
            flocals = ".format(**locals())"
            if suffix.startswith(flocals):
                if not prefix.strip().endswith("+"):
                    newline = prefix+"f"+string+suffix[len(flocals):]
        if line != newline:
            logg.info(" -%s", line)
            logg.info(" +%s", newline)
            changes += 1
        lines.append(newline)
    logg.debug("found %s lines in %s", len(lines), filename)
    if changes:
        logg.log(DONE, "found %s changes for %s", changes, filename)
    if WRITEBACK:
       with open(filename, "w") as f:
          for line in lines:
              print(line, file=f)

if __name__ == "__main__":
    from argparse import ArgumentParser
    o = ArgumentParser()
    o.add_argument("-v", "--verbose", action="count", default=0,
                   help="increase logging level [%(default)s]")
    o.add_argument("-i", "--in-place", dest="writeback", action="store_true", default=WRITEBACK,
                   help="write the changes back to the file [%(default)s]")
    o.add_argument("filename", 
                   help="the file to show the changes")
    opt = o.parse_args()
    logging.basicConfig(level = max(0, DONE - 10 * opt.verbose))
    WRITEBACK = opt.writeback
    run(opt.filename)
    
    
       
