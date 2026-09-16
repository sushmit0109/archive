# -*- coding: utf-8 -*-
"""SutonnyMJ (Bijoy ANSI) -> Bangla Unicode.

The National Election Investigation report is not a scan: it carries a full
text layer, but its Bangla is set in SutonnyMJ, a legacy Bijoy ANSI font, so
pdftotext yields Latin gibberish. This transcodes it.

Wraps the `bijoy2unicode` package with three corrections, each verified
against every occurrence in the document:

1. Reph. Upstream rewrites "RA+HALANT+kar" to "kar+RA+HALANT", which is
   backwards: in Bijoy the reph glyph U+00A9 is typed *after* the consonant
   it rides on, and Unicode writes \u09b0\u09cd *before* that cluster. It turned
   \u09a8\u09bf\u09b0\u09cd\u09ac\u09be\u099a\u09a8 into \u09a8\u09bf\u09ac\u09be\u09b0\u09cd\u099a\u09a8. We park the reph on a private-use
   sentinel so the upstream rearranger leaves it alone, then move it
   ourselves once clusters are formed -- allowing for pre-base kars that the
   rearranger parks between the consonant and the reph (\u09aa\u09c1\u09a8\u09b0\u09cd\u09a8\u09bf\u09b0\u09cd\u09ac\u09be\u099a\u09a8).
2. Font subset. This PDF embeds a SutonnyMJ subset whose cmap differs from
   stock Bijoy for four glyphs (see _SUBSET_FIX).
3. An upstream IndexError when a run ends on a pre-base kar.
"""
import re

from bijoy2unicode import converter, util

# Upstream indexes one past the end when a run ends on a pre-base kar
# (a bold/italic switch mid-word does it). Make the accessor total.
if not getattr(util.mbCharAt, "_total", False):
    _orig_char_at = util.mbCharAt

    def _safe_char_at(s, i):
        try:
            return _orig_char_at(s, i)
        except IndexError:
            return ""

    _safe_char_at._total = True  # guard: re-import must not re-wrap
    util.mbCharAt = _safe_char_at
    converter.util.mbCharAt = _safe_char_at

_REPH = "\ue000"
_C = "\u0995-\u09b9\u09ce\u09dc-\u09df"
# Vowel signs and marks the rearranger may park between cluster and reph.
_KAR = "\u09be-\u09cc\u09d7\u0981-\u0983\u09bc"
_CLUSTER = re.compile(
    "([" + _C + "](?:\u09cd[" + _C + "])*)([" + _KAR + "]*)" + _REPH)

# Glyphs whose meaning in this subset differs from the stock Bijoy map.
# U+00CD only ever follows U+0161 (na+halant) or U+00AF (sa+halant) here,
#         giving \u09a8\u09cd\u09a4 and \u09b8\u09cd\u09a4 -- so it is \u09a4, not upstream's \u09a4\u09cd\u09ae.
# U+00F8 follows \u09b2 \u09b6 \u09aa \u09ac, giving \u09b2\u09cd\u09b2 \u09b6\u09cd\u09b2 \u09aa\u09cd\u09b2 \u09ac\u09cd\u09b2 -- so \u09cd\u09b2, not \u09b8\u09cd\u09a8.
# U+00FF is \u0995\u09cd\u09b7 (\u09b6\u09bf\u0995\u09cd\u09b7\u09be, \u09aa\u09cd\u09b0\u09a4\u09cd\u09af\u0995\u09cd\u09b7, \u09b0\u0995\u09cd\u09b7\u09be\u0995\u09be\u09b0\u09c0); upstream has no entry at all.
# Each is rewritten to the Bijoy codepoint upstream already gets right.
_SUBSET_FIX = str.maketrans({
    "\u00cd": "Z",        # -> \u09a4
    "\u00f8": "\u00ac",   # -> \u09cd\u09b2
    "\u00ff": "\u00b6",   # -> \u0995\u09cd\u09b7
    "\u00d0": "\u00ca",   # -> \u09a3\u09cd\u09a1 (\u0995\u09b0\u09cd\u09ae\u0995\u09be\u09a3\u09cd\u09a1); upstream read it as a hyphen
    "\u00e6": "y",        # -> \u09c1 (\u0997\u09c1\u09b0\u09c1\u09a4\u09b0, \u09ac\u09bf\u09b0\u09c1\u09a6\u09cd\u09a7\u09c7): the post-\u09b0 u-kar, not \u09ae\u09cd\u09a8
})

# U+2018 is \u09cd\u09a4\u09c1, but the source also uses it before U+0076 (aa-kar) where
# \u09cd\u09a4 is meant (\u099a\u09bf\u09a8\u09cd\u09a4\u09be, not \u099a\u09bf\u09a8\u09cd\u09a4\u09c1\u09be). Drop the u-kar in that position.
_TU_BEFORE_AA = re.compile("\u09cd\u09a4\u09c1(?=\u09be)")

_conv = converter.Unicode()


def convert(text):
    """Transcode one run of SutonnyMJ-encoded text to Bangla Unicode."""
    if not text:
        return text
    text = text.translate(_SUBSET_FIX)
    text = text.replace("\u00a9", _REPH)
    text = _conv.convertBijoyToUnicode(text)
    prev = None
    while prev != text:  # clusters can nest; iterate to a fixed point
        prev = text
        text = _CLUSTER.sub("\u09b0\u09cd\\1\\2", text)
    text = _TU_BEFORE_AA.sub("\u09cd\u09a4", text)
    return text.replace(_REPH, "")
