import requests
import pandas as pd
import streamlit as st

# Streamlit App
st.title("Edmonton Oilers Data Analysis")

# Function to launch the script
def launch_script(url):
    dates = get_game_dates(url)
    game_day_urls = get_url_games(dates)
    games_info = []
    goals_info = []
    for index, game_day_url in enumerate(game_day_urls):
        game_info = get_game_info(game_day_url, index)
        games_info.append(game_info)
        goal_game_info = get_goals_info(game_day_url)
        goals_info.extend(goal_game_info)
    games_info_df = pd.DataFrame(games_info)
    goals_info_df = pd.DataFrame(goals_info)
    roster_df = get_roster()

    return games_info_df, goals_info_df, roster_df

def get_game_dates(url):
    first_game_data = '2023-10-11'
    response = requests.get(url)
    data = response.json()
    data_games = data['games']
    game_dates = [item['gameDate'] for item in data_games]
    index = game_dates.index(first_game_data)
    game_dates_regular = game_dates[index: index + 82]
    return game_dates_regular

def get_url_games(dates):
    return [f'https://api-web.nhle.com/v1/score/{date}' for date in dates]

def get_game_info(url, index):
    response = requests.get(url)
    data = response.json()
    data_games = data['games']
    data_game = find_game_day_data(data_games)
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

    return {
        'Game#': index + 1,
        'GameID': game_id,
        'Date': date,
        'Opponent': opponent,
        'Home/Away': away_or_home,
        'Scored goals': scored_goals,
        'Conceded goals': conceded_goals,
        'Win/Loss': win_loss,
    }

def find_game_day_data(data_games):
    for data in data_games:
        if data['awayTeam']['abbrev'] == 'EDM' or data['homeTeam']['abbrev'] == 'EDM':
            return data

def get_goals_info(url):
    response = requests.get(url)
    data = response.json()
    data_games = data['games']
    data_game = find_game_day_data(data_games)
    game_id = data_game['id']
    date = data_game['gameDate']
    goals = data_game['goals']
    goals_info = []

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

    return goals_info

def get_roster():
    url = "https://api-web.nhle.com/v1/roster/EDM/20232024"
    position_mapping = {
        'forwards': 'forward',
        'defensemen': 'defenseman',
        'goalies': 'goalie'
    }

    response = requests.get(url)
    data = response.json()
    roster_data = []

    for position, players in data.items():
        singular_position = position_mapping.get(position, position)
        for player in players:
            name = f"{player['firstName']['default']} {player['lastName']['default']}"
            roster_data.append({'Position': singular_position, 'Name': name})

    return pd.DataFrame(roster_data)

# Main logic for Streamlit App
api_url = 'https://api-web.nhle.com/v1/club-schedule-season/EDM/20232024'

if st.button('Fetch Data'):
    with st.spinner('Fetching data...'):
        games_info_df, goals_info_df, roster_df = launch_script(api_url)
        st.success('Data fetched successfully!')

        st.subheader("Games Information")
        st.dataframe(games_info_df)

        st.subheader("Goals Information")
        st.dataframe(goals_info_df)

        st.subheader("Roster Information")
        st.dataframe(roster_df)

        # Provide download links for CSV files
        st.download_button(
            label="Download Games Info as CSV",
            data=games_info_df.to_csv(index=False).encode('utf-8'),
            file_name='games_info.csv',
            mime='text/csv'
        )

        st.download_button(
            label="Download Goals Info as CSV",
            data=goals_info_df.to_csv(index=False).encode('utf-8'),
            file_name='goals_info.csv',
            mime='text/csv'
        )

        st.download_button(
            label="Download Roster Info as CSV",
            data=roster_df.to_csv(index=False).encode('utf-8'),
            file_name='roster.csv',
            mime='text/csv'
        )

