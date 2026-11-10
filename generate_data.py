import os
from pathlib import Path


def generate_corpus(num_files: int = 20, size_per_file_mb: float = 3.0) -> None:
    """
    Генерує корпус текстових файлів для тестування.
    num_files: кількість файлів
    size_per_file_mb: приблизний розмір кожного файлу в МБ
    """
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    # Базовий текст, який ми будемо повторювати
    base_text = (
        "It was the best of times, it was the worst of times. "
        "AI and machine learning are changing the world. "
        "Don't forget apostrophes: it's, don't, can't. "
        "Hyphenated words: well-known, state-of-the-art. "
        "Numbers: 1775, 2024, 3.14. "
    )

    # Скільки разів повторити текст, щоб отримати потрібний розмір (приблизно)
    # 1 повторення ~ 250 байт. 3 МБ ~ 3 * 1024 * 1024 / 250 ~ 12500 разів
    repetitions = int((size_per_file_mb * 1024 * 1024) / len(base_text))

    print(f"Генерація {num_files} файлів (по ~{size_per_file_mb} МБ)...")

    for i in range(1, num_files + 1):
        filename = data_dir / f"doc{i:02d}.txt"

        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(base_text + "\n" for _ in range(repetitions))

        size_mb = os.path.getsize(filename) / (1024 * 1024)
        print(f"Створено {filename}: {size_mb:.2f} MB")


if __name__ == "__main__":
    # Створюємо 20 файлів по 3 МБ (загалом ~60 МБ)
    generate_corpus(num_files=20, size_per_file_mb=3.0)