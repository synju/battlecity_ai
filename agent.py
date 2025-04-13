import pygame
import torch
import numpy as np
import os
import math

from policy_network import PolicyNetwork


class Agent:
	def __init__(self, game, action_dim, agent_id=""):
		self.game = game
		self.agent_id = agent_id
		self.tank = None
		self.opponent = None
		self.current_action = None  # Initialize the current action
		self.current_keys = None  # Initialize the current keys
		self.cycle_counter = 0  # Add a cycle counter
		self.decision_interval = 4  # Number of cycles between decisions

		# Agent PPO Variables
		self.memory = []  # Store (state, action, reward, next_state, done)
		self.action_dim = action_dim
		self.input_dim = None
		self.policy_net = None
		self.optimizer = None
		self.gamma = 0.99

		# Feature Variables
		self.max_bricks = len(self.game.map.bricks)
		self.max_steel_walls = len(self.game.map.steel_walls)
		self.max_bullets = 50
		self.max_eagles = 2

		# Add itself to agent list
		self.game.agents.append(self)

	def save_model(self, filename):
		torch.save(self.policy_net.state_dict(), filename)

	def load_model(self, filename):
		self.policy_net.load_state_dict(torch.load(filename))
		self.policy_net.eval()

	def setup_model(self, lr=0.001, model_filename=None):
		tank_features = (8 + (50 * 2)) * 2  # 8 attributes + bullet attributes (50*2) per tank
		eagle_features = 3 * self.max_eagles  # 3 attributes per eagle
		brick_features = 3 * self.max_bricks  # 3 attributes per brick
		steel_wall_features = 2 * self.max_steel_walls  # 2 attributes per steel_wall

		self.input_dim = tank_features + eagle_features + brick_features + steel_wall_features
		self.policy_net = PolicyNetwork(self.input_dim, self.action_dim)
		self.optimizer = torch.optim.Adam(self.policy_net.parameters(), lr)
		self.gamma = 0.99

		if model_filename and os.path.exists(model_filename):
			self.load_model(model_filename)

	def preprocess_state(self, state):
		# Flatten the game state
		tank1_state = state["tank1"]
		tank2_state = state["tank2"]
		eagles = state["eagles"]
		bricks = state["bricks"]
		steel_walls = state["steel_walls"]
		timeElapsed = state["timeElapsed"]

		tank1_features = [
			tank1_state["x"] / self.game.SCREEN_WIDTH,
			tank1_state["y"] / self.game.SCREEN_HEIGHT,
			int(tank1_state["direction"] == "UP"),
			int(tank1_state["direction"] == "DOWN"),
			int(tank1_state["direction"] == "LEFT"),
			int(tank1_state["direction"] == "RIGHT"),
			tank1_state["distance_to_tank2"],
			int(tank1_state["destroyed"]),
		]
		tank1_bullet_features = []
		for bullet in self.game.tank1.bullets:
			tank1_bullet_features.append(bullet.x / self.game.SCREEN_WIDTH)
			tank1_bullet_features.append(bullet.y / self.game.SCREEN_HEIGHT)
		while len(tank1_bullet_features) < self.max_bullets * 2:  # 2 attributes per bullet (x, y)
			tank1_bullet_features.append(0)  # Pad with 0 if fewer bullets exist
		tank2_features = [
			tank2_state["x"] / self.game.SCREEN_WIDTH,
			tank2_state["y"] / self.game.SCREEN_HEIGHT,
			int(tank2_state["direction"] == "UP"),
			int(tank2_state["direction"] == "DOWN"),
			int(tank2_state["direction"] == "LEFT"),
			int(tank2_state["direction"] == "RIGHT"),
			tank2_state["distance_to_tank1"],
			int(tank2_state["destroyed"]),
		]
		tank2_bullet_features = []
		for bullet in self.game.tank2.bullets:
			tank2_bullet_features.append(bullet.x / self.game.SCREEN_WIDTH)
			tank2_bullet_features.append(bullet.y / self.game.SCREEN_HEIGHT)
		while len(tank2_bullet_features) < self.max_bullets * 2:  # 2 attributes per bullet (x, y)
			tank2_bullet_features.append(0)  # Pad with 0 if fewer bullets exist

		# Eagle features
		eagle_features = []
		for eagle in eagles:
			eagle_features.append(eagle["x"] / self.game.SCREEN_WIDTH)
			eagle_features.append(eagle["y"] / self.game.SCREEN_HEIGHT)
			eagle_features.append(int(eagle["destroyed"]))
		while len(eagle_features) < self.max_eagles * 3:  # 3 attributes per eagle (x, y, destroyed)
			eagle_features.append(0)  # Pad with 0 if fewer eagles exist

		# Brick features
		brick_features = []
		for brick in bricks:
			brick_features.append(brick["x"] / self.game.SCREEN_WIDTH)
			brick_features.append(brick["y"] / self.game.SCREEN_HEIGHT)
			brick_features.append(int(brick["destroyed"]))
		while len(brick_features) < self.max_bricks * 3:
			brick_features.append(0)  # Pad with 0 if fewer bricks exist

		# Steel wall features
		steel_wall_features = []
		for wall in steel_walls:
			steel_wall_features.append(wall["x"] / self.game.SCREEN_WIDTH)
			steel_wall_features.append(wall["y"] / self.game.SCREEN_HEIGHT)
		while len(steel_wall_features) < self.max_steel_walls * 2:
			steel_wall_features.append(0)  # Pad with 0 if fewer steel walls exist

		# Combine all features
		flat_state = (
			tank1_features +
			tank1_bullet_features +
			tank2_features +
			tank2_bullet_features +
			eagle_features +
			brick_features +
			steel_wall_features +
			[timeElapsed]
		)

		state_tensor = torch.FloatTensor(flat_state[:self.input_dim])
		# print(f"State tensor shape: {state_tensor.shape}")
		return state_tensor

	def decide_action(self, state):
		state_tensor = self.preprocess_state(state).unsqueeze(0)
		action_probs = self.policy_net(state_tensor).detach().numpy().flatten()

		# Validate probabilities
		if not np.isclose(np.sum(action_probs), 1.0):
			raise ValueError(f"Action probabilities do not sum to 1: {action_probs}")

		# Sample an action based on probabilities
		action = np.random.choice(len(action_probs), p=action_probs)

		return action

	def get_agent_keys(self):
		# Map the action to Pygame key presses
		action = self.decide_action(self.game.get_game_state())

		keys = {
			pygame.K_UP: False,
			pygame.K_DOWN: False,
			pygame.K_LEFT: False,
			pygame.K_RIGHT: False,
			pygame.K_SPACE: False,
		}
		if action == 0:  # UP
			keys[pygame.K_UP] = True
		elif action == 1:  # DOWN
			keys[pygame.K_DOWN] = True
		elif action == 2:  # LEFT
			keys[pygame.K_LEFT] = True
		elif action == 3:  # RIGHT
			keys[pygame.K_RIGHT] = True
		elif action == 4:  # SHOOT
			keys[pygame.K_SPACE] = True
		return keys

	def map_action_to_keys(self, current_action):
		keys = {
			pygame.K_UP: False,
			pygame.K_DOWN: False,
			pygame.K_LEFT: False,
			pygame.K_RIGHT: False,
			#pygame.K_SPACE: False,
		}
		if current_action == 0:  # UP
			keys[pygame.K_UP] = True
		elif current_action == 1:  # DOWN
			keys[pygame.K_DOWN] = True
		elif current_action == 2:  # LEFT
			keys[pygame.K_LEFT] = True
		elif current_action == 3:  # RIGHT
			keys[pygame.K_RIGHT] = True
		#elif current_action == 4:  # SHOOT
			#keys[pygame.K_SPACE] = True
		return keys

	def check_done(self):
		# Define logic to determine if the game/reset condition is reached
		return self.tank.destroyed or self.tank.eagle["destroyed"] or self.opponent.destroyed or self.opponent.eagle["destroyed"] or self.game.timeElapsed >= self.game.max_time

	def store_transition(self, state, action, reward, next_state, done):
		# Preprocess states before storing
		processed_state = self.preprocess_state(state).numpy()
		processed_next_state = self.preprocess_state(next_state).numpy()
		self.memory.append((processed_state, action, reward, processed_next_state, done))

	def compute_rewards(self):
		round_num = self.game.iteration
		rewards = []
		points = 0.0

		# Phase 1: movement training (Normalized Distance)
		dist = self.get_distance_to_opponent()
		normalized = math.exp(-dist / 150.0)
		points += normalized * 10.0

		# Reward for destroying the opponent
		# if self.opponent.destroyed:
		# points += calculate_time_bonus(self.game.timeElapsed)

		# Reward for destroying the opponent's eagle
		# if self.opponent.eagle["destroyed"]:
		# points += calculate_time_bonus(self.game.timeElapsed)

		# Penalty for losing the agent's eagle
		# if self.tank.eagle["destroyed"]:
		# points -= 50.0

		# Penalty for losing the agent's eagle
		# if self.tank.destroyed:
		# points -= 50.0

		# Penalize if game timed out with no win condition
		# if not self.opponent.destroyed and not self.opponent.eagle["destroyed"]:
		# 	if self.game.timeElapsed >= self.game.max_time:
		# 		points -= 100.0  # ⛔ heavy punishment for wasting time
		# 	else:
		# 		points -= 30.0  # 🐢 still penalize for not being aggressive enough

		rewards.append(points)
		self.game.agent_points[self.agent_id] = points

		for i in range(min(len(self.memory), len(rewards))):
			self.memory[i] = (*self.memory[i][:2], rewards[i], *self.memory[i][3:])

	def train(self, batch_size=32, clip_epsilon=0.2, epochs=20):
		# Compute Rewards
		self.compute_rewards()

		if len(self.memory) < batch_size:
			return

		states, actions, rewards, dones = zip(*[(s, a, r, d) for s, a, r, _, d in self.memory])
		states = torch.FloatTensor(np.array(states))
		actions = torch.LongTensor(np.array(actions))
		rewards = torch.FloatTensor(np.array(rewards))
		dones = torch.FloatTensor(np.array(dones))

		G = []
		R = 0
		for reward, done in zip(reversed(rewards), reversed(dones)):
			if done:
				R = 0
			R = reward + self.gamma * R
			G.insert(0, R)
		G = torch.FloatTensor(G)
		G = (G - G.mean()) / (G.std() + 1e-8)

		for _ in range(epochs):
			probs = self.policy_net(states)
			dist = torch.distributions.Categorical(probs)
			log_probs = dist.log_prob(actions)

			new_probs = self.policy_net(states)
			new_dist = torch.distributions.Categorical(new_probs)
			new_log_probs = new_dist.log_prob(actions)

			ratios = torch.exp(new_log_probs - log_probs.detach())
			clipped_ratios = torch.clamp(ratios, 1 - clip_epsilon, 1 + clip_epsilon)
			loss = -torch.min(ratios * G, clipped_ratios * G).mean()

			self.optimizer.zero_grad()
			loss.backward()
			self.optimizer.step()

		self.memory = []

	def update(self):
		# End round if out of time or if tank or eagle is destroyed
		done = self.game.check_done()
		if self.tank.awaiting_decision:
			# Decision time
			current_state = self.game.get_game_state()
			self.current_action = self.decide_action(current_state)
			self.current_keys = self.map_action_to_keys(self.current_action)

			# Save this as "active movement" and start moving
			self.tank.active_keys = self.current_keys
			self.tank.awaiting_decision = False  # This is where it stops waiting for a decision
			self.tank.most_recent_decision_point = self.tank.temp_decision_point

			# Store transition for learning
			next_state = self.game.get_game_state()
			self.store_transition(current_state, self.current_action, 0.0, next_state, done)

		# Continue moving with stored keys
		if not self.tank.awaiting_decision and self.tank.active_keys:
			self.tank.perform_action(self.tank.active_keys, self.opponent)

	def calculate_time_bonus(self, time_elapsed):
		base_reward = 150.0
		return max(0.0, base_reward - 5.0 * time_elapsed)

	def get_distance_to_opponent(self):
		t1_center_x = self.tank.x + self.tank.width / 2
		t1_center_y = self.tank.y + self.tank.height / 2
		t2_center_x = self.opponent.x + self.opponent.width / 2
		t2_center_y = self.opponent.y + self.opponent.height / 2

		dx = t1_center_x - t2_center_x
		dy = t1_center_y - t2_center_y
		return (dx ** 2 + dy ** 2) ** 0.5
