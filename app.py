# Importing necessary libraries and modules
import streamlit as st
import googleapiclient.discovery
import pandas as pd
import plotly.express as px
from textblob import TextBlob

# Set your YouTube Data API key here
YOUTUBE_API_KEY = "AIzaSyD7OUR71LzrVXntYUXlSjUxv1ZCkjNYpGM"

# Initialize the YouTube Data API client
youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

# Function to get channel analytics
def get_channel_analytics(channel_id):
    try:
        response = youtube.channels().list(
            part="snippet,statistics",
            id=channel_id
        ).execute()

        channel_info = response.get("items", [])[0]["snippet"]
        statistics_info = response.get("items", [])[0]["statistics"]

        channel_title = channel_info.get("title", "N/A")
        description = channel_info.get("description", "N/A")
        country = channel_info.get("country", "N/A")

        total_videos = int(statistics_info.get("videoCount", 0))
        total_views = int(statistics_info.get("viewCount", 0))

        # Fetch all video details for the dataframe
        videos_df = get_all_video_details(channel_id)

        return channel_title, description, country, total_videos, total_views, videos_df
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching channel analytics: {e}")
        return None, None, None, None, None, None

# Function to fetch all video details for a channel
def get_all_video_details(channel_id):
    try:
        response = youtube.search().list(
            channelId=channel_id,
            type="video",
            part="id,snippet",
            maxResults=50
        ).execute()

        video_details = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            # Use a separate request to get video statistics
            video_info = youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            ).execute()

            statistics_info = video_info.get("items", [])[0]["statistics"]
            snippet_info = video_info.get("items", [])[0]["snippet"]
            views = int(statistics_info.get("viewCount", 0))
            likes = int(statistics_info.get("likeCount", 0))
            comments = int(statistics_info.get("commentCount", 0))
            upload_date = snippet_info.get("publishedAt", "N/A")
            channel_name = snippet_info.get("channelTitle", "N/A")
            thumbnail_url = snippet_info.get("thumbnails", {}).get("default", {}).get("url", "N/A")

            video_details.append((title, video_id, likes, views, comments, upload_date, channel_name, url))

        videos_df = pd.DataFrame(video_details, columns=["Title", "Video ID", "Likes", "Views", "Comments", "Upload Date", "Channel", "URL"])
        return videos_df
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video details: {e}")
        return pd.DataFrame(columns=["Title", "Video ID", "Likes", "Views", "Comments", "Upload Date", "Channel", "URL"])

# Function to get video recommendations based on user's topic
def get_video_recommendations(topic, max_results=10):
    try:
        response = youtube.search().list(
            q=topic,
            type="video",
            part="id,snippet",
            maxResults=max_results,
            order="viewCount"
        ).execute()

        video_details = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            title = item["snippet"]["title"]
            url = f"https://www.youtube.com/watch?v={video_id}"

            # Use a separate request to get video statistics
            video_info = youtube.videos().list(
                part="statistics,snippet",
                id=video_id
            ).execute()

            statistics_info = video_info.get("items", [])[0]["statistics"]
            snippet_info = video_info.get("items", [])[0]["snippet"]
            views = int(statistics_info.get("viewCount", 0))
            channel_name = snippet_info.get("channelTitle", "N/A")
            thumbnail_url = snippet_info.get("thumbnails", {}).get("default", {}).get("url", "N/A")
            comments = int(statistics_info.get("commentCount", 0))  # Include total comments

            video_details.append((title, video_id, views, channel_name, url, thumbnail_url, comments))  # Include total comments

        return video_details
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching video recommendations: {e}")
        return None

# Function to get video comments
def get_video_comments(video_id):
    try:
        comments = []
        results = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            textFormat="plainText",
            maxResults=100
        ).execute()

        while "items" in results:
            for item in results["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                comments.append(comment)

            # Get the next set of results
            if "nextPageToken" in results:
                results = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    pageToken=results["nextPageToken"],
                    maxResults=100
                ).execute()
            else:
                break

        return comments
    except googleapiclient.errors.HttpError as e:
        st.error(f"Error fetching comments: {e}")
        return []

# Function to analyze and categorize comments sentiment
def analyze_and_categorize_comments(comments):
    try:
        categorized_comments = {'Positive': [], 'Neutral': [], 'Negative': []}

        for comment in comments:
            analysis = TextBlob(comment)
            # Classify the polarity of the comment
            if analysis.sentiment.polarity > 0:
                categorized_comments['Positive'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))
            elif analysis.sentiment.polarity == 0:
                categorized_comments['Neutral'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))
            else:
                categorized_comments['Negative'].append((comment, analysis.sentiment.polarity, analysis.sentiment.subjectivity))

        return categorized_comments
    except Exception as e:
        st.error(f"Error analyzing comments: {e}")
        return {'Positive': [], 'Neutral': [], 'Negative': []}

# Main Streamlit app
st.title("Welcome to YouTube Analyzer!")

# Description of the YouTube Analyzer app
st.markdown(
    """
    🚀 Explore the fascinating world of YouTube with our Analyzer tool! Dive into detailed channel analytics, 
    discover top video recommendations, and unravel the sentiment hidden in comments. 
    Get ready for an interactive journey with vibrant charts and insightful statistics. 
    Let's embark on the YouTube adventure together! 🎉
    """
)
# Warning about YouTube API key
st.warning(
    """
    ⚠️ **Important Notice:** The YouTube Data API key used in this app is for demonstration purposes only.
    It may expire or reach its usage limit, resulting in errors. 
    Replace it with your own API key to ensure uninterrupted access to YouTube data. 
    Follow the instructions in the app's documentation to obtain and set up your API key.
    """
)
# Note about using YouTube IDs
st.info(
    """
    🚀 **Pro Tip:** To unlock the full power of YouTube Analyzer, use valid YouTube IDs for channels and videos!
    Input a valid Channel ID to unleash comprehensive analytics, or enter an exciting Video ID to discover sentiment and more.
    Get ready to embark on a thrilling journey of insights and exploration with YouTube IDs!
    """
)


# Sidebar
st.sidebar.title("YouTube Analyzer")
st.sidebar.subheader("Select a Task")

# Task 1: Channel Analytics
if st.sidebar.checkbox("Channel Analytics"):
    st.sidebar.subheader("Channel Analytics")
    channel_id_analytics = st.sidebar.text_input("Enter Channel ID for Analytics", value="")

    if st.sidebar.button("Get Channel Analytics"):
        channel_title, description, country, total_videos, total_views, videos_df = get_channel_analytics(channel_id_analytics)

        # Display Channel Overview
        st.subheader("Channel Overview")
        st.write(f"**Channel Title:** {channel_title}")
        st.write(f"**Description:** {description}")
        st.write(f"**Country:** {country}")
        st.write(f"**Total Videos:** {total_videos}")
        st.write(f"**Total Views:** {total_views}")

        # Advanced Charts for Channel Analytics
        st.subheader("Analytics Charts")

        # Time Series Chart for Views
        fig_views = px.line(videos_df, x="Title", y="Views", title="Views Over Time for Each Video", hover_data=["Title", "Likes", "Comments"])
        fig_views.update_layout(height=600, width=1000, hovermode="x unified")  # Increased size for better visibility
        st.plotly_chart(fig_views, use_container_width=True)

        # Bar Chart for Likes and Comments
        fig_likes_comments = px.bar(videos_df, x="Title", y=["Likes", "Comments"],
                                    title="Likes and Comments Comparison for Each Video", barmode="group", hover_data=["Title", "Views"])
        fig_likes_comments.update_layout(height=600, width=1000, hovermode="x unified")  # Increased size for better visibility
        st.plotly_chart(fig_likes_comments, use_container_width=True)

        # New Chart: Scatter Plot for Likes vs Views
        fig_likes_views = px.scatter(videos_df, x="Likes", y="Views", color="Channel",
                                     title="Scatter Plot for Likes vs Views Across Videos", hover_data=["Title"])
        fig_likes_views.update_layout(height=600, width=1000, hovermode="closest")  # Increased size for better visibility
        st.plotly_chart(fig_likes_views, use_container_width=True)

        # Additional: Display DataFrame of video details with clickable URLs
        st.subheader("All Video Details")
        videos_df['URL'] = videos_df['URL'].apply(lambda x: f"<a href='{x}' target='_blank'>{x}</a>")
        st.write(videos_df[['Title', 'Video ID', 'Likes', 'Views', 'Comments', 'Upload Date', 'Channel', 'URL']].to_html(escape=False), unsafe_allow_html=True)

# Task 2: Video Recommendation based on User's Topic of Interest
if st.sidebar.checkbox("Video Recommendation"):
    st.sidebar.subheader("Video Recommendation")
    topic_interest = st.sidebar.text_input("Enter Topic of Interest", value="")

    if st.sidebar.button("Get Video Recommendations"):
        video_recommendations = get_video_recommendations(topic_interest, max_results=10)

        # Display Video Recommendations
        st.subheader("Video Recommendations")
        for video in video_recommendations:
            st.write(f"**{video[0]}**")
            st.write(f"<img src='{video[5]}' alt='Thumbnail' style='max-height: 150px;'>", unsafe_allow_html=True)
            st.write(f"Video ID: {video[1]}")
            st.write(f"Views: {video[2]}")
            st.write(f"Channel: {video[3]}")
            st.write(f"Total Comments: {video[6]}")  # Display total comments
            st.write(f"Watch Video: [Link]({video[4]})")
            st.write("---")

# Task 3: Sentimental Analysis of Comments with Visualization
if st.sidebar.checkbox("Sentimental Analysis"):
    st.sidebar.subheader("Sentimental Analysis")
    video_id_sentiment = st.sidebar.text_input("Enter Video ID", value="")

    # Fetch video title for display
    video_info = youtube.videos().list(
        part="snippet",
        id=video_id_sentiment
    ).execute()

    video_title = video_info.get("items", [])[0]["snippet"]["title"] if video_info.get("items") else "Video Title N/A"

    # Display video title in the main interface
    st.subheader(f"Sentimental Analysis for Video: {video_title}")

    # Allow the user to choose the type of comments
    selected_sentiment = st.sidebar.selectbox("Select Comment Type", ["Positive", "Neutral", "Negative"])

    if st.sidebar.button("Analyze Sentiments"):
        comments_sentiment = get_video_comments(video_id_sentiment)

        # Analyze and categorize comments sentiment for all comments
        categorized_comments_all = analyze_and_categorize_comments(comments_sentiment)

        # Filter comments based on the selected sentiment
        filtered_comments = categorized_comments_all.get(selected_sentiment, [])

        # Display video title and visualization charts
        st.subheader("Video Information")
        st.write(f"**Video Title:** {video_title}")

        # Visualization Chart 1: Bar Chart for Sentiment Distribution with Differentiated Colors
        colors = {'Positive': 'green', 'Neutral': 'gray', 'Negative': 'red'}

        all_comments_count = [len(categorized_comments_all[sentiment]) for sentiment in ["Positive", "Neutral", "Negative"]]
        all_sentiments = ["Positive", "Neutral", "Negative"]
        fig_sentiment_bar_chart = px.bar(x=all_sentiments,
                                         y=all_comments_count,
                                         color=all_sentiments,
                                         color_discrete_map=colors,
                                         labels={"x": "Sentiment Type", "y": "Number of Comments"},
                                         title=f"Sentiment Distribution for All Comments",
                                         height=400)
        st.plotly_chart(fig_sentiment_bar_chart, use_container_width=True)

        # Visualization Chart 2: Scatter Plot for Relationship between Polarity and Subjectivity for All Comments
        all_comments_polarity = []
        all_comments_subjectivity = []

        for sentiment_type in categorized_comments_all.values():
            for comment_info in sentiment_type:
                all_comments_polarity.append(comment_info[1])
                all_comments_subjectivity.append(comment_info[2])

        fig_scatter_plot_all = px.scatter(x=all_comments_polarity,
                                          y=all_comments_subjectivity,
                                          color=[selected_sentiment] * len(all_comments_polarity),
                                          labels={"x": "Polarity", "y": "Subjectivity"},
                                          title=f"Relationship between Polarity and Subjectivity ",
                                          height=400)
        st.plotly_chart(fig_scatter_plot_all, use_container_width=True)

        # Display sentiment analysis results for the selected sentiment type
        st.subheader(f"Selected Sentiment Type: {selected_sentiment}")
        st.write(f"Total {selected_sentiment} Comments: {len(filtered_comments)}")

        # Additional code for displaying comments
        st.subheader(f"{selected_sentiment} Comments:")
        for idx, comment_info in enumerate(filtered_comments[:20]):
            comment_text, polarity, subjectivity = comment_info
            st.write(f"{idx + 1}. {comment_text} (Polarity: {polarity}, Subjectivity: {subjectivity})")

# Footer
st.sidebar.title("Connect with Me")
st.sidebar.markdown(
    "[LinkedIn](https://www.linkedin.com/in/hvamsi/) | "
    "[GitHub](https://github.com/hvamsiprakash)"
)
