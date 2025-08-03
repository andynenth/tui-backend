#!/bin/bash
# Script to run dataflow analysis and generate documentation

echo "🔍 Liap Tui Codebase Analysis Tool"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "final_dataflow_analyzer.py" ]; then
    echo "❌ Error: Must run from docs/analysis directory"
    echo "   cd backend/docs/analysis"
    exit 1
fi

# Menu
echo "Select analysis to run:"
echo "1) Complete Dataflow Analysis (recommended)"
echo "2) WebSocket Flow Analysis"
echo "3) Deep Component Analysis"
echo "4) Basic Analysis"
echo "5) Run All Analyses"
echo "0) Exit"
echo ""
read -p "Enter choice [0-5]: " choice

case $choice in
    1)
        echo "Running complete dataflow analysis..."
        python3 final_dataflow_analyzer.py
        echo ""
        echo "✅ Analysis complete! View results in:"
        echo "   - complete_dataflow_analysis.md"
        echo "   - dataflow_summary.md"
        ;;
    2)
        echo "Running WebSocket flow analysis..."
        python3 websocket_flow_analyzer.py
        echo ""
        echo "✅ Analysis complete! View results in:"
        echo "   - websocket_flows.md"
        ;;
    3)
        echo "Running deep component analysis..."
        python3 deep_codebase_analyzer.py
        echo ""
        echo "✅ Analysis complete! View results in:"
        echo "   - deep_analysis.md"
        ;;
    4)
        echo "Running basic analysis..."
        python3 analyze_codebase.py
        echo ""
        echo "✅ Analysis complete! View results in:"
        echo "   - codebase_analysis.md"
        ;;
    5)
        echo "Running all analyses..."
        echo ""
        echo "1/4 Basic analysis..."
        python3 analyze_codebase.py
        echo ""
        echo "2/4 Deep component analysis..."
        python3 deep_codebase_analyzer.py
        echo ""
        echo "3/4 WebSocket flow analysis..."
        python3 websocket_flow_analyzer.py
        echo ""
        echo "4/4 Complete dataflow analysis..."
        python3 final_dataflow_analyzer.py
        echo ""
        echo "✅ All analyses complete! Files generated:"
        echo "   - complete_dataflow_analysis.md (main)"
        echo "   - dataflow_summary.md"
        echo "   - deep_analysis.md"
        echo "   - websocket_flows.md"
        echo "   - codebase_analysis.md"
        ;;
    0)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "📊 To view diagrams:"
echo "   - Open .md files in VS Code with Mermaid extension"
echo "   - Push to GitHub for automatic rendering"
echo "   - Visit https://mermaid.live for online viewing"