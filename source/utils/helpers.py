import random

def generate_three_digits() -> str:
    return f"{random.randint(0, 999):03d}"
    
def pad_center(text: str, width: int = 5) -> str:
    """Membuat teks rata tengah dengan total lebar tertentu (padding spasi)."""
    text = str(text)
    if len(text) >= width:
        return text
    pad = width - len(text)
    left = pad // 2
    right = pad - left
    return ' ' * left + text + ' ' * right

def format_rupiah(amount: int) -> str:
    """Format angka menjadi format Rupiah dengan titik sebagai pemisah ribuan."""
    return f"{amount:,}".replace(",", ".")

