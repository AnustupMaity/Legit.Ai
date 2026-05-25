import unittest

if __name__ == "__main__":
    # Automatically discover and run all tests in the current directory
    loader = unittest.TestLoader()
    suite = loader.discover('.', pattern='main_test.py')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
