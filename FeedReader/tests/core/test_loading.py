import pathlib
import sys;sys.path.append(str(pathlib.Path(__file__).resolve().parent.parent.parent))
from unittest.mock import patch

from feedreader.core.exceptions import MissingParameter, InvalidParameter, NotASubclass
from feedreader.core.loading import CallableInvoker, ClassLoader, ImplementationBuilder, kwarg_lookup, \
    implementation_builder_factory, IImplementationBuilder

from feedreader.core.config import ClassConfig
from unittest import TestCase, mock


class CallableInvokerTests(TestCase):

    def test_Invoke_NotCallable_TypeErrorIsRaised(self):
        # Act + Assert
        self.assertRaises(TypeError, CallableInvoker().invoke, "string")

    def test_Invoke_CallableDoesNotTakeKwargs_TypeErrorIsRaised(self):
        # Act + Assert
        self.assertRaises(MissingParameter, CallableInvoker().invoke, lambda arg, *args: None)

    def test_Invoke_CallableWithArgsAndKwargs_CallableIsInvoked(self):
        # Arrange
        _args = ('arg1',)
        _kwargs = {'arg2': 'values'}

        def func(*args, **kwargs):
            self.assertEqual(args, _args)
            self.assertEqual(kwargs, _kwargs)

        # Act + Assert
        CallableInvoker().invoke(func, *_args, **_kwargs)


class ClassLoaderTests(TestCase):

    def test_Load_InvalidTypeOfParams_TypeErrorIsRaised(self):
        # Act + Assert
        self.assertRaises(TypeError, ClassLoader(mock.Mock()).load, 123)

    def test_Load_ParamIsNotAFullClassName_InvalidParameterIsRaised(self):
        # Act + Assert
        self.assertRaises(InvalidParameter, ClassLoader(mock.Mock()).load, "NotAFullClassName")

    @patch('importlib.import_module')
    def test_Load_ClassDoesNotExist_ImportErrorIsRaised(self, importModuleFuncMock):
        # Arrange
        importModuleFuncMock.return_value = "module"

        # Act + Assert
        self.assertRaises(ImportError, ClassLoader(mock.Mock()).load, "module.ClassName")

    @patch('importlib.import_module')
    def test_Load_ImportedTypeIsClass_InstanceIsReturned(self, importModuleFuncMock):
        # Arrange
        class DummyModule:
            ClassName = mock.Mock()

        importModuleFuncMock.return_value = DummyModule()
        invokerMock = mock.Mock()
        invokerMock.invoke.return_value = DummyModule.ClassName

        # Act
        instance = ClassLoader(invokerMock).load("module.ClassName")

        # Assert
        self.assertEqual(instance, DummyModule.ClassName)


class ImplementationBuilderTests(TestCase):

    def test_Build_ParamIsNotClassConfig_NotASubclassIsRaise(self):
        # Act + Assert
        self.assertRaises(NotASubclass, ImplementationBuilder(mock.Mock()).build, "")

    def test_Build_ValidClassConfig_InstanceIsReturned(self):
        # Arrange
        classLoaderMock = mock.Mock()
        config = ClassConfig(implementation='module.ClassName', args={'configArg': 'value'})

        # Act
        ImplementationBuilder(classLoaderMock).build(config)

        classLoaderMock.load.assert_called_once_with(config.implementation, configArg='value')


class ModuleTests(TestCase):

    def test_KwargsLookup_RequiredArgDoesNotExist_KeyErrorIsRaised(self):
        # Act + Assert
        self.assertRaises(KeyError, kwarg_lookup, {}, 'arg', True)

    def test_KwargsLookup_OptionalArgDoesNotExist_NoneIsReturned(self):
        # Act
        ret = kwarg_lookup({}, 'arg', False)

        # Assert
        self.assertIsNone(ret)

    def test_KwargsLookup_ArgExist_ValueIsReturned(self):
        # Act
        ret = kwarg_lookup({'arg': 'value'}, 'arg', False)

        # Assert
        self.assertEqual(ret, 'value')

    def test_ImplementationBuilderFactory_ImplementationBuilderIsReturned(self):
        # Act
        impl = implementation_builder_factory()

        # Assert
        self.assertTrue(issubclass(type(impl), IImplementationBuilder))
