"""
Tests for Simpy's real-time behavior.

"""
import time
try:
    # Python >= 3.3
    from time import perf_counter
except ImportError:
    # Python < 3.3
    from time import time as perf_counter

import pytest

from simpy.rt import RealtimeEnvironment, simulate


def process(env, log, sleep, timeout=1):
    """Test process."""
    while True:
        time.sleep(sleep)
        yield env.timeout(timeout)
        log.append(env.now)


def check_duration(real, expected):
    return expected <= real < (expected + 0.02)


@pytest.mark.parametrize('factor', [0.1, 0.05, 0.15])
def test_rt(log, factor):
    """Basic tests for simulate()."""
    env = RealtimeEnvironment(factor=factor)
    env.start(process(env, log, 0.01, 1))
    env.start(process(env, log, 0.02, 1))

    start = perf_counter()
    simulate(env, 2)
    duration = perf_counter() - start

    assert check_duration(duration, 2 * factor)
    assert log == [1, 1]


def test_rt_multiple_call(log):
    """Test multiple calls to simulate()."""
    env = RealtimeEnvironment(factor=0.05)
    env.start(process(env, log, 0.01, 2))
    env.start(process(env, log, 0.01, 3))

    start = perf_counter()
    simulate(env, 5)
    duration = perf_counter() - start

    # assert almost_equal(duration, 0.2)
    assert check_duration(duration, 5 * 0.05)
    assert log == [2, 3, 4]

    start = perf_counter()
    simulate(env, 12)
    duration = perf_counter() - start

    assert check_duration(duration, 7 * 0.05)
    assert log == [2, 3, 4, 6, 6, 8, 9, 10]


def test_rt_slow_sim_default_behavior(log):
    """By default, SimPy should raise an error if a simulation is too
    slow for the selected real-time factor."""
    env = RealtimeEnvironment(factor=0.05)
    env.start(process(env, log, 0.1, 1))

    err = pytest.raises(RuntimeError, simulate, env, 3)
    assert 'Simulation too slow for real time (0.05' in err.value.args[0]
    assert log == []


def test_rt_slow_sim_no_error(log):
    """Test ignoring slow simulations."""
    env = RealtimeEnvironment(factor=0.05, strict=False)
    env.start(process(env, log, 0.1, 1))

    start = perf_counter()
    simulate(env, 2)
    duration = perf_counter() - start

    assert check_duration(duration, 2 * 0.1)
    assert log == [1]


def test_rt_illegal_until():
    """Test illegal value for *until*."""
    env = RealtimeEnvironment()
    err = pytest.raises(ValueError, simulate, env, -1)
    assert err.value.args[0] == ('until(=-1.0) should be > the current '
            'simulation time.')