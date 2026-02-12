from datetime import date


def parse_date(date_str: str) -> date | None:
    """Parse date string in dd/mm/yyyy, dd/mm/yy or YYYY-MM-DD format to date object"""
    try:
        s = date_str.strip()
        if "-" in s and len(s) >= 8 and s[4] == "-":
            # ISO format: YYYY-MM-DD
            year, month, day = int(s[0:4]), int(s[5:7]), int(s[8:10])
        else:
            # Italian format: dd/mm/yyyy or dd/mm/yy
            parts = s.split("/")
            if len(parts) != 3:
                return None
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 100:
                year += 2000
        return date(year, month, day)
    except ValueError, AttributeError, IndexError:
        return None
