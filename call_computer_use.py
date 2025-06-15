"""
Simplified trends compilation entry point.
This module provides a clean interface for trends compilation using modular components.
"""
import asyncio
from trends.config import TrendsConfig
from trends.compiler import TrendsCompiler


def acknowledge_safety_check_callback(message: str) -> bool:
    """Handle safety check acknowledgments."""
    response = input(
        f"Safety Check Warning: {message}\nDo you want to acknowledge and proceed? (y/n): "
    ).lower()
    return response.strip() == "y"


async def compile_trends(user_query: str) -> str:
    """
    Main entry point for trends compilation.
    
    Args:
        user_query: The search query for trends analysis
        
    Returns:
        Compiled markdown report of the trends analysis
    """
    # Load and validate configuration
    config = TrendsConfig.from_env()
    config.validate()
      # Create compiler and run analysis
    compiler = TrendsCompiler(config)
    markdown_report = await compiler.compile_trends(user_query)
    
    # Print session summary
    print("\n=== Trends Compilation Session Summary ===")
    if markdown_report:
        print("Trends analysis completed successfully!")
        print(f"Report length: {len(markdown_report)} characters")
        print("\n=== Generated Trends Report ===")
        print(markdown_report)
    else:
        print("No trends report generated.")
    
    return markdown_report


if __name__ == "__main__":
    # Example usage
    query = "get me the latest trends in men's sports wear"
    asyncio.run(compile_trends(query))
