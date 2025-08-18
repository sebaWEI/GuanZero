import os
import csv
import argparse
from typing import List

import matplotlib.pyplot as plt


def read_fields(fields_path: str) -> List[str]:
	with open(fields_path, 'r', newline='') as f:
		row = f.readline().strip()
		# fields.csv stores a single header row: comma-separated field names
		return [col.strip() for col in row.split(',') if col.strip()]


def read_logs(logs_path: str, fieldnames: List[str]) -> List[dict]:
	rows = []
	with open(logs_path, 'r', newline='') as f:
		for line in f:
			if line.startswith('#'):
				# skip commented header line
				continue
			# csv with no header; use provided fieldnames to parse
			reader = csv.DictReader([line], fieldnames=fieldnames)
			for row in reader:
				rows.append(row)
	return rows


def to_float_list(rows: List[dict], key: str) -> List[float]:
	values = []
	for r in rows:
		v = r.get(key)
		if v is None or v == '':
			values.append(float('nan'))
			continue
		try:
			values.append(float(v))
		except Exception:
			values.append(float('nan'))
	return values


def moving_average(values: List[float], window: int) -> List[float]:
	if window <= 1:
		return values
	out = []
	sum_val = 0.0
	cnt = 0
	queue = []
	for v in values:
		queue.append(v)
		cnt += 1
		sum_val += v if v == v else 0.0  # skip NaNs in sum
		if cnt > window:
			old = queue.pop(0)
			cnt -= 1
			if old == old:
				sum_val -= old
		valid_cnt = sum(1 for x in queue if x == x)
		out.append(sum_val / valid_cnt if valid_cnt > 0 else float('nan'))
	return out


def plot_series(x, y, title: str, xlabel: str, ylabel: str, out_path: str):
	plt.figure(figsize=(8, 4))
	plt.plot(x, y, linewidth=1.5)
	plt.title(title)
	plt.xlabel(xlabel)
	plt.ylabel(ylabel)
	plt.grid(True, alpha=0.3)
	plt.tight_layout()
	plt.savefig(out_path)
	plt.close()


def main():
	parser = argparse.ArgumentParser(description='Plot training logs for a given experiment (xpid).')
	parser.add_argument('--savedir', type=str, default='guanzero_checkpoints', help='Root directory of experiments')
	parser.add_argument('--xpid', type=str, required=True, help='Experiment id (e.g., first_train)')
	parser.add_argument('--smoothing', type=int, default=50, help='Moving average window for smoothing (0/1 to disable)')
	parser.add_argument('--use_frames', action='store_true', help='Use frames on X-axis instead of tick')
	args = parser.parse_args()

	base = os.path.join(args.savedir, args.xpid)
	fields_path = os.path.join(base, 'fields.csv')
	logs_path = os.path.join(base, 'logs.csv')
	if not os.path.exists(fields_path) or not os.path.exists(logs_path):
		raise FileNotFoundError(f'Cannot find logs at {base}. Expected files: fields.csv and logs.csv')

	fieldnames = read_fields(fields_path)
	rows = read_logs(logs_path, fieldnames)

	x_key = 'frames' if args.use_frames and 'frames' in fieldnames else '_tick'
	# Sort rows by x_key to avoid backwards lines when logs were appended across restarts
	def _key_fn(r):
		v = r.get(x_key)
		try:
			return float(v)
		except Exception:
			return float('inf')
	rows.sort(key=_key_fn)

	x = to_float_list(rows, x_key)
	loss = to_float_list(rows, 'loss') if 'loss' in fieldnames else []
	mer = to_float_list(rows, 'mean_episode_return') if 'mean_episode_return' in fieldnames else []

	window = max(1, int(args.smoothing))
	if loss:
		loss_sm = moving_average(loss, window)
		plot_series(x, loss_sm, f'Loss ({args.xpid})', x_key, 'loss', os.path.join(base, f'{args.xpid}_loss.png'))
	if mer:
		mer_sm = moving_average(mer, window)
		plot_series(x, mer_sm, f'Mean Episode Return ({args.xpid})', x_key, 'mean_episode_return', os.path.join(base, f'{args.xpid}_mean_episode_return.png'))

	print(f'Plots saved to: {base}')


if __name__ == '__main__':
	main()
