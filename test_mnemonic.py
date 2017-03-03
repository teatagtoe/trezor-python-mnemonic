#!/usr/bin/env python
#
# Copyright (c) 2013 Pavol Rusnak
# Copyright (c) 2017 mruddy
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from __future__ import print_function

import io
import json
import random
import sys
import unicodedata
import unittest
from binascii import hexlify, unhexlify

from mnemonic import Mnemonic

class MnemonicTest(unittest.TestCase):

    def _check_list(self, language, vectors):
        mnemo = Mnemonic(language)
        for v in vectors:
            code = mnemo.to_mnemonic(unhexlify(v['entropy']))
            seed = hexlify(Mnemonic.to_seed(code, 'TREZOR' if 'passphrase' not in v else v['passphrase']))
            if sys.version >= '3':
                seed = seed.decode('utf8')
            self.assertIs(mnemo.check(v['mnemonic']), True)
            self.assertEqual(v['mnemonic'], code)
            self.assertEqual(v['seed'], seed)

    def test_vectors(self):
        with io.open('vectors.json', mode='rt', encoding='utf-8', newline=u'\n') as f:
            vectors = json.load(f)
        for lang in vectors.keys():
            self._check_list(lang, vectors[lang])

    def test_failed_checksum(self):
        code = 'bless cloud wheel regular tiny venue bird web grief security dignity zoo'
        mnemo = Mnemonic('english')
        self.assertFalse(mnemo.check(code))
        code = u'bless cloud wheel regular tiny venue bird web grief security dignity zoo'
        self.assertFalse(mnemo.check(code))

    def test_checksum(self):
        mnemo = Mnemonic('english')
        self.assertTrue(mnemo.check(u'error fragile gadget'))
        self.assertTrue(mnemo.check(u'error\u3000fragile gadget'))
        self.assertTrue(mnemo.check('error fragile gadget'))
        if sys.version >= '3':
            self.assertTrue(mnemo.check('error\u3000fragile gadget'))
        else:
            self.assertFalse(mnemo.check('error\u3000fragile gadget'))

    def test_detection(self):
        self.assertEqual('english', Mnemonic.detect_language('security'))

        with self.assertRaises(Exception):
            Mnemonic.detect_language('xxxxxxx')

    def test_collision(self):
        # Check for the same words across wordlists.
        # This is prohibited because of auto-detection feature of language.

        words = []
        languages = Mnemonic.list_languages()
        for lang in languages:
            mnemo = Mnemonic(lang)
            words += mnemo.wordlist

        words_unique = list(set(words[:]))
        self.assertEqual(len(words), len(words_unique))

    def test_lengths(self):
        languages = Mnemonic.list_languages()
        codepoints = { 'english': (3, 8) }
        glyphs = { 'english': (3, 8) }
        for lang in languages:
            if lang not in codepoints:
                print("Skipping Language '{}'".format(lang))
                continue
            mnemo = Mnemonic(lang)
            words = [w for w in mnemo.wordlist if not codepoints[lang][0] <= len(w) <= codepoints[lang][1]]
            print("Language '{}'".format(lang))
            self.assertListEqual(words, [])
            words = [w for w in mnemo.wordlist if not glyphs[lang][0] <= len(unicodedata.normalize('NFKC', w)) <= glyphs[lang][1]]
            print("Language '{}'".format(lang))
            self.assertListEqual(words, [])

    def test_validchars(self):
        # check if wordlists contain valid characters
        codepoints  = { 'english': u'abcdefghijklmnopqrstuvwxyz'}
        languages = Mnemonic.list_languages()
        for lang in languages:
            if lang not in codepoints:
                print("Skipping Language '{}'".format(lang))
                continue
            mnemo = Mnemonic(lang)
            letters = set(sum([list(w) for w in mnemo.wordlist], []))
            print("Language '{}'".format(lang))
            for l in letters:
                self.assertIn(l, codepoints[lang])

    def test_unique(self):
        # Check for duplicated words in wordlist

        print("------------------------------------")
        print("Test of sorted and unique wordlists:")

        languages = Mnemonic.list_languages()
        # note: some standardized wordlists are not in the order that they would be sorted here
        # this is also the reason for the use of a linear search instead of binary in the Mnemonic
        # class for lookups
        for lang in languages:
            mnemo = Mnemonic(lang)
            unique = set(mnemo.wordlist)
            print("Language '{}'".format(lang))
            self.assertEqual(len(unique), len(mnemo.wordlist))

    def test_root_len(self):
        print("------------------------------------")
        print("Test of word prefixes:")

        languages = Mnemonic.list_languages()
        problems_found = 0

        for lang in languages:
            mnemo = Mnemonic(lang)
            prefixes = []
            for w in mnemo.wordlist:
                pref = unicodedata.normalize('NFKC', w)[:4]
                if pref in prefixes:
                    words = [w2 for w2 in mnemo.wordlist if unicodedata.normalize('NFKC', w2)[:4] == pref]
                    print("Duplicate prefix", pref, "for words", words)
                    problems_found += 1

                prefixes.append(pref)

        self.assertEqual(problems_found, 0)

    def test_similarity(self):
        similar = (
            ('a', 'c'), ('a', 'e'), ('a', 'o'),
            ('b', 'd'), ('b', 'h'), ('b', 'p'), ('b', 'q'), ('b', 'r'),
            ('c', 'e'), ('c', 'g'), ('c', 'n'), ('c', 'o'), ('c', 'q'), ('c', 'u'),
            ('d', 'g'), ('d', 'h'), ('d', 'o'), ('d', 'p'), ('d', 'q'),
            ('e', 'f'), ('e', 'o'),
            ('f', 'i'), ('f', 'j'), ('f', 'l'), ('f', 'p'), ('f', 't'),
            ('g', 'j'), ('g', 'o'), ('g', 'p'), ('g', 'q'), ('g', 'y'),
            ('h', 'k'), ('h', 'l'), ('h', 'm'), ('h', 'n'), ('h', 'r'),
            ('i', 'j'), ('i', 'l'), ('i', 't'), ('i', 'y'),
            ('j', 'l'), ('j', 'p'), ('j', 'q'), ('j', 'y'),
            ('k', 'x'),
            ('l', 't'),
            ('m', 'n'), ('m', 'w'),
            ('n', 'u'), ('n', 'z'),
            ('o', 'p'), ('o', 'q'), ('o', 'u'), ('o', 'v'),
            ('p', 'q'), ('p', 'r'),
            ('q', 'y'),
            ('s', 'z'),
            ('u', 'v'), ('u', 'w'), ('u', 'y'),
            ('v', 'w'), ('v', 'y')
        )

        languages = Mnemonic.list_languages()

        fail = False
        for lang in languages:
            mnemo = Mnemonic(lang)

            for w1 in mnemo.wordlist:
                for w2 in mnemo.wordlist:
                    if len(w1) != len(w2):
                        continue

                    if w1 == w2:
                        continue

                    if w1 > w2:
                        # No need to print warning twice
                        continue

                    diff = []
                    for i in range(len(w1)):
                        if w1[i] != w2[i]:
                            if w1[i] < w2[i]:
                                pair = (w1[i], w2[i])
                            else:
                                pair = (w2[i], w1[i])

                            diff.append(pair)
                            # pairs.update((pair,))

                    if len(diff) == 1:
                        if list(diff)[0] in similar:
                            fail = True
                            print("Similar words (%s): %s, %s" % (lang, w1, w2))

        if fail:
            self.fail("Similar words found")

    def test_utf8_nfkd(self):
        # The same sentence in various UTF-8 forms
        words_nfkd = u'Pr\u030ci\u0301s\u030cerne\u030c z\u030clut\u030couc\u030cky\u0301 ku\u030an\u030c u\u0301pe\u030cl d\u030ca\u0301belske\u0301 o\u0301dy za\u0301ker\u030cny\u0301 uc\u030cen\u030c be\u030cz\u030ci\u0301 pode\u0301l zo\u0301ny u\u0301lu\u030a'
        words_nfc = u'P\u0159\xed\u0161ern\u011b \u017elu\u0165ou\u010dk\xfd k\u016f\u0148 \xfap\u011bl \u010f\xe1belsk\xe9 \xf3dy z\xe1ke\u0159n\xfd u\u010de\u0148 b\u011b\u017e\xed pod\xe9l z\xf3ny \xfal\u016f'
        words_nfkc = u'P\u0159\xed\u0161ern\u011b \u017elu\u0165ou\u010dk\xfd k\u016f\u0148 \xfap\u011bl \u010f\xe1belsk\xe9 \xf3dy z\xe1ke\u0159n\xfd u\u010de\u0148 b\u011b\u017e\xed pod\xe9l z\xf3ny \xfal\u016f'
        words_nfd = u'Pr\u030ci\u0301s\u030cerne\u030c z\u030clut\u030couc\u030cky\u0301 ku\u030an\u030c u\u0301pe\u030cl d\u030ca\u0301belske\u0301 o\u0301dy za\u0301ker\u030cny\u0301 uc\u030cen\u030c be\u030cz\u030ci\u0301 pode\u0301l zo\u0301ny u\u0301lu\u030a'

        passphrase_nfkd = u'Neuve\u030cr\u030citelne\u030c bezpec\u030cne\u0301 hesli\u0301c\u030cko'
        passphrase_nfc = u'Neuv\u011b\u0159iteln\u011b bezpe\u010dn\xe9 hesl\xed\u010dko'
        passphrase_nfkc = u'Neuv\u011b\u0159iteln\u011b bezpe\u010dn\xe9 hesl\xed\u010dko'
        passphrase_nfd = u'Neuve\u030cr\u030citelne\u030c bezpec\u030cne\u0301 hesli\u0301c\u030cko'

        seed_nfkd = Mnemonic.to_seed(words_nfkd, passphrase_nfkd)
        seed_nfc = Mnemonic.to_seed(words_nfc, passphrase_nfc)
        seed_nfkc = Mnemonic.to_seed(words_nfkc, passphrase_nfkc)
        seed_nfd = Mnemonic.to_seed(words_nfd, passphrase_nfd)

        self.assertEqual(seed_nfkd, seed_nfc)
        self.assertEqual(seed_nfkd, seed_nfkc)
        self.assertEqual(seed_nfkd, seed_nfd)

    def test_to_entropy(self):
        data = [bytearray((random.getrandbits(8) for _ in range(32))) for _ in range(1024)]
        data.append(b'Lorem ipsum dolor sit amet amet.')
        languages = Mnemonic.list_languages()
        for lang in languages:
            m = Mnemonic(lang)
            for d in data:
                self.assertEqual(m.to_entropy(Mnemonic.normalize_string(m.to_mnemonic(d)).split(u' ')), d)

    def test_expand_word(self):
        m = Mnemonic('english')
        self.assertEqual('', m.expand_word(''))
        self.assertEqual(' ', m.expand_word(' '))
        self.assertEqual('access', m.expand_word('access')) # word in list
        self.assertEqual('access', m.expand_word('acce')) # unique prefix expanded to word in list
        self.assertEqual('acb', m.expand_word('acb')) # not found at all
        self.assertEqual('acc', m.expand_word('acc')) # multi-prefix match
        self.assertEqual('act', m.expand_word('act')) # exact three letter match
        self.assertEqual('action', m.expand_word('acti')) # unique prefix expanded to word in list

    def test_expand(self):
        m = Mnemonic('english')
        self.assertEqual('access', m.expand('access'))
        self.assertEqual('access access acb acc act action', m.expand('access acce acb acc act acti'))
        self.assertEqual('abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about', m.expand('aban abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about'))

    def test_ideographic_space_compatibility(self):
        # https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki
        # "The wordlist can contain native characters, but they must be
        # encoded in UTF-8 using Normalization Form Compatibility
        # Decomposition (NFKD)."
        # "To create a binary seed from the mnemonic, we use the PBKDF2
        # function with a mnemonic sentence (in UTF-8 NFKD) used as the
        # password and the string "mnemonic" + passphrase (again in
        # UTF-8 NFKD) used as the salt."
        # https://github.com/bitcoin/bips/blob/master/bip-0039/bip-0039-wordlists.md
        # Japanese: "Developers implementing phrase generation or
        # checksum verification must separate words using ideographic
        # spaces / accommodate users inputting ideographic spaces."
        self.assertEqual(bytearray(u'\u3000', 'utf-8'), bytearray(Mnemonic.IDEOGRAPHIC_SPACE, 'utf-8'))
        self.assertEqual(bytearray([0xe3, 0x80, 0x80]), bytearray(Mnemonic.IDEOGRAPHIC_SPACE, 'utf-8'))
        self.assertEqual(u'\u3000', Mnemonic.IDEOGRAPHIC_SPACE)
        self.assertEqual(1, len(Mnemonic.IDEOGRAPHIC_SPACE))
        self.assertEqual('IDEOGRAPHIC SPACE', unicodedata.name(Mnemonic.IDEOGRAPHIC_SPACE))
        normalized_ideographic_space = unicodedata.normalize('NFKD', Mnemonic.IDEOGRAPHIC_SPACE)
        self.assertEqual(1, len(normalized_ideographic_space))
        self.assertEqual(' ', normalized_ideographic_space)
        self.assertEqual(u' ', normalized_ideographic_space)
        self.assertEqual('SPACE', unicodedata.name(normalized_ideographic_space))
        self.assertEqual(bytearray([0x20]), bytearray(normalized_ideographic_space, 'utf-8'))
        self.assertEqual(u'a b', Mnemonic.normalize_string(u'a\u3000b'))

def __main__():
    unittest.main()
if __name__ == "__main__":
    __main__()
