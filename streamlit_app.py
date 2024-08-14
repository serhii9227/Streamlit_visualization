import matplotlib.pyplot as plt
import streamlit as st
import requests
import pandas as pd

# API URLs and first game date
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

# Gather game and goal information
games_info = []
goals_info = []
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

            goals = data_game['goals']
            for goal in goals:
                period = goal['period']
                time = goal['timeInPeriod']
                team = goal['teamAbbrev']
                first_name = goal['firstName']['default']
                last_name = goal['lastName']['default']

                assist_1 = goal['assists'][0]['name']['default'] if len(goal['assists']) >= 1 else ''
                assist_2 = goal['assists'][1]['name']['default'] if len(goal['assists']) >= 2 else ''

                goals_info.append({
                    'ID': game_id,
                    'Date': date,
                    'Period': period,
                    'Team': team,
                    'Scored by': f"{first_name} {last_name}",
                    'Assist 1': assist_1,
                    'Assist 2': assist_2,
                    'Time': time
                })

# Convert the lists of game and goal information to DataFrames
df_games = pd.DataFrame(games_info)
df_goals = pd.DataFrame(goals_info)

# Fetch the roster data
url_roster = "https://api-web.nhle.com/v1/roster/EDM/20232024"
position_mapping = {
    'forwards': 'forward',
    'defensemen': 'defenseman',
    'goalies': 'goalie'
}

response = requests.get(url_roster)
data = response.json()
roster_data = []

for position, players in data.items():
    singular_position = position_mapping.get(position, position)
    for player in players:
        name = f"{player['firstName']['default']} {player['lastName']['default']}"
        roster_data.append({'Position': singular_position, 'Name': name})

# Convert the roster data to a DataFrame
df_roster = pd.DataFrame(roster_data)

# Streamlit interface
st.title("Edmonton Oilers 2023-2024 Data")

# Display the games dataset
st.header("Games Information")
st.write("Here is the dataset of the games played by Edmonton Oilers in the 2023-2024 season:")
st.dataframe(df_games)

# Display the goals dataset
st.header("Goals Information")
st.write("Here is the dataset of goals scored in Edmonton Oilers' games:")
st.dataframe(df_goals)

# Display the roster dataset
st.header("Roster Information")
st.write("Here is the roster of Edmonton Oilers for the 2023-2024 season:")
st.dataframe(df_roster)

# Optionally, allow users to download the datasets as CSV files
st.download_button(
    label="Download Games Info as CSV",
    data=df_games.to_csv(index=False).encode('utf-8'),
    file_name='games_info.csv',
    mime='text/csv',
)

st.download_button(
    label="Download Goals Info as CSV",
    data=df_goals.to_csv(index=False).encode('utf-8'),
    file_name='goals_info.csv',
    mime='text/csv',
)

st.download_button(
    label="Download Roster Info as CSV",
    data=df_roster.to_csv(index=False).encode('utf-8'),
    file_name='roster.csv',
    mime='text/csv',
)

# Filter the roster to get forwards
forwards = df_roster[df_roster['Position'] == 'forward']  # Adjust 'Position' if needed

# Streamlit interface
st.title("Points per Game for All Forwards - Edmonton Oilers 2023-2024")

# Create a figure for plotting
plt.figure(figsize=(18, 6))  # Make the plot wider

# Iterate over all forwards to plot their points per game
for player_full_name in forwards['Name']:  # Adjust the column name as needed
    last_name = player_full_name.split()[-1]  # Extract last name

    # Merge game data and goal data
    merged_data = pd.merge(df_goals, df_games[['GameID', 'Game#', 'Date', 'Win/Loss']], left_on='ID', right_on='GameID')

    player_points = []
    game_numbers = []
    results = []

    # Calculate points per game for each forward
    for game in df_games['Game#']:
        if game not in merged_data['Game#'].values:
            continue

        game_goals = merged_data[merged_data['Game#'] == game]

        game_points = 0
        for index, row in game_goals.iterrows():
            if last_name in str(row['Scored by']):
                game_points += 1
            if last_name in str(row['Assist 1']) or last_name in str(row['Assist 2']):
                game_points += 1

        player_points.append(game_points)
        game_numbers.append(game)

        result = merged_data[merged_data['Game#'] == game].iloc[0]['Win/Loss']
        results.append(result)

    plt.plot(game_numbers, player_points, marker='o', label=player_full_name)

# Set y-limits and prepare for annotation
ymin, ymax = plt.ylim()
annotation_offset = 6  # Set the y-position for all annotations

# Annotate game results
for game_number, result in zip(game_numbers, results):
    plt.annotate(result,
                 (game_number, annotation_offset),  # Align annotations on the same line
                 textcoords="offset points",
                 xytext=(0, 10),
                 ha='center',
                 rotation=90,
                 fontsize=8,
                 color='black')

# Set plot labels and title
plt.xlabel('Game#')
plt.ylabel('Points')
plt.title('Points per Game for All Forwards')
plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1))  # Adjust legend position
plt.grid(True)

# Set x-ticks and y-ticks
x_ticks = range(1, max(df_games['Game#']) + 1, 1)
plt.xticks(ticks=x_ticks, rotation=90)

y_ticks = range(0, int(ymax) + 2)
plt.yticks(ticks=y_ticks)

# Adjust layout
plt.tight_layout()
plt.subplots_adjust(top=0.85)  # Adjust the top margin to move the title up

# Show the plot in Streamlit
st.pyplot(plt)


