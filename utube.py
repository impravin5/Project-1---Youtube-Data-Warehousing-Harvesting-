import googleapiclient.discovery 
from googleapiclient.errors import HttpError
import mysql.connector
from mysql.connector import MySQLConnection
from mysql.connector import Error as MYSQLError
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta
import json

# Enter the API key
api_key = "AIzaSyCibfIeElex4WUa9LCqkYo7r5FJciFjGf0"  # Your YouTube API key
api_service_name = "youtube"
api_version = "v3"


youtube_data = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

try:
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Pravin@05",
        database="myapp",
        port="3306",
        auth_plugin="mysql_native_password"  # Ensure this line is present if needed
    )
    
    cursor = mydb.cursor()
    print("Connection successful")
except mysql.connector.Error as err:
    print(f"Connection not found")

# Get Channel Information
def get_channel_info(channel_id):
    cursor.execute("""CREATE TABLE IF NOT EXISTS channel_info (
                        channel_name VARCHAR(255),
                        channel_id VARCHAR(255) PRIMARY KEY,
                        subscribe INT,
                        views INT,
                        channel_description TEXT,
                        playlist_id VARCHAR(255)
                    )""")
    
    request = youtube_data.channels().list(
        part="snippet,contentDetails,statistics",
        id=channel_id
    )
    response = request.execute()
    
    channel_table = []
    for item in response.get('items', []):
        channel_data = {
            "channel_name": item['snippet']['title'],
            "channel_id": channel_id,
            "Subscriber": item['statistics']['subscriberCount'],
            "channel_views": item['statistics']['viewCount'],
            "channel_description": item['snippet']['description'],
            "playlist_id": item['contentDetails']['relatedPlaylists']['uploads']
        }
    
        cursor.execute("""INSERT INTO channel_info (channel_name, channel_id, subscribe, views, channel_description, playlist_id) VALUES (%s, %s, %s, %s, %s, %s)
                          ON DUPLICATE KEY UPDATE
                          channel_name = VALUES(channel_name),
                          subscribe = VALUES(subscribe),
                          views = VALUES(views),
                          channel_description = VALUES(channel_description),
                          playlist_id = VALUES(playlist_id)""",
                       (channel_data['channel_name'], channel_data['channel_id'], channel_data['Subscriber'], channel_data['channel_views'], channel_data['channel_description'], channel_data['playlist_id']))
        
        mydb.commit()
        channel_table.append(channel_data)
    return channel_table

# Get Video Ids
def get_video_ids(channel_id):
    video_ids = []
    response = youtube_data.channels().list(id=channel_id, part='contentDetails').execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    page_token = None

    while True:
        request_2 = youtube_data.playlistItems().list(
            part='snippet',
            playlistId=playlist_id,
            maxResults=50,
            pageToken= page_token).execute()
        for item in request_2['items']:
            video_ids.append(item['snippet']['resourceId']['videoId'])
        next_page_token = request_2.get('nextPageToken')

        if page_token is None:
            break
    
    return video_ids

# Get Video Details
def parse_duration(duration_str):
    try:
        duration_seconds = int(duration_str[2:-1])
        return duration_seconds
    except ValueError:
        return None

def get_video_details(video_ids):
    video_list = []
    for vid in video_ids:
        request = youtube_data.videos().list(
            part="snippet,contentDetails,statistics",
            id=vid
        )
        response = request.execute()

        cursor.execute("""CREATE TABLE IF NOT EXISTS video_details (
                    channel_name VARCHAR(255),
                    video_id VARCHAR(255) PRIMARY KEY,
                    video_name VARCHAR(255),
                    description TEXT,
                    tags TEXT,
                    published_date DATETIME,
                    views_count BIGINT,
                    likes_count INT,
                    dislikes_count INT,
                    favorite_count INT,
                    comments INT,
                    duration TIME,
                    thumbnail TEXT,
                    caption_status TEXT
                )""")

        for item in response['items']:
            video_data = {
                "channel_name":item['snippet']['channelTitle'],
                "Video_Id": item['id'],
                "video_name": item['snippet']['title'],
                "Description": item['snippet'].get('description', ''),
                "Tags": json.dumps(item.get('tags', [])),
                "Publish_Date": item['snippet']['publishedAt'],
                "Views": item['statistics'].get('viewCount', 0),
                "Likes": item['statistics'].get('likeCount', 0),
                "Dislikes": item['statistics'].get('dislikeCount', 0),
                "favorite_count": item['statistics'].get('favoriteCount', 0),
                "Comments": item['statistics'].get('commentCount', 0),
                "Duration": item['contentDetails'].get('duration'),
                "Thumbnail": json.dumps(item['snippet']['thumbnails']),
                "caption_status": item['contentDetails'].get('caption')
            }

            video_list.append(video_data)

            duration_seconds = parse_duration(video_data['Duration'])
            if duration_seconds is not None:
                duration = timedelta(seconds=duration_seconds)
            else:
                duration = timedelta(seconds=0)
            sql_duration = (datetime.min + duration).time()

            iso_datetime = video_data['Publish_Date']
            parsed_datetime = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
            mysql_published_date = parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("""INSERT INTO video_details (channel_name,video_id, video_name, description, tags, published_date, views_count, likes_count, dislikes_count, favorite_count, comments, duration, thumbnail, caption_status)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s )
                              ON DUPLICATE KEY UPDATE
                              channel_name = VALUES(channel_name),
                              video_id = VALUES(video_id),
                              video_name = VALUES(video_name),
                              description = VALUES(description),
                              tags = VALUES(tags),
                              published_date = VALUES(published_date),
                              views_count = VALUES(views_count),
                              likes_count = VALUES(likes_count),
                              dislikes_count = VALUES(dislikes_count),
                              favorite_count = VALUES(favorite_count),
                              comments = VALUES(comments),
                              duration = VALUES(duration),
                              thumbnail = VALUES(thumbnail),
                              caption_status = VALUES(caption_status)""",
                           (video_data['channel_name'],video_data['Video_Id'], video_data['video_name'], video_data['Description'], video_data['Tags'], mysql_published_date, video_data['Views'], video_data['Likes'], video_data['Dislikes'], video_data['favorite_count'], video_data['Comments'], sql_duration, video_data['Thumbnail'], video_data['caption_status']))

            mydb.commit()
    return video_list

# Get Comment Details
def get_comment_details(video_ids):
    comment_list = []
    try:
        cursor.execute("""CREATE TABLE IF NOT EXISTS comment_details (
                            comment_id VARCHAR(255) PRIMARY KEY,
                            video_id VARCHAR(255),
                            comment_text TEXT,
                            comment_author VARCHAR(255),
                            comment_published_date DATETIME
                        )""")
        for video_id in video_ids:
            request = youtube_data.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100
            )
            response = request.execute()

            for item in response['items']:
                comment_data = {
                    "Comment_ID": item['snippet']['topLevelComment']['id'],
                    "Video_Id": item['snippet']['topLevelComment']['snippet']['videoId'],
                    "Comment_Text": item['snippet']['topLevelComment']['snippet']['textDisplay'],
                    "comment_author_Name": item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                    "comment_published_date": item['snippet']['topLevelComment']['snippet']['publishedAt']
                }

                comment_list.append(comment_data)

                iso_datetime = comment_data['comment_published_date']
                parsed_datetime = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))
                mysql_published_date = parsed_datetime.strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute("""INSERT INTO comment_details (comment_id, video_id, comment_text, comment_author, comment_published_date)
                                  VALUES (%s, %s, %s, %s, %s)
                                  ON DUPLICATE KEY UPDATE
                                  video_id = VALUES(video_id),
                                  comment_text = VALUES(comment_text),
                                  comment_author = VALUES(comment_author),
                                  comment_published_date = VALUES(comment_published_date)""",
                               (comment_data['Comment_ID'], comment_data['Video_Id'], comment_data['Comment_Text'], comment_data['comment_author_Name'], mysql_published_date))
                mydb.commit()
                    
    except Exception as e:
        print(f"Error: {e}")
        
    return comment_list

# Get Playlist Id
def get_playlist_info(channel_id):
    cursor.execute("""CREATE TABLE IF NOT EXISTS playlist_info (
                        playlist_id VARCHAR(255) PRIMARY KEY,
                        playlist_name VARCHAR(255),
                        playlist_channel_id VARCHAR(255),
                        video_count BIGINT
                    )""")
    
    playlists = []
    request = youtube_data.playlists().list(
        part="snippet,contentDetails",
        channelId=channel_id
    )
    response = request.execute()
    next_page_token = None 
    for item in response.get('items', []):
        playlist_data = {
            "playlist_id": item['id'],
            "playlist_name": item['snippet']['title'],
            "playlist_channel_id": item['snippet']['channelId'],
            "video_count": item['contentDetails']['itemCount']
        }
    
        cursor.execute("""INSERT INTO playlist_info (playlist_id, playlist_name, playlist_channel_id, video_count) VALUES (%s, %s, %s, %s)
                          ON DUPLICATE KEY UPDATE
                          playlist_name = VALUES(playlist_name),
                          playlist_channel_id = VALUES(playlist_channel_id),
                          video_count = VALUES(video_count)""",
                       (playlist_data['playlist_id'], playlist_data['playlist_name'], playlist_data['playlist_channel_id'], playlist_data['video_count']))
        
        mydb.commit()
    
        playlists.append(playlist_data)
        break   

    return playlists

# Fetch All Data
def fetch_all_data(channel_id):
    channel_info = get_channel_info(channel_id)
    video_ids = get_video_ids(channel_id)
    video_details = get_video_details(video_ids)
    comment_details = get_comment_details(video_ids)
    playlist_details = get_playlist_info(channel_id)
    
    return {
        "channel_details": pd.DataFrame(channel_info),
        "video_ids": pd.DataFrame(video_ids),
        "video_details": pd.DataFrame(video_details),
        "comment_details": pd.DataFrame(comment_details),
        "playlist_details" :pd.DataFrame(playlist_details)
                                }

# Streamlit page
def main():
    
    st.sidebar.header(':green[Gateway to Data Collection,Analysis, FAQ]')
    option=st.sidebar.radio(":black[Select option]",['Home','Data Collection','Data Analysis', 'FAQ'])
    with st.sidebar:
    
       
        st.write('-----')
           
    if option=="Home":
            st.spinner("Collecting. Data....")
            st.title('***:red[You]Tube :violet[Data Harvesting & Warehousing using SQL and Streamlit]***')
            st.subheader(':violet[Domain :] Social Media')
            st.subheader(':violet[Skill Take Away :]')
            st.markdown(''' 
                        - Python scripting,
                        - Data Collection,
                        - API integration,
                        - Data Management using SQL,
                        - Visualization by Matplotlib,
                        - Streamlit''')
            st.subheader(":violet[Conclusion]")
            st.markdown("""This project aims to develop a user-friendly Streamlit application that utilizes the Google API to extract information on a YouTube channel, stores it in a SQL database, and enables users to search for channel details and join tables to view data in the app.""")
           

    elif option=="Data Collection":
            st.header('***:white[Data Collection and Upload]***', divider= 'red')
            st.markdown(''' Clicking the 'View & Store in SQL' button will display an overview of youtube channel''')
            channel_id = st.text_input("Enter Channel ID")

            if st.button("View & Store in SQL"):
                with st.spinner('Collecting data...'):
                    st.success("Channel Details Stored in DataBase Successfully")
                    try:
                        details = fetch_all_data(channel_id)
                        
                        st.subheader('Channel Details')
                        st.write(details["channel_details"])

                        st.subheader('Video Details')
                        st.write(details["video_details"])

                        st.subheader('Comment Details')
                        st.write(details["comment_details"])

                        st.subheader('Playlist_details')
                        st.write(details['playlist_details'])
                    except KeyError as e:
                        st.error(f"KeyError: {e}")
                    except Exception as e:
                        st.error(f"An error occurred: {e}")
                        
                        


                    except HttpError as e:
                        if e.resp.status == 403 and e.error_details[0]["reason"] == 'quotaExceeded':
                            st.error("API Quota exceeded. Please try again later.")
                        else:
                            st.error(f"An HTTP error occurred: {e}")
                    except ValueError as e:
                        st.error(f"{e}")
                 
                        st.error(f"Please ensure to give a valid channel ID. Error: {e}")

            if st.button('List of Stored Channel_Details'):
                cursor.execute("SELECT channel_name , COUNT(*) as video_count FROM video_details GROUP BY channel_name  ORDER BY video_count DESC")
                data = cursor.fetchall()
                df = pd.DataFrame(data, columns=['Channel Name' , 'Video_Count'])
                st.write(df)

    if option == "Data Analysis":
        st.header("Visualize the Details of Channels")

    # Fetch channel names
        cursor.execute("SELECT channel_name, COUNT(*) as video_count FROM video_details GROUP BY channel_name ORDER BY video_count DESC")
        channel_names_data = cursor.fetchall()
        channel_names = [channel[0] for channel in channel_names_data]  # Extract channel names
        selected_channels = st.multiselect("Select the Channels to view details", channel_names)
    
        if st.button("View"):
            for channel_name in selected_channels:
                st.subheader(f"Details for {channel_name}")
                query = "SELECT channel_name, views_count, likes_count FROM video_details WHERE channel_name=%s"
                cursor.execute(query, (channel_name,))
                channel_data = cursor.fetchall()
            
            if channel_data:
                df = pd.DataFrame(channel_data, columns=['Channel Name', 'Views Count', 'Likes Count'])
                st.write(df)
                views_sum = df['Views Count'].sum()
                likes_sum = df['Likes Count'].sum()
                labels = ['Views', 'Likes']
                sizes = [views_sum, likes_sum]

                fig, ax = plt.subplots()
                ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax.axis('equal') 
                plt.title(f"Views and Likes for {channel_name}")
                plt.legend()
                
                st.pyplot(fig)
            else:
                st.write(f"No data found for {channel_name}")

    elif option == "FAQ":
        
        st.header("Frequently Asked Questions",divider= 'red')
        st.subheader("Queries")
            
        questions = [
                    "1. What are the names of all the videos and their corresponding channels?",
                    "2. Which channels have the most number of videos, and how many videos do they have?",
                    "3. What are the top 10 most viewed videos and their respective channels?",
                    "4. How many comments were made on each video, and what are their corresponding video names?",
                    "5.Which videos have the highest number of likes, and what are their corresponding channel names?",
                    "6. What is the total number of likes and dislikes for each video, and what are  their corresponding video names?",
                    "7. What is the total number of views for each channel, and what are their corresponding channel names?",
                    "8. What are the names of all the channels that have published videos in the year 2022?",
                    "9. What is the average duration of all videos in each channel, and what are their corresponding channel names ?",
                    "10. Which videos have the highest number of comments, and what are their corresponding channel names?"
                    ]

        selected_questions = st.multiselect("Select questions to execute", questions)
        if st.button("Run Selected Queries"):

            for selected_question in selected_questions:
        
                if selected_question == questions[0]:
                    cursor.execute("SELECT channel_name,video_name FROM video_details GROUP BY channel_name")
                    data = cursor.fetchall()
                    df = pd.DataFrame(data, columns=['Channel Name', 'video_name'])
                    st.subheader(":violet[Names of All Videos & Channels]")
                    st.write(df)

                        
                elif selected_question == questions[1]:
                    cursor.execute("SELECT channel_name, COUNT(*) as video_count FROM video_details GROUP BY channel_name ORDER BY video_count DESC")
                    data=cursor.fetchall()
                    df = pd.DataFrame(data, columns=['Channel Name', 'Counts'])
                    st.subheader(":violet[Channels have the Most Number of Videos]")
                    st.write(df)

                    
                elif selected_question == questions[2]:
                    cursor.execute("SELECT channel_name,video_name AS title,views_count FROM video_details ORDER BY views_count DESC LIMIT 10")
                    data=cursor.fetchall()
                    df = pd.DataFrame(data, columns=['Channel Name', 'Title', 'Views(In Mn)'])
                    st.subheader(":violet[Top 10 Most Viwed Videos]")
                    st.write(df)

                elif selected_question == questions[3]:
                    cursor.execute("SELECT channel_name,video_name AS title,comments FROM video_details GROUP BY channel_name")
                    data=cursor.fetchall()
                    df=df=pd.DataFrame(data, columns=['Channel_name','Title','Comments'])
                    st.subheader(":violet[Comments Count for Each Videos]")
                    st.write(df)

                elif selected_question == questions[4]:
                    cursor.execute("SELECT channel_name,MAX(likes_count) as max_likes FROM video_details GROUP BY channel_name")
                    data=cursor.fetchall()
                    df=pd.DataFrame(data, columns=['Channel_Name','Likes'])
                    st.subheader(":violet[Videos have Highest NUmber of Likes]")
                    st.write(df)

                elif selected_question == questions[5]:
                    cursor.execute("SELECT channel_name ,video_name AS title, SUM(likes_count) as total_likes, SUM(dislikes_count) as total_dislikes FROM video_details GROUP BY title")
                    data=cursor.fetchall()
                    df=pd.DataFrame(data, columns=['Channel_Name','Title','Likes','Dislikes'])
                    st.subheader(":violet[Average Durations for each Channel]")
                    st.write(df)

                elif selected_question == questions[6]:
                    cursor.execute("SELECT channel_name, SUM(views_count) as total_views FROM video_details GROUP BY channel_name")
                    data=cursor.fetchall()
                    df = pd.DataFrame(data, columns=['Channel_Name', 'Views'])
                    st.subheader(":violet[Total Number of Views of Each Channel]")
                    st.write(df)

                elif selected_question == questions[7]:
                    cursor.execute("SELECT DISTINCT channel_name FROM video_details WHERE YEAR(published_date) = 2022; ")
                    data=cursor.fetchall()
                    df = pd.DataFrame(data, columns=['Channel_Name'])
                    st.subheader(":violet[Names of Channels have passed a videos in year of 2022]")
                    st.write(df)

                elif selected_question == questions[8]:
                    cursor.execute("SELECT channel_name, AVG(duration) AS avg_duration FROM video_details GROUP BY channel_name ")
                    data=cursor.fetchall()
                    df = pd.DataFrame(data, columns=['Channel_Name', 'Avg_Duration'])
                    st.subheader(":violet[Average Durations for each Channel]")
                    st.write(df)

                elif selected_question == questions[9]:
                    cursor.execute("""SELECT  channel_name,video_name AS title, SUM(comments) as comments
                            FROM video_details 
                            GROUP BY title, channel_name 
                            ORDER BY comments DESC 
                            LIMIT 25
                        """)
                    data = cursor.fetchall()
                    df=pd.DataFrame(data,columns=['Channel_Name','title','Comments'])
                    st.subheader(":violet[Top 25 Videos by Highest Number of Comments]")
                    st.write(df)
                    
            
if __name__ == "__main__":
    main()