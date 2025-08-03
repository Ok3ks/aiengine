from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP, MCPServerSSE
import asyncio
from aci import ACI
import os
import logfire

spotify_mcp = MCPServerStreamableHTTP(url='http://127.0.0.1:8000/mcp')
github_mcp_pat = os.environ['GITHUB_PERSONAL_ACCESS_TOKEN']
github_server = MCPServerStreamableHTTP(url='https://api.githubcopilot.com/mcp', headers={
        "Authorization": f"Bearer {github_mcp_pat}"
      },
)
arxiv_mcp = MCPServerSSE(url="http://0.0.0.0:8001/sse")
aci = ACI()
arxiv_function = aci.functions.get_definition("ARXIV__SEARCH_PAPERS")

# youtube_mcp
# twitter_mcp

agent = Agent('anthropic:claude-3-5-sonnet-latest', toolsets=[arxiv_mcp])
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
