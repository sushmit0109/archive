# -*- coding: utf-8 -*-
"""Decide how a PDF's text can be recovered -- or that it cannot be.

Font names alone are not enough. Several PDFs in this archive embed real
Unicode Bangla fonts (Nikosh, NikoshBAN) as subsets with no usable ToUnicode
CMap, so the "text layer" extracts as raw glyph ids -- runs of control bytes
like \\x13\\x14\\x02!9\\x0b. That looks like a dense text layer by character
count while carrying no recoverable text at all, so it must be detected by
inspecting the characters, not the fonts.

Verdicts:
  SCANNED  -- no text layer worth the name; needs OCR.
  BROKEN   -- text layer present but unmappable (glyph ids); needs OCR.
  BIJOY    -- legacy SutonnyMJ ANSI; transcode with bijoy_fix.
  UNICODE  -- already Bangla Unicode; take as-is.
"""
import re, sys

# Very common Bangla words. A correct extraction is dense with them; a PDF
# whose ToUnicode map is simply wrong yields valid-looking Bangla that
# contains almost none (কবিশে where কমিশন was meant). Measured per 1000
# characters: good text scores ~30+, a bad mapping ~9-11.
COMMON = ["এবং", "করা", "হয়", "জন্য", "থেকে", "সকল", "বিষয়", "মধ্যে", "সরকার",
          "কমিশন", "আইন", "নির্বাচন", "ব্যবস্থা", "সুপারিশ", "করে", "হবে", "এই",
          "যে", "না", "প্রতিবেদন", "সদস্য", "অধ্যায়"]
GOOD_SCORE = 20.0    # per 1000 chars
SCORE_MIN_CHARS = 8000   # a table of contents is legitimately word-poor;
                         # only judge vocabulary on a long run of prose


def word_score(text):
    """Common-Bangla-word density per 1000 characters."""
    if not text:
        return 0.0
    return 1000.0 * sum(text.count(w) for w in COMMON) / len(text)


def exotic_ratio(text):
    """Share of letters that are neither Bangla nor ASCII.

    A broken ToUnicode map splices Cyrillic/Greek/IPA letters into Bangla
    words (সংিবধান সংЅার, ɈাǇˉকালীন). Clean text is ~0%; garbled runs 5-16%.
    This is language-independent, so it does not fire on English documents.
    """
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    exotic = sum(1 for c in letters
                 if not ("\u0980" <= c <= "\u09FF" or c.isascii()))
    return 100.0 * exotic / len(letters)


BN_WORD = re.compile(r"[\u0980-\u09FF]+")
# Dependent vowel signs and hasanta. Bangla orthography never starts a word
# with one, so a PDF whose extraction reorders marks ahead of their consonant
# (\u09c7\u09ad\u09c7\u0999 \u09c7\u09ab\u09b2 for \u09ad\u09c7\u0999\u09c7 \u09ab\u09c7\u09b2) shows up immediately. Clean text is ~0%;
# that corruption runs ~25%. It survives inside a mostly-English document,
# where a Bangla-vocabulary test would never fire.
LEADING_MARK = set(chr(c) for c in range(0x09BE, 0x09CD)) | {"\u09CD", "\u09D7"}
LEADING_MATRA_MAX = 2.0
BN_MIN_CHARS = 8000


def bangla_words(text):
    return BN_WORD.findall(text)


def leading_matra_pct(text):
    words = bangla_words(text)
    if not words:
        return 0.0
    bad = sum(1 for w in words if w[0] in LEADING_MARK)
    return 100.0 * bad / len(words)


def bangla_share(text):
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    return sum(1 for c in letters if "\u0980" <= c <= "\u09FF") / len(letters)


# Calibrated on hand-checked samples: clean text 0-1.6% exotic, corrupt
# 5-16%. Bangla word density: clean prose ~30, clean legal/ToC ~12-14,
# nonsense 7-10.
EXOTIC_MAX = 3.0
SCORE_BAD = 10.0
SCORE_SUSPECT = 18.0  # between BAD and this: fill, but flag for a human look


def garble_verdict(text):
    """'ok' | 'garbled' | 'suspect', with the numbers behind it.

    Three independent corruptions turn up in this archive and each needs its
    own test: glyph-id/exotic splicing, marks reordered ahead of their
    consonant, and a mapping that yields valid Bangla letters in the wrong
    places. The last two are measured on the Bangla subset only, so a mostly
    English document with a corrupt Bangla quotation is still caught.
    """
    ex = exotic_ratio(text)
    if ex > EXOTIC_MAX:
        return "garbled", {"exotic": round(ex, 2)}
    lm = leading_matra_pct(text)
    if lm > LEADING_MATRA_MAX:
        return "garbled", {"leading_matra": round(lm, 2)}
    bn = " ".join(bangla_words(text))
    if len(bn) >= BN_MIN_CHARS:
        sc = word_score(bn)
        if sc < SCORE_BAD:
            return "garbled", {"score": round(sc, 1)}
        if sc < SCORE_SUSPECT:
            return "suspect", {"score": round(sc, 1)}
    return "ok", {"exotic": round(ex, 2), "leading_matra": round(lm, 2)}


def looks_garbled(text):
    return garble_verdict(text)[0] == "garbled"


BANGLA = re.compile(r"[ঀ-৿]")
# cp1252 high range that SutonnyMJ uses for Bangla glyphs
BIJOY_HI = re.compile(r"[ -ÿŒ-š–-•…‰‹-›€™]")
CTRL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F-]")
MIN_CPP = 100


def sample_text(doc, n=24):
    pages = doc.page_count
    if pages == 0:
        return "", 0, 0
    idx = sorted(set(int(i * (pages - 1) / max(n - 1, 1)) for i in range(min(n, pages))))
    parts, bijoy_fonts = [], 0
    for i in idx:
        page = doc[i]
        parts.append(page.get_text())
        for f in page.get_fonts():
            if "SutonnyMJ" in f[3]:
                bijoy_fonts += 1
    return "".join(parts), len(idx), bijoy_fonts


def classify(doc):
    text, n, bijoy_fonts = sample_text(doc)
    if n == 0:
        return "EMPTY", {}
    stripped = text.strip()
    cpp = len(stripped) // n
    ctrl = len(CTRL.findall(text))
    bn = len(BANGLA.findall(text))
    hi = len(BIJOY_HI.findall(text))
    letters = sum(c.isalpha() for c in text)
    total = max(len(text), 1)
    stats = {"cpp": cpp, "ctrl%": round(100 * ctrl / total, 1),
             "bangla%": round(100 * bn / total, 1),
             "bijoyhi%": round(100 * hi / total, 1), "pages": doc.page_count}
    if cpp < MIN_CPP:
        return "SCANNED", stats
    # Glyph-id soup: control bytes are never legitimate body text.
    if ctrl / total > 0.02:
        return "BROKEN", stats
    if bn / total > 0.25:
        v, extra = garble_verdict(text)
        stats.update(extra)
        if v == "garbled":
            return "GARBLED", stats
        return ("SUSPECT" if v == "suspect" else "UNICODE"), stats
    # Bijoy looks like Latin letters plus cp1252 high marks, with no Bangla.
    if bijoy_fonts and (hi + letters) / total > 0.3 and bn / total < 0.05:
        return "BIJOY", stats
    if bn / total > 0.05:
        v, extra = garble_verdict(text)
        stats.update(extra)
        if v == "garbled":
            return "GARBLED", stats
        return ("SUSPECT" if v == "suspect" else "UNICODE"), stats
    return "BROKEN", stats


if __name__ == "__main__":
    import fitz
    for p in sys.argv[1:]:
        d = fitz.open(p)
        k, s = classify(d)
        print(f"{k:<8} {s} {p}")
        d.close()
