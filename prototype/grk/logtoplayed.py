#!/usr/bin/env python3
"""
Convert a fixed-width traffic log into a fixed-width as-played style report
with realistic timing variance (for test data generation).

Usage:
    python3 convert.py input.log output.txt
    python3 convert.py zbt_20260827.log          # → asplayedzbT-260827.txt
    python3 logtoplayed.py input.log output.txt
    python3 log2played.py zbt_20260827.log          # → asplayedzbT-260827.txt
"""

import sys
import re
import random
from datetime import datetime, timedelta
from pathlib import Path

# ---------- Fixed-width positions (0-based) ----------
# Input
IN_CART_START, IN_CART_LEN = 3, 6
IN_TITLE_START, IN_TITLE_LEN = 12, 25
IN_DUR_MIN_START = 37          # 2 chars
IN_DUR_SEC_START = 39          # 2 chars
IN_HH_START = 53               # 2 chars
IN_MM_START = 56
IN_SS_START = 59

# Output (total line length 109)
OUT_LINE_LEN = 109
OUT_TITLE_START = 42
OUT_TITLE_WIDTH = OUT_LINE_LEN - OUT_TITLE_START   # 67

def parse_time(hh: str, mm: str, ss: str) -> datetime:
    """Parse HH MM SS into a datetime (date is dummy)."""
    return datetime(2000, 1, 1, int(hh), int(mm), int(ss))

def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M:%S")

def format_planned_duration(total_seconds: int) -> str:
    """H:MM:SS (no leading zero on hours)."""
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h}:{m:02d}:{s:02d}"

def format_actual_duration(total_seconds: int) -> str:
    """HH:MM:SS."""
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def random_start_offset() -> int:
    """
    Seconds offset for actual airtime.
    - Very rare early (up to 2 min)
    - Most spots 0–5 min late
    - Some 5–13 min late
    - Probability decreases with larger delay
    """
    r = random.random()
    if r < 0.025:                          # ~2.5 % early
        return -random.randint(1, 120)
    else:
        # Exponential-ish favouring smaller positive delays
        delay = int(random.expovariate(1 / 150))
        return min(delay, 780)

def random_actual_duration(planned: int) -> int:
    """Usually exact, occasionally ±1 or ±2 seconds."""
    r = random.random()
    if r < 0.70:
        return planned
    elif r < 0.85:
        delta = random.choice([-1, 1])
    else:
        delta = random.choice([-2, 2])
    return max(1, planned + delta)

def convert_line(line: str) -> str | None:
    line = line.rstrip("\n")
    if len(line) < 61:
        return None

    try:
        cart = line[IN_CART_START:IN_CART_START + IN_CART_LEN]
        title = line[IN_TITLE_START:IN_TITLE_START + IN_TITLE_LEN].rstrip()
        dur_mm = line[IN_DUR_MIN_START:IN_DUR_MIN_START + 2]
        dur_ss = line[IN_DUR_SEC_START:IN_DUR_SEC_START + 2]
        hh = line[IN_HH_START:IN_HH_START + 2]
        mm = line[IN_MM_START:IN_MM_START + 2]
        ss = line[IN_SS_START:IN_SS_START + 2]

        planned_secs = int(dur_mm) * 60 + int(dur_ss)
        requested = parse_time(hh, mm, ss)

        offset = random_start_offset()
        actual_start = requested + timedelta(seconds=offset)
        actual_secs = random_actual_duration(planned_secs)

        parts = [
            format_time(requested),
            " ",
            format_time(actual_start),
            " ",
            f"{format_planned_duration(planned_secs):<7}",
            " ",
            format_actual_duration(actual_secs),
            " ",
            cart,
            " ",
            f"{title:<{OUT_TITLE_WIDTH}}",
        ]
        out = "".join(parts)
        return out[:OUT_LINE_LEN].ljust(OUT_LINE_LEN)

    except (ValueError, IndexError):
        return None

def derive_output_name(input_path: Path) -> Path | None:
    """
    If input looks like zbt_YYYYMMDD.log
    return asplayedzbT-YYMMDD.txt
    """
    m = re.fullmatch(r"zbt_(\d{8})\.log", input_path.name, re.IGNORECASE)
    if not m:
        return None
    yyyymmdd = m.group(1)
    yymmdd = yyyymmdd[2:]          # drop the century
    return input_path.with_name(f"asplayedzbT-{yymmdd}.txt")

def main():
    if len(sys.argv) == 2:
        infile = Path(sys.argv[1])
        outfile = derive_output_name(infile)
        if outfile is None:
            print("When only one argument is given, the input file must be named "
                  "like zbt_YYYYMMDD.log\n"
                  "Example: python3 convert.py zbt_20260827.log",
                  file=sys.stderr)
            sys.exit(1)
    elif len(sys.argv) == 3:
        infile = Path(sys.argv[1])
        outfile = Path(sys.argv[2])
    else:
        print(f"Usage:\n"
              f"  {sys.argv[0]} input.log output.txt\n"
              f"  {sys.argv[0]} zbt_20260827.log          # → asplayedzbT-260827.txt",
              file=sys.stderr)
        sys.exit(1)

    if not infile.is_file():
        print(f"Input file not found: {infile}", file=sys.stderr)
        sys.exit(1)

    with open(infile, "r", encoding="utf-8", errors="replace") as fin, \
         open(outfile, "w", encoding="utf-8") as fout:

        count = 0
        for line in fin:
            converted = convert_line(line)
            if converted:
                fout.write(converted + "\n")
                count += 1

    print(f"Converted {count} spots → {outfile}")

if __name__ == "__main__":
    main()