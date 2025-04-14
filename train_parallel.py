from multiprocessing import Process
import time
import os
import subprocess  # ✅ to run the merge script after


def run_game_instance(instance_id, num_iterations=1):
	from game import Game
	agent1_file = f"policies/agent1_policy_{instance_id}.pth"
	agent2_file = f"policies/agent2_policy_{instance_id}.pth"
	game = Game(headless=True, agent1_file=agent1_file, agent2_file=agent2_file, max_iterations=num_iterations)
	game.main()


if __name__ == "__main__":
	num_instances = 50
	iterations_per_batch = 5
	total_iterations = 300

	batches = total_iterations // iterations_per_batch

	for batch in range(batches):
		print(f"\n🧠 Starting training batch {batch + 1}/{batches}...")
		processes = []

		for i in range(num_instances):
			p = Process(target=run_game_instance, args=(i, iterations_per_batch))
			p.start()
			processes.append(p)

		for p in processes:
			p.join()

		print(f"🔀 Merging policies after batch {batch + 1}...")
		subprocess.run(["python", "merge_policies.py"])
