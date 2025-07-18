import curses
import time
import textwrap
import random
import os


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
                    outfile.write(part)
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
    lines = ["Name und Vorname? Grzg...."]
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
    text = text[:max_x]  # Ensure line fits screen width
    typed_chars = []
    mistakes = 0
    start_time = time.time()

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"[{index}/{total}]")

        for i, expected_char in enumerate(text):
            if i < len(typed_chars):
                typed_char = typed_chars[i]
                if typed_char == expected_char:
                    color = curses.color_pair(1)
                else:
                    color = curses.color_pair(2)
                stdscr.addstr(2, i, typed_char, color)
            else:
                stdscr.addstr(2, i, expected_char, curses.A_DIM)

        if next_line:
            next_line = next_line[:max_x]
            stdscr.addstr(4, 0, next_line, curses.A_DIM)

        stdscr.move(2, len(typed_chars))
        stdscr.refresh()

        if len(typed_chars) == len(text):
            break

        ch = stdscr.get_wch()

        if isinstance(ch, str):
            if ord(ch) == 27:  # ESC
                if confirm_quit(stdscr):
                    return None
                else:
                    continue
            elif ord(ch) in (8, 127):  # Backspace
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


import curses
import time
import textwrap
import random
import os


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
                    outfile.write(part + "\n")
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
    text = text[:max_x]  # Ensure line fits screen width
    typed_chars = []
    mistakes = 0
    start_time = time.time()

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, f"[{index}/{total}]")

        for i, expected_char in enumerate(text):
            if i < len(typed_chars):
                typed_char = typed_chars[i]
                if typed_char == expected_char:
                    color = curses.color_pair(1)
                else:
                    color = curses.color_pair(2)
                stdscr.addstr(2, i, typed_char, color)
            else:
                stdscr.addstr(2, i, expected_char, curses.A_DIM)

        if next_line:
            next_line = next_line[:max_x]
            stdscr.addstr(4, 0, next_line, curses.A_DIM)

        stdscr.move(2, len(typed_chars))
        stdscr.refresh()

        if len(typed_chars) == len(text):
            break

        ch = stdscr.get_wch()

        if isinstance(ch, str):
            if ord(ch) == 27:  # ESC
                if confirm_quit(stdscr):
                    return None
                else:
                    continue
            elif ord(ch) in (8, 127):  # Backspace
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


def print_banner():
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
    print(banner)


def main():
    import sys

    def prompt_menu():
        print("Welcome to ")
        print_banner()
        print("1. Custom text")
        print("2. Randomly generated text")
        print("3. Extreme")
        return input("Enter a mode [1-3]: ").strip()

    choice = prompt_menu()

    if choice == "1":
        if not preprocess_text():
            return
        try:
            with open("processedcustom.txt", "r") as f:
                lines = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            print("Missing file: processedcustom.txt")
            return

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

    elif choice == "3":
        lines = load_extreme_lines()

    else:
        print("Goodbye!")
        return

    curses.wrapper(lambda stdscr: run_all_lines(stdscr, lines))


if __name__ == "__main__":
    main()
