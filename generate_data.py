import os

os.makedirs('data', exist_ok=True)

text = 'It was the best of times. AI and machine learning are changing the world. Don''t forget apostrophes: it''s, don''t, can''t. Hyphenated: well-known, state-of-the-art. Numbers: 1775, 2024. '

for i in range(1, 4):
    filename = f'data/doc{i}.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        f.writelines(text + '\n' for _ in range(15000))
    size_mb = os.path.getsize(filename) / (1024 * 1024)
    print(f'Created {filename}: {size_mb:.2f} MB')
