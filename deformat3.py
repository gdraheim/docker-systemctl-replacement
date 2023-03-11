#! /usr/bin/python3
import re
import logging

DONE = (logging.ERROR + logging.WARNING) // 2

logg = logging.getLogger("DEFORMAT")
logging.addLevelName(DONE, "DONE")

WRITEBACK=False
FSTRINGS=False
NEWS=False

def decompose(fstring):
    args = ""
    fmt = ""
    for elem in fstring.split("{"):
        if "}" in elem:
            arg, part = elem.split("}", 1)
            if ":" in arg:
                a, f = arg.split(":", 1)
                args += ", " + a
                fmt += "%" + f + part
            elif "!" in arg:
                a, f = arg.split("!", 1)
                if f == "s":
                    args += ", " + a
                    fmt += "%s" + part
                else:
                    args += ", rep" + f + "(" + a + ")"
                    fmt += "%s" + part
            else:
                args += ", " + arg
                fmt += "%s" + part
        else:
            fmt += elem
    return fmt, args

def run(filename):
    changes = 0
    lines = []
    srctext = open(filename).read()
    linenum = 0
    for line0 in srctext.splitlines():
        line = line0
        linenum += 1
        if re.match("^\\s*# [|]", line):
            continue # do not append 
        if re.match("^\\s*#", line):
            lines.append(line)
            continue
        maps = { "dbg_": "debug", "debug_": "debug", "info_": "info", "warn_": "warning", "warning_": "warning", "error_": "error"}
        m = re.match(r'(.*\s)(dbg_|debug_|info_|warn_|warning_|error_)[(]("[^"]*")[.]format[(][*][*]locals[(][)][)]([,].*[)].*)', line)
        if m:
            pref = m.group(1)
            warn = maps[m.group(2)]
            fmts = m.group(3)
            post = m.group(4)
            fmts = fmts[:-1] + ' %s"'
            logg.debug(" for %s(|%s|%s", warn, fmts, post)
            if FSTRINGS:
               fmt, args = decompose(fmts)
               line = pref + "logg." + warn + '(' + fmt + args + post
            else:
               line = pref + "logg." + warn + '(f' + fmts + post
        m = re.match(r'(.*\s)(dbg_|debug_|info_|warn_|warning_|error_)[(]("[^"]*")[.]format[(][*][*]locals[(][)][)]([)].*)', line)
        if m:
            pref = m.group(1)
            warn = maps[m.group(2)]
            fmts = m.group(3)
            post = m.group(4)
            logg.debug(" for %s(|%s|%s", warn, fmts, post)
            if FSTRINGS:
               fmt, args = decompose(fmts)
               line = pref + "logg." + warn + '(' + fmt + args + post
            else:
               line = pref + "logg." + warn + '(f' + fmts + post
        m = re.match(r'(.*\s)(dbg_|debug_|info_|warn_|warning_|error_)[(]("[^"]*")([,].*[)].*)', line)
        if m:
            pref = m.group(1)
            warn = maps[m.group(2)]
            fmts = m.group(3)
            post = m.group(4)
            fmts = fmts[:-1] + ' %s"'
            logg.debug(" for %s(|%s|%s", warn, fmts, args, post)
            if FSTRINGS:
               fmt, args = decompose(fmts)
               line = pref + "logg." + warn + '(' + fmt + args + post
            else:
               line = pref + "logg." + warn + '(f' + fmts + post
        m = re.match(r'(.*\s)(dbg_|debug_|info_|warn_|warning_|error_)[(]("[^"]*")([)].*)', line)
        if m:
            pref = m.group(1)
            warn = maps[m.group(2)]
            fmts = m.group(3)
            post = m.group(4)
            logg.debug(" for %s(|%s|%s", warn, fmts, args + post)
            if FSTRINGS:
               fmt, args = decompose(fmts)
               line = pref + "logg." + warn + '(' + fmt + args + post
            else:
               line = pref + "logg." + warn + '(f' + fmts + post
        m = re.match(r'(.*\s)(dbg_|debug_|info_|warn_|warning_|error_)[(]("[^"]*")\s*[+]([^+]*)$', line)
        if m:
            pref = m.group(1)
            warn = maps[m.group(2)]
            fmts = m.group(3)
            post = m.group(4)
            logg.debug(" for %s(|%s|%s", warn, fmts, args + post)
            fmt = fmt[:-1] + '%s"'
            line = pref + "logg." + warn + '(' + fmt + ", " + post
        m = re.match(r'def(\s+)(dbg_|debug_|info_|warn_|warning_|error_)[(](.*)', line)
        if m:
            pass
        else:
            m = re.match(r'(.*\s)(dbg_|debug_|info_|warn_|warning_|error_)[(](.*)', line)
            if m:
                logg.error("---- %s(%s", m.group(2), m.group(3))
        if line != line0:
            if not NEWS:
                logg.info(" -%s", line0)
            if True:
                logg.info(" +%s", line)
            changes += 1
        lines.append(line)
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
    o.add_argument("-f", "--fstrings", action="store_true", default=FSTRINGS,
                   help="decompose f-strings [%(default)s]")
    o.add_argument("-n", "--news", action="store_true", default=NEWS,
                   help="show only the new lines in diff [%(default)s]")
    o.add_argument("filename", 
                   help="the file to show the changes")
    opt = o.parse_args()
    logging.basicConfig(level = max(0, DONE - 10 * opt.verbose))
    WRITEBACK = opt.writeback
    FSTRINGS = opt.fstrings
    NEWS = opt.news
    run(opt.filename)
    
    
       
