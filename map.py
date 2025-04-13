import pygame
import random
from decision_point import DecisionPoint


class Map:
	def __init__(self, game, stage_file):
		self.game = game
		self.tiles = []
		self.bricks = []
		self.steel_walls = []
		self.eagles = []
		self.tank1_pos = None
		self.tank2_pos = None
		self.decision_points = []
		self.load_stage(stage_file)

	def load_stage(self, stage_file):
		with open(stage_file, "r") as f:
			for row_index, line in enumerate(f):
				row = []
				for col_index, tile in enumerate(line.rstrip()):
					if tile == "#":
						self.bricks.append({
							"x": col_index * self.game.TILE_SIZE,
							"y": row_index * self.game.TILE_SIZE,
							"destroyed": False
						})
					elif tile == "S":
						self.steel_walls.append({
							"x": col_index * self.game.TILE_SIZE,
							"y": row_index * self.game.TILE_SIZE
						})
					elif tile == "A" or tile == "B":
						self.eagles.append({
							"x": col_index * self.game.TILE_SIZE,
							"y": row_index * self.game.TILE_SIZE,
							"width": 64,  # Set eagle collision box width
							"height": 64,  # Set eagle collision box height
							"type": tile,
							"destroyed": False  # Intact initially
						})
					elif tile == "2":
						# self.tank2_pos = (544 - self.game.TANK_SIZE / 2, 32 - self.game.TANK_SIZE / 2)
						starting_positions = [
							[32, 32],
							[96, 32],
							[160, 32],
							[224, 32],
							[288, 32],
							[544, 32],
							[608, 32],
							[672, 32],
							[736, 32],
							[800, 32],
						]
						rand_pos = random.choice(starting_positions)
						self.tank2_pos = (
							rand_pos[0] - self.game.TANK_SIZE / 2,
							rand_pos[1] - self.game.TANK_SIZE / 2
						)
					elif tile == "1":
						#self.tank1_pos = (288 - self.game.TANK_SIZE / 2, 800 - self.game.TANK_SIZE / 2)
						starting_positions = [
							[32, 800],
							[96, 800],
							[160, 800],
							[224, 800],
							[288, 800],
							[544, 800],
							[608, 800],
							[672, 800],
							[736, 800],
							[800, 800],
						]
						rand_pos = random.choice(starting_positions)
						self.tank1_pos = (
							rand_pos[0] - self.game.TANK_SIZE / 2,
							rand_pos[1] - self.game.TANK_SIZE / 2
						)
					row.append(tile)
				self.tiles.append(row)
		self.generate_decision_points()

	def draw(self):
		# Draw Bricks
		for brick in self.bricks:
			if not brick["destroyed"]:
				self.game.screen.blit(self.game.IMAGES["#"], (brick["x"], brick["y"]))

		# Draw Steel
		for steel in self.steel_walls:
			self.game.screen.blit(self.game.IMAGES["S"], (steel["x"], steel["y"]))

		# Draw Eagles
		for eagle in self.eagles:
			if eagle["destroyed"]:
				self.game.screen.blit(self.game.IMAGES["C"], (eagle["x"], eagle["y"]))
			else:
				self.game.screen.blit(self.game.IMAGES[eagle["type"]], (eagle["x"], eagle["y"]))

		# Draw Tanks
		for tank in self.game.tanks:
			tank.draw()

	def add_decision_point(self, y, x):
		self.decision_points.append({
			"x": x,
			"y": y
		})

	def generate_decision_points(self):
		count = 0
		for y in range(26):
			if y % 2 != 0:
				for x in range(26):
					if x % 2 != 0:
						dp = DecisionPoint(self.game.TILE_SIZE * y, self.game.TILE_SIZE * x, count)
						count = count + 1
						self.decision_points.append(dp)
