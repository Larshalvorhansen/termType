import curses
import time
import textwrap
import random
import os
import subprocess
import re


def preprocess_text(
    input_path="custom.txt", output_path="processedcustom.txt", width=50
):
    try:
        with open(input_path, "r") as infile, open(output_path, "w") as outfile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                wrapped = textwrap.wrap(line, width=width)
                for part in wrapped:
                    outfile.write(part + " \n")
    except FileNotFoundError:
        print(f"Missing file: {input_path}")
        return False
    return True


def load_wordlist(path="common_words.txt"):
    try:
        with open(path, "r") as f:
            return [word.strip() for word in f if word.strip()]
    except FileNotFoundError:
        print(f"Missing word list: {path}")
        return []


def generate_random_lines(wordlist, num_lines=10, max_width=50):
    lines = []
    for _ in range(num_lines):
        line = ""
        while len(line) < max_width:
            word = random.choice(wordlist)
            if len(line + " " + word) <= max_width:
                line += " " + word if line else word
            else:
                break
        lines.append(line)
    return lines


def load_extreme_lines():
    lines = ["Name und forname:"]
    with open("g.txt", "r") as f:
        words = [line.strip() for line in f if line.strip()]
    for _ in range(49):
        line = " ".join(random.choices(words, k=random.randint(4, 10)))
        lines.append(line)
    return lines


def typing_tutor(stdscr, text, index, total, next_line=None):
    curses.curs_set(1)
    stdscr.clear()

    max_y, max_x = stdscr.getmaxyx()
    text = text[:max_x]
    typed_chars = []
    mistakes = 0
    start_time = time.time()

    while True:
        stdscr.clear()

        line_y = max_y // 2
        next_y = line_y + 2
        info_y = line_y - 2

        text_x = (max_x - len(text)) // 2
        info_x = (max_x - len(f"[{index}/{total}]")) // 2
        next_x = (max_x - len(next_line)) // 2 if next_line else 0

        stdscr.addstr(info_y, info_x, f"[{index}/{total}]")

        for i, expected_char in enumerate(text):
            if i < len(typed_chars):
                typed_char = typed_chars[i]
                if typed_char == expected_char:
                    color = curses.color_pair(1)
                else:
                    color = curses.color_pair(2)
                stdscr.addstr(line_y, text_x + i, typed_char, color)
            else:
                stdscr.addstr(line_y, text_x + i, expected_char, curses.A_DIM)

        if next_line:
            next_line = next_line[:max_x]
            stdscr.addstr(next_y, next_x, next_line, curses.A_DIM)

        stdscr.move(line_y, text_x + len(typed_chars))
        stdscr.refresh()

        if len(typed_chars) == len(text):
            break

        ch = stdscr.get_wch()

        if isinstance(ch, str):
            if ord(ch) == 27:
                if confirm_quit(stdscr):
                    return None
                else:
                    continue
            elif ord(ch) in (8, 127):
                if typed_chars:
                    typed_chars.pop()
                continue
            elif ch == "\n":
                continue
            elif len(ch) == 1:
                if ch != text[len(typed_chars)]:
                    mistakes += 1
                typed_chars.append(ch)

    end_time = time.time()
    return {"chars": len(text), "mistakes": mistakes, "time": end_time - start_time}


def confirm_quit(stdscr):
    stdscr.clear()
    stdscr.addstr(0, 0, "Do you wish to quit? (Y to quit, any key to continue)")
    stdscr.refresh()
    ch = stdscr.get_wch()
    return ch in ("y", "Y")


def calc_stats(stats):
    correct = stats["chars"]
    mistakes = stats["mistakes"]
    total = correct + mistakes
    duration = stats["time"]
    time_min = duration / 60
    wpm = (correct / 5) / time_min if time_min > 0 else 0
    acc = (correct / total) * 100 if total > 0 else 0
    return round(wpm), round(acc), round(duration, 2)


def save_stats(lines, total_stats):
    with open("statistics.txt", "a") as f:
        f.write(f"{time.ctime()} | {len(lines)} lines\n")
        for line, stats in zip(lines, total_stats):
            wpm, acc, dur = calc_stats(stats)
            preview = line[:30] + ("..." if len(line) > 30 else "")
            f.write(f'  "{preview}" | WPM: {wpm} | Acc: {acc}% | Time: {dur}s\n')
        total_chars = sum(s["chars"] for s in total_stats)
        total_mistakes = sum(s["mistakes"] for s in total_stats)
        total_time = sum(s["time"] for s in total_stats)
        overall_wpm = (total_chars / 5) / (total_time / 60) if total_time else 0
        overall_acc = (
            (total_chars / (total_chars + total_mistakes)) * 100
            if total_chars + total_mistakes
            else 0
        )
        f.write(
            f"  → Total WPM: {round(overall_wpm)}, Accuracy: {round(overall_acc)}%\n\n"
        )


def show_summary(stdscr, stats):
    total_chars = sum(s["chars"] for s in stats)
    total_mistakes = sum(s["mistakes"] for s in stats)
    total_time = sum(s["time"] for s in stats)
    wpm = (total_chars / 5) / (total_time / 60) if total_time > 0 else 0
    acc = (
        (total_chars / (total_chars + total_mistakes)) * 100
        if (total_chars + total_mistakes) > 0
        else 0
    )

    stdscr.clear()
    stdscr.addstr(0, 0, "Typing complete.", curses.A_BOLD)
    stdscr.addstr(2, 0, f"Total time:     {round(total_time, 2)}s")
    stdscr.addstr(3, 0, f"Total chars:    {total_chars}")
    stdscr.addstr(4, 0, f"Total mistakes: {total_mistakes}")
    stdscr.addstr(5, 0, f"Overall WPM:    {round(wpm)}")
    stdscr.addstr(6, 0, f"Accuracy:       {round(acc)}%")
    stdscr.addstr(8, 0, "Stats saved to statistics.txt. Press any key to exit.")
    stdscr.refresh()
    stdscr.getch()


def run_all_lines(stdscr, lines):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)
    curses.init_pair(2, curses.COLOR_RED, -1)

    results = []

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else None
        stats = typing_tutor(stdscr, line, i + 1, len(lines), next_line)
        if stats is None:
            break
        results.append(stats)

    save_stats(lines[: len(results)], results)
    show_summary(stdscr, results)


def print_bible_books():
    import shutil
    import math

    cols = shutil.get_terminal_size().columns

    books_with_chapters = [
        ("Genesis", 50),
        ("Exodus", 40),
        ("Leviticus", 27),
        ("Numbers", 36),
        ("Deuteronomy", 34),
        ("Joshua", 24),
        ("Judges", 21),
        ("Ruth", 4),
        ("1 Samuel", 31),
        ("2 Samuel", 24),
        ("1 Kings", 22),
        ("2 Kings", 25),
        ("1 Chronicles", 29),
        ("2 Chronicles", 36),
        ("Ezra", 10),
        ("Nehemiah", 13),
        ("Esther", 10),
        ("Job", 42),
        ("Psalms", 150),
        ("Proverbs", 31),
        ("Ecclesiastes", 12),
        ("Song of Solomon", 8),
        ("Isaiah", 66),
        ("Jeremiah", 52),
        ("Lamentations", 5),
        ("Ezekiel", 48),
        ("Daniel", 12),
        ("Hosea", 14),
        ("Joel", 3),
        ("Amos", 9),
        ("Obadiah", 1),
        ("Jonah", 4),
        ("Micah", 7),
        ("Nahum", 3),
        ("Habakkuk", 3),
        ("Zephaniah", 3),
        ("Haggai", 2),
        ("Zechariah", 14),
        ("Malachi", 4),
        ("Matthew", 28),
        ("Mark", 16),
        ("Luke", 24),
        ("John", 21),
        ("The Acts", 28),
        ("Romans", 16),
        ("1 Corinthians", 16),
        ("2 Corinthians", 13),
        ("Galatians", 6),
        ("Ephesians", 6),
        ("Philippians", 4),
        ("Colossians", 4),
        ("1 Thessalonians", 5),
        ("2 Thessalonians", 3),
        ("1 Timothy", 6),
        ("2 Timothy", 4),
        ("Titus", 3),
        ("Philemon", 1),
        ("Hebrews", 13),
        ("James", 5),
        ("1 Peter", 5),
        ("2 Peter", 3),
        ("1 John", 5),
        ("2 John", 1),
        ("3 John", 1),
        ("Jude", 1),
        ("Revelation", 22),
        ("Tobit", 14),
        ("Judith", 16),
        ("Esther (Greek)", 16),
        ("Wisdom of Solomon", 19),
        ("Sirach", 51),
        ("Baruch", 6),
        ("Prayer of Azariah", 1),
        ("Susanna", 1),
        ("Bel and the Dragon", 1),
        ("1 Maccabees", 16),
        ("2 Maccabees", 15),
        ("1 Esdras", 9),
        ("Prayer of Manasseh", 1),
        ("2 Esdras", 16),
    ]

    entries = [f"{name} ({chapters})" for name, chapters in books_with_chapters]

    col_count = 3
    rows = math.ceil(len(entries) / col_count)

    while len(entries) < rows * col_count:
        entries.append("")

    columns = [entries[i * rows : (i + 1) * rows] for i in range(col_count)]

    width = max(len(entry) for entry in entries) + 2
    for i in range(rows):
        line = "".join(columns[j][i].ljust(width) for j in range(col_count))
        print(line.center(cols))


def fisk_mode():
    print("\nBooks of the Bible:\n")
    print_bible_books()
    try:
        prompt = input(
            "\nEnter a chapter you want to type out. (e.g. John 3): "
        ).strip()
        if not prompt:
            print("No prompt entered.")
            return False

        print(f"Running: kjv {prompt}")
        result = subprocess.run(
            f"kjv {prompt}", shell=True, capture_output=True, text=True
        )

        if result.returncode != 0:
            print("ERROR: kjv command failed")
            print("stderr:", result.stderr)
            return False

        output = result.stdout.strip()
        if not output:
            print("ERROR: kjv returned empty output")
            return False

        cleaned = []

        base_prefix = re.match(r"^[^\d]+ \d+", prompt)
        prefix_pattern = base_prefix.group(0) if base_prefix else prompt

        for line in output.splitlines():
            line = re.sub(
                rf"^{re.escape(prefix_pattern)}:\s*", "", line, flags=re.IGNORECASE
            )
            line = re.sub(r"^\S+:\s*", "", line)
            line = re.sub(r"  +", " ", line)
            line = line.strip()
            if line:
                cleaned.append(line)

        with open("processedcustom.txt", "w") as f:
            for line in cleaned:
                for part in textwrap.wrap(line, width=50):
                    f.write(part + "\u0020\n")

        with open("processedcustom.txt", "r") as f:
            lines = []
            for raw in f:
                if raw.strip():
                    lines.append(raw.rstrip("\n"))

        curses.wrapper(lambda stdscr: run_all_lines(stdscr, lines))
        return True

    except Exception as e:
        print("Exception occurred:", e)
        return False


def main():
    import shutil

    os.system("clear")

    cols = shutil.get_terminal_size().columns

    def center(text):
        return text.center(cols)

    def center_banner(banner):
        return "\n".join(center(line) for line in banner.strip("\n").splitlines())

    import shutil

    cols = shutil.get_terminal_size().columns

    def center(text):
        return text.center(cols)

    print("\n" + center("=== Welcome to the Typing Tutor ==="))
    banner = r"""
       ___________     _               _____                
      |.---------.|   | |_ ___ _ _ _ _|_   _|  _ _ __  ___  
      ||>_       ||   |  _/ -_) '_| '  \| || || | '_ \/ -_) 
      ||         ||    \__\___|_| |_|_|_|_| \_, | .__/\___| 
      |'---------'|                         |__/|_|         
       `)__ ____('                                          
       [=== -- o ]                                          
     __'---------'__                                        
    """
    print(center_banner(banner))
    print(center("Choose a mode:"))
    print(center("[1] Custom text"))
    print(center("[2] Random text"))
    print(center("[3] Extreme mode"))
    print(center("[4] Fish mode"))

    choice = input().strip()

    if choice == "1":
        if not preprocess_text():
            return
        try:
            with open("processedcustom.txt", "r") as f:
                lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("Missing file: processedcustom.txt")
            return
        curses.wrapper(lambda stdscr: run_all_lines(stdscr, lines))

    elif choice == "2":
        wordlist = load_wordlist("common_words.txt")
        if not wordlist:
            return
        num_lines = input("Number of lines [default 20]: ").strip()
        try:
            num_lines = int(num_lines)
        except:
            num_lines = 20
        lines = generate_random_lines(wordlist, num_lines=num_lines)
        curses.wrapper(lambda stdscr: run_all_lines(stdscr, lines))

    elif choice == "3":
        lines = load_extreme_lines()
        curses.wrapper(lambda stdscr: run_all_lines(stdscr, lines))

    elif choice == "4":
        if fisk_mode():
            try:
                with open("processedcustom.txt", "r") as f:
                    lines = [line.strip() for line in f if line.strip()]
                curses.wrapper(lambda stdscr: run_all_lines(stdscr, lines))
            except FileNotFoundError:
                print("Failed to open processedcustom.txt")

    else:
        print("Invalid mode. Goodbye!")


if __name__ == "__main__":
    main()
