from unittest.mock import Mock, patch

import pytest
from cashews.backends.interface import Backend
from cashews.wrapper import Cache


@pytest.fixture()
def cache():
    _cache = Cache()
    _cache._disable = False
    _cache._target = Mock(wraps=Backend())
    return _cache


def test_setup(cache):
    backend = Mock()
    cache._target = None
    with patch("cashews.wrapper.Memory", backend):
        cache.setup("mem://localhost?test=1")
    backend.assert_called_with(test=1)


@pytest.mark.asyncio
async def test_init_disable(cache):
    backend = Mock(wraps=Backend())
    with patch("cashews.wrapper.Memory", Mock(return_value=backend)):
        await cache.init("mem://localhost?disable=1")
    backend.init.assert_not_called()
    assert cache.is_disable()


@pytest.mark.asyncio
async def test_disable_cmd(cache):
    await cache.init("mem://localhost", disable=("incr",))
    await cache.set("test", 10)
    await cache.incr("test")
    assert await cache.get("test") == 10

    cache.enable("incr")
    await cache.incr("test")
    assert await cache.get("test") == 11


@pytest.mark.asyncio
async def test_init(cache):
    backend = Mock(wraps=Backend())
    with patch("cashews.wrapper.Memory", Mock(return_value=backend)):
        await cache.init("mem://localhost")
    backend.init.assert_called_once()
    assert cache.is_enable()


@pytest.mark.asyncio
async def test_auto_init(cache):
    await cache.ping()
    cache._target.init.assert_called_once()


@pytest.mark.asyncio
async def test_hooks_call_ping(cache):
    hook = Mock(return_value=None)
    cache.execute_hooks = (hook,)
    cache.ping()
    hook.assert_not_called()
    await cache.ping()
    hook.assert_called_once_with("PING", "")


@pytest.mark.asyncio
async def test_hooks_call_clear(cache):
    hook = Mock(return_value=None)
    cache.execute_hooks = (hook,)
    await cache.clear()
    hook.assert_called_once_with("CLEAR", "")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "name", "attrs"),
    (
        ("get", "GET", ()),
        ("set", "SET", ("1",)),
        ("incr", "INCR", ()),
        ("delete", "DELETE", ()),
        ("expire", "EXPIRE", (10,)),
        ("set_lock", "LOCK", ("val", 10,)),
        ("unlock", "UNLOCK", ("val",)),
    ),
)
async def test_hooks_call_with_key(cache, method, name, attrs):
    hook = Mock(return_value=None)
    cache.execute_hooks = (hook,)
    await getattr(cache, method)("test", *attrs)
    hook.assert_called_once_with(name, "test")


@pytest.mark.asyncio
async def test_hooks_call_with_key_key_change(cache):
    async def hook(command, key):
        return "mykey"

    cache.execute_hooks = (hook,)

    await cache.get("test")
    cache._target.get.assert_called_once_with("mykey")
