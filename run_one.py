from game import Game
import os

if __name__ == "__main__":
	# Use merged policies
	agent1_file = "policies/agent1_policy_merged.pth"
	agent2_file = "policies/agent2_policy_merged.pth"

	# Launch in visual mode
	game = Game(headless=False, agent1_file=agent1_file, agent2_file=agent2_file)
	game.main()
