import os
from os.path import dirname, realpath
import sys
from glob import glob
from collections import Sequence
from .palette import ThreadPalette

class _ThreadCatalog(Sequence):
    """Holds a set of ThreadPalettes."""

    def __init__(self):
        self.palettes = []
        self.load_palettes(self.get_palettes_path())

    def get_palettes_path(self):
        if getattr(sys, 'frozen', None) is not None:
            path = sys._MEIPASS
        else:
            path = dirname(dirname(dirname(realpath(__file__))))

        return os.path.join(path, 'palettes')

    def load_palettes(self, path):
        for palette_file in glob(os.path.join(path, '*.gpl')):
            self.palettes.append(ThreadPalette(palette_file))

    def palette_names(self):
        return list(sorted(palette.name for palette in self))

    def __getitem__(self, item):
        return self.palettes[item]

    def __len__(self):
        return len(self.palettes)

    def _num_exact_color_matches(self, palette, threads):
        """Number of colors in stitch plan with an exact match in this palette."""

        return sum(1 for thread in threads if thread in palette)

    def match_and_apply_palette(self, stitch_plan):
        palette = self.match_palette(stitch_plan)

        if palette is not None:
            self.apply_palette(stitch_plan, palette)

        return palette

    def match_palette(self, stitch_plan):
        """Figure out which color palette was used

        Scans the catalog of color palettes and chooses one that seems most
        likely to be the one that the user used.  A palette will only be
        chosen if more tha 80% of the thread colors in the stitch plan are
        exact matches for threads in the palette.
        """

        threads = [color_block.color for color_block in stitch_plan]
        palettes_and_matches = [(palette, self._num_exact_color_matches(palette, threads))
                                for palette in self]
        palette, matches = max(palettes_and_matches, key=lambda item: item[1])

        if matches < 0.8 * len(stitch_plan):
            # if less than 80% of the colors are an exact match,
            # don't use this palette
            return None
        else:
            return palette

    def apply_palette(self, stitch_plan, palette):
        for color_block in stitch_plan:
            nearest = palette.nearest_color(color_block.color)

            color_block.color.name = nearest.name
            color_block.color.number = nearest.number
            color_block.color.manufacturer = nearest.manufacturer


_catalog = None

def ThreadCatalog():
    """Singleton _ThreadCatalog factory"""

    global _catalog
    if _catalog is None:
        _catalog = _ThreadCatalog()

    return _catalog