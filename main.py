import curses
import time
import textwrap


def preprocess_text(input_path="text.txt", output_path="processedtext.txt", width=50):
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

        # Draw current line with color-coded characters
        for i, expected_char in enumerate(text):
            if i < len(typed_chars):
                typed_char = typed_chars[i]
                if typed_char == expected_char:
                    color = curses.color_pair(1)  # green
                else:
                    color = curses.color_pair(2)  # red
                stdscr.addstr(2, i, typed_char, color)
            else:
                stdscr.addstr(2, i, expected_char, curses.A_DIM)

        # Show next line in gray
        if next_line:
            next_line = next_line[:max_x]
            stdscr.addstr(4, 0, next_line, curses.A_DIM)

        stdscr.move(2, len(typed_chars))  # Move cursor to current position
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
                continue  # ignore Enter
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


def save_stats(line, wpm, acc, duration):
    preview = line[:30] + ("..." if len(line) > 30 else "")
    with open("results.txt", "a") as f:
        f.write(
            f'{time.ctime()} | "{preview}" | WPM: {wpm} | Accuracy: {acc}% | Time: {duration}s\n'
        )


def run_all_lines(stdscr, lines):
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # correct = green
    curses.init_pair(2, curses.COLOR_RED, -1)  # wrong = red

    results = []

    for i, line in enumerate(lines):
        next_line = lines[i + 1] if i + 1 < len(lines) else None
        stats = typing_tutor(stdscr, line, i + 1, len(lines), next_line)
        if stats is None:
            stdscr.clear()
            stdscr.addstr(0, 0, "Quitting early.")
            return

        wpm, acc, dur = calc_stats(stats)
        save_stats(line, wpm, acc, dur)
        results.append(stats)

    total_chars = sum(r["chars"] for r in results)
    total_mistakes = sum(r["mistakes"] for r in results)
    total_time = sum(r["time"] for r in results)

    wpm = (total_chars / 5) / (total_time / 60) if total_time > 0 else 0
    acc = (
        (total_chars / (total_chars + total_mistakes)) * 100
        if (total_chars + total_mistakes) > 0
        else 0
    )

    stdscr.clear()
    stdscr.addstr(0, 0, "All lines completed.\n", curses.A_BOLD)
    stdscr.addstr(2, 0, f"Total time:     {round(total_time, 2)}s")
    stdscr.addstr(3, 0, f"Total chars:    {total_chars}")
    stdscr.addstr(4, 0, f"Total mistakes: {total_mistakes}")
    stdscr.addstr(5, 0, f"Overall WPM:    {round(wpm)}")
    stdscr.addstr(6, 0, f"Accuracy:       {round(acc)}%")

    stdscr.addstr(8, 0, "Stats saved to results.txt. Press any key to exit.")
    stdscr.refresh()
    stdscr.getch()


def main():
    if not preprocess_text():
        return

    try:
        with open("processedtext.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Missing file: processedtext.txt")
        return

    if not lines:
        print("Your processedtext.txt file is empty.")
        return

    curses.wrapper(lambda stdscr: run_all_lines(stdscr, lines))


if __name__ == "__main__":
    main()
