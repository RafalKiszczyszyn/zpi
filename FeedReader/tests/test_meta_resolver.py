from broker.core import MetaResolver, InjectService, ConfigArgs
from tests.utils import TestCase, CallVerifier


class MetaResolverTests(TestCase):

    def test_resolve_NoMetaClass_ClassRemainUnchanged(self):
        # Arrange
        class ClassWithoutMeta:
            pass
        obj = ClassWithoutMeta()
        attrs = dir(obj)
        sut = MetaResolver({})

        # Act
        sut.resolve(ClassWithoutMeta())

        # Assert
        self.assertSequenceEqual(attrs, dir(obj))

    def test_resolve_InvalidTypeOfMetaClassServices_ExceptionIsRaised(self):
        # Arrange
        class ClassWithMeta:
            class Meta:
                services = ['ServiceName']
        obj = ClassWithMeta()
        sut = MetaResolver({})

        # Act + Assert
        self.assertRaisesWithMessage(
            Exception, lambda: sut.resolve(obj),
            f'{obj.Meta}.services must be a list of InjectService.')

    def test_resolve_InjectedServiceDoesNotExist_OnInjectionFailureIsCalled(self):
        # Arrange
        inject_service = InjectService(service_name='ServiceName', attribute_name='attr')

        class ClassWithMeta:
            class Meta:
                services = [inject_service]

        call_verifier = CallVerifier()

        @call_verifier.wrap
        def on_injection_failure(_):
            pass

        obj = ClassWithMeta()
        sut = MetaResolver({}, on_injection_failure)

        # Act
        sut.resolve(obj)

        # Assert
        self.assertMethodCalledOnce(call_verifier)
        self.assertMethodCalledWithOnePositionalArgument(call_verifier)
        self.assertMethodCallArgsEqual([call_verifier.calls[0].args[0]], [inject_service])

    def test_resolve_InjectedServiceExists_ServiceIsInjected(self):
        # Arrange
        inject_service = InjectService(service_name='ServiceName', attribute_name='attr')
        services = {'ServiceName': 'service'}

        class ClassWithMeta:
            class Meta:
                services = [inject_service]

        obj = ClassWithMeta()
        sut = MetaResolver(services)

        # Act
        sut.resolve(obj)

        # Assert
        self.assertTrue(
            hasattr(obj, inject_service.attribute_name),
            f'Object does not have attribute: "{inject_service.attribute_name}".')
        self.assertEqual(
            getattr(obj, inject_service.attribute_name),
            services[inject_service.service_name],
            f'Injected service is not equal to specified in Meta class.')

    def test_resolve_InvalidTypeOfMetaClassArgs_ExceptionIsRaised(self):
        # Arrange
        class ClassWithMeta:
            class Meta:
                args = ['args']
        obj = ClassWithMeta()
        sut = MetaResolver({})

        # Act + Assert
        self.assertRaisesWithMessage(
            Exception, lambda: sut.resolve(obj),
            f'{obj.Meta}.args must be a ConfigArgs.')

    def test_resolve_NoRequiredConfigArg_ExceptionIsRaised(self):
        # Arrange
        req_attr = 'arg'

        class ClassWithMeta:
            class Meta:
                args = ConfigArgs(required=[req_attr])

        obj = ClassWithMeta()
        sut = MetaResolver({})

        # Act + Assert
        self.assertRaisesWithMessage(
            Exception, lambda: sut.resolve(obj),
            f'Required attribute \'{req_attr}\' was not given for {type(obj)}.')

    def test_resolve_RequiredConfigArgExistsButOptionalDoesNot_RequiredArgIsInjected(self):
        # Arrange
        req_attr = 'req_arg'
        opt_attr = 'opt_arg'

        class ClassWithMeta:
            class Meta:
                args = ConfigArgs(required=[req_attr], optional=[opt_attr])

        obj = ClassWithMeta()
        sut = MetaResolver({})

        # Act
        sut.resolve(obj, args={req_attr: 'value'})

        self.assertTrue(hasattr(obj, req_attr), f'Object does not have attribute: {req_attr}.')
        self.assertEqual(getattr(obj, req_attr), 'value', f'Required attribute value differ from expected.')
        self.assertFalse(hasattr(obj, opt_attr), f'Object should not have optional attribute: {opt_attr}')

    def test_resolve_ValidateConfigArgsButObjectDoesNotHaveValidValidationMethod_ExceptionIsThrown(self):
        # Arrange
        req_attr = 'req_arg'
        opt_attr = 'opt_arg'

        class ClassWithMeta:
            class Meta:
                args = ConfigArgs(required=[req_attr], optional=[opt_attr], validate=True)

            def validate_config_args(self, arg0):
                pass

        obj = ClassWithMeta()
        sut = MetaResolver({})

        # Act + Assert
        self.assertRaisesWithMessage(
            Exception,
            lambda: sut.resolve(obj, args={req_attr: 'value', opt_attr: 'value'}),
            f'{type(obj)} does not have validate_config_args method that takes 0 arguments, required to validate args.')

    def test_resolve_ValidateConfigArgs_ValidateConfigArgsIsCalled(self):
        # Arrange
        req_attr = 'req_arg'
        opt_attr = 'opt_arg'
        call_verifier = CallVerifier()

        class ClassWithMeta:
            class Meta:
                args = ConfigArgs(required=[req_attr], optional=[opt_attr], validate=True)

            @call_verifier.wrap
            def validate_config_args(self):
                pass

        obj = ClassWithMeta()
        sut = MetaResolver({})

        # Act
        sut.resolve(obj, args={req_attr: 'value', opt_attr: 'value'})

        # Assert
        self.assertMethodCalledOnce(call_verifier)
