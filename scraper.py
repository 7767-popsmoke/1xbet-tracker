def parse_category(o1: float, ox: float, o2: float):
    """
    Accepte toutes les cotes de 2.00 à 2.99 et de 3.00 à 3.99 sans restriction.
    """
    def get_tier(val):
        if 2.00 <= val <= 2.99:
            return 2
        elif 3.00 <= val <= 3.99:
            return 3
        return None

    t1, tx, t2 = get_tier(o1), get_tier(ox), get_tier(o2)

    # Si une cote sort des limites [2.00 - 3.99], le match est écarté
    if None in (t1, tx, t2):
        return None

    base_pattern = f"{t1}/{tx}/{t2}"
    if base_pattern not in ["2/3/3", "3/3/2"]:
        return None

    # Détermination de la variante selon les décimales réelles
    if o1 < ox and ox < o2:
        variant = "[1 < X < 2]"
    elif o1 < o2 and o2 < ox:
        variant = "[1 < 2 < X]"
    elif ox < o1 and o1 < o2:
        variant = "[X < 1 < 2]"
    elif ox < o2 and o2 < o1:
        variant = "[X < 2 < 1]"
    elif o2 < o1 and o1 < ox:
        variant = "[2 < 1 < X]"
    elif o2 < ox and ox < o1:
        variant = "[2 < X < 1]"
    elif o1 == ox and ox < o2:
        variant = "[1 = X < 2]"
    elif o2 < o1 and o1 == ox:
        variant = "[2 < 1 = X]"
    elif o1 == o2 and o2 < ox:
        variant = "[1 = 2 < X]"
    elif ox < o1 and o1 == o2:
        variant = "[X < 1 = 2]"
    elif ox == o2 and o2 < o1:
        variant = "[X = 2 < 1]"
    elif o1 < ox and ox == o2:
        variant = "[1 < X = 2]"
    elif o1 == ox and ox == o2:
        variant = "[1 = X = 2]"
    elif o1 < ox and ox > o2:
        variant = "[1 < X > 2]"
    elif o2 < ox and ox > o1:
        variant = "[2 < X > 1]"
    else:
        variant = "[1 < X < 2]"

    return f"{base_pattern} {variant}"
