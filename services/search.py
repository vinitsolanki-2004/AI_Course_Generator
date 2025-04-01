import streamlit as st
from services.get_env import GOOGLE_API_KEY, GOOGLE_CSE_ID
from googleapiclient.discovery import build

def google_search(query, num_results=5):
    """Perform a Google search and return the results."""
    try:
        # Build the service
        service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        
        # Execute the search
        result = service.cse().list(q=query, cx=GOOGLE_CSE_ID, num=num_results).execute()
        
        # Extract search snippets and titles
        search_results = []
        if "items" in result:
            for item in result["items"]:
                search_results.append({
                    "title": item["title"],
                    "snippet": item.get("snippet", ""),
                    "link": item["link"]
                })
        
        # Format the search results into a string
        formatted_results = ""
        for i, res in enumerate(search_results, 1):
            formatted_results += f"Result {i}:\nTitle: {res['title']}\nSnippet: {res['snippet']}\nLink: {res['link']}\n\n"
        return formatted_results
    except Exception as e:
        st.error(f"Error performing Google search: {e}")
        return f"Unable to retrieve search results. Error: {str(e)}"
    
def search_youtube_videos(query, max_results=3):
    """Search for YouTube videos related to the query."""
    try:
        # If no API key, return empty list
        if not GOOGLE_API_KEY:
            return []
            
        # Build the YouTube service
        youtube = build('youtube', 'v3', developerKey=GOOGLE_API_KEY)
        
        # Call the search.list method to get videos
        search_response = youtube.search().list(
            q=query,
            part='snippet',
            maxResults=max_results,
            type='video'
        ).execute()
        
        # Extract video information
        videos = []
        for item in search_response.get('items', []):
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            thumbnail = item['snippet']['thumbnails']['medium']['url']
            channel = item['snippet']['channelTitle']
            
            videos.append({
                'video_id': video_id,
                'title': title,
                'thumbnail': thumbnail,
                'channel': channel,
                'url': f"https://www.youtube.com/watch?v={video_id}"
            })
            
        return videos
    except Exception as e:
        st.warning(f"Could not fetch YouTube videos: {e}")
        return []