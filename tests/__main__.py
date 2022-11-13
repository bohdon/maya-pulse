import unittest
import maya.standalone


def run_tests():
    loader = unittest.TestLoader()
    start_dir = "tests"
    suite = loader.discover(start_dir)

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


def main():
    maya.standalone.initialize()
    run_tests()


main()
