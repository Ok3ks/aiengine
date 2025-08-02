from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP
import asyncio
import os
import logfire

spotify_mcp = MCPServerStreamableHTTP(url='http://127.0.0.1:8000/mcp')
github_mcp_pat = os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']
github_server = MCPServerStreamableHTTP(url='https://api.githubcopilot.com/mcp', headers={
        "Authorization": f"Bearer {github_mcp_pat}"
      },
)

# youtube_mcp
# twitter_mcp

agent = Agent('anthropic:claude-3-5-sonnet-latest', toolsets=[spotify_mcp], instructions="You are an excellent DJ with global taste at the same time niche taste, You are independent, You do not rely on the user's taste before recommendation.")
agent.set_mcp_sampling_model()


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("query")

    args = parser.parse_args()
    async with agent:
        result = await agent.run(args.query)  # Maybe try Chat
    print(result.output)

if __name__ == '__main__':
    logfire.configure()
    logfire.instrument_pydantic_ai()
    asyncio.run(main())
