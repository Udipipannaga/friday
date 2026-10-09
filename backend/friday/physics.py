"""A deliberately narrow, deterministic lift-versus-weight calculator.

This is a tool, not a physics-trained language model or a flight simulator.
"""

import math

from pydantic import BaseModel, ConfigDict, Field


class PhysicsInputError(ValueError):
    pass


class Quantity(BaseModel):
    model_config = ConfigDict(extra='forbid')

    value: float = Field(ge=0, le=1_000_000_000, allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=12)


class LiftSupportInput(BaseModel):
    model_config = ConfigDict(extra='forbid')

    mass: Quantity
    wing_area: Quantity
    air_speed: Quantity
    air_density: Quantity
    lift_coefficient: float = Field(ge=-4, le=4, allow_inf_nan=False)
    gravity: Quantity = Field(default_factory=lambda: Quantity(value=9.81, unit='m/s2'))


_UNITS = {
    'mass': {'kg': 1, 'g': 0.001},
    'wing_area': {'m2': 1, 'cm2': 0.0001},
    'air_speed': {'m/s': 1, 'km/h': 1 / 3.6},
    'air_density': {'kg/m3': 1},
    'gravity': {'m/s2': 1},
}


def _si(name: str, quantity: Quantity) -> float:
    factor = _UNITS[name].get(quantity.unit)
    if factor is None:
        raise PhysicsInputError(f'{name} must use one of: {", ".join(_UNITS[name])}.')
    value = quantity.value * factor
    if not math.isfinite(value):
        raise PhysicsInputError(f'{name} is outside the supported range.')
    return value


def solve_lift_support(data: LiftSupportInput) -> dict:
    """L = 0.5 * rho * v² * S * CL; W = m * g, in SI units.

    The comparison is static and assumes the supplied CL and speed; it does not
    predict stall, trim, drag, stability, or actual flight safety.
    """
    mass = _si('mass', data.mass)
    area = _si('wing_area', data.wing_area)
    speed = _si('air_speed', data.air_speed)
    density = _si('air_density', data.air_density)
    gravity = _si('gravity', data.gravity)
    if mass <= 0 or area <= 0 or density <= 0 or gravity <= 0:
        raise PhysicsInputError('Mass, wing area, air density, and gravity must be positive.')
    if mass > 100_000 or area > 10_000 or speed > 1_000 or density > 100 or gravity > 100:
        raise PhysicsInputError('An input exceeds the supported SI range.')
    lift = 0.5 * density * speed * speed * area * data.lift_coefficient
    weight = mass * gravity
    if not (math.isfinite(lift) and math.isfinite(weight)):
        raise PhysicsInputError('The calculated force is outside the supported range.')
    return {
        'lift': {'value': lift, 'unit': 'N'},
        'weight': {'value': weight, 'unit': 'N'},
        'margin': {'value': lift - weight, 'unit': 'N'},
        'supports_weight': lift >= weight,
        'method': 'L = 0.5 * air_density * air_speed^2 * wing_area * lift_coefficient; W = mass * gravity',
        'scope': 'Static lift-versus-weight estimate only; not a flight-safety or aerodynamic simulation.',
    }


_FORCE_UNITS = {'N': 1, 'mN': 0.001, 'kN': 1000}


def force_newtons(value: object) -> float:
    """Validate a submitted force, rejecting a wrong dimension or nonfinite value."""
    if not isinstance(value, dict) or set(value) != {'value', 'unit'}:
        raise PhysicsInputError('A force requires exactly value and unit.')
    unit = value['unit']
    number = value['value']
    if not isinstance(unit, str) or unit not in _FORCE_UNITS or isinstance(number, bool) or not isinstance(number, (int, float)):
        raise PhysicsInputError('Force must be a numeric value in N, mN, or kN.')
    if not (-1_000_000_000_000 <= number <= 1_000_000_000_000):
        raise PhysicsInputError('Force is outside the supported range.')
    result = float(number) * _FORCE_UNITS[unit]
    if not math.isfinite(result):
        raise PhysicsInputError('Force must be finite.')
    return result
