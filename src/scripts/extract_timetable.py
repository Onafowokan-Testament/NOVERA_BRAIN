import re

import pandas as pd
import pdfplumber


def extract_timetable_from_pdf(pdf_path: str) -> pd.DataFrame:
    """
    Extract timetable from Covenant University PDF using pdfplumber.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        DataFrame with: day, room, building, time_start, time_end, course_code, entry_type
    """

    # Time slots
    time_slots = [
        ("8am", "9am"),
        ("9am", "10am"),
        ("10am", "11am"),
        ("11am", "12noon"),
        ("12noon", "1pm"),
        ("1pm", "2pm"),
        ("2pm", "3pm"),
        ("3pm", "4pm"),
        ("4pm", "5pm"),
        ("5pm", "6pm"),
        ("6pm", "7pm"),
        ("7pm", "8pm"),
    ]

    all_records = []

    # Open PDF
    with pdfplumber.open(pdf_path) as pdf:
        print(f"📄 Processing {len(pdf.pages)} pages...")

        current_day = None

        for page_num, page in enumerate(pdf.pages, 1):
            print(f"  Page {page_num}...")

            # Extract tables from the page
            tables = page.extract_tables()

            if not tables:
                # Try extracting text to find day
                text = page.extract_text()
                day = extract_day_from_text(text)
                if day:
                    current_day = day
                continue

            # Process each table
            for table in tables:
                if not table or len(table) < 2:
                    continue

                # Check for day in table or page text
                page_text = page.extract_text()
                day = extract_day_from_text(page_text)
                if day:
                    current_day = day

                # Process table rows
                for row in table:
                    if not row or len(row) < 3:
                        continue

                    # Skip header rows
                    if is_header_row(row):
                        continue

                    # Extract room/hall (first column)
                    room = clean_text(row[0])
                    if not room or len(room) < 2:
                        continue

                    # Extract building (last column)
                    building = clean_text(row[-1])

                    # Extract entries (middle columns - one per time slot)
                    # Assuming columns 1 to -1 are time slots
                    entries = row[1:-1]

                    # Process each time slot
                    for idx, entry in enumerate(entries):
                        if idx >= len(time_slots):
                            break

                        entry = clean_text(entry)
                        if not entry:
                            continue

                        time_start, time_end = time_slots[idx]
                        entry_type = classify_entry_type(entry)

                        # Split multiple courses
                        if entry_type == "regular_class":
                            courses = split_courses(entry)
                            for course in courses:
                                all_records.append(
                                    {
                                        "day": current_day,
                                        "room": room,
                                        "building": building,
                                        "time_start": time_start,
                                        "time_end": time_end,
                                        "course_code": course,
                                        "entry_type": entry_type,
                                    }
                                )
                        else:
                            all_records.append(
                                {
                                    "day": current_day,
                                    "room": room,
                                    "building": building,
                                    "time_start": time_start,
                                    "time_end": time_end,
                                    "course_code": entry,
                                    "entry_type": entry_type,
                                }
                            )

    # Create DataFrame
    df = pd.DataFrame(all_records)

    # Clean up
    df = df[df["day"].notna()]  # Remove rows without day
    df = df.drop_duplicates()

    # Sort
    day_order = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]
    df["day"] = pd.Categorical(df["day"], categories=day_order, ordered=True)
    df = df.sort_values(["day", "time_start"]).reset_index(drop=True)

    return df


def extract_day_from_text(text: str) -> str:
    """Extract day of week from text"""
    if not text:
        return None

    text_upper = text.upper()
    days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]

    for day in days:
        if day in text_upper:
            return day

    return None


def is_header_row(row: list) -> bool:
    """Check if row is a header row"""
    if not row:
        return False

    first_cell = str(row[0]).upper()

    # Check for common header patterns
    header_keywords = ["ROOM/HALL/LAB", "BUILDING", "8AM_9AM", "DAY:", "TIME TABLE"]

    for keyword in header_keywords:
        if keyword in first_cell:
            return True

    return False


def clean_text(text) -> str:
    """Clean extracted text"""
    if text is None:
        return ""

    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)  # Normalize whitespace
    text = text.replace("\n", " ")

    return text


def classify_entry_type(entry: str) -> str:
    """Classify the type of entry"""
    entry_upper = entry.upper()

    if "BREAK TIME" in entry_upper or entry_upper == "BREAK":
        return "break_time"
    elif "CHAPEL" in entry_upper:
        return "chapel_service"
    elif "EDS" in entry_upper and "PRACTICAL" in entry_upper:
        return "eds_practical"
    elif "TMCSPORT" in entry_upper or "TMC" in entry_upper:
        return "tmc_sport"
    elif "BIBLE" in entry_upper or "FELLOWSHIP" in entry_upper:
        return "bible_study"
    elif "DLD" in entry_upper:
        return "dld"
    elif "SERVICE" in entry_upper:
        return "chapel_service"
    else:
        return "regular_class"


def split_courses(entry: str) -> list:
    """
    Split combined course codes.
    Examples:
    - "MKT314" -> ["MKT314"]
    - "CHE313/333/TCH311" -> ["CHE313", "CHE333", "TCH311"]
    - "ACC111/112" -> ["ACC111", "ACC112"]
    """
    entry = entry.strip()

    # Split by forward slash
    parts = entry.split("/")

    courses = []
    prefix = None

    for part in parts:
        part = part.strip()

        # Full course code (letters + numbers)
        match = re.match(r"^([A-Z]{2,4})(\d{3})$", part)
        if match:
            prefix = match.group(1)
            courses.append(part)

        # Just numbers, use previous prefix
        elif re.match(r"^\d{3}$", part) and prefix:
            courses.append(f"{prefix}{part}")

        # Fallback
        else:
            if part:
                courses.append(part)

    return courses if courses else [entry]


def save_timetable(df: pd.DataFrame, csv_path: str = "covenant_timetable.csv"):
    """Save timetable to CSV"""
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Saved {len(df)} records to {csv_path}")


def show_stats(df: pd.DataFrame):
    """Display statistics"""
    print("\n" + "=" * 60)
    print("📊 TIMETABLE EXTRACTION SUMMARY")
    print("=" * 60)
    print(f"Total entries: {len(df)}")

    print("\n📅 Entries by day:")
    print(df["day"].value_counts().sort_index())

    print("\n📚 Entry types:")
    print(df["entry_type"].value_counts())

    classes = df[df["entry_type"] == "regular_class"]
    print(f"\n🎓 Unique courses: {classes['course_code'].nunique()}")
    print(f"🏢 Buildings: {df['building'].nunique()}")
    print(f"🚪 Rooms/Halls: {df['room'].nunique()}")

    print("\n📋 Sample entries:")
    print(df.head(15).to_string(index=False, max_colwidth=20))


# Main execution
if __name__ == "__main__":
    # Path to your PDF file
    pdf_path = "new_timetable.pdf"

    try:
        # Extract timetable
        print("🚀 Starting extraction...")
        df = extract_timetable_from_pdf(pdf_path)

        # Show statistics
        show_stats(df)

        # Save to CSV
        save_timetable(df)

        print("\n✨ Extraction complete!")

    except FileNotFoundError:
        print(f"❌ Error: PDF file not found at '{pdf_path}'")
        print("Please update the pdf_path variable with the correct path.")
    except Exception as e:
        print(f"❌ Error during extraction: {str(e)}")
        import traceback

        traceback.print_exc()
