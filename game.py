import pygame
import sys
import os
import time

from agent import Agent
from tank import Tank
from map import Map


class Game:
	def __init__(self, headless=False, agent1_file=None, agent2_file=None, max_iterations=1):
		self.headless = headless
		self.agent1_file = agent1_file or "policies/agent1_policy_merged.pth"
		self.agent2_file = agent2_file or "policies/agent2_policy_merged.pth"
		self.iteration_limit = max_iterations if self.headless else None

		# Time
		self.timeElapsed = 0
		self.start_time = time.time()
		self.max_time = 12  # Seconds per game
		self.clock = pygame.time.Clock()

		# Game Variables & Agents
		self.initialized = False
		self.running = True
		self.iteration = 0
		self.map = None
		self.tanks = []
		self.tank1 = None
		self.tank2 = None
		self.agents = []
		self.agent1 = None
		self.agent2 = None
		self.agent_points = {
			'agent_1': 0,
			'agent_2': 0,
		}
		self.round_has_ended = False
		self.training_cycle_count = 0

		# Constants
		self.SCREEN_WIDTH, self.SCREEN_HEIGHT = 832, 832  # 26x26 grid of 32x32 tiles
		self.TILE_SIZE = 32
		self.FPS = 60
		self.ASSET_PATH = os.path.join(os.path.dirname(__file__), "assets/images")
		self.IMAGES = {
			"#": pygame.image.load(os.path.join(self.ASSET_PATH, "brick.png")),
			"S": pygame.image.load(os.path.join(self.ASSET_PATH, "steel.png")),
			"A": pygame.image.load(os.path.join(self.ASSET_PATH, "eagle.png")),
			"B": pygame.image.load(os.path.join(self.ASSET_PATH, "eagle.png")),
			"C": pygame.image.load(os.path.join(self.ASSET_PATH, "eagle-destroyed.png")),
		}
		self.TANK_SIZE = 52

		# Preloaded tank images
		self.tank1_images = {
			"UP": pygame.image.load(os.path.join(self.ASSET_PATH, "tank1-up.png")),
			"DOWN": pygame.image.load(os.path.join(self.ASSET_PATH, "tank1-down.png")),
			"LEFT": pygame.image.load(os.path.join(self.ASSET_PATH, "tank1-left.png")),
			"RIGHT": pygame.image.load(os.path.join(self.ASSET_PATH, "tank1-right.png")),
		}
		self.tank2_images = {
			"UP": pygame.image.load(os.path.join(self.ASSET_PATH, "tank2-up.png")),
			"DOWN": pygame.image.load(os.path.join(self.ASSET_PATH, "tank2-down.png")),
			"LEFT": pygame.image.load(os.path.join(self.ASSET_PATH, "tank2-left.png")),
			"RIGHT": pygame.image.load(os.path.join(self.ASSET_PATH, "tank2-right.png")),
		}

		# Initialize Pygame
		pygame.init()

		# Initialize Window
		if not self.headless:
			self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
			pygame.display.set_caption("Battle City Clone")

	def close_application(self):
		self.running = False
		pygame.quit()
		sys.exit()

	def print_agent_points(self):
		self.iteration += 1
		print(f"Iteration: {self.iteration}, Agent 1: {self.agent_points['agent_1']}, Agent 2: {self.agent_points['agent_2']}")

	def get_game_state(self):
		# Enhanced state to include distances, bullets, and threats
		state = {
			"tank1": {
				"x": self.tank1.x,
				"y": self.tank1.y,
				"direction": self.tank1.direction,
				"bullets": [{"x": bullet.x, "y": bullet.y} for bullet in self.tank1.bullets],
				"distance_to_tank2": ((self.tank1.x - self.tank2.x) ** 2 + (self.tank1.y - self.tank2.y) ** 2) ** 0.5,
				"destroyed": self.tank1.destroyed,
			},
			"tank2": {
				"x": self.tank2.x,
				"y": self.tank2.y,
				"direction": self.tank2.direction,
				"bullets": [{"x": bullet.x, "y": bullet.y} for bullet in self.tank2.bullets],
				"distance_to_tank1": ((self.tank2.x - self.tank1.x) ** 2 + (self.tank2.y - self.tank1.y) ** 2) ** 0.5,
				"destroyed": self.tank2.destroyed,
			},
			"eagles": [{"x": eagle["x"], "y": eagle["y"], "destroyed": eagle["destroyed"]} for eagle in self.map.eagles],
			"bricks": [{"x": brick["x"], "y": brick["y"], "destroyed": brick["destroyed"]} for brick in self.map.bricks],
			"steel_walls": [{"x": steel_wall["x"], "y": steel_wall["y"]} for steel_wall in self.map.steel_walls],
			"timeElapsed": self.timeElapsed,
		}
		return state

	def save_and_load_models(self):
		if self.headless:
			process_id = os.getpid()
			self.agent1_file = f"policies/agent1_policy_{process_id}.pth"
			self.agent2_file = f"policies/agent2_policy_{process_id}.pth"

			self.agent1.save_model(self.agent1_file)
			self.agent2.save_model(self.agent2_file)

			self.agent1.load_model(self.agent1_file)
			self.agent2.load_model(self.agent2_file)

	def init_game(self):
		# Use merged as starting model if they exist
		if os.path.exists("policies/agent1_policy_merged.pth"):
			self.agent1_file = "policies/agent1_policy_merged.pth"
		if os.path.exists("policies/agent2_policy_merged.pth"):
			self.agent2_file = "policies/agent2_policy_merged.pth"

		# Setup Tanks
		self.start_time = time.time()  # Reset start time when game starts
		self.map = Map(self, os.path.join(os.path.dirname(__file__), "stages/stage0.txt"))
		self.tanks = []
		self.tank1 = Tank(self, *self.map.tank1_pos, self.tank1_images)
		self.tank2 = Tank(self, *self.map.tank2_pos, self.tank2_images)
		self.tank1.opponent = self.tank2
		self.tank2.opponent = self.tank1
		self.tank1.eagle = min(self.map.eagles, key=lambda eagle: ((self.tank1.x - eagle["x"]) ** 2 + (self.tank1.y - eagle["y"]) ** 2) ** 0.5)
		self.tank2.eagle = min(self.map.eagles, key=lambda eagle: ((self.tank2.x - eagle["x"]) ** 2 + (self.tank2.y - eagle["y"]) ** 2) ** 0.5)

		# Setup Agents
		self.agents = []
		action_dim = 4  # 5 actions: UP, DOWN, LEFT, RIGHT, SHOOT (taken 1 out to ensure its only 4 actions for now)
		self.agent1 = Agent(self, action_dim, "agent_1")
		self.agent2 = Agent(self, action_dim, "agent_2")
		self.agent1.tank = self.tank1
		self.agent2.tank = self.tank2
		self.agent1.opponent = self.tank2
		self.agent2.opponent = self.tank1

		self.agent1.setup_model(0.001, self.agent1_file)
		self.agent2.setup_model(0.002, self.agent2_file)

		# Game Variables
		self.round_has_ended = False

		# Save and Load Models
		self.save_and_load_models()

		# Game is Fully Initialized
		self.initialized = True

	def train(self):
		self.print_agent_points()
		for agent in self.agents:
			agent.train()

	def round_over(self):
		if self.headless:
			if self.round_has_ended:
				return  # Prevent multiple calls per round

			self.round_has_ended = True  # Lock
			self.training_cycle_count += 1
			if self.training_cycle_count >= 5:
				self.train()
				self.training_cycle_count = 0

		self.init_game()

	def check_done(self):
		return (
			self.tank1.destroyed or self.tank1.eagle["destroyed"]
			or self.tank2.destroyed or self.tank2.eagle["destroyed"]
			or self.timeElapsed >= self.max_time
		)

	def update(self):
		# Initialize game if not initialized yet.
		if not self.initialized:
			self.init_game()

		# Handle Key Presses and Events
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.close_application()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					self.close_application()
				if event.key == pygame.K_r:
					self.init_game()

		# Update tanks (really just updates bullets...)
		for tank in self.tanks:
			tank.update()

		# Update Agents
		for agent in self.agents:
			agent.update()

		# ✅ Centralized game-over check
		if self.check_done() and not self.round_has_ended:
			self.round_over()

	def draw(self):
		if not self.headless:
			# Clear Screen
			self.screen.fill((0, 0, 0))

			# Draw the map
			self.map.draw()

			# Decision Points: small white dots
			# self.draw_points()

			# Update the display
			pygame.display.flip()

	def draw_points(self):
		font = pygame.font.SysFont(None, 16)  # or any size you want
		for dp in self.map.decision_points:
			# Draw the point
			pygame.draw.circle(self.screen, (255, 255, 255), (dp.x, dp.y), 5)

			# Create the text surface
			label = font.render(f"{dp.x},{dp.y}", True, (255, 255, 255))

			# Draw the text slightly below and to the left
			self.screen.blit(label, (dp.x - 10, dp.y + 6))

	# Main game loop
	def main(self):
		while self.running and (self.iteration_limit is None or self.iteration < self.iteration_limit):
			self.timeElapsed = round(time.time() - self.start_time)
			self.update()
			self.draw()
			self.clock.tick(self.FPS)

		# Automatically stop headless mode after iteration limit is reached
		if self.headless:
			self.running = False


if __name__ == "__main__":
	game = Game()
	game.main()
