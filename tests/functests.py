#! /usr/bin/env python3
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,line-too-long,too-many-lines,too-many-public-methods
# pylint: disable=invalid-name,unspecified-encoding,consider-using-with,multiple-statements
""" testing functions directly in strip_python3 module """

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "2.1.1075"

from typing import Optional, Any
import sys
import re
import shutil
import inspect
import unittest
import logging
import os.path
from fnmatch import fnmatchcase as fnmatch

logg = logging.getLogger(os.path.basename(__file__))

SYSTEMCTL = "files/docker/systemctl3.py"
TODO = 0
KEEP = 0
NIX = ""
VV = "-vv"

if __name__ == "__main__":
    # unittest.main()
    from optparse import OptionParser  # pylint: disable=deprecated-module
    cmdline = OptionParser("%prog [options] test*",
                      epilog=__doc__.strip().split("\n", 1)[0])
    cmdline.add_option("-v", "--verbose", action="count", default=0,
                  help="increase logging level [%default]")
    cmdline.add_option("-l", "--logfile", metavar="FILE", default="",
                  help="additionally save the output log to a file [%default]")
    cmdline.add_option("--todo", action="count", default=TODO,
                  help="show when an alternative outcome is desired [%default]")
    cmdline.add_option("--failfast", action="store_true", default=False,
                  help="Stop the test run on the first error or failure. [%default]")
    cmdline.add_option("--xmlresults", metavar="FILE", default=None,
                  help="capture results as a junit xml file [%default]")
    cmdline.add_option("--with", "--systemctl", dest="systemctl", metavar="PY", default=SYSTEMCTL)
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    TODO = opt.todo
    SYSTEMCTL = opt.systemctl
    VV = "-v" + ("v" * opt.verbose)
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)

logg.warning("importing %s", SYSTEMCTL)
if "files/docker/systemctl3" in SYSTEMCTL:
    sys.path = [os.curdir] + sys.path
    from files.docker import systemctl3 as app # pylint: disable=wrong-import-position,import-error,no-name-in-module
elif "src/systemctl3" in SYSTEMCTL:
    sys.path = [os.curdir] + sys.path
    from src import systemctl3 as app # type: ignore[no-redef,attr-defined,unused-ignore] # pylint: disable=no-name-in-module
elif "src/systemctl" in SYSTEMCTL:
    sys.path = [os.curdir] + sys.path
    from src import systemctl as app # type: ignore[no-redef,attr-defined,unused-ignore] # pylint: disable=no-name-in-module
elif "tmp/systemctl3" in SYSTEMCTL:
    sys.path = [os.curdir] + sys.path
    from tmp import systemctl3 as app # type: ignore[no-redef,attr-defined,unused-ignore] # pylint: disable=no-name-in-module
elif "tmp/systemctl" in SYSTEMCTL:
    sys.path = [os.curdir] + sys.path
    from tmp import systemctl as app # type: ignore[no-redef,attr-defined,unused-ignore] # pylint: disable=no-name-in-module
else:
    raise ImportError(F"unknown src location {SYSTEMCTL}")

def shell_file(filename: str, content: str) -> None:
    text_file(filename, content)
    os.chmod(filename, 0o775)
def text_file(filename: str, content: str) -> None:
    filedir = os.path.dirname(filename)
    if not os.path.isdir(filedir):
        os.makedirs(filedir)
    f = open(filename, "w")
    if content.startswith("\n"):
        x = re.match("(?s)\n( *)", content)
        assert x is not None
        indent = x.group(1)
        for line in content[1:].split("\n"):
            if line.startswith(indent):
                line = line[len(indent):]
            f.write(line+"\n")
    else:
        f.write(content)
    f.close()
    logg.info("::: made %s", filename)
def get_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name # type: ignore[union-attr]
def get_caller_caller_name() -> str:
    currentframe = inspect.currentframe()
    if not currentframe: return "global"
    frame = currentframe.f_back.f_back.f_back # type: ignore[union-attr]
    return frame.f_code.co_name # type: ignore[union-attr]

def execmode(val: app.ExecMode) -> str:
    bits = ["check" if val.check else "nocheck"]
    if val.nouser:
        bits += ["nouser"]
    if val.noexpand:
        bits += ["noexpand"]
    if val.argv0:
        bits += ["argv0"]
    return "+".join(bits)

class AppUnitTest(unittest.TestCase):
    def assertEq(self, val1: Any, val2: Any, msg: str = NIX) -> None: # type: ignore[explicit-any]
        self.assertEqual(val2, val1, msg)
    def caller_testname(self) -> str:
        name = get_caller_caller_name()
        x1 = name.find("_")
        if x1 < 0: return name
        x2 = name.find("_", x1+1)
        if x2 < 0: return name
        return name[:x2]
    def testname(self, suffix: Optional[str] = None) -> str:
        name = self.caller_testname()
        if suffix:
            return name + "_" + suffix
        return name
    def testdir(self, testname: Optional[str] = None, keep: bool = False) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir) and not keep:
            shutil.rmtree(newdir)
        if not os.path.isdir(newdir):
            os.makedirs(newdir)
        return newdir
    def rm_testdir(self, testname: Optional[str] = None) -> str:
        testname = testname or self.caller_testname()
        newdir = "tmp/tmp."+testname
        if os.path.isdir(newdir):
            if not KEEP:
                shutil.rmtree(newdir)
        return newdir
    def test_0100(self) -> None:
        n = app.to_int(0)
        y = app.to_int(1)
        x = app.to_int(2)
        self.assertEqual(n, 0)
        self.assertEqual(y, 1)
        self.assertEqual(x, 2)
    def test_0101(self) -> None:
        n = app.to_int("0")
        y = app.to_int("1")
        x = app.to_int("2")
        z = app.to_int("zz", 11)
        d = app.to_int("1.1.1")
        e = app.to_int("1.1.1", -1)
        f = app.to_int(["wrong"]) # type: ignore[arg-type]
        self.assertEqual(n, 0)
        self.assertEqual(y, 1)
        self.assertEqual(x, 2)
        self.assertEqual(z, 11)
        self.assertEqual(d, 0)
        self.assertEqual(e, -1)
        self.assertEqual(f, 0)
    def test_0105(self) -> None:
        n = app.to_intN(None, 11)
        m = app.to_intN("m", 11)
        x = app.to_intN("2")
        y = app.to_intN("1")
        z = app.to_intN("0")
        d = app.to_intN("1.1.1")
        e = app.to_intN("1.1.1", -1)
        f = app.to_intN(["wrong"]) # type: ignore[arg-type]
        self.assertEqual(n, 11)
        self.assertEqual(m, 11)
        self.assertEqual(x, 2)
        self.assertEqual(y, 1)
        self.assertEqual(z, 0)
        self.assertEqual(d, None)
        self.assertEqual(e, -1)
        self.assertEqual(f, None)
    def test_0109(self) -> None:
        n = app.int_mode("")
        x = app.int_mode("2")
        y = app.int_mode("1")
        z = app.int_mode("0")
        q = app.int_mode("qq")
        r = app.int_mode("11")
        d = app.int_mode("1.1.1")
        e = app.int_mode("1.1.1", -1)
        f = app.int_mode(["wrong"]) # type: ignore[arg-type]
        self.assertEqual(n, None)
        self.assertEqual(x, 2)
        self.assertEqual(y, 1)
        self.assertEqual(z, 0)
        self.assertEqual(q, None)
        self.assertEqual(r, 9)
        self.assertEqual(d, None)
        self.assertEqual(e, -1)
        self.assertEqual(f, None)
    def test_0110(self) -> None:
        n = app.strYes(None)
        x = app.strYes(False)
        y = app.strYes(True)
        z = app.strYes("zz")
        self.assertEqual(n, "no")
        self.assertEqual(x, "no")
        self.assertEqual(y, "yes")
        self.assertEqual(z, "zz")
    def test_0111(self) -> None:
        n = app.strE(None)
        x = app.strE(False)
        y = app.strE(True)
        z = app.strE("zz")
        self.assertEqual(n, "")
        self.assertEqual(x, "")
        self.assertEqual(y, "*")
        self.assertEqual(z, "zz")
    def test_0112(self) -> None:
        n = app.strE(None)
        x = app.strE(False)
        y = app.strE(True)
        z = app.strE("zz")
        self.assertTrue(n is app.NIX)
        self.assertTrue(x is app.NIX)
        self.assertTrue(y is app.ALL)
        self.assertFalse(z is app.NIX)
    def test_0113(self) -> None:
        n = app.strQ(None)
        x = app.strQ(0)
        y = app.strQ(1)
        z = app.strQ("zz")
        q = app.strQ("")
        self.assertEqual(n, "")
        self.assertEqual(x, "0")
        self.assertEqual(y, "1")
        self.assertEqual(z, "'zz'")
        self.assertEqual(q, "''")
    def test_0115(self) -> None:
        s20 = "0123456789" * 2
        s90 = "0123456789" * 9
        x20 = app.o22(s20)
        x90 = app.o22(s90)
        xxx = app.o22(["x"])   # type: ignore[arg-type]
        self.assertEq(x20, s20)
        self.assertEq(x90, "01234...67890123456789")
        self.assertEq(len(x90), 22)
        self.assertEq(xxx, ["x"])
        n = app.o22(None) # type: ignore[arg-type]
        z = app.o22(0) # type: ignore[arg-type]
        self.assertEqual(n, None)
        self.assertEqual(z, 0)
    def test_0116(self) -> None:
        s20 = "0123456789" * 2
        s90 = "0123456789" * 9
        x20 = app.o44(s20)
        x90 = app.o44(s90)
        xxx = app.o44(["x"])   # type: ignore[arg-type]
        self.assertEq(x20, s20)
        self.assertEq(x90, "0123456789...9012345678901234567890123456789")
        self.assertEq(len(x90), 44)
        self.assertEq(xxx, ["x"])
        n = app.o44(None) # type: ignore[arg-type]
        z = app.o44(0) # type: ignore[arg-type]
        self.assertEq(n, None)
        self.assertEq(z, 0)
    def test_0117(self) -> None:
        s20 = "0123456789" * 2
        s90 = "0123456789" * 9
        x20 = app.o77(s20)
        x90 = app.o77(s90)
        xxx = app.o77(["x"])   # type: ignore[arg-type]
        self.assertEq(x20, s20)
        self.assertEq(x90, "01234567890123456789...678901234567890123456789012345678901234567890123456789")
        self.assertEq(len(x90), 77)
        self.assertEq(xxx, ["x"])
        n = app.o77(None) # type: ignore[arg-type]
        z = app.o77(0) # type: ignore[arg-type]
        self.assertEqual(n, None)
        self.assertEqual(z, 0)
    def test_0118(self) -> None:
        n00 = app.delayed(0)
        n01 = app.delayed(1)
        n02 = app.delayed(2)
        n09 = app.delayed(9)
        n10 = app.delayed(10)
        n11 = app.delayed(11)
        n99 = app.delayed(99)
        n111 = app.delayed(111)
        self.assertEqual(n00, "...")
        self.assertEqual(n01, "+1.")
        self.assertEqual(n02, "+2.")
        self.assertEqual(n09, "+9.")
        self.assertEqual(n10, "10.")
        self.assertEqual(n11, "11.")
        self.assertEqual(n99, "99.")
        self.assertEqual(n111, "111.")
    def test_0119(self) -> None:
        n00 = app.delayed(0,":")
        n01 = app.delayed(1,":")
        n02 = app.delayed(2,":")
        n09 = app.delayed(9,":")
        n10 = app.delayed(10,":")
        n11 = app.delayed(11,":")
        n99 = app.delayed(99,":")
        n111 = app.delayed(111,":")
        self.assertEqual(n00, "..:")
        self.assertEqual(n01, "+1:")
        self.assertEqual(n02, "+2:")
        self.assertEqual(n09, "+9:")
        self.assertEqual(n10, "10:")
        self.assertEqual(n11, "11:")
        self.assertEqual(n99, "99:")
        self.assertEqual(n111, "111:")
    def test_0120(self) -> None:
        n0 = app.to_list(None)
        n1 = app.to_list([])
        n2 = app.to_list("")
        n3 = app.to_list(())
        n4 = app.to_list(0) # type: ignore[arg-type]
        x1 = app.to_list([""])
        y1 = app.to_list(("",))
        z1 = app.to_list(",")
        x2 = app.to_list(["",""])
        y2 = app.to_list(("",""))
        z2 = app.to_list(",,")
        self.assertEqual(n0, [])
        self.assertEqual(n1, [])
        self.assertEqual(n2, [])
        self.assertEqual(n3, [])
        self.assertEqual(n4, [])
        self.assertEqual(x1, [""])
        self.assertEqual(y1, [""])
        self.assertEqual(z1, ["",""])
        self.assertEqual(x2, ["",""])
        self.assertEqual(y2, ["",""])
        self.assertEqual(z2, ["","",""])
    def test_0122(self) -> None:
        n1 = app.commalist([""])
        n2 = app.commalist(["", ""])
        n3 = app.commalist([" "])
        n4 = app.commalist(["", " "])
        x1 = app.commalist([","])
        x2 = app.commalist([",", ","])
        x3 = app.commalist([", "])
        x4 = app.commalist([" ,", " , "])
        a1 = app.commalist(["a"])
        a2 = app.commalist(["a", ""])
        a3 = app.commalist(["a,", ","])
        b1 = app.commalist(["a,b"])
        b2 = app.commalist(["a,b", ""])
        c1 = app.commalist(["a,b", "c"])
        c2 = app.commalist(["a,b", "", "c"])
        self.assertEq(n1, [])
        self.assertEq(n2, [])
        self.assertEq(n3, [])
        self.assertEq(n4, [])
        self.assertEq(x1, [])
        self.assertEq(x2, [])
        self.assertEq(x3, [])
        self.assertEq(x4, [])
        self.assertEq(a1, ["a"])
        self.assertEq(a2, ["a"])
        self.assertEq(a3, ["a"])
        self.assertEq(b1, ["a", "b"])
        self.assertEq(b2, ["a", "b"])
        self.assertEq(c1, ["a", "b", "c"])
        self.assertEq(c2, ["a", "b", "c"])
    def test_0124(self) -> None:
        n1 = app.wordlist([""])
        n2 = app.wordlist(["", ""])
        n3 = app.wordlist([" "])
        n4 = app.wordlist(["", " "])
        x1 = app.wordlist([","])
        x2 = app.wordlist([",", ","])
        x3 = app.wordlist([", "])
        x4 = app.wordlist([" ,", " , "])
        a1 = app.wordlist(["a"])
        a2 = app.wordlist(["a", ""])
        a3 = app.wordlist(["a,", ","])
        b1 = app.wordlist(["a b"])
        b2 = app.wordlist(["a b", ""])
        c1 = app.wordlist(["a b", "c"])
        c2 = app.wordlist(["a b", "", "c"])
        c3 = app.wordlist(["a b ", " ", "c "])
        self.assertEq(n1, [])
        self.assertEq(n2, [])
        self.assertEq(n3, [])
        self.assertEq(n4, [])
        self.assertEq(x1, [','])
        self.assertEq(x2, [',',','])
        self.assertEq(x3, [','])
        self.assertEq(x4, [',',','])
        self.assertEq(a1, ["a"])
        self.assertEq(a2, ["a"])
        self.assertEq(a3, ['a,',','])
        self.assertEq(b1, ["a", "b"])
        self.assertEq(b2, ["a", "b"])
        self.assertEq(c1, ["a", "b", "c"])
        self.assertEq(c2, ["a", "b", "c"])
        self.assertEq(c3, ["a", "b", "c"])
    def test_0130(self) -> None:
        n = app.fnmatched("a")
        z = app.fnmatched("a", "")
        x = app.fnmatched("a", "", "b")
        a = app.fnmatched("a", "a")
        b = app.fnmatched("a", "b")
        c = app.fnmatched("a", "b", "a")
        self.assertTrue(n)
        self.assertTrue(z)
        self.assertTrue(x)
        self.assertTrue(a)
        self.assertFalse(b)
        self.assertTrue(c)
    def test_0201(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "UDP"
        have = app.strINET(socket.SOCK_DGRAM)
        self.assertEqual(have, want)
    def test_0202(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "TCP"
        have = app.strINET(socket.SOCK_STREAM)
        self.assertEqual(have, want)
    def test_0203(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "RAW"
        have = app.strINET(socket.SOCK_RAW)
        self.assertEqual(have, want)
    def test_0204(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "RDM"
        have = app.strINET(socket.SOCK_RDM)
        self.assertEqual(have, want)
    def test_0205(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "SEQ"
        have = app.strINET(socket.SOCK_SEQPACKET)
        self.assertEqual(have, want)
    def test_0209(self) -> None:
        import socket # pylint: disable=import-outside-toplevel,unused-import
        want = "<?>"
        have = app.strINET(255)
        self.assertEqual(have, want)
    def test_0210(self) -> None:
        orig = "foo/bar-1@/var.lock$"
        want = "foo-bar\\x2d1\\x40-var.lock\\x24"
        have = app.unit_name_escape(orig)
        self.assertEqual(have, want)
        back = app.unit_name_unescape(have)
        self.assertEqual(back, orig)
    def test_0230(self) -> None:
        runs = os.environ.get("XDG_RUNTIME_DIR", "")
        want = runs or "/tmp/run-"
        have = app.get_runtime_dir()
        logg.info("have %s", have)
        self.assertTrue(have.startswith(want))
    def test_0231(self) -> None:
        runs = os.environ.get("XDG_RUNTIME_DIR", "")
        want = runs or "/tmp/run-"
        have = app.get_RUN()
        logg.info("have %s", have)
        want = "/tmp/run"
        have = app.get_RUN(True)
        logg.info("have %s", have)
        self.assertTrue(have.startswith(want))
    def test_0232(self) -> None:
        runs = os.environ.get("XDG_RUNTIME_DIR", "")
        want = runs or "/tmp/run-"
        have = app.get_PID_DIR()
        logg.info("have %s", have)
        self.assertTrue(have.startswith(want))
        want = "/tmp/run"
        have = app.get_PID_DIR(True)
        logg.info("have %s", have)
        self.assertTrue(have.startswith(want))
    def test_0233(self) -> None:
        home = os.path.expanduser("~")
        have = app.get_HOME()
        logg.info("have %s", have)
        self.assertEqual(have, home)
        home = os.path.expanduser("~root")
        have = app.get_HOME(True)
        logg.info("have %s", have)
        self.assertEqual(have, home)
    def test_0234(self) -> None:
        have = app.is_good_root(None)
        self.assertEq(have, True)
        have = app.is_good_root("")
        self.assertEq(have, True)
        have = app.is_good_root("/")
        self.assertEq(have, False)
        have = app.is_good_root("/a")
        self.assertEq(have, False)
        have = app.is_good_root("/a/b")
        self.assertEq(have, False)
        have = app.is_good_root("/a/b/")
        self.assertEq(have, False)
        have = app.is_good_root("/a/b/c")
        self.assertEq(have, True)
        have = app.is_good_root("a/b")
        self.assertEq(have, False)
        have = app.is_good_root("a/b/")
        self.assertEq(have, False)
        have = app.is_good_root("a/b/c")
        self.assertEq(have, True)
    def test_0235(self) -> None:
        have = app.os_path("","")
        self.assertEq(have, "")
        have = app.os_path("","y")
        self.assertEq(have, "y")
        have = app.os_path("x","")
        self.assertEq(have, "")
        have = app.os_path("x","y")
        self.assertEq(have, "x/y")
        have = app.os_path("x","/y")
        self.assertEq(have, "x/y")
        have = app.os_path("x","//y")
        self.assertEq(have, "//y")
    def test_0236(self) -> None:
        have = app.get_unit_type("foo")
        self.assertEq(have, None)
        have = app.get_unit_type("foo.c")
        self.assertEq(have, None)
        have = app.get_unit_type("foo.py")
        self.assertEq(have, None)
        have = app.get_unit_type("foo.txt")
        self.assertEq(have, None)
        have = app.get_unit_type("foo.html")
        self.assertEq(have, None)
        have = app.get_unit_type("foo.htmlx")
        self.assertEq(have, "htmlx")
        have = app.get_unit_type("foo.timer")
        self.assertEq(have, "timer")
        have = app.get_unit_type("foo.target")
        self.assertEq(have, "target")
        have = app.get_unit_type("foo.socket")
        self.assertEq(have, "socket")
        have = app.get_unit_type("foo.service")
        self.assertEq(have, "service")
    def test_0237(self) -> None:
        pre, cmd = app.checkprefix("foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre, "")
        pre, cmd = app.checkprefix("-foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre, "-")
        pre, cmd = app.checkprefix("-!foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre, "-!")
        pre, cmd = app.checkprefix("!-foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre, "!-")
        pre, cmd = app.checkprefix("-+!@foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre, "-+!@")
        pre, cmd = app.checkprefix("-+:|foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre, "-+:|")
        pre, cmd = app.checkprefix("")
        self.assertEq(cmd, "")
        self.assertEq(pre, "")
    def test_0238(self) -> None:
        pre, cmd = app.exec_path("foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre.mode, "")
        self.assertTrue(pre.check)
        self.assertFalse(pre.nouser)
        self.assertFalse(pre.noexpand)
        self.assertFalse(pre.argv0)
        pre, cmd = app.exec_path("-foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre.mode, "-")
        self.assertFalse(pre.check)
        self.assertFalse(pre.nouser)
        self.assertFalse(pre.noexpand)
        self.assertFalse(pre.argv0)
        pre, cmd = app.exec_path("-!foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre.mode, "-!")
        self.assertFalse(pre.check)
        self.assertTrue(pre.nouser)
        self.assertFalse(pre.noexpand)
        self.assertFalse(pre.argv0)
        pre, cmd = app.exec_path("!-foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre.mode, "!-")
        self.assertFalse(pre.check)
        self.assertTrue(pre.nouser)
        self.assertFalse(pre.noexpand)
        self.assertFalse(pre.argv0)
        pre, cmd = app.exec_path("-+!@foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre.mode, "-+!@")
        self.assertFalse(pre.check)
        self.assertTrue(pre.nouser)
        self.assertFalse(pre.noexpand)
        self.assertTrue(pre.argv0)
        pre, cmd = app.exec_path("-+:|foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre.mode, "-+:|")
        self.assertFalse(pre.check)
        self.assertTrue(pre.nouser)
        self.assertTrue(pre.noexpand)
        self.assertFalse(pre.argv0)
        pre, cmd = app.exec_path("")
        self.assertEq(cmd, "")
        self.assertEq(pre.mode, "")
        self.assertTrue(pre.check)
        self.assertFalse(pre.nouser)
        self.assertFalse(pre.noexpand)
        self.assertFalse(pre.argv0)
    def test_0239(self) -> None:
        pre, cmd = app.load_path("foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre.mode, "")
        self.assertTrue(pre.check)
        pre, cmd = app.load_path("-foo")
        self.assertEq(cmd, "foo")
        self.assertEq(pre.mode, "-")
        self.assertFalse(pre.check)
        pre, cmd = app.load_path("-!foo")
        self.assertEq(cmd, "!foo")
        self.assertEq(pre.mode, "-")
        self.assertFalse(pre.check)
        pre, cmd = app.load_path("!-foo")
        self.assertEq(cmd, "!-foo")
        self.assertEq(pre.mode, "")
        self.assertTrue(pre.check)
        pre, cmd = app.load_path("-+:|foo")
        self.assertEq(cmd, "+:|foo")
        self.assertEq(pre.mode, "-")
        self.assertFalse(pre.check)
        pre, cmd = app.load_path("")
        self.assertEq(cmd, "")
        self.assertEq(pre.mode, "")
        self.assertTrue(pre.check)
    def test_0240(self) -> None:
        want = 777
        have = app.time_to_seconds("infinity", 777)
        logg.info("have %s", have)
        self.assertEqual(have, want)
    def test_0241(self) -> None:
        want = 111
        have = app.time_to_seconds("111", 777)
        logg.info("have %s", have)
        self.assertEqual(have, want)
        have = app.time_to_seconds("111s", 777)
        logg.info("have %s", have)
        self.assertEqual(have, want)
        have = app.time_to_seconds("111 s", 777)
        logg.info("have %s", have)
        self.assertEqual(have, want)
        have = app.time_to_seconds("999 s", 777)
        logg.info("have %s", have)
        self.assertEqual(have, 777)
        have = app.time_to_seconds("999ms", 777)
        logg.info("have %s", have)
        self.assertEqual(have, 0.999)
        have = app.time_to_seconds("xxs", 777)
        logg.info("have %s", have)
        self.assertEqual(have, 99)
        have = app.time_to_seconds("xxms", 777)
        logg.info("have %s", have)
        self.assertEqual(have, 1)
        have = app.time_to_seconds("s", 777)
        logg.info("have %s", have)
        self.assertEqual(have, 1)
        have = app.time_to_seconds("ms", 777)
        logg.info("have %s", have)
        self.assertEqual(have, 1)
    def test_0242(self) -> None:
        want = 6660
        have = app.time_to_seconds("111min", 7777)
        logg.info("have %s", have)
        self.assertEqual(have, want)
        have = app.time_to_seconds("111m", 7777)
        logg.info("have %s", have)
        self.assertEqual(have, want)
        have = app.time_to_seconds("111 m", 7777)
        logg.info("have %s", have)
        self.assertEqual(have, 111) # TODO
        have = app.time_to_seconds("9999 m", 7777)
        logg.info("have %s", have)
        self.assertEqual(have, 7777)
        have = app.time_to_seconds("xxmin", 7777)
        logg.info("have %s", have)
        self.assertEqual(have, 99*60)
        have = app.time_to_seconds("xxm", 7777)
        logg.info("have %s", have)
        self.assertEqual(have, 99*60)
        have = app.time_to_seconds("m", 777)
        logg.info("have %s", have)
        self.assertEqual(have, 1)
        have = app.time_to_seconds("min", 777)
        logg.info("have %s", have)
        self.assertEqual(have, 1)
    def test_0260(self) -> None:
        have = app.pid_zombie(None) # type: ignore[arg-type]
        logg.info("have %s", have)
        self.assertFalse(have)
        have = app.pid_zombie(-1)
        logg.info("have %s", have)
        self.assertFalse(have)
        self.assertRaises(ValueError, lambda: app.pid_zombie(0))
        have = app.pid_zombie(1)
        logg.info("have %s", have)
        self.assertFalse(have)
        maxpid = int(open('/proc/sys/kernel/pid_max').read())
        logg.info("maxpid %s", maxpid)
        have = app.pid_zombie(maxpid+1)
        logg.info("have %s", have)
        self.assertFalse(have)
        have = app.pid_zombie(os.getpid())
        logg.info("have %s", have)
        self.assertFalse(have)
    def test_0270(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.txt"
        svc2 = "test2.txt"
        text_file(F"{tmp}/{svc1}", """info""")
        have = app.get_exist_path([svc1,svc2])
        self.assertEq(have, None)
        have = app.get_exist_path([F"{tmp}/{svc1}",F"{tmp}/{svc2}"])
        self.assertEq(have, F"{tmp}/{svc1}")
        have = app.get_exist_path([F"{tmp}/{svc2}",F"{tmp}/{svc1}"])
        self.assertEq(have, F"{tmp}/{svc1}")
        self.rm_testdir()
    def test_0271(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.txt"
        svc2 = "test2.txt"
        text_file(F"{tmp}/{svc1}", """info""")
        size1 = os.path.getsize(F"{tmp}/{svc1}")
        app.shutil_truncate(F"{tmp}/{svc1}")
        size2 = os.path.getsize(F"{tmp}/{svc1}")
        self.assertNotEqual(size1, size2)
        self.assertEqual(size2, 0)
        new1: Optional[int]
        try:
            new1 = os.path.getsize(F"{tmp}/{svc2}")
        except OSError:
            new1 = None
        app.shutil_truncate(F"{tmp}/{svc2}")
        new2 = os.path.getsize(F"{tmp}/{svc2}")
        self.assertNotEqual(new1, new2)
        self.assertEqual(new1, None)
        self.assertEqual(new2, 0)
        app.shutil_truncate(F"{tmp}/subdir/{svc2}")
        sub2 = os.path.getsize(F"{tmp}/subdir/{svc2}")
        self.assertEqual(sub2, 0)
    def test_0272(self) -> None:
        tmp = self.testdir()
        files = app.SystemctlUnitFiles(tmp)
        want = os.path.expanduser("~/.config/systemd/user")
        have = files.user_folder()
        logg.info("have %s", have)
        self.assertEq(have, want)
        have = files.system_folder()
        logg.info("have %s", have)
        self.assertEq(have, "/etc/systemd/system")
        files._SYSTEMD_UNIT_PATH = "" # pylint: disable=protected-access
        self.assertRaises(FileNotFoundError, files.user_folder)
        self.assertRaises(FileNotFoundError, files.system_folder)
        self.rm_testdir()
    def test_0273(self) -> None:
        """ same as test_373 but using Unitfiles """
        tmp = self.testdir()
        log1 = "test1.log"
        log_file1 = F"{tmp}/{log1}"
        text_file(log_file1, """
        info
        here""")
        tail_cmd = F"{tmp}/tail.py"
        shell_file(tail_cmd, """
        #!/usr/bin/env python3
        from optparse import OptionParser
        cmdline = OptionParser("%prog")
        cmdline.add_option("-F", "--follow", action="store_true")
        cmdline.add_option("-n", "--lines", metavar="lines")
        opt, args = cmdline.parse_args()
        assert args
        print(open(args[0]).read())
        """)
        app.logg.info("======== lines")
        files = app.SystemctlUnitFiles(tmp)
        journal = app.SystemctlJournal(files)
        journal.exec_spawn = True
        journal.tail_cmds = [tail_cmd]
        x = journal.tail_log_file(log_file1, 1)
        self.assertEq(x, 0)
        app.logg.info("======== follow")
        files = app.SystemctlUnitFiles(tmp)
        journal = app.SystemctlJournal(files)
        journal.exec_spawn = True
        journal.tail_cmds = [tail_cmd]
        x = journal.tail_log_file(log_file1, 1, True)
        self.assertEq(x, 0)
        app.logg.info("======== cat")
        journal = app.SystemctlJournal(files)
        journal.exec_spawn = True
        journal.no_pager = True
        journal.less_cmds = [tail_cmd]
        x = journal.tail_log_file(log_file1)
        self.assertEq(x, 0)
        app.logg.info("======== less")
        journal = app.SystemctlJournal(files)
        journal.exec_spawn = True
        journal.less_cmds = journal.cat_cmds
        x = journal.tail_log_file(log_file1)
        self.assertEq(x, 0)
        app.logg.info("======== no less")
        journal = app.SystemctlJournal(files)
        journal.exec_spawn = True
        journal.less_cmds = []
        x = journal.tail_log_file(log_file1)
        self.assertEq(x, 1)
        app.logg.info("======== no cat")
        journal = app.SystemctlJournal(files)
        journal.exec_spawn = True
        journal.cat_cmds = []
        journal.no_pager = True
        x = journal.tail_log_file(log_file1)
        self.assertEq(x, 1)
        app.logg.info("======== no tail")
        journal = app.SystemctlJournal(files)
        journal.exec_spawn = True
        journal.tail_cmds = []
        x = journal.tail_log_file(log_file1, 1)
        self.assertEq(x, 1)
        app.logg.info("======== no follow")
        journal = app.SystemctlJournal(files)
        journal.exec_spawn = True
        journal.tail_cmds = []
        x = journal.tail_log_file(log_file1, 1, True)
        self.assertEq(x, 1)
        app.logg.info("======== DONE")
    def test_0300(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Unit]
        Description = foo""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        want = "foo"
        conf = unit.get_conf(svc1)
        have = unit.get_Description(conf)
        self.assertEqual(want, have)
        self.rm_testdir()
    def test_0310(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = /usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "check"
        want = ["/usr/bin/false"]
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0311(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = -/usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "nocheck"
        want = ["/usr/bin/false"]
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0312(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = -!/usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "nocheck+nouser"
        want = ["/usr/bin/false"]
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0313(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = !-/usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "nocheck+nouser"
        want = ["/usr/bin/false"]
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0314(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = !!-/usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "nocheck+nouser"
        want = ["/usr/bin/false"]
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0315(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = -+/usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "nocheck+nouser"
        want = ["/usr/bin/false"]
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0316(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = +-/usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "nocheck+nouser"
        want = ["/usr/bin/false"]
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0317(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = +:/usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "check+nouser+noexpand"
        want = ["/usr/bin/false"]
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0318(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = +@/usr/bin/true /usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "check+nouser+argv0"
        want = ["/usr/bin/true"] # not false
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0319(self) -> None:
        tmp = self.testdir()
        svc1 = "test1.service"
        text_file(F"{tmp}/{svc1}", """
        [Service]
        ExecStart = |@/usr/bin/true /usr/bin/false""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_file(svc1, F"{tmp}/{svc1}")
        mode = "check+argv0" # pipe is ignored
        want = ["/usr/bin/true"] # not false
        conf = unit.get_conf(svc1)
        env = unit.get_env(conf)
        for cmd in conf.getlist("Service", "ExecStart", []):
            exe, newcmd = unit.expand_cmd(cmd, env, conf)
            logg.info("[%s] %s", execmode(exe), app.shell_cmd(newcmd))
            self.assertEqual(want, newcmd)
            self.assertEqual(mode, execmode(exe))
        self.rm_testdir()
    def test_0373(self) -> None:
        """ adding to test_273 but using Systemctl """
        tmp = self.testdir()
        svc1 = F"{tmp}/etc/systemd/system/test1.service"
        os.makedirs(os.path.dirname(svc1))
        text_file(svc1, """
        [Service]
        ExecStart = |@/usr/bin/true /usr/bin/false""")
        systemctl = app.Systemctl(tmp)
        conf = systemctl.unitfiles.get_conf("test1.service")
        log_file1 = systemctl.journal.get_log_from(conf)
        text_file(log_file1, """
        info
        here""")
        tail_cmd = F"{tmp}/tail.py"
        shell_file(tail_cmd, """
        #!/usr/bin/env python3
        from optparse import OptionParser
        cmdline = OptionParser("%prog")
        cmdline.add_option("-F", "--follow", action="store_true")
        cmdline.add_option("-n", "--lines", metavar="lines")
        opt, args = cmdline.parse_args()
        assert args
        print(open(args[0]).read())
        """)
        systemctl.journal.tail_cmds = [tail_cmd]
        systemctl.journal.less_cmds = [tail_cmd]
        systemctl.journal.cat_cmds = [tail_cmd]
        systemctl.journal.exec_spawn = True
        app.logg.info("======== less")
        systemctl.log_units(["test1.service"])
        app.logg.info("======== lines")
        systemctl.log_units(["test1.service"], 100)
        app.logg.info("======== follow")
        systemctl.log_units(["test1.service"], 100, True)
        app.logg.info("======== cat")
        systemctl.journal.no_pager = True
        systemctl.log_units(["test1.service"])
        app.logg.info("======== module")
        systemctl.log_modules("test1")
        app.logg.info("======== DONE")

if __name__ == "__main__":
    # unittest.main()
    suite = unittest.TestSuite()
    if not cmdline_args:
        cmdline_args = ["test_*"]
    for arg in cmdline_args:
        for classname in sorted(globals()):
            if not classname.endswith("Test"):
                continue
            testclass = globals()[classname]
            for method in sorted(dir(testclass)):
                if arg.endswith("/"):
                    arg = arg[:-1]
                if "*" not in arg:
                    arg += "*"
                if len(arg) > 2 and arg[1] == "_":
                    arg = "test" + arg[1:]
                if fnmatch(method, arg):
                    suite.addTest(testclass(method))
    # select runner
    xmlresults = None
    if opt.xmlresults:
        if os.path.exists(opt.xmlresults):
            os.remove(opt.xmlresults)
        xmlresults = open(opt.xmlresults, "w")
        logg.info("xml results into %s", opt.xmlresults)
    if not logfile:
        if xmlresults:
            import xmlrunner # type: ignore[import-error,import-untyped,unused-ignore] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
            testresult = TestRunner(xmlresults, verbosity=opt.verbose).run(suite)
        else:
            TestRunner = unittest.TextTestRunner
            testresult = TestRunner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        TestRunner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner # type: ignore[import-error,import-untyped,unused-ignore] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
        testresult = TestRunner(logfile.stream, verbosity=opt.verbose).run(suite) # type: ignore[import-error,unused-ignore]
    if not testresult.wasSuccessful():
        sys.exit(1)
