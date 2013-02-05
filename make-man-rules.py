#  -*- Mode: python; coding: utf-8; indent-tabs-mode: nil -*- */
#
#  This file is part of systemd.
#
#  Copyright 2013 Zbigniew Jędrzejewski-Szmek
#
#  systemd is free software; you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as published by
#  the Free Software Foundation; either version 2.1 of the License, or
#  (at your option) any later version.
#
#  systemd is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with systemd; If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function
import xml.etree.ElementTree as tree
import collections
import sys

SECTION = '''\
MANPAGES += \\
	{manpages}
MANPAGES_ALIAS += \\
	{aliases}
{rules}
'''

CONDITIONAL = '''\
if {conditional}
''' \
+ SECTION + \
'''\
endif
'''

HEADER = '''\
# Do not edit. Generated by make-man-rules.py.
# Regenerate with 'make update-man-list'.

'''

CLEANFILES = '''\

CLEANFILES += \\
	{cleanfiles}
'''

def man(page, number):
    return 'man/{}.{}'.format(page, number)

def add_rules(rules, name):
    xml = tree.parse(name)
    # print('parsing {}'.format(name), file=sys.stderr)
    conditional = xml.getroot().get('conditional') or ''
    rulegroup = rules[conditional]
    refmeta = xml.find('./refmeta')
    title = refmeta.find('./refentrytitle').text
    number = refmeta.find('./manvolnum').text
    refnames = xml.findall('./refnamediv/refname')
    target = man(refnames[0].text, number)
    if title != refnames[0].text:
        raise ValueError('refmeta and refnamediv disagree: ' + name)
    for refname in refnames:
        assert all(refname not in group
                   for group in rules.values()), "duplicate page name"
        alias = man(refname.text, number)
        rulegroup[alias] = target
        # print('{} => {} [{}]'.format(alias, target, conditional), file=sys.stderr)

def create_rules(*xml_files):
    " {conditional => {alias-name => source-name}} "
    rules = collections.defaultdict(dict)
    for name in xml_files:
        add_rules(rules, name)
    return rules

def mjoin(files):
    return ' \\\n\t'.join(sorted(files) or '#')

def make_makefile(rules, cleanfiles):
    return HEADER + '\n'.join(
        (CONDITIONAL if conditional else SECTION).format(
            manpages=mjoin(set(rulegroup.values())),
            aliases=mjoin(k for k,v in rulegroup.items() if k != v),
            rules='\n'.join('{}: {}'.format(k,v)
                            for k,v in sorted(rulegroup.items())
                            if k != v),
            conditional=conditional)
        for conditional,rulegroup in sorted(rules.items())) + \
        CLEANFILES.format(cleanfiles=mjoin(cleanfiles))

if __name__ == '__main__':
    sources = set(sys.argv[1:])
    spares = set([source for source in sources
                  if source + '.in' in sources])
    rules = create_rules(*(sources - spares))
    print(make_makefile(rules, spares), end='')
