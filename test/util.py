import unittest


def main(module_name):
    import sys
    tests = unittest.defaultTestLoader.loadTestsFromModule(
        sys.modules[module_name])
    test_suite = unittest.TestSuite(tests)
    unittest.TextTestRunner(verbosity=2).run(test_suite)


class replace(object):
    def __init__(self, parent, name, new_obj):
        self.parent = parent
        self.name = name
        self.new_obj = new_obj

    def __enter__(self):
        self.real_obj = getattr(self.parent, self.name)
        setattr(self.parent, self.name, self.new_obj)

    def __exit__(self, exc_type, exc_value, traceback):
        setattr(self.parent, self.name, self.real_obj)


class Bucket(dict):
    def __init__(self, *a, **kw):
        super(Bucket, self).__init__(*a, **kw)
        self.__dict__ = self
