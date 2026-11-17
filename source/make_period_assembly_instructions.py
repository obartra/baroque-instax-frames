# SPDX-License-Identifier: MIT
"""Use the shared five-step guide with the final period-catalog geometry."""
import make_assembly_instructions as guide
from assembly_steps import draw
from paths import P

if __name__=='__main__':
    draw(guide,
         P/'15-Rocaille-Floral-Corners-Instax-Mini-3-Magnets.3mf',
         P/'13-Rocaille-Segmental-Arch-Instax-Mini-3-Magnets.3mf',
         P/'validation/15-Rocaille-Floral-Corners-geometry.json',
         P/'instructions')
