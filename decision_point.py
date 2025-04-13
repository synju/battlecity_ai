class DecisionPoint:
	def __init__(self, x, y, index):
		self.x = x
		self.y = y
		self.index = index

	def __repr__(self):
		return f"<DecisionPoint x={self.x}, y={self.y}>"

	def is_near(self, px, py, radius=2):
		return abs(self.x - px) < radius and abs(self.y - py) < radius

	def get_index(self):
		return self.index
