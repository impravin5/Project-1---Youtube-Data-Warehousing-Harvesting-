# Project-1---Youtube-Data-Warehousing-Harvesting-

#YouTube Data Harvesting and Warehousing using SQL and Streamlit
#Overview
          This project aims to develop a user-friendly Streamlit application that utilizes the Google API to extract information on a YouTube channel, store it in a SQL database, and enable users to search for channel details and join tables to view data in the app. The main features of this project include:
          -Data Collection
          -Data Storage in SQL Database
          -Data Analysis and Visualization
          -Frequently Asked Questions (FAQ) Section


## Key Features

- **Channel Information**: Retrieve and store channel details such as name, ID, subscriber count, total views, description, and upload playlist ID.
- **Video Details**: Retrieve and store video details such as video ID, name, description, tags, publish date, view count, like count, dislike count, favorite count, comment count, duration, thumbnail, and caption status.
- **Comment Details**: Retrieve and store comments for each video, including comment ID, video ID, text, author name, and publish date.

## Technologies Used

- **Python**: Scripting and API integration.
- **MySQL**: Database for storing the retrieved data.
- **Streamlit**: Web interface for interacting with the system.
- **YouTube API**: To fetch data from YouTube.

## Key Features
Home Page: 
          An introduction to the project, its purpose, and the skills gained.
Data Collection: 
          Users can input a YouTube channel ID to fetch and store data into the SQL database.
Data Analysis: 
          Visualizations and data insights from the collected YouTube data.
FAQ: 
          Predefined queries to answer common questions about the data.

## Dependencies:

-googleapiclient.discovery:
          To interact with the YouTube API.
-mysql.connector: 
          For connecting and interacting with the MySQL database.
-pandas: 
          For data manipulation and analysis.
-streamlit:
          For creating the web application.
-matplotlib:
          For plotting charts.
-plotly.express: 
          For interactive visualizations.
-datetime:
          For date and time manipulation.
-json: 
          For JSON operations.

# **API Initialization**:
          #youtube_data = googleapiclient.discovery.build(api_service_name, api_version, developerKey=api_key)

#**Database Connection**:
python
Copy code
mydb = mysql.connector.connect(
    host="Hostname",
    user="root",
    password="password",
    database="database",
    port="port",
    auth_plugin="mysql_native_password"
)
cursor = mydb.cursor()

# **Channel Information Extraction**:
          - Create table for storing channel information.
          - Fetch and store channel data using YouTube API.
# **Video Information Extraction**:
           - Fetch video IDs from the channel's upload playlist.
           - Extract detailed information about each video and store it in the database.
# **Comment Information Extraction**:
          - Fetch comments for each video and store them in the database.
# **Playlist Information Extraction**:
           -Fetch playlist details for the channel and store them in the database.
# **Data Visualization and Analysis**:
          - Use Streamlit to create an interactive user interface.
          - Provide options to visualize data such as the number of views, likes, and comments for selected channels.
# **Frequently Asked Questions**:
          - Predefined queries to answer common questions such as the most viewed videos, channels with the most videos, etc.

## Conclusion
          #This project aims to develop a user-friendly Streamlit application that utilizes the Google API to extract information on a YouTube #channel, stores it in a SQL database, and enables users to search for channel details and join tables to view data in the app
           


