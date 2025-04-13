# Bullet class
import pygame


class Bullet:
	def __init__(self, game, x, y, dx, dy):
		self.game = game
		self.x = x
		self.y = y
		self.dx = dx
		self.dy = dy
		self.width = 10
		self.height = 10
		self.color = (255, 255, 255)

	def update(self):
		self.x += self.dx
		self.y += self.dy

	def draw(self):
		pygame.draw.rect(self.game.screen, self.color, (self.x, self.y, self.width, self.height))

	def is_off_screen(self):
		return self.x < 0 or self.x > self.game.SCREEN_WIDTH or self.y < 0 or self.y > self.game.SCREEN_HEIGHT

	def collides_with(self, wall):
		# Check collision with a wall
		return (
			self.x < wall["x"] + self.game.TILE_SIZE
			and self.x + self.width > wall["x"]
			and self.y < wall["y"] + self.game.TILE_SIZE
			and self.y + self.height > wall["y"]
		)

	def collides_with_eagle(self, eagle):
		# Check collision with a wall
		return (
			self.x < eagle["x"] + 64
			and self.x + self.width > eagle["x"]
			and self.y < eagle["y"] + 64
			and self.y + self.height > eagle["y"]
		)

	def create_damage_bounds(self):
		# Create damage bounds based on the bullet's movement direction
		if self.dy != 0:  # Vertical movement
			return {
				"x": self.x - 12,
				"y": self.y,
				"width": 32,
				"height": 16,
			}
		elif self.dx != 0:  # Horizontal movement
			return {
				"x": self.x,
				"y": self.y - 12,
				"width": 16,
				"height": 32,
			}

	def collides_with_tank(self, tank):
		# Check if any corner of the bullet is inside the tank's bounding box
		corners = [
			(self.x, self.y),  # Top-left
			(self.x + self.width, self.y),  # Top-right
			(self.x, self.y + self.height),  # Bottom-left
			(self.x + self.width, self.y + self.height),  # Bottom-right
		]

		for corner_x, corner_y in corners:
			if (
				tank.x <= corner_x <= tank.x + tank.width
				and tank.y <= corner_y <= tank.y + tank.height
			):
				return True

		return False

	def collides_with_bullet(self, other_bullet):
		# Check if this bullet collides with another bullet
		return (
			self.x < other_bullet.x + other_bullet.width
			and self.x + self.width > other_bullet.x
			and self.y < other_bullet.y + other_bullet.height
			and self.y + self.height > other_bullet.y
		)
