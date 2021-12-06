import unittest
from dataclasses import dataclass


class CallVerifier:

    @dataclass
    class CallData:
        args: tuple
        kwargs: dict
        result: object

    def __init__(self):
        self.calls = []

    def wrap(self, func):
        def inner(*args, **kwargs):
            calldata = self.CallData(args, kwargs, func(*args, **kwargs))
            self.calls.append(calldata)
            return calldata.result
        return inner


class TestCase(unittest.TestCase):

    def assertRaisesWithMessage(self, exception_type, callable, message):
        try:
            callable()
        except Exception as e:
            self.assertTrue(type(e) == exception_type, f'{type(e)} was raised, but expected {exception_type}')
            self.assertEqual(str(e), message)

    def assertMethodCalledOnce(self, call_verifier: CallVerifier):
        self.assertEqual(len(call_verifier.calls), 1, 'Method should be called once.')

    def assertMethodCalledWithOnePositionalArgument(self, call_verifier: CallVerifier):
        self.assertEqual(len(call_verifier.calls[0].args), 1, 'Method should be called with one positional argument.')

    def assertMethodCallArgsEqual(self, expected, actual):
        self.assertSequenceEqual(expected, actual, 'Expected call args differ.')
