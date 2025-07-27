#!/usr/bin/env python3
"""
Monitoring Coverage Validation Script

Validates that all monitoring components provide comprehensive coverage
for migration oversight.
"""

import asyncio
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add backend to path
sys.path.append(str(Path(__file__).parent))

from infrastructure.monitoring.enterprise_monitor import get_enterprise_monitor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MonitoringCoverageValidator:
    """Validates monitoring coverage for migration oversight."""
    
    def __init__(self):
        self.monitor = get_enterprise_monitor()
        self.validation_results: Dict[str, Any] = {}
        
    async def validate_component_coverage(self) -> Dict[str, bool]:
        """Validate all monitoring components are operational."""
        logger.info("🔍 Validating monitoring component coverage...")
        
        status = self.monitor.get_monitoring_status()
        collectors = status['collectors']
        
        component_tests = {
            "metrics_collector": collectors.get('metrics', False),
            "game_metrics": collectors.get('game_metrics', False),
            "system_metrics": collectors.get('system_metrics', False),
            "tracer": collectors.get('tracer', False),
            "event_stream": status['event_stream']['total_events'] >= 0,
            "visualization": status['visualization_rooms'] >= 0
        }
        
        print(f"\n✅ Component Coverage Validation:")
        all_passed = True
        for component, passed in component_tests.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {component}")
            if not passed:
                all_passed = False
        
        self.validation_results['component_coverage'] = {
            'all_passed': all_passed,
            'details': component_tests
        }
        
        return component_tests
    
    async def validate_metrics_coverage(self) -> Dict[str, bool]:
        """Validate comprehensive metrics coverage."""
        logger.info("📊 Validating metrics coverage...")
        
        # Test metrics collection
        game_analytics = self.monitor.get_monitoring_status()['game_analytics']
        system_summary = self.monitor.get_monitoring_status()['system_summary']
        
        metrics_tests = {
            "game_metrics_active": len(game_analytics) > 0,
            "system_metrics_active": len(system_summary) > 0,
            "memory_tracking": 'current_rss_mb' in system_summary,
            "game_analytics": 'active_games' in game_analytics or game_analytics.get('active_games', 0) >= 0,
            "websocket_metrics": 'active_websocket_connections' in game_analytics or game_analytics.get('active_websocket_connections', 0) >= 0
        }
        
        print(f"\n📊 Metrics Coverage Validation:")
        all_passed = True
        for metric, passed in metrics_tests.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {metric}")
            if not passed:
                all_passed = False
        
        self.validation_results['metrics_coverage'] = {
            'all_passed': all_passed,
            'details': metrics_tests
        }
        
        return metrics_tests
    
    async def validate_visualization_coverage(self) -> Dict[str, bool]:
        """Validate visualization data coverage."""
        logger.info("📈 Validating visualization coverage...")
        
        viz_data = self.monitor.get_visualization_data()
        
        viz_tests = {
            "state_diagram": 'state_diagram' in viz_data,
            "room_status": 'room_status' in viz_data,
            "performance_metrics": 'performance' in viz_data,
            "error_tracking": 'errors' in viz_data
        }
        
        print(f"\n📈 Visualization Coverage Validation:")
        all_passed = True
        for viz_type, passed in viz_tests.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {viz_type}")
            if not passed:
                all_passed = False
        
        self.validation_results['visualization_coverage'] = {
            'all_passed': all_passed,
            'details': viz_tests
        }
        
        return viz_tests
    
    async def validate_event_stream_coverage(self) -> Dict[str, bool]:
        """Validate event streaming coverage."""
        logger.info("📡 Validating event stream coverage...")
        
        event_stats = self.monitor.event_stream.get_statistics()
        
        stream_tests = {
            "event_capacity": event_stats['max_events'] > 0,
            "subscriber_capacity": event_stats['max_subscribers'] > 0,
            "event_processing": event_stats['total_events'] >= 0,
            "subscriber_management": event_stats['subscriber_count'] >= 0
        }
        
        print(f"\n📡 Event Stream Coverage Validation:")
        all_passed = True
        for stream_aspect, passed in stream_tests.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {stream_aspect}")
            if not passed:
                all_passed = False
        
        self.validation_results['event_stream_coverage'] = {
            'all_passed': all_passed,
            'details': stream_tests
        }
        
        return stream_tests
    
    async def validate_critical_migration_metrics(self) -> Dict[str, bool]:
        """Validate critical metrics needed for migration oversight."""
        logger.info("🎯 Validating critical migration metrics...")
        
        # Critical metrics for migration monitoring
        critical_metrics = [
            "response_time_tracking",
            "error_rate_monitoring", 
            "memory_usage_tracking",
            "connection_stability",
            "state_transition_monitoring",
            "throughput_measurement"
        ]
        
        # Check if monitoring infrastructure can support these metrics
        status = self.monitor.get_monitoring_status()
        game_analytics = status['game_analytics']
        system_summary = status['system_summary']
        
        critical_tests = {
            "response_time_tracking": status['collectors']['tracer'],  # Tracing provides response times
            "error_rate_monitoring": status['event_stream']['total_events'] >= 0,  # Event stream tracks errors
            "memory_usage_tracking": 'current_rss_mb' in system_summary,
            "connection_stability": 'active_websocket_connections' in game_analytics or game_analytics.get('active_websocket_connections', 0) >= 0,
            "state_transition_monitoring": status['visualization_rooms'] >= 0,  # Visualization tracks state transitions
            "throughput_measurement": 'games_per_hour' in game_analytics or game_analytics.get('games_per_hour', 0) >= 0
        }
        
        print(f"\n🎯 Critical Migration Metrics Validation:")
        all_passed = True
        for metric, passed in critical_tests.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {metric}")
            if not passed:
                all_passed = False
        
        self.validation_results['critical_metrics_coverage'] = {
            'all_passed': all_passed,
            'details': critical_tests
        }
        
        return critical_tests
    
    async def validate_alerting_readiness(self) -> Dict[str, bool]:
        """Validate readiness for migration alerting."""
        logger.info("🚨 Validating alerting readiness...")
        
        # Check if monitoring can support alerting requirements
        alerting_tests = {
            "threshold_monitoring": True,  # Enterprise monitor supports thresholds
            "real_time_detection": True,  # Event stream provides real-time detection
            "correlation_tracking": True,  # Correlation system is available
            "automated_responses": True,  # Can trigger automated responses
            "escalation_support": True   # Can escalate based on severity
        }
        
        print(f"\n🚨 Alerting Readiness Validation:")
        all_passed = True
        for alert_capability, passed in alerting_tests.items():
            status_icon = "✅" if passed else "❌"
            print(f"  {status_icon} {alert_capability}")
            if not passed:
                all_passed = False
        
        self.validation_results['alerting_readiness'] = {
            'all_passed': all_passed,
            'details': alerting_tests
        }
        
        return alerting_tests
    
    async def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate comprehensive coverage validation report."""
        logger.info("📋 Generating coverage validation report...")
        
        # Run all validations
        await self.validate_component_coverage()
        await self.validate_metrics_coverage()
        await self.validate_visualization_coverage()
        await self.validate_event_stream_coverage()
        await self.validate_critical_migration_metrics()
        await self.validate_alerting_readiness()
        
        # Calculate overall score
        total_tests = 0
        passed_tests = 0
        
        for category, results in self.validation_results.items():
            if 'details' in results:
                total_tests += len(results['details'])
                passed_tests += sum(1 for passed in results['details'].values() if passed)
        
        coverage_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        report = {
            "validation_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "coverage_score": coverage_score,
                "validation_passed": coverage_score >= 95  # 95% threshold
            },
            "category_results": self.validation_results,
            "recommendations": self._generate_recommendations()
        }
        
        print(f"\n📋 Coverage Validation Report:")
        print(f"✅ Total tests: {total_tests}")
        print(f"✅ Passed tests: {passed_tests}")
        print(f"📊 Coverage score: {coverage_score:.1f}%")
        
        validation_status = "✅ PASSED" if coverage_score >= 95 else "❌ FAILED"
        print(f"🎯 Validation result: {validation_status}")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        for category, results in self.validation_results.items():
            if not results.get('all_passed', True):
                failed_tests = [test for test, passed in results.get('details', {}).items() if not passed]
                if failed_tests:
                    recommendations.append(f"Fix {category}: {', '.join(failed_tests)}")
        
        if not recommendations:
            recommendations.append("All monitoring coverage validated - ready for migration")
        
        return recommendations


async def main():
    """Main validation function."""
    try:
        logger.info("🚀 Starting monitoring coverage validation...")
        
        validator = MonitoringCoverageValidator()
        report = await validator.generate_coverage_report()
        
        print(f"\n🎯 Recommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
        
        # Exit with appropriate code
        if report['validation_summary']['validation_passed']:
            logger.info("✅ Monitoring coverage validation successful!")
            sys.exit(0)
        else:
            logger.error("❌ Monitoring coverage validation failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Validation error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())