import pygame

from decision_point import DecisionPoint
from bullet import Bullet


class Tank:
	def __init__(self, game, x, y, images):
		self.game = game
		self.is_shooting = False  # Track whether the tank is shooting
		self.x = x
		self.y = y
		self.width = 52
		self.height = 52
		self.images = images
		self.direction = "UP"
		self.bullets = []
		self.last_shot_time = 0
		self.opponent = None
		self.destroyed = False
		self.game.tanks.append(self)
		self.damage_bounds_rect = {}

		self.active_keys = None  # current movement keys

		self.awaiting_decision = True
		self.most_recent_decision_point = DecisionPoint(0, 0, 0)
		self.temp_decision_point = DecisionPoint(0, 0, 0)

	def update(self):
		self.update_bullets(self.game.map.bricks, self.game.map.steel_walls, self.game.map.eagles, self.game.tank2, self.opponent.bullets)
		self.temp_decision_point = self.get_nearest_decision_point()
		if self.temp_decision_point and self.temp_decision_point.get_index() != self.most_recent_decision_point.get_index():
			self.awaiting_decision = True
			#print("Awaiting Decision")

	def draw(self):
		if not self.destroyed:
			# Draw the tank
			current_image = self.images[self.direction]
			self.game.screen.blit(current_image, (self.x, self.y))

			# Draw the bullets
			for bullet in self.bullets:
				bullet.draw()

			if self.damage_bounds_rect:
				pygame.draw.rect(self.game.screen, (255, 0, 0), (self.damage_bounds_rect["x"], self.damage_bounds_rect["y"], self.damage_bounds_rect["width"], self.damage_bounds_rect["height"]))

	def perform_action(self, keys, opponent):
		if self.destroyed:
			return

		# Calculate the tank's new position based on input
		new_x, new_y = self.x, self.y

		if keys and keys[pygame.K_UP]:
			new_y -= 4
			self.direction = "UP"
		elif keys and keys[pygame.K_DOWN]:
			new_y += 4
			self.direction = "DOWN"
		elif keys and keys[pygame.K_LEFT]:
			new_x -= 4
			self.direction = "LEFT"
		elif keys and keys[pygame.K_RIGHT]:
			new_x += 4
			self.direction = "RIGHT"
		elif keys and keys[pygame.K_SPACE]:
			self.shoot()

		# Check for collisions with walls, eagles, and the other tank
		if not self.check_collisions(new_x, new_y, self.game.map.bricks, self.game.map.steel_walls, self.game.map.eagles, opponent):
			if 0 <= new_x <= self.game.SCREEN_WIDTH - self.width and 0 <= new_y <= self.game.SCREEN_HEIGHT - self.height:
				self.x, self.y = new_x, new_y

	def check_collisions(self, new_x, new_y, bricks, steel_walls, eagles, opponent):
		if self.destroyed:
			return False

		# Check collision with bricks
		for brick in bricks:
			if new_x < brick["x"] + self.game.TILE_SIZE and new_x + self.width > brick["x"] and new_y < brick["y"] + self.game.TILE_SIZE and new_y + self.height > brick["y"] and not brick["destroyed"]:
				return True

		# Check collision with bricks
		for steel_wall in steel_walls:
			if (
				new_x < steel_wall["x"] + self.game.TILE_SIZE
				and new_x + self.width > steel_wall["x"]
				and new_y < steel_wall["y"] + self.game.TILE_SIZE
				and new_y + self.height > steel_wall["y"]
			):
				return True

		# Check collision with intact eagles
		for eagle in eagles:
			if not eagle["destroyed"]:
				if (
					new_x < eagle["x"] + eagle["width"]
					and new_x + self.width > eagle["x"]
					and new_y < eagle["y"] + eagle["height"]
					and new_y + self.height > eagle["y"]
				):
					return True

		# Check collision with the other tank
		if opponent and (
			opponent.x < new_x + self.width
			and opponent.x + opponent.width > new_x
			and opponent.y < new_y + self.height
			and opponent.y + opponent.height > new_y
		):
			return True

		return False

	def shoot(self):
		"""Fire a bullet if allowed."""
		current_time = pygame.time.get_ticks()
		if current_time - self.last_shot_time >= 500:  # Allow one shot every 500ms
			self.last_shot_time = current_time

			# Calculate the bullet's starting position based on the tank's direction
			if self.direction == "UP":
				bullet_x = self.x + self.width // 2 - 5
				bullet_y = self.y - 10
				velocity_x, velocity_y = 0, -10
			elif self.direction == "DOWN":
				bullet_x = self.x + self.width // 2 - 5
				bullet_y = self.y + self.height
				velocity_x, velocity_y = 0, 10
			elif self.direction == "LEFT":
				bullet_x = self.x - 10
				bullet_y = self.y + self.height // 2 - 5
				velocity_x, velocity_y = -10, 0
			elif self.direction == "RIGHT":
				bullet_x = self.x + self.width
				bullet_y = self.y + self.height // 2 - 5
				velocity_x, velocity_y = 10, 0
			else:
				return  # Invalid direction, do nothing

			# Create a new bullet and append it to the bullets list
			bullet = Bullet(self.game, bullet_x, bullet_y, velocity_x, velocity_y)
			self.bullets.append(bullet)

	def update_bullets(self, bricks, steel_walls, eagles, enemy_tank, enemy_bullets):
		if self.destroyed:
			return

		for bullet in self.bullets:
			bullet_removed = False
			bullet.update()
			if bullet.is_off_screen():
				self.bullets.remove(bullet)
			else:
				damage_bounds = bullet.create_damage_bounds()

				# Tank
				if not bullet_removed:
					if bullet.collides_with_tank(enemy_tank):
						bullet_removed = True
						enemy_tank.destroy()
				if bullet_removed:
					self.bullets.remove(bullet)
					break

				# Eagle
				if not bullet_removed:
					for eagle in eagles:
						if not eagle["destroyed"] and bullet.collides_with_eagle(eagle):
							bullet_removed = True
							eagle["destroyed"] = True
				if bullet_removed:
					self.bullets.remove(bullet)
					break

				# Bricks
				if not bullet_removed:
					for brick in bricks:
						if not brick["destroyed"]:
							if (
								(damage_bounds["x"] <= brick["x"] < damage_bounds["x"] + damage_bounds["width"] and damage_bounds["y"] <= brick["y"] < damage_bounds["y"] + damage_bounds["height"]) or
								(damage_bounds["x"] <= brick["x"] + self.game.TILE_SIZE < damage_bounds["x"] + damage_bounds["width"] and damage_bounds["y"] <= brick["y"] < damage_bounds["y"] + damage_bounds["height"]) or
								(damage_bounds["x"] <= brick["x"] < damage_bounds["x"] + damage_bounds["width"] and damage_bounds["y"] <= brick["y"] + self.game.TILE_SIZE < damage_bounds["y"] + damage_bounds["height"]) or
								(damage_bounds["x"] <= brick["x"] + self.game.TILE_SIZE < damage_bounds["x"] + damage_bounds["width"] and damage_bounds["y"] <= brick["y"] + self.game.TILE_SIZE < damage_bounds["y"] + damage_bounds["height"])
							):
								bullet_removed = True
								brick["destroyed"] = True
				if bullet_removed:
					self.bullets.remove(bullet)
					break

				# Steel Wall
				if not bullet_removed:
					for steel_wall in steel_walls:
						if bullet.collides_with(steel_wall):
							bullet_removed = True
				if bullet_removed:
					self.bullets.remove(bullet)
					break

				# Enemy Bullet
				if not bullet_removed:
					for enemy_bullet in enemy_bullets:
						if bullet.collides_with_bullet(enemy_bullet):
							bullet_removed = True
							enemy_bullets.remove(enemy_bullet)
				if bullet_removed:
					self.bullets.remove(bullet)
					break

	def destroy(self):
		self.destroyed = True

	def get_nearest_decision_point(self):
		tank_center_x = self.x + self.game.TANK_SIZE / 2
		tank_center_y = self.y + self.game.TANK_SIZE / 2
		for dp in self.game.map.decision_points:
			if dp.is_near(tank_center_x, tank_center_y):
				return dp
		return False
