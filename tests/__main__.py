
import unittest

import maya.standalone
maya.standalone.initialize()

# pulse setup
import pulse
pulse.load_builtin_actions()

# run tests
loader = unittest.TestLoader()
start_dir = 'tests'
suite = loader.discover(start_dir)

runner = unittest.TextTestRunner(verbosity=2)
runner.run(suite)
