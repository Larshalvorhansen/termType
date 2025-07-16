import curses
import time


def typing_tutor(stdscr, text, index, total):
    curses.curs_set(1)
    stdscr.clear()

    # Line progress indicator
    stdscr.addstr(0, 0, f"[{index}/{total}]")
    stdscr.addstr(2, 0, text)

    i = 0
    mistakes = 0
    start_time = time.time()

    while i < len(text):
        ch = stdscr.get_wch()

        if isinstance(ch, str) and ord(ch) == 27:  # ESC
            if confirm_quit(stdscr):
                return None  # user chose to quit
            else:
                stdscr.clear()
                stdscr.addstr(0, 0, f"[{index}/{total}]")
                stdscr.addstr(2, 0, text)
                stdscr.move(2, i)
                stdscr.refresh()
                continue

        correct = ch == text[i]
        color = curses.color_pair(1) if correct else curses.color_pair(2)
        stdscr.addstr(2, i, text[i], color)

        if correct:
            i += 1
        else:
            mistakes += 1

        stdscr.refresh()

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
        stats = typing_tutor(stdscr, line, i + 1, len(lines))
        if stats is None:
            stdscr.clear()
            stdscr.addstr(0, 0, "Quitting early.")
            return

        wpm, acc, dur = calc_stats(stats)
        save_stats(line, wpm, acc, dur)
        results.append(stats)

    # Compute overall stats
    total_chars = sum(r["chars"] for r in results)
    total_mistakes = sum(r["mistakes"] for r in results)
    total_time = sum(r["time"] for r in results)
    total_entries = len(results)

    wpm = (total_chars / 5) / (total_time / 60) if total_time > 0 else 0
    acc = (
        (total_chars / (total_chars + total_mistakes)) * 100
        if (total_chars + total_mistakes) > 0
        else 0
    )

    # Show summary
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
    try:
        with open("text.txt", "r") as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Missing file: text.txt")
        return

    if not lines:
        print("Your text.txt file is empty.")
        return

    curses.wrapper(lambda stdscr: run_all_lines(stdscr, lines))


if __name__ == "__main__":
    main()
