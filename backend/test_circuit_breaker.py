#!/usr/bin/env python3
"""
Test Circuit Breaker Implementation

Validates that circuit breakers properly prevent infinite loops and system overload.
"""

import asyncio
import time
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine.circuit_breaker import get_circuit, CircuitConfig, CircuitBreakerException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_basic_circuit_breaker():
    """Test basic circuit breaker functionality"""
    logger.info("🔌 Testing basic circuit breaker functionality...")
    
    # Create a test circuit with low thresholds
    config = CircuitConfig(
        failure_threshold=3,
        success_threshold=2,
        timeout=2.0,
        max_operations_per_second=5
    )
    circuit = get_circuit("test_basic", config)
    
    # Test successful operations
    for i in range(5):
        try:
            async with circuit:
                logger.info(f"✅ Operation {i} succeeded")
        except Exception as e:
            logger.error(f"❌ Operation {i} failed: {e}")
    
    stats = circuit.get_stats()
    logger.info(f"📊 Stats after success: {stats}")
    
    # Test failures
    for i in range(5):
        try:
            async with circuit:
                if i < 3:  # First 3 fail
                    raise ValueError(f"Simulated failure {i}")
                logger.info(f"✅ Operation {i} succeeded")
        except CircuitBreakerException as e:
            logger.info(f"🚨 Circuit breaker blocked operation {i}: {e}")
        except ValueError:
            logger.info(f"⚠️ Operation {i} failed (expected)")
    
    final_stats = circuit.get_stats()
    logger.info(f"📊 Final stats: {final_stats}")
    
    return final_stats["state"] == "open"

async def test_rate_limiting():
    """Test rate limiting functionality"""
    logger.info("⚡ Testing rate limiting...")
    
    config = CircuitConfig(
        max_operations_per_second=3,  # Very low rate limit
        failure_threshold=10  # High failure threshold so rate limit triggers first
    )
    circuit = get_circuit("test_rate", config)
    
    blocked_count = 0
    success_count = 0
    
    # Try to exceed rate limit
    for i in range(10):
        try:
            async with circuit:
                success_count += 1
                logger.info(f"✅ Operation {i} succeeded")
        except CircuitBreakerException as e:
            blocked_count += 1
            logger.info(f"🚨 Operation {i} rate limited: {e}")
        
        await asyncio.sleep(0.1)  # Small delay
    
    logger.info(f"📊 Rate limit test: {success_count} succeeded, {blocked_count} blocked")
    return blocked_count > 0

async def test_recovery():
    """Test circuit breaker recovery"""
    logger.info("🔄 Testing circuit breaker recovery...")
    
    config = CircuitConfig(
        failure_threshold=2,
        success_threshold=2,
        timeout=1.0  # Short timeout for quick recovery
    )
    circuit = get_circuit("test_recovery", config)
    
    # Force circuit to open
    for i in range(3):
        try:
            async with circuit:
                raise ValueError(f"Failure {i}")
        except (ValueError, CircuitBreakerException):
            pass
    
    logger.info(f"🔴 Circuit state after failures: {circuit.get_stats()['state']}")
    
    # Wait for timeout
    await asyncio.sleep(1.5)
    
    # Try recovery
    recovery_attempts = 0
    for i in range(5):
        try:
            async with circuit:
                recovery_attempts += 1
                logger.info(f"✅ Recovery attempt {i} succeeded")
        except CircuitBreakerException as e:
            logger.info(f"🚨 Recovery attempt {i} blocked: {e}")
    
    final_state = circuit.get_stats()["state"]
    logger.info(f"🟢 Circuit state after recovery: {final_state}")
    
    return final_state == "closed" and recovery_attempts >= 2

async def test_infinite_loop_prevention():
    """Test that circuit breaker prevents infinite loops"""
    logger.info("🔁 Testing infinite loop prevention...")
    
    config = CircuitConfig(
        max_operations_per_second=10,
        failure_threshold=5,
        timeout=1.0
    )
    circuit = get_circuit("test_loop", config)
    
    # Simulate rapid operations that could create infinite loop
    operations = 0
    blocked = 0
    start_time = time.time()
    
    while time.time() - start_time < 2.0:  # Run for 2 seconds
        try:
            async with circuit:
                operations += 1
                # Simulate some work
                await asyncio.sleep(0.01)
        except CircuitBreakerException:
            blocked += 1
    
    total_ops = operations + blocked
    ops_per_second = total_ops / 2.0
    
    logger.info(f"📊 Loop prevention: {operations} ops, {blocked} blocked, {ops_per_second:.1f} ops/sec")
    
    # Should be limited to reasonable rate
    return ops_per_second < 50  # Should be well under limit due to rate limiting

async def main():
    """Run all circuit breaker tests"""
    logger.info("🚀 Starting circuit breaker tests...")
    
    tests = [
        ("Basic Functionality", test_basic_circuit_breaker),
        ("Rate Limiting", test_rate_limiting),
        ("Recovery", test_recovery),
        ("Infinite Loop Prevention", test_infinite_loop_prevention)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running test: {test_name}")
        try:
            result = await test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: CRASHED - {e}")
            results[test_name] = False
    
    # Summary
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🎯 CIRCUIT BREAKER TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"✅ Passed: {passed}/{total}")
    logger.info(f"❌ Failed: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED - Circuit breakers working!")
        sys.exit(0)
    else:
        logger.error("💥 SOME TESTS FAILED - Circuit breakers need attention!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())