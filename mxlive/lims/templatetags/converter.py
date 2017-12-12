from django import template

register = template.Library()  

_h = 4.13566733e-15 # eV.s
_c = 299792458e10   # A/s
  
@register.filter("energy_to_wavelength")  
def energy_to_wavelength(energy): 
    """Convert energy in keV to wavelength in angstroms."""
    if energy == 0.0:
        return 0.0
    return (_h*_c)/(energy*1000.0)


@register.filter("humanize_minutes")
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