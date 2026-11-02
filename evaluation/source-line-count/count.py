#!/usr/bin/env python3
"""Count physical code lines in the pinned XLA example, excluding comments."""
from pathlib import Path
import bisect
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
source = (HERE / 'algebraic_simplifier.cc').read_text()
lines = source.splitlines(keepends=True)
fragment = ''.join(lines[3828:4180])
assert 'AlgebraicSimplifierVisitor::AssociativeReorderNestedDot(' in fragment
tokens = re.compile(r'(?P<comment>//[^\n]*|/\*[\s\S]*?\*/)|(?P<string>"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\')|(?P<other>[^\s])')
newlines = [m.start() for m in re.finditer('\n', fragment)]
code_lines = set()
for token in tokens.finditer(fragment):
    if token.lastgroup != 'comment':
        code_lines.update(range(bisect.bisect_right(newlines, token.start()), bisect.bisect_right(newlines, token.end()-1)+1))
report = dict(function='AssociativeReorderNestedDot', start_line=3829, end_line=4180,
              nonblank_including_comments=sum(bool(line.strip()) for line in fragment.splitlines()),
              nonblank_excluding_comments=len(code_lines),
              sha256=hashlib.sha256((HERE/'algebraic_simplifier.cc').read_bytes()).hexdigest(),
              url='https://raw.githubusercontent.com/openxla/xla/9cb4e2005f963acc873dc95facd3b7d134dbf108/xla/hlo/transforms/simplifiers/algebraic_simplifier.cc',
              procedure='Count physical lines containing at least one non-comment C++ token; includes signature and braces.')
assert report['nonblank_including_comments'] == 315
assert report['nonblank_excluding_comments'] == 269
(HERE/'count.json').write_text(json.dumps(report,indent=2)+'\n')
print('269 nonblank code lines excluding comments; 315 if comments are included.')
