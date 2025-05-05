# Cluedo Game Implementation

## Project Description
This project is a digital implementation of the classic murder mystery board game Cluedo (also known as Clue). The game allows players to assume the roles of characters trying to solve a murder by identifying the murderer, the weapon used, and the room where the crime occurred.

## How to Run the Game

### Prerequisites
Before running the game, ensure you have the following installed:
- Python 3.6 or higher
- Required Python packages:
  - matplotlib
  - numpy
  - pandas
  - moviepy (optional, for game animations)

### Installation
1. Clone this repository or download the source code
2. Install the required dependencies:
```
pip install matplotlib numpy pandas
pip install moviepy  # Optional, for game animations
```

### Running the Game
1. Navigate to the source code directory
2. Run the main.py file:
```
python main.py
```
3. Follow the on-screen prompts to set up the game:
   - Enter the number of human players (0-6)
   - Enter the number of AI players (0-6)
   - The total number of players will be adjusted to be between 3-6

## Game Rules

### Overview
Cluedo is a murder mystery game where players move around a mansion, gather clues, and make deductions to identify:
1. The murderer (one of the game characters)
2. The murder weapon
3. The room where the murder took place

### Gameplay
1. Players take turns rolling dice and moving around the mansion board
2. When a player enters a room, they can make a suggestion about the murder
3. Other players must show cards that disprove the suggestion if they have them
4. Players gather information from these interactions to deduce the solution
5. When a player thinks they know the solution, they can make an accusation
6. If the accusation is correct, they win; if incorrect, they are eliminated from the game

### Game Modes
- Human players: Interactive gameplay where human players make decisions
- AI players: Computer-controlled players that make decisions automatically
- Mixed: A combination of human and AI players

## Project Structure
The project is organized into several modules:
- `Actions/`: Contains game actions like movement and suggestions
- `Data/`: Game data and constants
- `Game/`: Core game logic and management
- `Knowledge/`: Player knowledge and deduction systems
- `Objects/`: Game objects and entities
- `Output/`: Generated game outputs (scoresheets, board states)
- `Player/`: Player classes (human and AI)
- `Visualization/`: Board rendering and visualization
- `main.py`: Main entry point for the game

## Features
- Interactive gameplay with human players
- AI players with strategic decision-making
- Visual representation of the game board
- Detailed scoresheets tracking player knowledge
- Game animations showing the progression of the game
- Support for 3-6 players (any combination of human and AI)

## Output
The game generates several outputs in the `Output/` directory:
- Scoresheets for each round
- Final scoresheet
- Board state visualizations
- Game animation (created at the end of the game)

## Development
This project was developed as part of CS 670 - Artificial Intelligence course, applying concepts of logic programming and artificial intelligence to create intelligent game agents.
