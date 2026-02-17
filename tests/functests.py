#! /usr/bin/env python3
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,line-too-long,too-many-lines,too-many-public-methods
# pylint: disable=invalid-name,unspecified-encoding,consider-using-with,multiple-statements
""" testing functions directly in strip_python3 module """

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "2.1.1071"

from typing import Optional
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

class AppUnitTest(unittest.TestCase):
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
        self.assertEqual(n, 0)
        self.assertEqual(y, 1)
        self.assertEqual(x, 2)
        self.assertEqual(z, 11)
    def test_0105(self) -> None:
        n = app.to_intN(None, 11)
        m = app.to_intN("m", 11)
        x = app.to_intN("2")
        y = app.to_intN("1")
        z = app.to_intN("0")
        self.assertEqual(n, 11)
        self.assertEqual(m, 11)
        self.assertEqual(x, 2)
        self.assertEqual(y, 1)
        self.assertEqual(z, 0)
    def test_0109(self) -> None:
        n = app.int_mode("")
        x = app.int_mode("2")
        y = app.int_mode("1")
        z = app.int_mode("0")
        q = app.int_mode("qq")
        r = app.int_mode("11")
        self.assertEqual(n, None)
        self.assertEqual(x, 2)
        self.assertEqual(y, 1)
        self.assertEqual(z, 0)
        self.assertEqual(q, None)
        self.assertEqual(r, 9)
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
        self.assertEqual(x20, s20)
        self.assertEqual(x90, "01234...67890123456789")
        self.assertEqual(len(x90), 22)
        n = app.o22(None) # type: ignore[arg-type]
        z = app.o22(0) # type: ignore[arg-type]
        self.assertEqual(n, None)
        self.assertEqual(z, 0)
    def test_0116(self) -> None:
        s20 = "0123456789" * 2
        s90 = "0123456789" * 9
        x20 = app.o44(s20)
        x90 = app.o44(s90)
        self.assertEqual(x20, s20)
        self.assertEqual(x90, "0123456789...9012345678901234567890123456789")
        self.assertEqual(len(x90), 44)
        n = app.o44(None) # type: ignore[arg-type]
        z = app.o44(0) # type: ignore[arg-type]
        self.assertEqual(n, None)
        self.assertEqual(z, 0)
    def test_0117(self) -> None:
        s20 = "0123456789" * 2
        s90 = "0123456789" * 9
        x20 = app.o77(s20)
        x90 = app.o77(s90)
        self.assertEqual(x20, s20)
        self.assertEqual(x90, "01234567890123456789...678901234567890123456789012345678901234567890123456789")
        self.assertEqual(len(x90), 77)
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
        self.assertEqual(n1, [])
        self.assertEqual(n2, [])
        self.assertEqual(n3, [])
        self.assertEqual(n4, [])
        self.assertEqual(x1, [])
        self.assertEqual(x2, [])
        self.assertEqual(x3, [])
        self.assertEqual(x4, [])
        self.assertEqual(a1, ["a"])
        self.assertEqual(a2, ["a"])
        self.assertEqual(a3, ["a"])
        self.assertEqual(b1, ["a", "b"])
        self.assertEqual(b2, ["a", "b"])
        self.assertEqual(c1, ["a", "b", "c"])
        self.assertEqual(c2, ["a", "b", "c"])
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
    def test_0300(self) -> None:
        tmp = self.testdir()
        tmp1 = F"{tmp}/test1.service"
        text_file(tmp1, """
        [Unit]
        Description = foo""")
        unit = app.SystemctlUnitFiles()
        unit.add_unit_sysd_file("test1.service", tmp1)
        want = "foo"
        have = unit.get_Description(unit.get_conf("test1.service"))
        self.assertEqual(have, want)
        self.rm_testdir()
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
