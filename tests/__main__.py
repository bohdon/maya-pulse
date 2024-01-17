import os
import sys
import unittest
import maya.standalone


def run_tests():
    print("\n\n>>> Running pulse tests...")

    loader = unittest.TestLoader()
    start_dir = "tests"
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


def main():
    maya.standalone.initialize()
    run_tests()


main()
