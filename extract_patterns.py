#!/usr/bin/env python3
"""
Extract toll-free and premium rate patterns from libphonenumber XML
and generate Phony DSL additions.
"""

import xml.etree.ElementTree as ET
import re
from collections import defaultdict

def clean_pattern(pattern):
    """Remove whitespace and newlines from XML patterns."""
    if pattern is None:
        return None
    return re.sub(r'\s+', '', pattern.strip())

def parse_libphonenumber_xml(xml_path):
    """Parse libphonenumber metadata and extract toll-free/premium patterns."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    patterns = {}

    for territory in root.findall('.//territory'):
        country_code = territory.get('countryCode')
        iso_code = territory.get('id')

        if not country_code or not iso_code:
            continue

        entry = {
            'code': country_code,
            'iso': iso_code,
            'toll_free': None,
            'premium': None,
            'shared_cost': None,
            'voip': None,
            'personal': None
        }

        # Extract toll-free pattern
        toll_free = territory.find('.//tollFree/nationalNumberPattern')
        if toll_free is not None:
            entry['toll_free'] = clean_pattern(toll_free.text)

        # Extract premium rate pattern
        premium = territory.find('.//premiumRate/nationalNumberPattern')
        if premium is not None:
            entry['premium'] = clean_pattern(premium.text)

        # Extract shared cost pattern
        shared = territory.find('.//sharedCost/nationalNumberPattern')
        if shared is not None:
            entry['shared_cost'] = clean_pattern(shared.text)

        # Extract voip pattern
        voip = territory.find('.//voip/nationalNumberPattern')
        if voip is not None:
            entry['voip'] = clean_pattern(voip.text)

        # Extract personal number pattern
        personal = territory.find('.//personalNumber/nationalNumberPattern')
        if personal is not None:
            entry['personal'] = clean_pattern(personal.text)

        if country_code not in patterns:
            patterns[country_code] = []
        patterns[country_code].append(entry)

    return patterns

def load_phony_countries(countries_file):
    """Parse phony countries.rb to see what's already defined."""
    with open(countries_file, 'r') as f:
        content = f.read()

    phony_countries = {}

    # Find all country definitions
    for match in re.finditer(r"country\s+'(\d+)'", content):
        code = match.group(1)
        phony_countries[code] = True

    return phony_countries

def convert_to_phony_pattern(regex_pattern, number_type):
    """
    Convert libphonenumber regex to Phony DSL suggestions.
    This is a simple heuristic - complex patterns need manual review.
    """
    if not regex_pattern:
        return []

    suggestions = []

    # Simple patterns like "800\d{6,7}"
    simple_match = re.match(r'^(\d+)\\d\{(\d+),?(\d+)?\}$', regex_pattern)
    if simple_match:
        prefix = simple_match.group(1)
        min_len = simple_match.group(2)
        max_len = simple_match.group(3) if simple_match.group(3) else min_len
        suggestions.append({
            'type': 'simple',
            'prefix': prefix,
            'min_length': min_len,
            'max_length': max_len,
            'pattern': regex_pattern
        })
        return suggestions

    # Patterns with alternatives like "508\d{6,7}|80\d{6,8}"
    if '|' in regex_pattern:
        parts = regex_pattern.split('|')
        for part in parts:
            sub_suggestions = convert_to_phony_pattern(part.strip(), number_type)
            suggestions.extend(sub_suggestions)
        return suggestions

    # Complex pattern - return as-is for manual conversion
    suggestions.append({
        'type': 'complex',
        'pattern': regex_pattern,
        'needs_manual_review': True
    })

    return suggestions

def main():
    patterns = parse_libphonenumber_xml('resources/PhoneNumberMetadata.xml')
    phony_countries = load_phony_countries('lib/phony/countries.rb')

    print("="*80)
    print("TOLL-FREE AND PREMIUM RATE PATTERNS FROM LIBPHONENUMBER")
    print("="*80)
    print()

    # Group by country code
    for code in sorted(patterns.keys(), key=lambda x: int(x)):
        entries = patterns[code]

        # Check if any entry has toll-free or premium
        has_special = any(e['toll_free'] or e['premium'] for e in entries)
        if not has_special:
            continue

        in_phony = "✓" if code in phony_countries else "✗"

        for entry in entries:
            if entry['toll_free'] or entry['premium']:
                print(f"{in_phony} +{code:4s} ({entry['iso']:2s})")

                if entry['toll_free']:
                    print(f"  Toll-free: {entry['toll_free']}")
                    suggestions = convert_to_phony_pattern(entry['toll_free'], 'toll_free')
                    for s in suggestions:
                        if s['type'] == 'simple':
                            print(f"    Phony: match(/^({s['prefix']})\\d{{{s['min_length']},{s['max_length']}}}$/) >> split(...)")
                        elif s['type'] == 'complex':
                            print(f"    Phony: match(/^{s['pattern']}$/) >> split(...) # NEEDS MANUAL REVIEW")

                if entry['premium']:
                    print(f"  Premium: {entry['premium']}")
                    suggestions = convert_to_phony_pattern(entry['premium'], 'premium')
                    for s in suggestions:
                        if s['type'] == 'simple':
                            print(f"    Phony: match(/^({s['prefix']})\\d{{{s['min_length']},{s['max_length']}}}$/) >> split(...)")
                        elif s['type'] == 'complex':
                            print(f"    Phony: match(/^{s['pattern']}$/) >> split(...) # NEEDS MANUAL REVIEW")

                print()

    # Summary statistics
    total_with_tollfree = sum(1 for code, entries in patterns.items() for e in entries if e['toll_free'])
    total_with_premium = sum(1 for code, entries in patterns.items() for e in entries if e['premium'])

    print("="*80)
    print(f"SUMMARY: {total_with_tollfree} countries with toll-free, {total_with_premium} with premium")
    print("="*80)

if __name__ == '__main__':
    main()
