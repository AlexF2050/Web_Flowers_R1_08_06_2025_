import os

def count_non_empty_lines(directory, extensions):
    total = 0
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = [line for line in f if line.strip()]
                    total += len(lines)
    return total

if __name__ == "__main__":
    directory = input("Введите путь к проекту (нажмите Enter для текущей папки): ") or '.'
    py_count = count_non_empty_lines(directory, ('.py',))
    html_count = count_non_empty_lines(directory, ('.html',))
    print(f"Непустых строк в .py файлах: {py_count}")
    print(f"Непустых строк в .html файлах: {html_count}")