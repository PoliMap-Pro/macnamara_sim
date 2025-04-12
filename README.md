# MacNamara Election Simulator

A simulation tool for the Australian House of Representatives election in the MacNamara electorate, using preferential (ranked choice) voting.

## Features

- Simulates preferential voting with four parties: ALP, LIB, GRN, and OTH (Others/Independents)
- Configurable primary vote percentages
- Configurable preference flows between parties
- Visualizes primary vote share and two-party preferred results
- Accurately models the Australian electoral system's instant-runoff voting

## Requirements

- Python 3.8+
- Streamlit
- Pandas
- Plotly
- Votekit

## Installation

```bash
# Using uv (recommended)
uv pip install -r requirements.txt
```

## Usage

```bash
# Run the Streamlit app
uv run streamlit run app.py
```

## How It Works

The simulation uses the Votekit library to model preferential voting. It takes primary vote percentages for each party and preference flows between parties as input, then simulates the counting process to determine the final two candidates and their vote percentages.