import sys
import shlex
from analysis.core import LogAnalyzer

def main():
    analyzer = LogAnalyzer()
    
    print("""
╔══════════════════════════════════════════╗
║        Journal Log Analyzer REPL         ║
║          Interactive Log Analysis        ║
╚══════════════════════════════════════════╝
    """)
    
    while True:
        try:
            cmd_input = input("\nlog-analyzer> ").strip()
            
            if cmd_input.lower() in ['quit', 'q', 'exit']:
                print("Goodbye!")
                break
                
            elif cmd_input.lower() == 'help' or cmd_input == '?':
                analyzer.show_help()
                
            elif cmd_input.lower().startswith('load'):
                # Use shlex to properly handle quoted arguments with spaces
                try:
                    parts = shlex.split(cmd_input)
                except ValueError:
                    # If there's a parsing error, fall back to simple split
                    parts = cmd_input.split()
                
                limit = None
                since = None
                until = None
                
                # Skip the first part (the command 'load')
                for part in parts[1:]:
                    if part.isdigit():
                        limit = int(part)
                    elif part.startswith('since='):
                        since = part.split('=', 1)[1]  # Split only on first '='
                        # Remove quotes if they're present
                        since = since.strip('"\'')
                    elif part.startswith('until='):
                        until = part.split('=', 1)[1]
                        until = until.strip('"\'')
                
                analyzer.load_logs(limit, since, until)

            elif cmd_input.lower() == 'analyze':
                analyzer.analyze_logs()
                
            elif cmd_input.lower() == 'summary':
                analyzer.show_summary()
                
            elif cmd_input.lower().startswith('detailed'):
                parts = cmd_input.split()
                month = parts[1] if len(parts) > 1 else None
                domain = parts[2] if len(parts) > 2 else None
                analyzer.show_detailed(month, domain)
                
            elif cmd_input.lower().startswith('search'):
                parts = cmd_input.split()
                if len(parts) < 2:
                    print("Usage: search <keyword> [level]")
                else:
                    keyword = parts[1]
                    level = parts[2] if len(parts) > 2 else None
                    analyzer.search_logs(keyword, level)
                    
            elif cmd_input.lower() == 'stats':
                analyzer.show_stats()
                
            elif cmd_input.lower().startswith('visualize') or cmd_input.lower().startswith('viz'):
                analyzer.show_visualization()

            elif cmd_input.lower().startswith('table'):
                parts = cmd_input.split()
                table_type = parts[1] if len(parts) > 1 else "summary"
                limit = int(parts[2]) if len(parts) > 2 else 20
                analyzer.show_table(table_type, limit)

            elif cmd_input.lower() == 'browse':
                analyzer.browse_table()

            elif cmd_input.lower() == 'advanced':
                analyzer.add_advanced_features()

            elif cmd_input.lower().startswith('export'):
                parts = cmd_input.split()
                if len(parts) >= 2:
                    analyzer.export_data(parts[1])
                else:
                    print("Usage: export <format>")

            elif cmd_input.lower() == 'tui':
                print("Launching TUI...")
                # Launch the TUI in a subprocess
                import subprocess
                subprocess.run([sys.executable, "tui/app.py"])

            elif cmd_input == '':
                continue
                
            else:
                print(f"Unknown command: {cmd_input}")
                print("Type 'help' for available commands.")
                
        except KeyboardInterrupt:
            print("\n\nUse 'quit' or 'q' to exit.")
        except Exception as e:
            print(f"Error: {e}")
'''
import argparse
import sys
from typing import List, Optional

from .analysis.core import LogAnalyzer
from .visualization.charts import ChartRenderer
from .visualization.tables import TableRenderer
from .data.export import ExportManager

class LogalyzerCLI:
    """Command-line interface"""
    
    def __init__(self):
        self.analyzer = LogAnalyzer()
        self.chart_renderer = ChartRenderer()
        self.table_renderer = TableRenderer()
        self.export_manager = ExportManager()
        
    def run(self, args: Optional[List[str]] = None):
        """Main CLI entry point"""
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        if parsed_args.command == "analyze":
            self._handle_analyze(parsed_args)
        elif parsed_args.command == "visualize":
            self._handle_visualize(parsed_args)
        elif parsed_args.command == "table":
            self._handle_table(parsed_args)
        elif parsed_args.command == "export":
            self._handle_export(parsed_args)
        elif parsed_args.command == "tui":
            self._handle_tui()
        else:
            parser.print_help()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description="Advanced log analysis tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s analyze --limit 5000
  %(prog)s visualize --chart priority --output chart.png
  %(prog)s table --type summary --format rich
  %(prog)s export --format json --output analysis.json
  %(prog)s tui
            """
        )
        
        subparsers = parser.add_subparsers(
            dest="command",
            help="Command to execute"
        )
        
        # Analyze command
        analyze_parser = subparsers.add_parser(
            "analyze",
            help="Analyze logs"
        )
        analyze_parser.add_argument(
            "--limit", "-n",
            type=int,
            default=1000,
            help="Number of log entries to analyze"
        )
        analyze_parser.add_argument(
            "--since",
            help="Start time (e.g., '1 hour ago', '2024-01-01')"
        )
        analyze_parser.add_argument(
            "--until",
            help="End time"
        )
        
        # Visualize command
        viz_parser = subparsers.add_parser(
            "visualize",
            help="Create visualizations"
        )
        viz_parser.add_argument(
            "--chart",
            choices=["priority", "domain", "timeline", "heatmap"],
            default="priority",
            help="Type of chart to create"
        )
        viz_parser.add_argument(
            "--output", "-o",
            help="Output file (default: show on screen)"
        )
        
        # Table command
        table_parser = subparsers.add_parser(
            "table",
            help="Display tables"
        )
        table_parser.add_argument(
            "--type",
            choices=["summary", "detailed", "errors", "domains"],
            default="summary",
            help="Table type"
        )
        table_parser.add_argument(
            "--format",
            choices=["rich", "plain", "csv"],
            default="rich",
            help="Output format"
        )
        
        # Export command
        export_parser = subparsers.add_parser(
            "export",
            help="Export analysis results"
        )
        export_parser.add_argument(
            "--format",
            choices=["json", "csv", "html", "md"],
            required=True,
            help="Export format"
        )
        export_parser.add_argument(
            "--output", "-o",
            required=True,
            help="Output file"
        )
        
        # TUI command
        subparsers.add_parser(
            "tui",
            help="Launch Textual TUI"
        )
        
        return parser
    
    def _handle_analyze(self, args):
        """Handle analyze command"""
        result = self.analyzer.analyze(
            limit=args.limit,
            since=args.since,
            until=args.until
        )
        
        print(f"Analysis complete:")
        print(f"  Total entries: {result.total_entries}")
        print(f"  Errors: {result.error_count}")
        print(f"  Error rate: {result.summary.get('error_rate', 0):.1f}%")
        
        if result.patterns:
            print(f"\nPatterns detected: {len(result.patterns)}")
            for pattern in result.patterns[:3]:  # Show first 3
                print(f"  • {pattern.get('type')}: {pattern.get('message')}")
    
    def _handle_visualize(self, args):
        """Handle visualize command"""
        # Load or analyze data first
        result = self.analyzer.analyze(limit=1000)
        
        if args.chart == "priority":
            self.chart_renderer.priority_distribution(result)
        elif args.chart == "domain":
            self.chart_renderer.domain_distribution(result)
        elif args.chart == "timeline":
            self.chart_renderer.timeline(result)
        elif args.chart == "heatmap":
            self.chart_renderer.heatmap(result)
        
        if args.output:
            plt.savefig(args.output, dpi=300, bbox_inches='tight')
            print(f"Chart saved to {args.output}")
        else:
            plt.show()
    
    def _handle_table(self, args):
        """Handle table command"""
        result = self.analyzer.analyze(limit=500)
        
        if args.type == "summary":
            self.table_renderer.summary(result, format=args.format)
        elif args.type == "detailed":
            self.table_renderer.detailed(result, format=args.format)
        elif args.type == "errors":
            self.table_renderer.errors(result, format=args.format)
        elif args.type == "domains":
            self.table_renderer.domains(result, format=args.format)
    
    def _handle_export(self, args):
        """Handle export command"""
        result = self.analyzer.analyze(limit=1000)
        self.export_manager.export(result, args.format, args.output)
        print(f"Exported to {args.output}")
    
    def _handle_tui(self):
        """Handle TUI command"""
        from .tui.app import LogalyzerTUI
        app = LogalyzerTUI()
        app.run()

def main():
    """Entry point for CLI"""
    cli = LogalyzerCLI()
    cli.run()

if __name__ == "__main__":
    main()

'''