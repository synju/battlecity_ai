import torch
import torch.nn as nn
import torch.nn.functional as F


class PolicyNetwork(nn.Module):
	def __init__(self, input_dim, action_dim):
		super(PolicyNetwork, self).__init__()
		self.fc1 = nn.Linear(input_dim, 256)  # Match input_dim to your game's state vector size
		self.fc2 = nn.Linear(256, 256)
		self.fc3 = nn.Linear(256, 128)
		self.fc4 = nn.Linear(128, action_dim)  # Match action_dim to the number of possible actions

	def forward(self, x):
		x = F.relu(self.fc1(x))
		x = F.relu(self.fc2(x))
		x = F.relu(self.fc3(x))
		x = F.softmax(self.fc4(x), dim=-1)  # Output probabilities
		return x
