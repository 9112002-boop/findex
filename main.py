from pathlib import Path
from stats import collect_stats
from greedy_stats import collect_stats_greedy

def main():
    data_dir = Path('data')
    print('--- Streaming version ---')
    s = collect_stats(data_dir)
    for k, v in s.items(): print(k, v)
    print('--- Greedy version ---')
    g = collect_stats_greedy(data_dir)
    for k, v in g.items(): print(k, v)

if __name__ == '__main__':
    main()
