"""Contains custom magodo Todo spells used by greatday."""

from __future__ import annotations

from typing import List

from magodo.spells import register_spell_factory
from magodo.types import TodoSpell


GREAT_SPELLS: List[TodoSpell] = []
spell = register_spell_factory(GREAT_SPELLS)
