import re


def normalize_phone(raw: str) -> str:
    """Farklı yazımları tek biçime çevirir: 0555 123 45 67 / 5551234567 / +905551234567 -> +905551234567"""
    digits = re.sub(r"[\s\-()]", "", raw.strip())
    digits = digits.removeprefix("+")
    if not digits.isdigit():
        raise ValueError("Telefon numarası yalnızca rakamlardan oluşmalıdır.")
    if len(digits) == 12 and digits.startswith("90"):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]
    if len(digits) != 10 or not digits.startswith("5"):
        raise ValueError("Geçerli bir cep telefonu numarası girin (örn. 5551234567).")
    return "+90" + digits
