# test_movement_fix.py
from Game.Game import Game
from Actions.Movement import get_available_moves

def main():
    # Create a game instance
    game = Game(0, 3)  # 0 human players, 3 AI players
    
    # Print character positions
    print("Character Board Positions:")
    for name, position in game.character_board.positions.items():
        print(f"- {name}: {position}")
    
    # Test movement for each character
    for player in game.players:
        character_name = player.character_name
        position = player.character.position
        
        print(f"\nTesting movement for {character_name} at position {position}")
        
        # Test with different dice rolls
        for dice_roll in [1, 2, 6]:
            # Get available moves using the fixed method
            available_moves = get_available_moves(
                position,
                game.mansion_board,
                game.character_board,
                dice_roll
            )
            
            print(f"  With dice roll {dice_roll}, available moves: {available_moves}")

if __name__ == "__main__":
    main()