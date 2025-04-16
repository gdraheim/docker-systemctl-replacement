#! /usr/bin/env python3
# pylint: disable=missing-module-docstring,missing-class-docstring,missing-function-docstring,line-too-long,too-many-lines,too-many-public-methods
# pylint: disable=invalid-name,unspecified-encoding,consider-using-with
""" testing functions directly in strip_python3 module """

__copyright__ = "(C) Guido Draheim, licensed under the EUPL"""
__version__ = "2.1.1152"

import sys
import unittest
import logging
import os.path
from fnmatch import fnmatchcase as fnmatch

logg = logging.getLogger(os.path.basename(__file__))

sys.path.append(os.curdir)
from systemctl2 import systemctl3 as app # pylint: disable=wrong-import-position,import-error,no-name-in-module

TODO = 0
VV = "-vv"

class AppUnitTest(unittest.TestCase):
    def test_1100(self) -> None:
        n = app.to_int(0)
        y = app.to_int(1)
        x = app.to_int(2)
        self.assertEqual(n, 0)
        self.assertEqual(y, 1)
        self.assertEqual(x, 2)
    def test_1101(self) -> None:
        n = app.to_int("0")
        y = app.to_int("1")
        x = app.to_int("2")
        z = app.to_int("zz", 11)
        self.assertEqual(n, 0)
        self.assertEqual(y, 1)
        self.assertEqual(x, 2)
        self.assertEqual(z, 11)
    def test_1105(self) -> None:
        n = app.to_int_if(None, 11)
        x = app.to_int_if("2")
        y = app.to_int_if("1")
        z = app.to_int_if("0")
        self.assertEqual(n, 11)
        self.assertEqual(x, 2)
        self.assertEqual(y, 1)
        self.assertEqual(z, 0)
    def test_1110(self) -> None:
        n = app.yes_str(None)
        x = app.yes_str(False)
        y = app.yes_str(True)
        z = app.yes_str("zz") # type: ignore[arg-type]
        self.assertEqual(n, "no")
        self.assertEqual(x, "no")
        self.assertEqual(y, "yes")
        self.assertEqual(z, "zz")
    def test_1120(self) -> None:
        n = app.nix_str(None)
        x = app.nix_str(False)
        y = app.nix_str(True)
        z = app.nix_str("zz") # type: ignore[arg-type]
        self.assertEqual(n, "")
        self.assertEqual(x, "")
        self.assertEqual(y, "*")
        self.assertEqual(z, "zz")
    def test_1121(self) -> None:
        n = app.nix_str(None)
        x = app.nix_str(False)
        y = app.nix_str(True)
        z = app.nix_str("zz") # type: ignore[arg-type]
        self.assertTrue(n is app.NIX)
        self.assertTrue(x is app.NIX)
        self.assertTrue(y is app.ALL)
        self.assertFalse(z is app.NIX)
    def test_1130(self) -> None:
        n = app.q_str(None)
        x = app.q_str(0)
        y = app.q_str(1)
        z = app.q_str("zz")
        q = app.q_str("")
        self.assertEqual(n, "")
        self.assertEqual(x, "0")
        self.assertEqual(y, "1")
        self.assertEqual(z, "'zz'")
        self.assertEqual(q, "''")
    def test_1201(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "UDP"
        have = app.sock_type_str(socket.SOCK_DGRAM)
        self.assertEqual(have, want)
    def test_1202(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "TCP"
        have = app.sock_type_str(socket.SOCK_STREAM)
        self.assertEqual(have, want)
    def test_1203(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "RAW"
        have = app.sock_type_str(socket.SOCK_RAW)
        self.assertEqual(have, want)
    def test_1204(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "RDM"
        have = app.sock_type_str(socket.SOCK_RDM)
        self.assertEqual(have, want)
    def test_1205(self) -> None:
        import socket # pylint: disable=import-outside-toplevel
        want = "SEQ"
        have = app.sock_type_str(socket.SOCK_SEQPACKET)
        self.assertEqual(have, want)
    def test_1209(self) -> None:
        import socket # pylint: disable=import-outside-toplevel,unused-import
        want = "<?>"
        have = app.sock_type_str(255)
        self.assertEqual(have, want)

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
    opt, cmdline_args = cmdline.parse_args()
    logging.basicConfig(level = logging.WARNING - opt.verbose * 5)
    TODO = opt.todo
    VV = "-v" + ("v" * opt.verbose)
    logfile = None
    if opt.logfile:
        if os.path.exists(opt.logfile):
            os.remove(opt.logfile)
        logfile = logging.FileHandler(opt.logfile)
        logfile.setFormatter(logging.Formatter("%(levelname)s:%(relativeCreated)d:%(message)s"))
        logging.getLogger().addHandler(logfile)
        logg.info("log diverted to %s", opt.logfile)
    #
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
            import xmlrunner # type: ignore[import-error,import-untyped] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
            testresult = TestRunner(xmlresults, verbosity=opt.verbose).run(suite)
        else:
            TestRunner = unittest.TextTestRunner
            testresult = TestRunner(verbosity=opt.verbose, failfast=opt.failfast).run(suite)
    else:
        TestRunner = unittest.TextTestRunner
        if xmlresults:
            import xmlrunner # type: ignore[import-error,import-untyped] # pylint: disable=import-error
            TestRunner = xmlrunner.XMLTestRunner
        testresult = TestRunner(logfile.stream, verbosity=opt.verbose).run(suite) # type: ignore
    if not testresult.wasSuccessful():
        sys.exit(1)
