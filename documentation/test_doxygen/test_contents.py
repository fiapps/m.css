#
#   This file is part of m.css.
#
#   Copyright © 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025
#             Vladimír Vondruš <mosra@centrum.cz>
#
#   Permission is hereby granted, free of charge, to any person obtaining a
#   copy of this software and associated documentation files (the "Software"),
#   to deal in the Software without restriction, including without limitation
#   the rights to use, copy, modify, merge, publish, distribute, sublicense,
#   and/or sell copies of the Software, and to permit persons to whom the
#   Software is furnished to do so, subject to the following conditions:
#
#   The above copyright notice and this permission notice shall be included
#   in all copies or substantial portions of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
#   THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#   FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#   DEALINGS IN THE SOFTWARE.
#

import os
import pickle
import pygments
import re
import shutil
import subprocess
import unittest

from hashlib import sha1

from doxygen import EntryType
from _search import pretty_print, searchdata_filename

from . import BaseTestCase, IntegrationTestCase, doxygen_version, parse_version

def dot_version():
    return re.match(r'.*version (?P<version>\d+\.\d+\.\d+).*', subprocess.check_output(['dot', '-V'], stderr=subprocess.STDOUT).decode('utf-8').strip()).group('version')

class Typography(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')
        self.assertEqual(*self.actual_expected_contents('index.html'))

    @unittest.skipUnless(parse_version(doxygen_version()) > parse_version("1.8.17"), "new features in 1.8.17")
    def test_1817(self):
        self.run_doxygen(wildcard='doxygen1817.xml')
        self.assertEqual(*self.actual_expected_contents('doxygen1817.html'))

class Blocks(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='*.xml')
        self.assertEqual(*self.actual_expected_contents('index.html'))
        # Multiple xrefitems should be merged into one
        self.assertEqual(*self.actual_expected_contents('File_8h.html'))

    @unittest.skipUnless(parse_version(doxygen_version()) > parse_version("1.8.18"), "new features in 1.8.18")
    def test_1818(self):
        self.run_doxygen(wildcard='*.xml')
        self.assertEqual(*self.actual_expected_contents('doxygen1818.html'))

    def test_xrefitem(self):
        self.run_doxygen(wildcard='*.xml')

        if parse_version(doxygen_version()) > parse_version("1.8.14"):
            self.assertEqual(*self.actual_expected_contents('todo.html'))
        # https://github.com/doxygen/doxygen/pull/6587 fucking broke this
        else:
            self.assertEqual(*self.actual_expected_contents('todo.html', 'todo_1814.html'))

        # 1.8.18 to 1.8.20 has a different order, not sure why
        if parse_version(doxygen_version()) >= parse_version("1.8.18") and parse_version(doxygen_version()) < parse_version("1.9.0"):
            self.assertEqual(*self.actual_expected_contents('old.html', 'old_1818.html'))
        elif parse_version(doxygen_version()) > parse_version("1.8.14"):
            self.assertEqual(*self.actual_expected_contents('old.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('old.html', 'old_1814.html'))

class Internal(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')
        self.assertEqual(*self.actual_expected_contents('index.html'))

class Code(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')

        # Pygments 2.10+ properly highlight Whitespace as such, and not as
        # Text
        if parse_version(pygments.__version__) >= parse_version("2.10"):
            self.assertEqual(*self.actual_expected_contents('index.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-pygments29.html'))

    def test_warnings(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='warnings.xml')

        # Pygments 2.10+ properly highlight Whitespace as such, and not as
        # Text
        if parse_version(pygments.__version__) >= parse_version("2.10"):
            self.assertEqual(*self.actual_expected_contents('warnings.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('warnings.html', 'warnings-pygments29.html'))
        self.assertEqual(cm.output, [
            "WARNING:root:warnings.xml: no filename attribute in <programlisting>, assuming C++",
            "WARNING:root:warnings.xml: inline code has multiple lines, fallback to a code block",
            "WARNING:root:warnings.xml: inline code has multiple lines, fallback to a code block"
        ])

class CodeLanguage(IntegrationTestCase):
    @unittest.skipUnless(parse_version(doxygen_version()) > parse_version("1.8.13"),
                         "https://github.com/doxygen/doxygen/pull/621")
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')

        # Pygments 2.10+ properly highlight Whitespace as such, and not as
        # Text. Pygments 2.14+ further improve on that.
        if parse_version(pygments.__version__) >= parse_version("2.14"):
            self.assertEqual(*self.actual_expected_contents('index.html'))
        elif parse_version(pygments.__version__) >= parse_version("2.10"):
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-pygments213.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-pygments29.html'))

    @unittest.skipUnless(parse_version(doxygen_version()) > parse_version("1.8.13"),
                         "https://github.com/doxygen/doxygen/pull/623")
    def test_ansi(self):
        self.run_doxygen(wildcard='ansi.xml')
        self.assertEqual(*self.actual_expected_contents('ansi.html'))

    @unittest.skipUnless(parse_version(doxygen_version()) > parse_version("1.8.13"),
                         "https://github.com/doxygen/doxygen/pull/621")
    def test_warnings(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='warnings.xml')

        self.assertEqual(*self.actual_expected_contents('warnings.html'))
        self.assertEqual(cm.output, [
            "WARNING:root:warnings.xml: no filename attribute in <programlisting>, assuming C++",
            "WARNING:root:warnings.xml: unrecognized language of .whatthehell in <programlisting>, highlighting disabled",
            "WARNING:root:warnings.xml: @include / @snippet / @skip[line] produced an empty code block, probably a wrong match expression?"
        ])

class Image(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')

        # Versions before 1.9.1(?) don't have the alt attribute preserved for
        # <img>
        if parse_version(doxygen_version()) >= parse_version("1.9.1"):
            self.assertEqual(*self.actual_expected_contents('index.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-1820.html'))

        self.assertTrue(os.path.exists(os.path.join(self.path, 'html', 'tiny.png')))

    def test_warnings(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='warnings.xml')

        self.assertEqual(*self.actual_expected_contents('warnings.html'))
        self.assertEqual(cm.output, [
            "WARNING:root:warnings.xml: image nonexistent.png was not found in XML_OUTPUT"
        ])

    @unittest.skipUnless(parse_version(doxygen_version()) > parse_version("1.8.15"),
                         "fully fixed after 1.8.15")
    def test_imagelink(self):
        self.run_doxygen(wildcard='imagelink.xml')
        self.assertEqual(*self.actual_expected_contents('imagelink.html'))

class Math(IntegrationTestCase):
    @unittest.skipUnless(shutil.which('latex'),
                         "Math rendering requires LaTeX installed")
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')
        self.assertEqual(*self.actual_expected_contents('index.html'))

    @unittest.skipUnless(shutil.which('latex'),
                         "Math rendering requires LaTeX installed")
    def test_latex_error(self):
        with self.assertRaises(subprocess.CalledProcessError) as context:
            self.run_doxygen(wildcard='error.xml')

class MathCodeFallback(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')

        # Doxygen 1.9.8+ (or maybe earlier? 1.9.1 not yet) changes the spacing,
        if parse_version(doxygen_version()) >= parse_version("1.9.8"):
            self.assertEqual(*self.actual_expected_contents('index.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-191.html'))

class MathCached(IntegrationTestCase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Actually generated from $ \frac{\tau}{2} $ tho
        self.tau_half_hash = sha1(r"""$ \pi $""".encode('utf-8')).digest()
        self.tau_half = """<?xml version='1.0' encoding='UTF-8'?>
<!-- This file was generated by dvisvgm 2.6.3 -->
<svg version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' width='5.847936pt' height='15.326665pt' viewBox='1.195514 -8.1387 4.678349 12.261332'>
<defs>
<path id='g1-50' d='M2.247572 -1.625903C2.375093 -1.745455 2.709838 -2.008468 2.83736 -2.12005C3.331507 -2.574346 3.801743 -3.012702 3.801743 -3.737983C3.801743 -4.686426 3.004732 -5.300125 2.008468 -5.300125C1.052055 -5.300125 0.422416 -4.574844 0.422416 -3.865504C0.422416 -3.474969 0.73325 -3.419178 0.844832 -3.419178C1.012204 -3.419178 1.259278 -3.53873 1.259278 -3.841594C1.259278 -4.25604 0.860772 -4.25604 0.765131 -4.25604C0.996264 -4.837858 1.530262 -5.037111 1.920797 -5.037111C2.662017 -5.037111 3.044583 -4.407472 3.044583 -3.737983C3.044583 -2.909091 2.462765 -2.303362 1.522291 -1.338979L0.518057 -0.302864C0.422416 -0.215193 0.422416 -0.199253 0.422416 0H3.57061L3.801743 -1.42665H3.55467C3.53076 -1.267248 3.466999 -0.868742 3.371357 -0.71731C3.323537 -0.653549 2.717808 -0.653549 2.590286 -0.653549H1.171606L2.247572 -1.625903Z'/>
<path id='g0-28' d='M2.502615 -2.909091H3.929265C4.056787 -2.909091 4.144458 -2.909091 4.224159 -2.972852C4.319801 -3.060523 4.343711 -3.164134 4.343711 -3.211955C4.343711 -3.435118 4.144458 -3.435118 4.008966 -3.435118H1.601993C1.43462 -3.435118 1.131756 -3.435118 0.74122 -3.052553C0.454296 -2.765629 0.231133 -2.399004 0.231133 -2.343213C0.231133 -2.271482 0.286924 -2.247572 0.350685 -2.247572C0.430386 -2.247572 0.446326 -2.271482 0.494147 -2.335243C0.884682 -2.909091 1.354919 -2.909091 1.538232 -2.909091H2.223661L1.538232 -0.70137C1.482441 -0.518057 1.378829 -0.191283 1.378829 -0.151432C1.378829 0.03188 1.546202 0.095641 1.641843 0.095641C1.936737 0.095641 1.984558 -0.183313 2.008468 -0.302864L2.502615 -2.909091Z'/>
</defs>
<g id='page1'>
<use x='1.195514' y='-4.707126' xlink:href='#g0-28'/>
<rect x='1.195514' y='-3.227886' height='0.478187' width='4.678349'/>
<use x='1.417597' y='4.122632' xlink:href='#g1-50'/>
</g>
</svg>"""
        # Actually generated from \[ a^3 + b^3 \neq c^3 \] tho
        # Doxygen 1.9.8+ (or maybe earlier? 1.9.1 not yet) changes the spacing,
        # so have to calculate the hash differently
        if parse_version(doxygen_version()) >= parse_version("1.9.8"):
            self.fermat_hash = sha1("""\\[\n    a^2 + b^2 = c^2\n\\]""".encode('utf-8')).digest()
        else:
            self.fermat_hash = sha1(r"""\[ a^2 + b^2 = c^2 \]""".encode('utf-8')).digest()
        self.fermat = """<?xml version='1.0' encoding='UTF-8'?>
<!-- This file was generated by dvisvgm 2.6.3 -->
<svg version='1.1' xmlns='http://www.w3.org/2000/svg' xmlns:xlink='http://www.w3.org/1999/xlink' width='75.028924pt' height='15.496355pt' viewBox='164.01086 -12.397084 60.023139 12.397084'>
<defs>
<path id='g0-54' d='M7.531756 -8.093649C7.627397 -8.261021 7.627397 -8.284932 7.627397 -8.320797C7.627397 -8.404483 7.555666 -8.5599 7.388294 -8.5599C7.244832 -8.5599 7.208966 -8.488169 7.12528 -8.320797L1.75741 2.116065C1.661768 2.283437 1.661768 2.307347 1.661768 2.343213C1.661768 2.438854 1.745455 2.582316 1.900872 2.582316C2.044334 2.582316 2.080199 2.510585 2.163885 2.343213L7.531756 -8.093649Z'/>
<path id='g3-43' d='M4.770112 -2.761644H8.069738C8.237111 -2.761644 8.452304 -2.761644 8.452304 -2.976837C8.452304 -3.203985 8.249066 -3.203985 8.069738 -3.203985H4.770112V-6.503611C4.770112 -6.670984 4.770112 -6.886177 4.554919 -6.886177C4.327771 -6.886177 4.327771 -6.682939 4.327771 -6.503611V-3.203985H1.028144C0.860772 -3.203985 0.645579 -3.203985 0.645579 -2.988792C0.645579 -2.761644 0.848817 -2.761644 1.028144 -2.761644H4.327771V0.537983C4.327771 0.705355 4.327771 0.920548 4.542964 0.920548C4.770112 0.920548 4.770112 0.71731 4.770112 0.537983V-2.761644Z'/>
<path id='g3-61' d='M8.069738 -3.873474C8.237111 -3.873474 8.452304 -3.873474 8.452304 -4.088667C8.452304 -4.315816 8.249066 -4.315816 8.069738 -4.315816H1.028144C0.860772 -4.315816 0.645579 -4.315816 0.645579 -4.100623C0.645579 -3.873474 0.848817 -3.873474 1.028144 -3.873474H8.069738ZM8.069738 -1.649813C8.237111 -1.649813 8.452304 -1.649813 8.452304 -1.865006C8.452304 -2.092154 8.249066 -2.092154 8.069738 -2.092154H1.028144C0.860772 -2.092154 0.645579 -2.092154 0.645579 -1.876961C0.645579 -1.649813 0.848817 -1.649813 1.028144 -1.649813H8.069738Z'/>
<path id='g1-97' d='M3.598506 -1.422665C3.53873 -1.219427 3.53873 -1.195517 3.371357 -0.968369C3.108344 -0.633624 2.582316 -0.119552 2.020423 -0.119552C1.530262 -0.119552 1.255293 -0.561893 1.255293 -1.267248C1.255293 -1.924782 1.625903 -3.263761 1.853051 -3.765878C2.259527 -4.60274 2.82142 -5.033126 3.287671 -5.033126C4.076712 -5.033126 4.23213 -4.052802 4.23213 -3.957161C4.23213 -3.945205 4.196264 -3.789788 4.184309 -3.765878L3.598506 -1.422665ZM4.363636 -4.483188C4.23213 -4.794022 3.90934 -5.272229 3.287671 -5.272229C1.936737 -5.272229 0.478207 -3.526775 0.478207 -1.75741C0.478207 -0.573848 1.171606 0.119552 1.984558 0.119552C2.642092 0.119552 3.203985 -0.394521 3.53873 -0.789041C3.658281 -0.083686 4.220174 0.119552 4.578829 0.119552S5.224408 -0.095641 5.439601 -0.526027C5.630884 -0.932503 5.798257 -1.661768 5.798257 -1.709589C5.798257 -1.769365 5.750436 -1.817186 5.678705 -1.817186C5.571108 -1.817186 5.559153 -1.75741 5.511333 -1.578082C5.332005 -0.872727 5.104857 -0.119552 4.614695 -0.119552C4.267995 -0.119552 4.244085 -0.430386 4.244085 -0.669489C4.244085 -0.944458 4.27995 -1.075965 4.387547 -1.542217C4.471233 -1.841096 4.531009 -2.10411 4.62665 -2.450809C5.068991 -4.244085 5.176588 -4.674471 5.176588 -4.746202C5.176588 -4.913574 5.045081 -5.045081 4.865753 -5.045081C4.483188 -5.045081 4.387547 -4.62665 4.363636 -4.483188Z'/>
<path id='g1-98' d='M2.761644 -7.998007C2.773599 -8.045828 2.797509 -8.117559 2.797509 -8.177335C2.797509 -8.296887 2.677958 -8.296887 2.654047 -8.296887C2.642092 -8.296887 2.211706 -8.261021 1.996513 -8.237111C1.793275 -8.225156 1.613948 -8.201245 1.398755 -8.18929C1.111831 -8.16538 1.028144 -8.153425 1.028144 -7.938232C1.028144 -7.81868 1.147696 -7.81868 1.267248 -7.81868C1.876961 -7.81868 1.876961 -7.711083 1.876961 -7.591532C1.876961 -7.507846 1.78132 -7.161146 1.733499 -6.945953L1.446575 -5.798257C1.327024 -5.32005 0.645579 -2.606227 0.597758 -2.391034C0.537983 -2.092154 0.537983 -1.888917 0.537983 -1.733499C0.537983 -0.514072 1.219427 0.119552 1.996513 0.119552C3.383313 0.119552 4.817933 -1.661768 4.817933 -3.395268C4.817933 -4.495143 4.196264 -5.272229 3.299626 -5.272229C2.677958 -5.272229 2.116065 -4.758157 1.888917 -4.519054L2.761644 -7.998007ZM2.008468 -0.119552C1.625903 -0.119552 1.207472 -0.406476 1.207472 -1.338979C1.207472 -1.733499 1.243337 -1.960648 1.458531 -2.797509C1.494396 -2.952927 1.685679 -3.718057 1.733499 -3.873474C1.75741 -3.969116 2.462765 -5.033126 3.275716 -5.033126C3.801743 -5.033126 4.040847 -4.507098 4.040847 -3.88543C4.040847 -3.311582 3.706102 -1.960648 3.407223 -1.338979C3.108344 -0.6934 2.558406 -0.119552 2.008468 -0.119552Z'/>
<path id='g1-99' d='M4.674471 -4.495143C4.447323 -4.495143 4.339726 -4.495143 4.172354 -4.351681C4.100623 -4.291905 3.969116 -4.112578 3.969116 -3.921295C3.969116 -3.682192 4.148443 -3.53873 4.375592 -3.53873C4.662516 -3.53873 4.985305 -3.777833 4.985305 -4.25604C4.985305 -4.829888 4.435367 -5.272229 3.610461 -5.272229C2.044334 -5.272229 0.478207 -3.56264 0.478207 -1.865006C0.478207 -0.824907 1.123786 0.119552 2.343213 0.119552C3.969116 0.119552 4.99726 -1.147696 4.99726 -1.303113C4.99726 -1.374844 4.925529 -1.43462 4.877709 -1.43462C4.841843 -1.43462 4.829888 -1.422665 4.722291 -1.315068C3.957161 -0.298879 2.82142 -0.119552 2.367123 -0.119552C1.542217 -0.119552 1.279203 -0.836862 1.279203 -1.43462C1.279203 -1.853051 1.482441 -3.012702 1.912827 -3.825654C2.223661 -4.387547 2.86924 -5.033126 3.622416 -5.033126C3.777833 -5.033126 4.435367 -5.009215 4.674471 -4.495143Z'/>
<path id='g2-51' d='M2.016438 -2.662017C2.646077 -2.662017 3.044583 -2.199751 3.044583 -1.362889C3.044583 -0.366625 2.478705 -0.071731 2.056289 -0.071731C1.617933 -0.071731 1.020174 -0.231133 0.74122 -0.653549C1.028144 -0.653549 1.227397 -0.836862 1.227397 -1.099875C1.227397 -1.354919 1.044085 -1.538232 0.789041 -1.538232C0.573848 -1.538232 0.350685 -1.40274 0.350685 -1.083935C0.350685 -0.326775 1.163636 0.167372 2.072229 0.167372C3.132254 0.167372 3.873474 -0.565878 3.873474 -1.362889C3.873474 -2.024408 3.347447 -2.630137 2.534496 -2.805479C3.164134 -3.028643 3.634371 -3.57061 3.634371 -4.208219S2.917061 -5.300125 2.088169 -5.300125C1.235367 -5.300125 0.589788 -4.837858 0.589788 -4.23213C0.589788 -3.937235 0.789041 -3.809714 0.996264 -3.809714C1.243337 -3.809714 1.40274 -3.985056 1.40274 -4.216189C1.40274 -4.511083 1.147696 -4.622665 0.972354 -4.630635C1.307098 -5.068991 1.920797 -5.092902 2.064259 -5.092902C2.271482 -5.092902 2.87721 -5.029141 2.87721 -4.208219C2.87721 -3.650311 2.646077 -3.315567 2.534496 -3.188045C2.295392 -2.940971 2.11208 -2.925031 1.625903 -2.893151C1.474471 -2.885181 1.41071 -2.87721 1.41071 -2.773599C1.41071 -2.662017 1.482441 -2.662017 1.617933 -2.662017H2.016438Z'/>
</defs>
<g id='page1'>
<use x='164.01086' y='-2.324596' xlink:href='#g1-97'/>
<use x='170.155804' y='-7.260782' xlink:href='#g2-51'/>
<use x='177.544782' y='-2.324596' xlink:href='#g3-43'/>
<use x='189.306097' y='-2.324596' xlink:href='#g1-98'/>
<use x='194.283203' y='-7.260782' xlink:href='#g2-51'/>
<use x='202.336347' y='-2.324596' xlink:href='#g0-54'/>
<use x='202.336347' y='-2.324596' xlink:href='#g3-61'/>
<use x='214.761828' y='-2.324596' xlink:href='#g1-99'/>
<use x='219.799816' y='-7.260782' xlink:href='#g2-51'/>
</g>
</svg>"""

    # This is using the cache, so doesn't matter if LaTeX is found or not
    def test(self):
        math_cache = (0, 5, {
            self.tau_half_hash: (5, 0.344841, self.tau_half),
            self.fermat_hash: (5, 0.0, self.fermat),
            b'does not exist': (5, 0.0, 'something')})
        with open(os.path.join(self.path, 'xml/math.cache'), 'wb') as f:
            pickle.dump(math_cache, f)

        self.run_doxygen(wildcard='math.xml')
        # Same as done above, there's different spacing in 1.9.8+
        if parse_version(doxygen_version()) >= parse_version("1.9.8"):
            self.assertEqual(*self.actual_expected_contents('math.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('math.html', 'math-197.html'))

        # Expect that after the operation the global cache age is bumped,
        # unused entries removed and used entries age bumped as well
        with open(os.path.join(self.path, 'xml/math.cache'), 'rb') as f:
            math_cache_actual = pickle.load(f)
        math_cache_expected = (0, 6, {
            self.tau_half_hash: (6, 0.344841, self.tau_half),
            self.fermat_hash: (6, 0.0, self.fermat)})
        self.assertEqual(math_cache_actual, math_cache_expected)

    @unittest.skipUnless(shutil.which('latex'),
                         "Math rendering requires LaTeX installed")
    def test_uncached(self):
        # Write some bullshit there, which gets immediately reset
        with open(os.path.join(self.path, 'xml/math.cache'), 'wb') as f:
            pickle.dump((1337, 0, {"something different"}), f)

        self.run_doxygen(wildcard='math-uncached.xml')

        with open(os.path.join(self.path, 'math.html')) as f:
            expected_contents = f.read().strip()
        # The file is the same expect for titles of the formulas. Replace them
        # and then compare.
        with open(os.path.join(self.path, 'html', 'math-uncached.html')) as f:
            actual_contents = f.read().strip().replace(r'a^3 + b^3 \neq c^3', 'a^2 + b^2 = c^2').replace(r'\frac{\tau}{2}', r'\pi')

        self.assertEqual(actual_contents, expected_contents)

        # Expect that after the operation the global cache is filled
        with open(os.path.join(self.path, 'xml/math.cache'), 'rb') as f:
            math_cache_actual = pickle.load(f)
        math_cache_expected = (0, 0, {
            sha1('$ \frac{\tau}{2} $'.encode('utf-8')).digest():
                (0, 0.344841, self.tau_half),
            sha1(r'\[ a^3 + b^3 \neq c^3 \]'.encode('utf-8')).digest():
                (0, 0.0, self.fermat)})
        self.assertEqual(math_cache_actual, math_cache_expected)

    def test_noop(self):
        if os.path.exists(os.path.join(self.path, 'xml/math.cache')):
            shutil.rmtree(os.path.join(self.path, 'xml/math.cache'))

        # Processing without any math
        self.run_doxygen(wildcard='indexpage.xml')

        # There should be no file generated
        self.assertFalse(os.path.exists(os.path.join(self.path, 'xml/math.cache')))

class Tagfile(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')

        # Pygments 2.10+ properly highlight Whitespace as such, and not as
        # Text
        if parse_version(pygments.__version__) >= parse_version("2.10"):
            self.assertEqual(*self.actual_expected_contents('index.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-pygments29.html'))

class Custom(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')

        # Pygments 2.10+ properly highlight Whitespace as such, and not as
        # Text
        if parse_version(pygments.__version__) >= parse_version("2.10"):
            self.assertEqual(*self.actual_expected_contents('index.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-pygments29.html'))

    @unittest.skipUnless(shutil.which('latex'),
                         "Math rendering requires LaTeX installed")
    def test_math(self):
        self.run_doxygen(wildcard='math.xml')
        self.assertEqual(*self.actual_expected_contents('math.html'))

    def test_dot(self):
        self.run_doxygen(wildcard='dot.xml')

        # The damn thing adopted Chrome versioning apparently. No idea if the
        # output changed in version 7, 8 or 9 already.
        if parse_version(dot_version()) >= parse_version("10.0"):
            file = 'dot.html'
        # Used to be >= 2.44.0, but 2.42.2 appears to have the same output
        elif parse_version(dot_version()) >= parse_version("2.42.2"):
            file = 'dot-2.html'
        else:
            file = 'dot-240.html'

        self.assertEqual(*self.actual_expected_contents('dot.html', file))

class AutobriefCppComments(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='File_8h.xml')
        self.assertEqual(*self.actual_expected_contents('File_8h.html'))

class AutobriefBlockquote(IntegrationTestCase):
    def test(self):
        # ///> in a brief used to cause a multi-line brief in 1.8.18+, which
        # caused the whole brief to be discarded with a warning. That's no
        # longer the case in 1.12, there it's put into the detailed description
        # instead. Not sure if that changed due to
        # https://github.com/doxygen/doxygen/issues/10902 or something else in
        # some earlier version.
        if parse_version(doxygen_version()) >= (1, 12):
            self.run_doxygen(wildcard='File_8h.xml')
            self.assertEqual(*self.actual_expected_contents('File_8h.html'))
        else:
            with self.assertLogs() as cm:
                self.run_doxygen(wildcard='File_8h.xml')

            self.assertEqual(*self.actual_expected_contents('File_8h.html', 'File_8h-111.html'))
            self.assertEqual(cm.output, [
                "WARNING:root:File_8h.xml: ignoring brief description containing multiple paragraphs. Please modify your markup to remove any block elements from the following: <blockquote><p>An enum on the right</p></blockquote>"
            ])

# JAVADOC_AUTOBRIEF should be nuked from orbit. Or implemented from scratch,
# properly.

class AutobriefHr(IntegrationTestCase):
    @unittest.skipUnless(parse_version(doxygen_version()) < parse_version("1.8.15"),
                         "1.8.15 doesn't put <hruler> into <briefdescription> anymore")
    def test_1814(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='namespaceNamespace.xml')

        self.assertEqual(*self.actual_expected_contents('namespaceNamespace.html', 'namespaceNamespace_1814.html'))
        # Twice because it's a namespace docs and once it's parsed in
        # extract_metadata() and once in parse_xml()
        self.assertEqual(cm.output, 2*[
            "WARNING:root:namespaceNamespace.xml: JAVADOC_AUTOBRIEF / QT_AUTOBRIEF produced a brief description with block elements. That's not supported, ignoring the whole contents of <hr/>"
        ])

    @unittest.skipUnless(parse_version(doxygen_version()) >= parse_version("1.8.15"),
                         "1.8.15 doesn't put <hruler> into <briefdescription> anymore")
    def test(self):
        # No warnings should be produced here
        # TODO use self.assertNoLongs() on 3.10+
        self.run_doxygen(wildcard='namespaceNamespace.xml')
        self.assertEqual(*self.actual_expected_contents('namespaceNamespace.html'))

class AutobriefMultiline(IntegrationTestCase):
    def test(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='namespaceNamespace.xml')

        self.assertEqual(*self.actual_expected_contents('namespaceNamespace.html'))
        # Twice because it's a namespace docs and once it's parsed in
        # extract_metadata() and once in parse_xml(). Can't put it into a
        # function doc because the @{ then wouldn't work there as it has no
        # associated @name.
        self.assertEqual(cm.output, 2*[
            "WARNING:root:namespaceNamespace.xml: JAVADOC_AUTOBRIEF / QT_AUTOBRIEF produced a multi-line brief description. That's not supported, using just the first paragraph of <p>First line of a brief output</p><p>Second line of a brief output gets ignored with a warning.</p>",
        ])

class AutobriefHeading(IntegrationTestCase):
    @unittest.skipUnless(parse_version(doxygen_version()) < parse_version("1.8.15"),
                         "1.8.15 doesn't put <heading> into <briefdescription> anymore")
    def test_1814(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='namespaceNamespace.xml')

        self.assertEqual(*self.actual_expected_contents('namespaceNamespace.html', 'namespaceNamespace_1814.html'))
        # Twice because it's a namespace docs and once it's parsed in
        # extract_metadata() and once in parse_xml()
        self.assertEqual(cm.output, 2*[
            "WARNING:root:namespaceNamespace.xml: JAVADOC_AUTOBRIEF / QT_AUTOBRIEF produced a brief description with block elements. That's not supported, ignoring the whole contents of <p>===============</p><h4>The Thing </h4>",
        ])

    @unittest.skipUnless(parse_version(doxygen_version()) >= parse_version("1.8.15"),
                         "1.8.15 doesn't put <heading> into <briefdescription> anymore")
    def test(self):
        # No warnings should be produced here
        # TODO use self.assertNoLongs() on 3.10+
        self.run_doxygen(wildcard='namespaceNamespace.xml')
        self.assertEqual(*self.actual_expected_contents('namespaceNamespace.html'))

class BriefMultilineIngroup(IntegrationTestCase):
    @unittest.skipUnless(parse_version(doxygen_version()) < parse_version("1.8.16"),
        "1.8.16 doesn't merge adjacent paragraphs into brief in presence of an @ingroup anymore")
    def test_1815(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='group__thatgroup.xml')

        self.assertEqual(*self.actual_expected_contents('group__thatgroup.html', 'group__thatgroup_1815.html'))
        self.assertEqual(cm.output, [
            "WARNING:root:group__thatgroup.xml: ignoring brief description containing multiple paragraphs. Please modify your markup to remove any block elements from the following: <p>Function that's in a group</p><p>Lines of detailed description that get merged to the brief for no freaking reason.</p>"
        ])

    @unittest.skipUnless(parse_version(doxygen_version()) >= parse_version("1.8.16"),
        "1.8.16 doesn't merge adjacent paragraphs into brief in presence of an @ingroup anymore")
    def test(self):
        # No warnings should be produced here
        # TODO use self.assertNoLongs() on 3.10+
        self.run_doxygen(wildcard='group__thatgroup.xml')
        self.assertEqual(*self.actual_expected_contents('group__thatgroup.html'))

class SectionUnderscoreOne(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')
        self.assertEqual(*self.actual_expected_contents('index.html'))

class SectionsHeadings(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')
        self.assertEqual(*self.actual_expected_contents('index.html'))

    def test_functions(self):
        self.run_doxygen(wildcard='File_8h.xml')
        self.assertEqual(*self.actual_expected_contents('File_8h.html'))

    def test_warnings(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='*arnings*.xml')

        # https://github.com/doxygen/doxygen/issues/11016, merged into 1.12, is
        # responsible I think. It got better, yes.
        if parse_version(doxygen_version()) >= (1, 11):
            page = 'warnings.html'
            file = 'Warnings_8h.html'
            output = [
                # Once for every extra level
                "WARNING:root:Warnings_8h.xml: more than three levels of sections in member descriptions are not supported, stopping at <h6>",
                "WARNING:root:Warnings_8h.xml: more than three levels of sections in member descriptions are not supported, stopping at <h6>",
                "WARNING:root:Warnings_8h.xml: more than three levels of sections in member descriptions are not supported, stopping at <h6>",
                "WARNING:root:warnings.xml: more than five levels of sections are not supported, stopping at <h6>",
            ]
        else:
            page = 'warnings-110.html'
            file = 'Warnings_8h-110.html'
            output = [
                # Once for the first extra level, then two more for another
                "WARNING:root:Warnings_8h.xml: more than three levels of sections in member descriptions are not supported, stopping at <h6>",
                'WARNING:root:Warnings_8h.xml: more than three levels of Markdown headings in member descriptions are not supported, stopping at <h6>',
                'WARNING:root:Warnings_8h.xml: more than three levels of Markdown headings in member descriptions are not supported, stopping at <h6>',
                "WARNING:root:Warnings_8h.xml: a Markdown heading underline was apparently misparsed by Doxygen, prefix the headings with # instead",
                "WARNING:root:warnings.xml: more than five levels of Markdown headings for top-level docs are not supported, stopping at <h6>",
                "WARNING:root:warnings.xml: a Markdown heading underline was apparently misparsed by Doxygen, prefix the headings with # instead",
            ]

        self.assertEqual(*self.actual_expected_contents('warnings.html', page))
        self.assertEqual(*self.actual_expected_contents('Warnings_8h.html', file))
        self.assertEqual(cm.output, output)

class AnchorInBothGroupAndNamespace(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='*.xml')

        # The change in https://github.com/doxygen/doxygen/issues/8790 is
        # stupid because the XML is no longer self-contained. I refuse to
        # implement parsing of nested XMLs, so the output will lack some
        # members if groups are used.
        if parse_version(doxygen_version()) >= parse_version("1.9.7"):
            self.assertEqual(*self.actual_expected_contents('namespaceFoo.html', 'namespaceFoo-stupid.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('namespaceFoo.html'))

        self.assertEqual(*self.actual_expected_contents('group__fizzbuzz.html'))

class AnchorHtmlNoPrefixBug(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='some-long-page-name.xml')
        self.assertEqual(*self.actual_expected_contents('some-long-page-name.html'))

class UnexpectedSections(IntegrationTestCase):
    def test(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='File_8h.xml')

        self.assertEqual(*self.actual_expected_contents('File_8h.html'))
        self.assertEqual(cm.output, [
            "WARNING:root:File_8h.xml: unexpected @tparam / @param / @return / @retval / @exception found inside a @section, ignoring",
            "WARNING:root:File_8h.xml: unexpected @param / @return / @retval / @exception found in top-level description, ignoring",
            "WARNING:root:File_8h.xml: unexpected @tparam / @retval / @exception found in macro description, ignoring",
            "WARNING:root:File_8h.xml: unexpected @tparam / @param / @return / @retval / @exception found in enum description, ignoring",
            "WARNING:root:File_8h.xml: unexpected @tparam / @param / @return / @retval / @exception found in enum value description, ignoring",
            "WARNING:root:File_8h.xml: unexpected @param / @return / @retval / @exception found in typedef description, ignoring",
            "WARNING:root:File_8h.xml: unexpected @param / @return / @retval / @exception found in variable description, ignoring",
        ])

class Dot(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')

        # The damn thing adopted Chrome versioning apparently. No idea if the
        # output changed in version 7, 8 or 9 already.
        if parse_version(dot_version()) >= parse_version("10.0"):
            file = 'index.html'
        # Used to be >= 2.44.0, but 2.42.2 appears to have the same output
        elif parse_version(dot_version()) >= parse_version("2.42.2"):
            file = 'index-2.html'
        else:
            file = 'index-240.html'

        self.assertEqual(*self.actual_expected_contents('index.html', file))

    @unittest.skipUnless(parse_version(doxygen_version()) >= parse_version("1.8.16"),
        "1.8.16+ drops the whole <dotfile> tag if the file doesn't exist, which is incredibly dumb")
    def test_warnings(self):
        # No warnings should be produced here
        # TODO use self.assertNoLongs() on 3.10+
        self.run_doxygen(wildcard='warnings.xml')
        self.assertEqual(*self.actual_expected_contents('warnings.html'))

    @unittest.skipUnless(parse_version(doxygen_version()) < parse_version("1.8.16"),
        "1.8.16+ drops the whole <dotfile> tag if the file doesn't exist, which is incredibly dumb")
    def test_warnings_1815(self):
        with self.assertLogs() as cm:
            self.run_doxygen(wildcard='warnings.xml')

        self.assertEqual(*self.actual_expected_contents('warnings.html', 'warnings_1815.html'))
        self.assertEqual(cm.output, [
            "WARNING:warnings.xml: file passed to @dotfile was not found, rendering an empty graph"
        ])

class HtmlonlyHtmlinclude(IntegrationTestCase):
    def test_htmlinclude(self):
        self.run_doxygen(wildcard='indexpage.xml')
        self.assertEqual(*self.actual_expected_contents('index.html'))

    @unittest.skipUnless(parse_version(doxygen_version()) >= parse_version("1.8.18"),
        "1.8.17 and older doesn't include @htmlonly in XML output")
    def test_htmlonly(self):
        self.run_doxygen(wildcard='html-only.xml')
        self.assertEqual(*self.actual_expected_contents('html-only.html'))

    def test_warnings(self):
        self.run_doxygen(wildcard='warnings.xml')
        self.assertEqual(*self.actual_expected_contents('warnings.html'))

_css_colors_src = re.compile(r"""<span class="mh">#(?P<hex>[0-9a-f]{6})</span>""")
_css_colors_dst = r"""<span class="mh">#\g<hex><span class="m-code-color" style="background-color: #\g<hex>;"></span></span>"""

def _add_color_swatch(str):
    return _css_colors_src.sub(_css_colors_dst, str)

class CodeFilters(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml', config={
            'M_CODE_FILTERS_PRE': {
                'CSS': lambda str: str.replace(':', ': ').replace('{', ' {'),
            },
            'M_CODE_FILTERS_POST': {
                'CSS': _add_color_swatch,
            }
        })

        # Pygments 2.10+ properly highlight Whitespace as such, and not as
        # Text. Compared to elsewhere, in this case the difference is only with
        # 2.11+.
        if parse_version(pygments.__version__) >= parse_version("2.11"):
            self.assertEqual(*self.actual_expected_contents('index.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-pygments210.html'))

class Blockquote(IntegrationTestCase):
    def test(self):
        self.run_doxygen(wildcard='indexpage.xml')

        # Pygments 2.10+ properly highlight Whitespace as such, and not as
        # Text
        if parse_version(pygments.__version__) >= parse_version("2.10"):
            self.assertEqual(*self.actual_expected_contents('index.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('index.html', 'index-pygments29.html'))

class HtmlEscape(IntegrationTestCase):
    def setUp(self):
        IntegrationTestCase.setUp(self)

        # Doxygen does *almost* a good job of escaping everything, except the
        # bit in <includes>. Patch that up.
        for i in [
            'structClass.xml',
            'structSub_3_01char_00_01T_01_4.xml',
            'structSub_3_01char_00_01T_01_4_1_1Nested.xml',
            # These two are broken only in 1.8.16 and older, the second one
            # isn't actually used for anything but still produces an error log
            # if not patched.
            'Fi_6le_8h.xml',
            'structSub.xml'
        ]:
            with open(os.path.join(self.path, 'xml', i), 'r+') as f:
                contents = f.read()
                f.seek(0)
                f.truncate(0)
                f.write(contents.replace('Fi&le.h', 'Fi&amp;le.h'))

    def test(self):
        self.run_doxygen(wildcard='*.xml')

        # Page title escaping, content escaping
        self.assertEqual(*self.actual_expected_contents('pages.html'))

        # Versions before 1.9.1(?) don't have the alt attribute preserved for
        # <img>
        if parse_version(doxygen_version()) >= parse_version("1.9.1"):
            self.assertEqual(*self.actual_expected_contents('page.html'))
        else:
            self.assertEqual(*self.actual_expected_contents('page.html', 'page-1820.html'))

        # Filename escaping
        self.assertEqual(*self.actual_expected_contents('files.html'))
        self.assertEqual(*self.actual_expected_contents('Fi_6le_8h.html'))

        # Class name escaping; include, symbol and value escaping
        self.assertEqual(*self.actual_expected_contents('annotated.html'))
        self.assertEqual(*self.actual_expected_contents('structClass.html'))
        self.assertEqual(*self.actual_expected_contents('structSub_3_01char_00_01T_01_4.html'))
        self.assertEqual(*self.actual_expected_contents('structSub_3_01char_00_01T_01_4_1_1Nested.html'))

    def test_search(self):
        # Re-run everything with search enabled, the search data shouldn't be
        # escaped. Not done as part of above as it'd unnecessarily inflate the
        # size of compared files with the search icon and popup.
        self.run_doxygen(index_pages=[], wildcard='*.xml', config={
            'SEARCH_DISABLED': False,
            'SEARCH_DOWNLOAD_BINARY': True
        })

        with open(os.path.join(self.path, 'html', searchdata_filename.format(search_filename_prefix='searchdata')), 'rb') as f:
            serialized = f.read()
            search_data_pretty = pretty_print(serialized, entryTypeClass=EntryType)[0]
        # print(search_data_pretty)
        self.assertEqual(search_data_pretty, """
8 symbols
fi&le.h [2]
||     :$
||      :functionshouldhavespecializednameescaped<char&> [0]
||                                                      ($
||                                                       ) [1]
|unctionshouldhavespecializednameescaped<char&> [0]
||                                             ($
||                                              ) [1]
page <&> title <&> should be escaped, in the page list also [3]
class [7]
|    :$
|     :enum [4]
|      suffixshouldbeescaped [5]
|      |                    ($
|      |                     ) [6]
enum [4]
suffixshouldbeescaped [5]
| |                  ($
| |                   ) [6]
| b<char, t> [8]
| |         :$
| |          :nested [9]
nested [9]
0: ::functionShouldHaveSpecializedNameEscaped<char&>() [prefix=2[:14], suffix_length=2, type=FUNC] -> #a3b5d61927252197070e8d998f643a2b2
1:  [prefix=0[:48], type=FUNC] ->
2: Fi&le.h [type=FILE] -> Fi_6le_8h.html
3: Page <&> title <&> should be escaped, in the page list also [type=PAGE] -> page.html
4: ::Enum [prefix=7[:16], type=ENUM] -> #abc566500394204b1aff6106bb4559e18
5: ::suffixShouldBeEscaped(const Type<char>::ShouldBeEscaped&) && [prefix=7[:16], suffix_length=39, type=FUNC] -> #a0dbbef222ebfc3607c4ad7283ec260c3
6:  [prefix=5[:50], suffix_length=37, type=FUNC] ->
7: Class [type=STRUCT] -> structClass.html
8: Sub<char, T> [type=STRUCT] -> structSub_3_01char_00_01T_01_4.html
9: ::Nested [prefix=8[:30], type=STRUCT] -> _1_1Nested.html
(EntryType.PAGE, CssClass.SUCCESS, 'page'),
(EntryType.NAMESPACE, CssClass.PRIMARY, 'namespace'),
(EntryType.GROUP, CssClass.SUCCESS, 'group'),
(EntryType.CLASS, CssClass.PRIMARY, 'class'),
(EntryType.STRUCT, CssClass.PRIMARY, 'struct'),
(EntryType.UNION, CssClass.PRIMARY, 'union'),
(EntryType.TYPEDEF, CssClass.PRIMARY, 'typedef'),
(EntryType.DIR, CssClass.WARNING, 'dir'),
(EntryType.FILE, CssClass.WARNING, 'file'),
(EntryType.FUNC, CssClass.INFO, 'func'),
(EntryType.DEFINE, CssClass.INFO, 'define'),
(EntryType.ENUM, CssClass.PRIMARY, 'enum'),
(EntryType.ENUM_VALUE, CssClass.DEFAULT, 'enum val'),
(EntryType.VAR, CssClass.DEFAULT, 'var')
""".strip())
