import asyncio
import argparse
import sys
from call_computer_use import compile_trends


async def main():
    """Main entry point for the application."""

    user_query = "get me the latest trends in men's sports wear"
    
    try:
        print(f"=== Trend Search Computer Use Agent ===")
        print(f"Query: {user_query}")
        print(f"Starting browser automation...")
        
        # Run the computer use agent
        conversation_history = await compile_trends(user_query)

        print("\n=== Session Summary ===")
        print(f"Total messages in conversation: {len(conversation_history)}")
        print("Trend search completed!")
        
    except KeyboardInterrupt:
        print("\nSession interrupted by user")
    except Exception as e:
        print(f"Error running application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

