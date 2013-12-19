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