import torch
import os


def merge_policies(pattern, output_file):
	files = [
		f for f in os.listdir("policies")
		if f.startswith(pattern) and f.endswith(".pth") and "merged" not in f
	]
	if not files:
		print(f"❌ No policies found for pattern: {pattern}")
		return

	print(f"🔄 Merging {len(files)} files into {output_file}")
	state_dicts = [torch.load(os.path.join("policies", f)) for f in files]
	avg_state = {}

	for key in state_dicts[0]:
		avg_state[key] = sum(d[key] for d in state_dicts) / len(state_dicts)

	torch.save(avg_state, os.path.join("policies", output_file))
	print(f"✅ Saved merged model to {output_file}")

	# 🧹 Delete only the originals, NOT the merged file
	for f in files:
		os.remove(os.path.join("policies", f))
		print(f"🗑️  Deleted {f}")


if __name__ == "__main__":
	merge_policies("agent1_policy_", "agent1_policy_merged.pth")
	merge_policies("agent2_policy_", "agent2_policy_merged.pth")
