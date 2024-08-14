import requests
import pandas as pd
import streamlit as st

# Streamlit App
st.title("Edmonton Oilers Data Analysis")

api_url_schedule = 'https://api-web.nhle.com/v1/club-schedule-season/EDM/20232024'
first_game_data = '2023-10-11'

# Fetch the schedule data
response = requests.get(api_url_schedule)
data_api = response.json()
data_games = data_api['games']

# Extract game dates
game_dates = [item['gameDate'] for item in data_games]

# Find the index of the first game and get the regular season games
index = game_dates.index(first_game_data)
game_dates_regular = game_dates[index: index + 82]

# Construct URLs for each game day
game_day_urls = [f'https://api-web.nhle.com/v1/score/{date}' for date in game_dates_regular]

# Gather game information
games_info = []
for index, game_day_url in enumerate(game_day_urls):
    response = requests.get(game_day_url)
    data_url = response.json()
    data_games = data_url['games']
    for data_game in data_games:
        if data_game['awayTeam']['abbrev'] == 'EDM' or data_game['homeTeam']['abbrev'] == 'EDM':
            game_id = data_game['id']
            date = data_game['gameDate']

            if data_game['awayTeam']['abbrev'] == 'EDM':
                opponent = data_game['homeTeam']['abbrev']
                away_or_home = 'away'
                scored_goals = data_game['awayTeam']['score']
                conceded_goals = data_game['homeTeam']['score']
            else:
                opponent = data_game['awayTeam']['abbrev']
                away_or_home = 'home'
                scored_goals = data_game['homeTeam']['score']
                conceded_goals = data_game['awayTeam']['score']

            win_loss = 'Win' if scored_goals > conceded_goals else 'Loss'

            game_info = {
                'Game#': index + 1,
                'GameID': game_id,
                'Date': date,
                'Opponent': opponent,
                'Home/Away': away_or_home,
                'Scored goals': scored_goals,
                'Conceded goals': conceded_goals,
                'Win/Loss': win_loss,
            }
            games_info.append(game_info)

# Convert the list of game information to a DataFrame
df = pd.DataFrame(games_info)

# Streamlit interface
st.title("Edmonton Oilers Game Info")
st.write("Here is the dataset of the games played by Edmonton Oilers in the 2023-2024 season:")
st.dataframe(df)

# Optionally, allow users to download the CSV file
csv = df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download data as CSV",
    data=csv,
    file_name='games_info.csv',
    mime='text/csv',
)

