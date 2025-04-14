import torch
import os
import tempfile
import time


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
		#print(f"🗑️ Deleted {f}")
	print("🗑️ Deleted policy files")


def clean_temp_files(prefixes, older_than_seconds=300):
	temp_dir = tempfile.gettempdir()
	now = time.time()
	deleted = 0

	for filename in os.listdir(temp_dir):
		filepath = os.path.join(temp_dir, filename)
		if not os.path.isfile(filepath):
			continue

		if any(filename.startswith(prefix) for prefix in prefixes):
			try:
				modified_time = os.path.getmtime(filepath)
				if now - modified_time > older_than_seconds:
					os.remove(filepath)
					deleted += 1
			except Exception as e:
				print(f"⚠️ Could not delete {filename}: {e}")

	print(f"🧹 Temp cleanup done. {deleted} file(s) removed from {temp_dir}")


if __name__ == "__main__":
	merge_policies("agent1_policy_", "agent1_policy_merged.pth")
	merge_policies("agent2_policy_", "agent2_policy_merged.pth")
	clean_temp_files(prefixes=["agent1_policy_", "agent2_policy_", "torch_", "mp-"])
