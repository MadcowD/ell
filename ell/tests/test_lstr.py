import numpy as np
import pytest
from ell.lstr import lstr


class TestLstr:
    def test_init(self):
        # Test initialization with string content only
        s = lstr("hello")
        assert str(s) == "hello"
        assert s.logits is None
        assert s.originator == frozenset()

        # Test initialization with logits and originator
        logits = np.array([0.1, 0.2])
        originator = "model1"
        s = lstr("world", logits=logits, originator=originator)
        assert str(s) == "world"
        assert np.array_equal(s.logits, logits)
        assert s.originator == frozenset({originator})

    def test_add(self):
        s1 = lstr("hello")
        s2 = lstr("world", originator="model2")
        assert isinstance(s1 + s2, str)
        result = s1 + s2
        assert str(result) == "helloworld"
        assert result.logits is None
        assert result.originator == frozenset({"model2"})

    def test_mod(self):
        s = lstr("hello %s")
        result = s % "world"
        assert str(result) == "hello world"
        assert result.logits is None
        assert result.originator == frozenset()

    def test_mul(self):
        s = lstr("ha", originator="model3")
        result = s * 3
        assert str(result) == "hahaha"
        assert result.logits is None
        assert result.originator == frozenset({"model3"})

    def test_getitem(self):
        s = lstr(
            "hello", logits=np.array([0.1, 0.2, 0.3, 0.4, 0.5]), originator="model4"
        )
        result = s[1:4]
        assert str(result) == "ell"
        assert result.logits is None
        assert result.originator == frozenset({"model4"})

    def test_upper(self):
        # Test upper method without originator and logits
        s = lstr("hello")
        result = s.upper()
        assert str(result) == "HELLO"
        assert result.logits is None
        assert result.originator == frozenset()

        # Test upper method with originator
        s = lstr("world", originator="model11")
        result = s.upper()
        assert str(result) == "WORLD"
        assert result.logits is None
        assert result.originator == frozenset({"model11"})

    def test_join(self):
        s = lstr(", ", originator="model5")
        parts = [lstr("hello"), lstr("world", originator="model6")]
        result = s.join(parts)
        assert str(result) == "hello, world"
        assert result.logits is None
        assert result.originator == frozenset({"model5", "model6"})

    def test_split(self):
        s = lstr("hello world", originator="model7")
        parts = s.split()
        assert [str(p) for p in parts] == ["hello", "world"]
        assert all(p.logits is None for p in parts)
        assert all(p.originator == frozenset({"model7"}) for p in parts)

    def test_partition(self):
        s = lstr("hello, world", originator="model8")
        part1, sep, part2 = s.partition(", ")
        assert (str(part1), str(sep), str(part2)) == ("hello", ", ", "world")
        assert all(p.logits is None for p in (part1, sep, part2))
        assert all(p.originator == frozenset({"model8"}) for p in (part1, sep, part2))

    def test_formatting(self):
        s = lstr("Hello {}!")
        filled = s.format(lstr("world", originator="model9"))
        assert str(filled) == "Hello world!"
        assert filled.logits is None
        assert filled.originator == frozenset({"model9"})

    def test_repr(self):
        s = lstr("test", logits=np.array([1.0]), originator="model10")
        assert "test" in repr(s)
        assert "model10" in repr(s.originator)


# Run the tests
if __name__ == "__main__":
    pytest.main()
