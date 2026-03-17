"""
clean_jsonl.py
--------------
Cleans a messy JSONL / JSON file into proper JSONL format:
  - Handles multiple concatenated JSON arrays
  - Handles pretty-printed (multi-line) objects
  - Fixes missing commas between array elements
  - Fixes invalid JSON escape sequences (e.g. bare backslashes)
  - Strips Windows-style CRLF line endings
  - Removes duplicate records (by sample_id if present, else by full content)
  - One valid JSON object per line in the output

Usage:
    python clean_jsonl.py input.jsonl output.jsonl
    python clean_jsonl.py input.jsonl            # overwrites input file
"""

import json
import re
import sys
import os


def fix_invalid_escapes(text: str) -> str:
    """
    Replace invalid JSON escape sequences (backslash followed by a character
    that is not a valid JSON escape) with a double backslash.
    Valid JSON escapes: backslash + one of: " \\ / b f n r t uXXXX
    """
    return re.sub(r'\\([^"\\/bfnrtu\r\n])', r'\\\\\1', text)


def fix_missing_commas(text: str) -> str:
    """
    Fix missing commas between array elements where a closing bracket
    is immediately followed by a quoted key on the next line.
    e.g.  ]\n"nextKey"  -->  ],\n"nextKey"
    """
    return re.sub(r'(\])\r?\n(")', r'\1,\n\2', text)


def extract_records(text: str) -> tuple[list[dict], list[tuple[int, str]]]:
    """
    Stream-parse all JSON objects from text that may contain:
      - Multiple concatenated arrays: [...][...]
      - Mixed single-line and multi-line objects
      - Stray commas, brackets, and whitespace between objects

    Returns (records, errors) where errors is a list of (position, message).
    """
    decoder = json.JSONDecoder()
    records = []
    errors = []
    pos = 0
    text = text.strip()

    while pos < len(text):
        # Skip whitespace, commas, array brackets
        while pos < len(text) and text[pos] in ' \t\n\r,[]':
            pos += 1
        if pos >= len(text):
            break

        if text[pos] == '{':
            try:
                obj, end_pos = decoder.raw_decode(text, pos)
                records.append(obj)
                pos = end_pos
            except json.JSONDecodeError as e:
                errors.append((pos, str(e)))
                # Skip to the next top-level object
                next_obj = text.find('\n{', pos + 1)
                if next_obj == -1:
                    break
                pos = next_obj + 1
        else:
            pos += 1

    return records, errors


def deduplicate(records: list[dict]) -> tuple[list[dict], int]:
    """
    Remove duplicate records.
    Uses 'sample_id' as the deduplication key if present,
    otherwise falls back to full content comparison.
    Returns (deduplicated_records, duplicate_count).
    """
    seen = set()
    unique = []
    dupes = 0

    for rec in records:
        key = rec.get('sample_id') or json.dumps(rec, sort_keys=True)
        if key in seen:
            dupes += 1
        else:
            seen.add(key)
            unique.append(rec)

    return unique, dupes


def clean_jsonl(input_path: str, output_path: str) -> None:
    print(f"Reading:  {input_path}")

    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_size = len(content)

    # Step 1: Fix structural issues
    content = fix_missing_commas(content)
    content = fix_invalid_escapes(content)

    # Step 2: Extract all JSON objects
    records, errors = extract_records(content)

    if errors:
        print(f"  ⚠️  {len(errors)} record(s) could not be parsed and were skipped:")
        for pos, msg in errors:
            print(f"     pos {pos}: {msg}")

    # Step 3: Deduplicate
    records, dupes = deduplicate(records)
    if dupes:
        print(f"  ⚠️  {dupes} duplicate record(s) removed")

    # Step 4: Write clean JSONL (one object per line, LF line endings)
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')

    # Step 5: Verify every output line parses cleanly
    bad_lines = 0
    with open(output_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  ❌ Output line {i} failed validation: {e}")
                bad_lines += 1

    new_size = os.path.getsize(output_path)
    status = "✅" if bad_lines == 0 else "❌"
    print(f"Writing:  {output_path}")
    print(f"  {status} {len(records)} valid records written")
    print(f"  Original size: {original_size:,} bytes → {new_size:,} bytes")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python clean_jsonl.py input.jsonl [output.jsonl]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file

    if not os.path.exists(input_file):
        print(f"Error: file not found: {input_file}")
        sys.exit(1)

    clean_jsonl(input_file, output_file)