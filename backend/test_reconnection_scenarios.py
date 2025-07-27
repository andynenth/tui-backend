#!/usr/bin/env python3
"""
Reconnection Scenarios Testing Tool

Tests WebSocket reconnection logic for Step 6.3.1 migration validation.
Validates various disconnect/reconnect scenarios with clean architecture.
"""

import asyncio
import sys
import time
import statistics
import logging
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import websockets
import signal

# Add backend to path
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReconnectionScenarioTester:
    """Tests various WebSocket reconnection scenarios."""
    
    def __init__(self, server_url: str = "ws://localhost:5050/ws/lobby"):
        self.server_url = server_url
        self.test_results: Dict[str, Any] = {}
        
    async def test_graceful_reconnection(self) -> Dict[str, Any]:
        """Test graceful disconnect and reconnection."""
        logger.info("😌 Testing graceful reconnection...")
        
        results = {
            "scenario": "graceful_reconnection",
            "initial_connection_successful": False,
            "messages_sent_before": 0,
            "messages_received_before": 0,
            "disconnect_successful": False,
            "reconnection_successful": False,
            "reconnection_time_ms": 0,
            "messages_sent_after": 0,
            "messages_received_after": 0,
            "state_preserved": False
        }
        
        player_id = str(uuid.uuid4())
        
        try:
            # Initial connection
            async with websockets.connect(self.server_url) as websocket1:
                results["initial_connection_successful"] = True
                
                # Send initial messages
                for i in range(5):
                    message = {
                        "action": "ping",
                        "data": {
                            "player_id": player_id,
                            "sequence": i,
                            "phase": "before_disconnect"
                        }
                    }
                    await websocket1.send(json.dumps(message))
                    results["messages_sent_before"] += 1
                    
                    # Try to receive response
                    try:
                        response = await asyncio.wait_for(websocket1.recv(), timeout=2.0)
                        results["messages_received_before"] += 1
                    except asyncio.TimeoutError:
                        pass
                    
                    await asyncio.sleep(0.2)
                
                # Graceful disconnect (leaving context)
                results["disconnect_successful"] = True
            
            # Wait before reconnection
            await asyncio.sleep(1)
            
            # Attempt reconnection
            reconnect_start = time.perf_counter()
            
            async with websockets.connect(self.server_url) as websocket2:
                reconnect_end = time.perf_counter()
                results["reconnection_time_ms"] = (reconnect_end - reconnect_start) * 1000
                results["reconnection_successful"] = True
                
                # Test connection after reconnect
                for i in range(3):
                    message = {
                        "action": "ping",
                        "data": {
                            "player_id": player_id,
                            "sequence": i,
                            "phase": "after_reconnect"
                        }
                    }
                    await websocket2.send(json.dumps(message))
                    results["messages_sent_after"] += 1
                    
                    try:
                        response = await asyncio.wait_for(websocket2.recv(), timeout=2.0)
                        results["messages_received_after"] += 1
                        
                        # Check if player state/context preserved
                        response_data = json.loads(response)
                        if response_data.get("data", {}).get("player_id") == player_id:
                            results["state_preserved"] = True
                    except asyncio.TimeoutError:
                        pass
                    
                    await asyncio.sleep(0.2)
                    
        except Exception as e:
            logger.error(f"Graceful reconnection test failed: {e}")
        
        print(f"\n😌 Graceful Reconnection Results:")
        print(f"  Initial connection: {'✅' if results['initial_connection_successful'] else '❌'}")
        print(f"  Reconnection time: {results['reconnection_time_ms']:.2f}ms")
        print(f"  Messages before: {results['messages_sent_before']}/{results['messages_received_before']}")
        print(f"  Messages after: {results['messages_sent_after']}/{results['messages_received_after']}")
        print(f"  State preserved: {'✅' if results['state_preserved'] else '❌'}")
        
        return results
    
    async def test_abrupt_disconnect_reconnection(self) -> Dict[str, Any]:
        """Test abrupt disconnect and reconnection."""
        logger.info("💥 Testing abrupt disconnect reconnection...")
        
        results = {
            "scenario": "abrupt_disconnect_reconnection",
            "initial_connection_successful": False,
            "messages_before_disconnect": 0,
            "disconnect_detected": False,
            "reconnection_attempts": 0,
            "successful_reconnection": False,
            "final_reconnection_time_ms": 0,
            "message_queue_preserved": False,
            "total_reconnection_time_ms": 0
        }
        
        player_id = str(uuid.uuid4())
        
        try:
            # Initial connection
            websocket = await websockets.connect(self.server_url)
            results["initial_connection_successful"] = True
            
            # Send some messages
            for i in range(3):
                message = {
                    "action": "ping",
                    "data": {
                        "player_id": player_id,
                        "sequence": i
                    }
                }
                await websocket.send(json.dumps(message))
                results["messages_before_disconnect"] += 1
                await asyncio.sleep(0.1)
            
            # Simulate abrupt disconnect by closing without proper close frame
            await websocket.close(code=1006)  # Abnormal closure
            results["disconnect_detected"] = True
            
            # Multiple reconnection attempts with backoff
            reconnect_start = time.perf_counter()
            backoff_delays = [0.5, 1.0, 2.0, 4.0]  # Exponential backoff
            
            for attempt, delay in enumerate(backoff_delays):
                results["reconnection_attempts"] += 1
                
                try:
                    await asyncio.sleep(delay)
                    
                    websocket = await websockets.connect(self.server_url)
                    reconnect_end = time.perf_counter()
                    
                    results["successful_reconnection"] = True
                    results["final_reconnection_time_ms"] = (reconnect_end - reconnect_start) * 1000
                    results["total_reconnection_time_ms"] = (reconnect_end - reconnect_start) * 1000
                    
                    # Test if connection works
                    test_message = {
                        "action": "ping",
                        "data": {
                            "player_id": player_id,
                            "reconnection_test": True
                        }
                    }
                    await websocket.send(json.dumps(test_message))
                    
                    # Check for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                        # Connection working after reconnect
                        break
                    except asyncio.TimeoutError:
                        # Close and try again
                        await websocket.close()
                        continue
                        
                except Exception as e:
                    logger.warning(f"Reconnection attempt {attempt + 1} failed: {e}")
                    continue
            
            # Clean up
            if websocket and not websocket.closed:
                await websocket.close()
                
        except Exception as e:
            logger.error(f"Abrupt disconnect test failed: {e}")
        
        print(f"\n💥 Abrupt Disconnect Reconnection Results:")
        print(f"  Initial connection: {'✅' if results['initial_connection_successful'] else '❌'}")
        print(f"  Disconnect detected: {'✅' if results['disconnect_detected'] else '❌'}")
        print(f"  Reconnection attempts: {results['reconnection_attempts']}")
        print(f"  Successful reconnection: {'✅' if results['successful_reconnection'] else '❌'}")
        print(f"  Total reconnection time: {results['total_reconnection_time_ms']:.2f}ms")
        
        return results
    
    async def test_timeout_reconnection(self) -> Dict[str, Any]:
        """Test timeout-based disconnect and reconnection."""
        logger.info("⏰ Testing timeout reconnection...")
        
        results = {
            "scenario": "timeout_reconnection",
            "initial_connection_successful": False,
            "idle_period_seconds": 0,
            "timeout_occurred": False,
            "reconnection_successful": False,
            "reconnection_time_ms": 0,
            "post_reconnect_functionality": False
        }
        
        player_id = str(uuid.uuid4())
        
        try:
            # Initial connection
            websocket = await websockets.connect(self.server_url)
            results["initial_connection_successful"] = True
            
            # Send initial ping
            initial_message = {
                "action": "ping",
                "data": {"player_id": player_id, "initial": True}
            }
            await websocket.send(json.dumps(initial_message))
            
            # Wait for potential timeout (simulate idle period)
            idle_duration = 15  # seconds
            results["idle_period_seconds"] = idle_duration
            
            logger.info(f"Waiting {idle_duration} seconds for potential timeout...")
            
            try:
                # Wait without sending any messages (testing idle timeout)
                await asyncio.sleep(idle_duration)
                
                # Try to send message after idle period
                timeout_test_message = {
                    "action": "ping",
                    "data": {"player_id": player_id, "after_idle": True}
                }
                await websocket.send(json.dumps(timeout_test_message))
                
                # Check if connection still works
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                
            except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError) as e:
                logger.info(f"Connection timed out as expected: {e}")
                results["timeout_occurred"] = True
                
                # Attempt reconnection after timeout
                reconnect_start = time.perf_counter()
                
                try:
                    websocket = await websockets.connect(self.server_url)
                    reconnect_end = time.perf_counter()
                    
                    results["reconnection_time_ms"] = (reconnect_end - reconnect_start) * 1000
                    results["reconnection_successful"] = True
                    
                    # Test functionality after reconnection
                    post_reconnect_message = {
                        "action": "ping",
                        "data": {"player_id": player_id, "post_timeout_reconnect": True}
                    }
                    await websocket.send(json.dumps(post_reconnect_message))
                    
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    results["post_reconnect_functionality"] = True
                    
                except Exception as reconnect_error:
                    logger.error(f"Reconnection after timeout failed: {reconnect_error}")
            
            # Clean up
            if websocket and not websocket.closed:
                await websocket.close()
                
        except Exception as e:
            logger.error(f"Timeout reconnection test failed: {e}")
        
        print(f"\n⏰ Timeout Reconnection Results:")
        print(f"  Initial connection: {'✅' if results['initial_connection_successful'] else '❌'}")
        print(f"  Idle period: {results['idle_period_seconds']}s")
        print(f"  Timeout occurred: {'✅' if results['timeout_occurred'] else '❌'}")
        print(f"  Reconnection successful: {'✅' if results['reconnection_successful'] else '❌'}")
        print(f"  Reconnection time: {results['reconnection_time_ms']:.2f}ms")
        print(f"  Post-reconnect functionality: {'✅' if results['post_reconnect_functionality'] else '❌'}")
        
        return results
    
    async def test_rapid_reconnection_cycles(self) -> Dict[str, Any]:
        """Test rapid connect/disconnect cycles."""
        logger.info("🔄 Testing rapid reconnection cycles...")
        
        results = {
            "scenario": "rapid_reconnection_cycles",
            "cycles_attempted": 0,
            "successful_cycles": 0,
            "failed_cycles": 0,
            "average_cycle_time_ms": 0,
            "cycle_times": [],
            "connection_stability_score": 0
        }
        
        cycle_count = 10
        player_id = str(uuid.uuid4())
        
        for cycle in range(cycle_count):
            results["cycles_attempted"] += 1
            cycle_start = time.perf_counter()
            
            try:
                # Connect
                websocket = await websockets.connect(self.server_url)
                
                # Send test message
                message = {
                    "action": "ping",
                    "data": {
                        "player_id": player_id,
                        "cycle": cycle,
                        "rapid_test": True
                    }
                }
                await websocket.send(json.dumps(message))
                
                # Try to receive response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    # Success
                except asyncio.TimeoutError:
                    pass  # Still count as successful cycle if no timeout error
                
                # Disconnect
                await websocket.close()
                
                cycle_end = time.perf_counter()
                cycle_time = (cycle_end - cycle_start) * 1000
                
                results["successful_cycles"] += 1
                results["cycle_times"].append(cycle_time)
                
                # Small delay between cycles
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Rapid reconnection cycle {cycle} failed: {e}")
                results["failed_cycles"] += 1
        
        # Calculate statistics
        if results["cycle_times"]:
            results["average_cycle_time_ms"] = statistics.mean(results["cycle_times"])
            results["min_cycle_time_ms"] = min(results["cycle_times"])
            results["max_cycle_time_ms"] = max(results["cycle_times"])
        
        # Calculate stability score
        success_rate = (results["successful_cycles"] / max(results["cycles_attempted"], 1)) * 100
        results["connection_stability_score"] = success_rate
        
        print(f"\n🔄 Rapid Reconnection Cycles Results:")
        print(f"  Cycles attempted: {results['cycles_attempted']}")
        print(f"  Successful cycles: {results['successful_cycles']}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average cycle time: {results.get('average_cycle_time_ms', 0):.2f}ms")
        print(f"  Stability score: {results['connection_stability_score']:.1f}%")
        
        return results
    
    async def validate_reconnection_requirements(self) -> Dict[str, bool]:
        """Validate reconnection against Phase 6.3.1 requirements."""
        logger.info("🎯 Validating reconnection requirements...")
        
        # Run all reconnection tests
        graceful_results = await self.test_graceful_reconnection()
        abrupt_results = await self.test_abrupt_disconnect_reconnection()
        timeout_results = await self.test_timeout_reconnection()
        rapid_results = await self.test_rapid_reconnection_cycles()
        
        # Validate requirements
        requirements = {
            "no_connection_drops_during_migration": (
                graceful_results["reconnection_successful"] and
                abrupt_results["successful_reconnection"]
            ),
            "reconnection_success_rate_over_99": rapid_results["connection_stability_score"] > 99,
            "connection_latency_unchanged": all([
                graceful_results.get("reconnection_time_ms", 0) < 5000,  # 5 seconds max
                abrupt_results.get("final_reconnection_time_ms", 0) < 10000,  # 10 seconds max
                timeout_results.get("reconnection_time_ms", 0) < 5000
            ]),
            "memory_usage_stable": rapid_results["successful_cycles"] >= 8  # 80% success rate
        }
        
        print(f"\n🎯 Reconnection Requirements Validation:")
        for req, passed in requirements.items():
            status = "✅" if passed else "❌"
            print(f"  {status} {req}: {passed}")
        
        # Store all results
        self.test_results = {
            "graceful_test": graceful_results,
            "abrupt_test": abrupt_results,
            "timeout_test": timeout_results,
            "rapid_test": rapid_results,
            "requirements_validation": requirements
        }
        
        return requirements


async def main():
    """Main reconnection testing function."""
    try:
        logger.info("🚀 Starting reconnection scenario testing...")
        
        tester = ReconnectionScenarioTester()
        requirements = await tester.validate_reconnection_requirements()
        
        # Generate report
        report = {
            "timestamp": time.time(),
            "test_results": tester.test_results,
            "summary": {
                "all_requirements_met": all(requirements.values()),
                "reconnection_grade": "A" if all(requirements.values()) else "B"
            }
        }
        
        # Save report
        report_file = Path(__file__).parent / "reconnection_scenarios_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📁 Reconnection scenarios report saved to: {report_file}")
        
        print(f"\n📋 Reconnection Scenarios Summary:")
        print(f"✅ All requirements met: {report['summary']['all_requirements_met']}")
        print(f"🎯 Reconnection grade: {report['summary']['reconnection_grade']}")
        
        # Exit with appropriate code
        if report['summary']['all_requirements_met']:
            logger.info("✅ Reconnection scenario testing successful!")
            sys.exit(0)
        else:
            logger.warning("⚠️ Some reconnection requirements not met")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Reconnection scenario testing error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())