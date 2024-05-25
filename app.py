import streamlit as st
import pandas as pd
from joblib import load
from pathlib import Path

# Function to load the model using the appropriate caching decorator
@st.cache_resource
def load_model(model_path):
    model = load(model_path)
    return model

# CP Calculation function
def calculate_cp(attack, defense, hp, iv_attack, iv_defense, iv_hp, cpm):
    return int(((attack + iv_attack) * (defense + iv_defense)**0.5 * (hp + iv_hp)**0.5 * cpm**2) / 10)

# Function to fetch best movesets based on DPS, ensuring two distinct charge moves
def fetch_best_moves(pokemon_name, pokemon_data):
    try:
        filtered_data = pokemon_data[pokemon_data['NAME'].str.lower() == pokemon_name.lower()]
        best_fast_move = filtered_data.loc[filtered_data['ADJUSTED_FAST_MOVE_DPS'].idxmax()]
        top_charge_moves = filtered_data.nlargest(3, 'ADJUSTED_CHARGE_MOVE_DPS').drop_duplicates(subset=['CHARGE_MOVE'])
        return {
            "fast_move": (best_fast_move['FAST_MOVE'], round(best_fast_move['ADJUSTED_FAST_MOVE_DPS'], 2)),
            "charge_moves": [(row['CHARGE_MOVE'], round(row['ADJUSTED_CHARGE_MOVE_DPS'], 2)) for index, row in top_charge_moves.iterrows()][:2]
        }
    except Exception as e:
        st.error(f"Error fetching moves: {e}")
        return {"fast_move": (None, None), "charge_moves": [(None, None), (None, None)]}

# Function to estimate level based on CP
def estimate_level(cp, levels_data, base_stats, ivs, buddy_boost=False):
    possible_levels = []
    for level, cpm in levels_data.items():
        estimated_cp = calculate_cp(base_stats['BASE_ATTACK'], base_stats['BASE_DEFENSE'], base_stats['BASE_HP'], *ivs, cpm)
        if (buddy_boost and cp <= estimated_cp * 1.1) or (not buddy_boost and cp <= estimated_cp):
            possible_levels.append((level, abs(cp - estimated_cp)))

    if possible_levels:
        return min(possible_levels, key=lambda x: x[1])[0]
    return None

# Display function for each Pokémon input
def display_pokemon_input(index, pokemon_data, levels_data):
    st.subheader(f'Pokemon {index + 1}')
    pokemon_name = st.text_input(f'Pokemon {index + 1} Name', key=f'name{index}')
    cp = st.number_input(f'Exact CP for Pokemon {index + 1}', min_value=10, max_value=5010, step=1, key=f'cp{index}')
    buddy_boost = st.checkbox("Buddy Boost", key=f'buddy{index}')
    iv_attack = st.slider('IV Attack', 0, 15, key=f'iv_attack{index}')
    iv_defense = st.slider('IV Defense', 0, 15, key=f'iv_defense{index}')
    iv_hp = st.slider('IV HP (Stamina)', 0, 15, key=f'iv_hp{index}')

    if pokemon_name and cp:
        base_stats = pokemon_data[pokemon_data['NAME'] == pokemon_name][['BASE_ATTACK', 'BASE_DEFENSE', 'BASE_HP']].iloc[0].to_dict()
        moveset = fetch_best_moves(pokemon_name, pokemon_data)
        ivs = (iv_attack, iv_defense, iv_hp)
        estimated_level = estimate_level(cp, levels_data, base_stats, ivs, buddy_boost)
        
        st.write(f"Best Fast Move: {moveset['fast_move'][0]} (DPS: {moveset['fast_move'][1]})")
        for i, move in enumerate(moveset['charge_moves']):
            st.write(f"Top Charge Move {i+1}: {move[0]} (DPS: {move[1]})")
        if estimated_level:
            st.write(f'Estimated Level for Pokemon {index + 1}: {estimated_level}')
        else:
            st.error("Level couldn't be estimated. Please adjust CP or enable Buddy Boost.")

# Main function to set up Streamlit app
def main():
    data = pd.read_csv('notebooks/model_development/data.csv')
    levels_data = pd.read_csv('datasets/levels.csv', index_col='LEVEL')['CPM'].to_dict()
    model_path = Path('models/great_league_model.joblib')
    model_great_league = load_model(model_path)
    st.header('Choose Your League')
    selected_league = st.radio("Select League", ('Great League', 'Ultra League', 'Master League'))

    if selected_league == 'Great League':
        st.header('Great League Team Setup')
        for i in range(3):
            display_pokemon_input(i, data, levels_data)
        if st.button('Make Team Recommendations'):
            # Team recommendation logic goes here
            st.write("Team recommendations will be displayed here.")

if __name__ == "__main__":
    main()
