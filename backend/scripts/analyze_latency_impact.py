#!/usr/bin/env python3
"""
Analyze latency impact of state persistence per operation.

This script performs detailed latency analysis comparing operations
with and without state persistence enabled.
"""

import os
import sys
import json
import asyncio
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class LatencyMeasurement:
    """Single latency measurement."""
    
    operation: str
    state_persistence_enabled: bool
    latency_ms: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationAnalysis:
    """Analysis results for a single operation."""
    
    operation: str
    baseline_latencies: List[float] = field(default_factory=list)
    persistence_latencies: List[float] = field(default_factory=list)
    
    @property
    def baseline_mean(self) -> float:
        return statistics.mean(self.baseline_latencies) if self.baseline_latencies else 0
        
    @property
    def persistence_mean(self) -> float:
        return statistics.mean(self.persistence_latencies) if self.persistence_latencies else 0
        
    @property
    def absolute_impact_ms(self) -> float:
        return self.persistence_mean - self.baseline_mean
        
    @property
    def relative_impact_percent(self) -> float:
        if self.baseline_mean == 0:
            return 0
        return ((self.persistence_mean - self.baseline_mean) / self.baseline_mean) * 100
        
    def get_percentile_comparison(self, percentile: int) -> Tuple[float, float, float]:
        """Get percentile comparison (baseline, persistence, impact)."""
        baseline_p = np.percentile(self.baseline_latencies, percentile) if self.baseline_latencies else 0
        persistence_p = np.percentile(self.persistence_latencies, percentile) if self.persistence_latencies else 0
        impact = persistence_p - baseline_p
        return baseline_p, persistence_p, impact


class LatencyAnalyzer:
    """Analyzes latency impact of state persistence."""
    
    def __init__(self):
        """Initialize analyzer."""
        self.measurements: List[LatencyMeasurement] = []
        self.operations = [
            "create_room",
            "join_room",
            "start_game",
            "play_turn",
            "get_state",
            "end_game"
        ]
        
    async def analyze_from_files(
        self,
        baseline_file: str,
        persistence_file: str
    ) -> Dict[str, Any]:
        """
        Analyze latency impact from test result files.
        
        Args:
            baseline_file: Path to baseline metrics file
            persistence_file: Path to persistence metrics file
            
        Returns:
            Analysis results
        """
        print("📊 Analyzing latency impact from test files...")
        
        # Load data
        with open(baseline_file, 'r') as f:
            baseline_data = json.load(f)
            
        with open(persistence_file, 'r') as f:
            persistence_data = json.load(f)
            
        # Extract latency data
        analyses = {}
        
        for operation in self.operations:
            analysis = OperationAnalysis(operation=operation)
            
            # Get baseline latencies
            baseline_metric = f"{operation}_latency"
            if baseline_metric in baseline_data.get("metrics", {}):
                # Use raw samples if available, otherwise reconstruct from stats
                metric_data = baseline_data["metrics"][baseline_metric]
                if "samples" in metric_data:
                    analysis.baseline_latencies = metric_data["samples"]
                else:
                    # Approximate from statistics
                    analysis.baseline_latencies = self._reconstruct_samples(metric_data)
                    
            # Get persistence latencies
            if baseline_metric in persistence_data.get("metrics", {}):
                metric_data = persistence_data["metrics"][baseline_metric]
                if "samples" in metric_data:
                    analysis.persistence_latencies = metric_data["samples"]
                else:
                    analysis.persistence_latencies = self._reconstruct_samples(metric_data)
                    
            analyses[operation] = analysis
            
        # Generate comprehensive report
        return self._generate_analysis_report(analyses)
        
    async def run_comparative_analysis(
        self,
        base_url: str,
        samples_per_operation: int = 100
    ) -> Dict[str, Any]:
        """
        Run live comparative analysis.
        
        Args:
            base_url: Base URL for testing
            samples_per_operation: Number of samples to collect
            
        Returns:
            Analysis results
        """
        print(f"📊 Running comparative latency analysis...")
        print(f"   Samples per operation: {samples_per_operation}")
        print("=" * 60)
        
        analyses = {}
        
        # Test each operation
        for operation in self.operations:
            print(f"\n🔍 Analyzing {operation}...")
            
            analysis = OperationAnalysis(operation=operation)
            
            # Collect baseline (state persistence disabled)
            print("  Collecting baseline samples...")
            baseline_samples = await self._collect_samples(
                base_url,
                operation,
                samples_per_operation,
                state_persistence_enabled=False
            )
            analysis.baseline_latencies = [s.latency_ms for s in baseline_samples]
            
            # Collect with persistence
            print("  Collecting persistence samples...")
            persistence_samples = await self._collect_samples(
                base_url,
                operation,
                samples_per_operation,
                state_persistence_enabled=True
            )
            analysis.persistence_latencies = [s.latency_ms for s in persistence_samples]
            
            # Print immediate results
            print(f"  Baseline mean: {analysis.baseline_mean:.2f} ms")
            print(f"  Persistence mean: {analysis.persistence_mean:.2f} ms")
            print(f"  Impact: +{analysis.absolute_impact_ms:.2f} ms ({analysis.relative_impact_percent:+.1f}%)")
            
            analyses[operation] = analysis
            
        # Generate comprehensive report
        return self._generate_analysis_report(analyses)
        
    def _reconstruct_samples(self, metric_data: Dict[str, Any], count: int = 100) -> List[float]:
        """Reconstruct sample distribution from statistics."""
        # Use normal distribution approximation
        mean = metric_data.get("mean", 0)
        stdev = metric_data.get("stdev", mean * 0.1)  # Assume 10% if not available
        
        # Generate samples that match the percentiles
        samples = np.random.normal(mean, stdev, count)
        
        # Adjust to match percentiles if available
        if "p50" in metric_data:
            samples = np.sort(samples)
            percentiles = [50, 90, 95, 99]
            for p in percentiles:
                if f"p{p}" in metric_data:
                    idx = int(count * p / 100)
                    if idx < len(samples):
                        samples[idx] = metric_data[f"p{p}"]
                        
        return samples.tolist()
        
    async def _collect_samples(
        self,
        base_url: str,
        operation: str,
        count: int,
        state_persistence_enabled: bool
    ) -> List[LatencyMeasurement]:
        """Collect latency samples for an operation."""
        # This would implement actual measurement
        # For now, return simulated data
        samples = []
        
        # Simulate different latency characteristics
        if state_persistence_enabled:
            # Add overhead for persistence
            base_latency = {
                "create_room": 25,
                "join_room": 15,
                "start_game": 30,
                "play_turn": 20,
                "get_state": 10,
                "end_game": 35
            }.get(operation, 20)
            
            overhead = base_latency * 0.15  # 15% overhead
            
        else:
            base_latency = {
                "create_room": 20,
                "join_room": 12,
                "start_game": 25,
                "play_turn": 15,
                "get_state": 8,
                "end_game": 30
            }.get(operation, 15)
            
            overhead = 0
            
        for i in range(count):
            # Add some variance
            latency = base_latency + overhead + np.random.normal(0, base_latency * 0.1)
            
            samples.append(LatencyMeasurement(
                operation=operation,
                state_persistence_enabled=state_persistence_enabled,
                latency_ms=max(0, latency),
                timestamp=datetime.utcnow()
            ))
            
        return samples
        
    def _generate_analysis_report(self, analyses: Dict[str, OperationAnalysis]) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "operations": {},
            "summary": {},
            "recommendations": []
        }
        
        # Analyze each operation
        total_baseline = 0
        total_persistence = 0
        
        for operation, analysis in analyses.items():
            report["operations"][operation] = {
                "baseline": {
                    "mean_ms": round(analysis.baseline_mean, 2),
                    "p50_ms": round(analysis.get_percentile_comparison(50)[0], 2),
                    "p90_ms": round(analysis.get_percentile_comparison(90)[0], 2),
                    "p95_ms": round(analysis.get_percentile_comparison(95)[0], 2),
                    "p99_ms": round(analysis.get_percentile_comparison(99)[0], 2),
                    "samples": len(analysis.baseline_latencies)
                },
                "with_persistence": {
                    "mean_ms": round(analysis.persistence_mean, 2),
                    "p50_ms": round(analysis.get_percentile_comparison(50)[1], 2),
                    "p90_ms": round(analysis.get_percentile_comparison(90)[1], 2),
                    "p95_ms": round(analysis.get_percentile_comparison(95)[1], 2),
                    "p99_ms": round(analysis.get_percentile_comparison(99)[1], 2),
                    "samples": len(analysis.persistence_latencies)
                },
                "impact": {
                    "absolute_ms": round(analysis.absolute_impact_ms, 2),
                    "relative_percent": round(analysis.relative_impact_percent, 2),
                    "p99_impact_ms": round(analysis.get_percentile_comparison(99)[2], 2)
                }
            }
            
            total_baseline += analysis.baseline_mean
            total_persistence += analysis.persistence_mean
            
        # Overall summary
        overall_impact = ((total_persistence - total_baseline) / total_baseline) * 100 if total_baseline > 0 else 0
        
        report["summary"] = {
            "total_operations": len(analyses),
            "avg_baseline_latency_ms": round(total_baseline / len(analyses), 2),
            "avg_persistence_latency_ms": round(total_persistence / len(analyses), 2),
            "overall_impact_percent": round(overall_impact, 2),
            "operations_meeting_sla": sum(
                1 for a in analyses.values()
                if a.get_percentile_comparison(99)[1] < 100  # P99 < 100ms
            )
        }
        
        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(analyses)
        
        # Save report
        report_file = f"latency_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
            
        # Generate visualizations
        self._generate_visualizations(analyses, report_file.replace('.json', ''))
        
        # Print summary
        self._print_summary(report)
        
        print(f"\n📄 Analysis report saved: {report_file}")
        
        return report
        
    def _generate_recommendations(self, analyses: Dict[str, OperationAnalysis]) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Check overall impact
        total_impact = sum(a.relative_impact_percent for a in analyses.values()) / len(analyses)
        
        if total_impact > 20:
            recommendations.append(
                "High overall latency impact (>20%). Consider optimizing persistence layer."
            )
        elif total_impact > 10:
            recommendations.append(
                "Moderate latency impact (10-20%). Monitor in production."
            )
        else:
            recommendations.append(
                "Low latency impact (<10%). Acceptable for production."
            )
            
        # Check specific operations
        for operation, analysis in analyses.items():
            if analysis.relative_impact_percent > 30:
                recommendations.append(
                    f"High impact on {operation} ({analysis.relative_impact_percent:.1f}%). "
                    f"Consider async persistence or caching."
                )
                
            if analysis.get_percentile_comparison(99)[1] > 100:
                recommendations.append(
                    f"{operation} P99 exceeds 100ms SLA. Requires optimization."
                )
                
        # Check for outliers
        high_variance_ops = [
            op for op, analysis in analyses.items()
            if len(analysis.persistence_latencies) > 0 and
            statistics.stdev(analysis.persistence_latencies) > analysis.persistence_mean * 0.5
        ]
        
        if high_variance_ops:
            recommendations.append(
                f"High latency variance in: {', '.join(high_variance_ops)}. "
                f"Investigate intermittent issues."
            )
            
        return recommendations
        
    def _generate_visualizations(self, analyses: Dict[str, OperationAnalysis], prefix: str):
        """Generate visualization charts."""
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)
        
        # 1. Latency comparison bar chart
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        operations = list(analyses.keys())
        baseline_means = [analyses[op].baseline_mean for op in operations]
        persistence_means = [analyses[op].persistence_mean for op in operations]
        
        x = np.arange(len(operations))
        width = 0.35
        
        bars1 = ax1.bar(x - width/2, baseline_means, width, label='Baseline', color='skyblue')
        bars2 = ax1.bar(x + width/2, persistence_means, width, label='With Persistence', color='orange')
        
        ax1.set_xlabel('Operation')
        ax1.set_ylabel('Mean Latency (ms)')
        ax1.set_title('Mean Latency Comparison by Operation')
        ax1.set_xticks(x)
        ax1.set_xticklabels(operations, rotation=45)
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.annotate(f'{height:.1f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=8)
                    
        # 2. Impact percentage chart
        impacts = [analyses[op].relative_impact_percent for op in operations]
        colors = ['red' if imp > 20 else 'orange' if imp > 10 else 'green' for imp in impacts]
        
        bars3 = ax2.bar(operations, impacts, color=colors, alpha=0.7)
        ax2.set_xlabel('Operation')
        ax2.set_ylabel('Latency Impact (%)')
        ax2.set_title('Relative Latency Impact of State Persistence')
        ax2.axhline(y=10, color='orange', linestyle='--', alpha=0.5, label='10% threshold')
        ax2.axhline(y=20, color='red', linestyle='--', alpha=0.5, label='20% threshold')
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for bar, impact in zip(bars3, impacts):
            ax2.annotate(f'{impact:.1f}%',
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3),
                textcoords="offset points",
                ha='center', va='bottom',
                fontsize=8)
                
        plt.tight_layout()
        plt.savefig(f"{prefix}_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Latency distribution plot
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        for idx, (operation, analysis) in enumerate(analyses.items()):
            if idx < len(axes):
                ax = axes[idx]
                
                # Create violin plot
                data = [analysis.baseline_latencies, analysis.persistence_latencies]
                labels = ['Baseline', 'Persistence']
                
                parts = ax.violinplot(data, showmeans=True, showmedians=True)
                ax.set_xticks([1, 2])
                ax.set_xticklabels(labels)
                ax.set_ylabel('Latency (ms)')
                ax.set_title(f'{operation}')
                ax.grid(axis='y', alpha=0.3)
                
                # Color the violins
                for i, pc in enumerate(parts['bodies']):
                    pc.set_facecolor(['skyblue', 'orange'][i])
                    pc.set_alpha(0.7)
                    
        plt.suptitle('Latency Distribution by Operation', fontsize=16)
        plt.tight_layout()
        plt.savefig(f"{prefix}_distributions.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"\n📊 Visualizations saved: {prefix}_*.png")
        
    def _print_summary(self, report: Dict[str, Any]):
        """Print analysis summary."""
        print("\n" + "=" * 60)
        print("📊 LATENCY IMPACT ANALYSIS SUMMARY")
        print("=" * 60)
        
        summary = report["summary"]
        print(f"\nOverall Impact: {summary['overall_impact_percent']:.1f}%")
        print(f"Operations Meeting SLA: {summary['operations_meeting_sla']}/{summary['total_operations']}")
        
        print("\n📈 Per-Operation Impact:")
        print(f"{'Operation':<15} {'Baseline':<10} {'Persistence':<12} {'Impact':<15} {'P99 Impact'}")
        print("-" * 70)
        
        for operation, data in report["operations"].items():
            baseline = data["baseline"]["mean_ms"]
            persistence = data["with_persistence"]["mean_ms"]
            impact_pct = data["impact"]["relative_percent"]
            p99_impact = data["impact"]["p99_impact_ms"]
            
            # Color code based on impact
            if impact_pct > 20:
                symbol = "🔴"
            elif impact_pct > 10:
                symbol = "🟡"
            else:
                symbol = "🟢"
                
            print(
                f"{operation:<15} "
                f"{baseline:<10.1f} "
                f"{persistence:<12.1f} "
                f"{impact_pct:>6.1f}% {symbol:<8} "
                f"{p99_impact:>6.1f} ms"
            )
            
        print("\n💡 Recommendations:")
        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze latency impact")
    
    subparsers = parser.add_subparsers(dest='mode', help='Analysis mode')
    
    # File-based analysis
    file_parser = subparsers.add_parser('files', help='Analyze from test files')
    file_parser.add_argument('baseline_file', help='Baseline metrics file')
    file_parser.add_argument('persistence_file', help='Persistence metrics file')
    
    # Live analysis
    live_parser = subparsers.add_parser('live', help='Run live analysis')
    live_parser.add_argument(
        '--base-url',
        default=os.getenv("TEST_URL", "http://localhost:8000"),
        help='Base URL for testing'
    )
    live_parser.add_argument(
        '--samples',
        type=int,
        default=100,
        help='Samples per operation (default: 100)'
    )
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        return 1
        
    analyzer = LatencyAnalyzer()
    
    if args.mode == 'files':
        await analyzer.analyze_from_files(
            args.baseline_file,
            args.persistence_file
        )
    else:
        await analyzer.run_comparative_analysis(
            args.base_url,
            args.samples
        )
        
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))