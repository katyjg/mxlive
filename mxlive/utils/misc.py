

def humanize_duration(hours, sec=False):
    if hours:
        days = int(hours / 24)
        minutes = max(0, int((hours % 1) * 60))
        seconds = sec and max(0, int(hours % 3600)) or 0
        hours = max(0, int(hours % 24))
        return "{d}{sepd}{h}{seph}{m}{seps}{s}".format(**{
            'd': days and "{} day{}".format(days, days > 1 and 's' or '') or "",
            'sepd': days and hours and ', ' or '',
            'h': hours and "{} hour{}".format(hours, hours > 1 and 's' or '') or "",
            'seph': (days or hours) and minutes and ', ' or '',
            'm': minutes and "{} minute{}".format(minutes, minutes > 1 and 's' or '') or "",
            'seps': sec and (days or hours or minutes) and seconds and ', ' or '',
            's': sec and seconds and "{} second{}".format(seconds, seconds > 1 and 's' or '') or ""
        })
    return "0 minutes"


def natural_duration(delta, sec=False):
    hours = delta.total_seconds()/3600
    return humanize_duration(hours, sec=sec)