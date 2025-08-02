import os
import sys
import json
from typing import Optional, List

from mcp.server.fastmcp import FastMCP
from spotipy import SpotifyException
import spotify_api
from utils import normalize_redirect_uri
from mcp.types import Request
from starlette.responses import Response


# Setup basic logging
def setup_logger():
    class Logger:
        def info(self, message: str):
            print(f"[INFO] {message}", file=sys.stderr)

        def error(self, message: str):
            print(f"[ERROR] {message}", file=sys.stderr)
    return Logger()

logger = setup_logger()

# Normalize the redirect URI according to Spotify's requirements
if spotify_api.REDIRECT_URI:
    spotify_api.REDIRECT_URI = normalize_redirect_uri(spotify_api.REDIRECT_URI)

# Create the Spotify MCP server in stateless HTTP mode
spotify_mcp = FastMCP(name="Spotify Server")
spotify_client = spotify_api.Client(logger)

# ------------------------------------------------------------------------------
# TOOL: Playback
# Manages the current playback with actions: 'get', 'start', 'pause', 'skip'
# ------------------------------------------------------------------------------
@spotify_mcp.tool()
async def playback(action: str, spotify_uri: Optional[str] = None, num_skips: int = 1) -> str:
    """
    Manage playback. Actions:
      - get: Get information about the current track.
      - start: Start playback of a new item (or resume if no URI is provided).
      - pause: Pause playback.
      - skip: Skip the current track (optionally skip multiple tracks using num_skips).
    """
    try:
        if action == "get":
            logger.info("Attempting to get current track")
            curr_track = await spotify_client.get_current_track()
            if curr_track:
                logger.info(f"Current track: {curr_track.get('name', 'Unknown')}")
                return json.dumps(curr_track, indent=2)
            return "No track playing."
        elif action == "start":
            logger.info(f"Starting playback with spotify_uri: {spotify_uri}")
            await spotify_client.start_playback(spotify_uri=spotify_uri)
            return "Playback starting."
        elif action == "pause":
            logger.info("Pausing playback")
            await spotify_client.pause_playback()
            return "Playback paused."
        elif action == "skip":
            logger.info(f"Skipping {num_skips} track(s)")
            await spotify_client.skip_track(n=num_skips)
            return "Skipped to next track."
        else:
            return f"Unknown playback action: {action}"
    except SpotifyException as se:
        logger.error(f"Spotify Client error: {str(se)}")
        return f"Spotify Client error occurred: {str(se)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Unexpected error occurred: {str(e)}"

# ------------------------------------------------------------------------------
# TOOL: Queue
# Manage the playback queue by either adding a track or retrieving the current queue.
# ------------------------------------------------------------------------------
@spotify_mcp.tool()
async def queue_tool(action: str, track_id: Optional[str] = None) -> str:
    """
    Manage the playback queue.
    Actions:
      - add: Add track to the queue (requires track_id).
      - get: Retrieve the current queue.
    """
    try:
        if action == "add":
            if not track_id:
                return "track_id is required for add action."
            logger.info(f"Adding track {track_id} to queue")
            await spotify_client.add_to_queue(track_id)
            return "Track added to queue."
        elif action == "get":
            logger.info("Retrieving queue")
            current_queue = await spotify_client.get_queue()
            return json.dumps(current_queue, indent=2)
        else:
            return f"Unknown queue action: {action}. Supported actions are: add, get."
    except Exception as e:
        logger.error(f"Error in queue_tool: {str(e)}")
        return f"Error: {str(e)}"

# ------------------------------------------------------------------------------
# TOOL: GetInfo
# Get detailed information about a Spotify item (track, album, artist, or playlist)
# ------------------------------------------------------------------------------
@spotify_mcp.tool()
async def get_info(item_uri: str) -> str:
    """
    Get detailed information about a Spotify item.
    The behavior depends on the type of item referenced by item_uri.
    """
    try:
        logger.info(f"Retrieving info for item: {item_uri}")
        item_info = await spotify_client.get_info(item_uri=item_uri)
        return json.dumps(item_info, indent=2)
    except Exception as e:
        logger.error(f"Error in get_info: {str(e)}")
        return f"Error: {str(e)}"

# ------------------------------------------------------------------------------
# TOOL: Search
# Search for tracks, albums, artists, or playlists on Spotify.
# ------------------------------------------------------------------------------

@spotify_mcp.tool()
async def search_audiobook(query: str, qtype: str = "audiobook", limit: int = 10) -> str:
    """
    Search for Spotify content.
    Parameters:
      - query: The search term.
      - qtype: The type of item (track, album, artist, playlist, or multiple comma-separated types).
      - limit: Maximum number of results to return.
    """

    # classify query into labels
    # check if query has listed labels
    # create classification agent, which maps queries to labels (available labels")

    try:
        logger.info(f"Searching for '{query}' with type '{qtype}'")
        search_results = await spotify_client.search(query=query, qtype=qtype, limit=limit)
        return json.dumps(search_results, indent=2)
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        return f"Error: {str(e)}"
    
@spotify_mcp.tool()
async def search(query: str, qtype: str = "track", limit: int = 10) -> str:
    """
    Search for Spotify content.
    Parameters:
      - query: The search term.
      - qtype: The type of item (track, album, artist, playlist, or multiple comma-separated types).
      - limit: Maximum number of results to return.
    """
    try:
        logger.info(f"Searching for '{query}' with type '{qtype}'")
        search_results = await spotify_client.search(query=query, qtype=qtype, limit=limit)
        return json.dumps(search_results, indent=2)
    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        return f"Error: {str(e)}"

# ------------------------------------------------------------------------------
# TOOL: Playlist
# Manage Spotify playlists.
# Actions include:
#   - get: List user's playlists.
#   - get_tracks: Get tracks in a specified playlist.
#   - add_tracks: Add tracks to a playlist.
#   - remove_tracks: Remove tracks from a playlist.
#   - change_details: Change the playlist's details.
# ------------------------------------------------------------------------------
@spotify_mcp.tool()
async def playlist(
    action: str,
    playlist_id: Optional[str] = None,
    track_ids: Optional[List[str]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Manage Spotify playlists.
    Actions:
      - get: Retrieve the current user's playlists.
      - get_tracks: Get tracks for a given playlist (requires playlist_id).
      - add_tracks: Add track(s) to a playlist (requires playlist_id and track_ids).
      - remove_tracks: Remove track(s) from a playlist (requires playlist_id and track_ids).
      - change_details: Update the playlist name and/or description (requires playlist_id).
      - create_playlist: Create the playlist 
    """
    try:
        if action == "get":
            logger.info("Retrieving user playlists")
            playlists = await spotify_client.get_current_user_playlists()
            return json.dumps(playlists, indent=2)
        elif action == "get_tracks":
            if not playlist_id:
                return "playlist_id is required for get_tracks action."
            logger.info(f"Getting tracks for playlist: {playlist_id}")
            tracks = await spotify_client.get_playlist_tracks(playlist_id)
            return json.dumps(tracks, indent=2)
        elif action == "add_tracks":
            if not playlist_id or not track_ids:
                return "playlist_id and track_ids are required for add_tracks action."
            logger.info(f"Adding tracks {track_ids} to playlist {playlist_id}")
            await spotify_client.add_tracks_to_playlist(playlist_id=playlist_id, track_ids=track_ids)
            return "Tracks added to playlist."
        elif action == "remove_tracks":
            if not playlist_id or not track_ids:
                return "playlist_id and track_ids are required for remove_tracks action."
            logger.info(f"Removing tracks {track_ids} from playlist {playlist_id}")
            await spotify_client.remove_tracks_from_playlist(playlist_id=playlist_id, track_ids=track_ids)
            return "Tracks removed from playlist."
        elif action == "change_details":
            if not playlist_id:
                return "playlist_id is required for change_details action."
            if not (name or description):
                return "At least one of name or description is required for change_details action."
            logger.info(f"Changing details for playlist {playlist_id}")
            await spotify_client.change_playlist_details(playlist_id=playlist_id, name=name, description=description)
            return "Playlist details changed."
        elif action == "create_playlist":
            if not playlist_id:
                return "playlist_id is required for create_playlist action."
            if not (name or description):
                return "At least one of name or description is required for change_details action."
            logger.info(f"Create details for playlist {playlist_id}")
            await spotify_client.create_playlist(name, description)
            return "Create playlist."
        else:
            return f"Unknown playlist action: {action}."
    except Exception as e:
        logger.error(f"Error in playlist tool: {str(e)}")
        return f"Error: {str(e)}"

@spotify_mcp.custom_route("/success", methods=["GET", "POST"])
async def success_endpoint(request: Request) -> Response:
    return Response(content={
        "status": "success",
        "message": "The request was processed successfully."
    })
# ------------------------------------------------------------------------------
# If desired, you can combine this FastMCP server with others (or with Starlette)
# using an async lifespan function. For example:
#
#   @contextlib.asynccontextmanager
#   async def lifespan(app: Starlette):
#       async with spotify_mcp.session_manager.run():
#           yield

# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Run the Spotify FastMCP server on stand-alone mode,
    # using SSE as the transport and mounting it at "/spotify".
    spotify_mcp.run(transport='streamable-http')
    # spotify_mcp.run(transport="sse", mount_path="/spotify") 
