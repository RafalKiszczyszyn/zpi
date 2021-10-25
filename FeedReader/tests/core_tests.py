import unittest
from broker.core import *


test_variable = "Sample text"


class TestClass:

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class ClassLoaderTests(unittest.TestCase):

    def test__load__no_module_name__none(self):
        # Arrange
        full_class_name = 'ShortClassName'

        # Act + Assert
        self.assertRaisesRegex(ClassLoaderException,
                               f"{full_class_name} must be a full class name.",
                               ClassLoader.load,
                               full_class_name)

    def test__load__non_existent_module__none(self):
        # Arrange
        full_class_name = 'module.ClassName'

        # Act + Assert
        self.assertRaisesRegex(ClassLoaderException,
                               f"Module specified in {full_class_name} does not exist.",
                               ClassLoader.load,
                               full_class_name)

    def test__load__not_a_class__none(self):
        # Arrange
        class_full_name = str(self.__module__) + '.test_variable'

        # Act
        _class = ClassLoader.load(class_full_name)

        # Assert
        self.assertIsNone(_class)

    def test__load__class__instance(self):
        # Arrange
        class_full_name = str(self.__module__) + '.TestClass'

        # Act
        _class = ClassLoader.load(class_full_name)

        # Assert
        self.assertIsInstance(_class, TestClass)

    def test__load__class_with_args__instance(self):
        # Arrange
        class_full_name = str(self.__module__) + '.TestClass'
        args = [1, 2, 3]
        kwargs = {"key": "value"}

        # Act
        _class = ClassLoader.load(class_full_name, *args, **kwargs)

        # Assert
        self.assertIsInstance(_class, TestClass)
        self.assertSequenceEqual(_class.args, args)
        self.assertDictEqual(_class.kwargs, kwargs)
