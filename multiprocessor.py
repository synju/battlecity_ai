import multiprocessing
import time
import os

### THIS WILL NOT WORK !!!
### THIS WILL NOT WORK !!!
### THIS WILL NOT WORK !!!
### THIS WILL NOT WORK !!!
### THIS WILL NOT WORK !!!
### THIS WILL NOT WORK !!!
### THIS WILL NOT WORK !!!
### THIS WILL NOT WORK !!!

def start_game_instance(instance_id):
	from game import Game  # Importing inside the function to avoid global issues
	print(f"Game instance {instance_id} started (PID: {os.getpid()})")
	game = Game()
	game.main()


if __name__ == "__main__":
	processes = []
	for i in range(10):  # 10 instances
		process = multiprocessing.Process(target=start_game_instance, args=(i,))
		processes.append(process)
		process.start()
		time.sleep(0.100)  # Wait 1 second before starting the next process

	for process in processes:
		process.join()

	print("All game instances finished.")
