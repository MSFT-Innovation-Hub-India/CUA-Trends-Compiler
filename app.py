import asyncio
import argparse
import sys
from call_computer_use import compile_trends


async def main() -> str:
    """Main entry point for the application."""

    user_query = "get me the latest trends in men's sports wear"
    
    try:
        print(f"=== Trend Search Computer Use Agent ===")
        print(f"Query: {user_query}")
        print(f"Starting browser automation...")
          # Run the computer use agent
        markdown_report = await compile_trends(user_query)

        print("\n=== Session Summary ===")
        if markdown_report:
            print("Trends analysis completed successfully!")
            print(f"Report length: {len(markdown_report)} characters")
            print("\n=== Generated Trends Report ===")
            print(markdown_report)
        else:
            print("No trends report generated.")
        
        return markdown_report
        
    except KeyboardInterrupt:
        print("\nSession interrupted by user")
    except Exception as e:
        print(f"Error running application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

