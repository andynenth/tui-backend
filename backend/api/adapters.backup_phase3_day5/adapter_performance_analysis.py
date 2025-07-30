#!/usr/bin/env python3
"""
Analyze adapter performance bottlenecks
"""

import asyncio
import time
import cProfile
import pstats
from io import StringIO


async def baseline_async():
    """Baseline async function"""
    return {"result": "ok"}


def baseline_sync():
    """Baseline sync function"""
    return {"result": "ok"}


async def test_async_overhead():
    """Test pure async function call overhead"""
    iterations = 100000

    print("\n🔬 Async Function Call Overhead Analysis\n")

    # Test 1: Direct sync return
    start = time.time()
    for _ in range(iterations):
        result = {"result": "ok"}
    sync_time = time.time() - start
    print(f"Direct sync return: {sync_time:.3f}s for {iterations} calls")
    print(f"  Per call: {sync_time/iterations*1000000:.2f} microseconds")

    # Test 2: Sync function call
    start = time.time()
    for _ in range(iterations):
        result = baseline_sync()
    sync_func_time = time.time() - start
    overhead = ((sync_func_time - sync_time) / sync_time) * 100
    print(f"\nSync function call: {sync_func_time:.3f}s (+{overhead:.1f}% overhead)")
    print(f"  Per call: {sync_func_time/iterations*1000000:.2f} microseconds")

    # Test 3: Async function call
    start = time.time()
    for _ in range(iterations):
        await baseline_async()
    async_time = time.time() - start
    overhead = ((async_time - sync_time) / sync_time) * 100
    print(f"\nAsync function call: {async_time:.3f}s (+{overhead:.1f}% overhead)")
    print(f"  Per call: {async_time/iterations*1000000:.2f} microseconds")

    # Test 4: Dict lookup
    test_dict = {"ping": baseline_sync, "pong": baseline_sync}
    start = time.time()
    for _ in range(iterations):
        func = test_dict.get("ping")
        if func:
            result = func()
    dict_lookup_time = time.time() - start
    overhead = ((dict_lookup_time - sync_time) / sync_time) * 100
    print(
        f"\nDict lookup + sync call: {dict_lookup_time:.3f}s (+{overhead:.1f}% overhead)"
    )
    print(f"  Per call: {dict_lookup_time/iterations*1000000:.2f} microseconds")

    # Test 5: Multiple async calls (simulating adapter pattern)
    async def adapter_simulation(message):
        action = message.get("action")
        if action == "ping":
            return await baseline_async()
        return None

    start = time.time()
    test_msg = {"action": "ping"}
    for _ in range(iterations):
        await adapter_simulation(test_msg)
    adapter_time = time.time() - start
    overhead = ((adapter_time - sync_time) / sync_time) * 100
    print(
        f"\nAdapter pattern simulation: {adapter_time:.3f}s (+{overhead:.1f}% overhead)"
    )
    print(f"  Per call: {adapter_time/iterations*1000000:.2f} microseconds")

    print("\n📊 Summary")
    print("=" * 50)
    print(f"Base operation:     {sync_time/iterations*1000000:.2f} μs")
    print(
        f"Sync function:      +{(sync_func_time-sync_time)/iterations*1000000:.2f} μs overhead"
    )
    print(
        f"Async function:     +{(async_time-sync_time)/iterations*1000000:.2f} μs overhead"
    )
    print(
        f"Dict lookup:        +{(dict_lookup_time-sync_time)/iterations*1000000:.2f} μs overhead"
    )
    print(
        f"Adapter pattern:    +{(adapter_time-sync_time)/iterations*1000000:.2f} μs overhead"
    )

    # Conclusion
    print("\n💡 Key Findings:")
    print(
        f"- Async function calls add ~{(async_time-sync_func_time)/iterations*1000000:.1f} μs per call"
    )
    print(
        f"- Dict lookups add ~{(dict_lookup_time-sync_func_time-sync_time)/iterations*1000000:.1f} μs per call"
    )
    print(
        f"- For 40,000 messages, async overhead alone is ~{(async_time-sync_func_time)*40:.0f}ms"
    )
    print("\n🎯 To achieve 20% overhead target:")
    print("- Need to eliminate async calls in hot path")
    print("- Consider sync adapters for simple operations")
    print("- Use async only for I/O-bound operations")


if __name__ == "__main__":
    asyncio.run(test_async_overhead())
