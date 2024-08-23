import numpy as np
import pytest
from ell._lstr import _lstr


class TestLstr:
    def test_init(self):
        # Test initialization with string content only
        s = _lstr("hello")
        assert str(s) == "hello"
        assert s.logits is None
        assert s._origin_trace == frozenset()

        # Test initialization with logits and _origin_trace
        logits = np.array([0.1, 0.2])
        _origin_trace = "model1"
        s = _lstr("world", logits=logits, _origin_trace=_origin_trace)
        assert str(s) == "world"
        assert np.array_equal(s.logits, logits)
        assert s._origin_trace == frozenset({_origin_trace})

    def test_add(self):
        s1 = _lstr("hello")
        s2 = _lstr("world", _origin_trace="model2")
        assert isinstance(s1 + s2, str)
        result = s1 + s2
        assert str(result) == "helloworld"
        assert result.logits is None
        assert result._origin_trace == frozenset({"model2"})

    def test_mod(self):
        s = _lstr("hello %s")
        result = s % "world"
        assert str(result) == "hello world"
        assert result.logits is None
        assert result._origin_trace == frozenset()

    def test_mul(self):
        s = _lstr("ha", _origin_trace="model3")
        result = s * 3
        assert str(result) == "hahaha"
        assert result.logits is None
        assert result._origin_trace == frozenset({"model3"})

    def test_getitem(self):
        s = _lstr(
            "hello", logits=np.array([0.1, 0.2, 0.3, 0.4, 0.5]), _origin_trace="model4"
        )
        result = s[1:4]
        assert str(result) == "ell"
        assert result.logits is None
        assert result._origin_trace == frozenset({"model4"})

    def test_upper(self):
        # Test upper method without _origin_trace and logits
        s = _lstr("hello")
        result = s.upper()
        assert str(result) == "HELLO"
        assert result.logits is None
        assert result._origin_trace == frozenset()

        # Test upper method with _origin_trace
        s = _lstr("world", _origin_trace="model11")
        result = s.upper()
        assert str(result) == "WORLD"
        assert result.logits is None
        assert result._origin_trace == frozenset({"model11"})

    def test_join(self):
        s = _lstr(", ", _origin_trace="model5")
        parts = [_lstr("hello"), _lstr("world", _origin_trace="model6")]
        result = s.join(parts)
        assert str(result) == "hello, world"
        assert result.logits is None
        assert result._origin_trace == frozenset({"model5", "model6"})

    def test_split(self):
        s = _lstr("hello world", _origin_trace="model7")
        parts = s.split()
        assert [str(p) for p in parts] == ["hello", "world"]
        assert all(p.logits is None for p in parts)
        assert all(p._origin_trace == frozenset({"model7"}) for p in parts)

    def test_partition(self):
        s = _lstr("hello, world", _origin_trace="model8")
        part1, sep, part2 = s.partition(", ")
        assert (str(part1), str(sep), str(part2)) == ("hello", ", ", "world")
        assert all(p.logits is None for p in (part1, sep, part2))
        assert all(p._origin_trace == frozenset({"model8"}) for p in (part1, sep, part2))

    def test_formatting(self):
        s = _lstr("Hello {}!")
        filled = s.format(_lstr("world", _origin_trace="model9"))
        assert str(filled) == "Hello world!"
        assert filled.logits is None
        assert filled._origin_trace == frozenset({"model9"})

    def test_repr(self):
        s = _lstr("test", logits=np.array([1.0]), _origin_trace="model10")
        assert "test" in repr(s)
        assert "model10" in repr(s._origin_trace)


# Run the tests
if __name__ == "__main__":
    pytest.main()
