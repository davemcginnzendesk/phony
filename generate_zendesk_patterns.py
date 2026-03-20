#!/usr/bin/env python3
"""
Extract toll-free and premium patterns for Zendesk-supported countries.
"""

import xml.etree.ElementTree as ET
import re

# Zendesk-supported countries with toll_free enabled (from zendesk_voice_core)
ZENDESK_TOLL_FREE_COUNTRIES = {
    '1': 'US/CA',  # US & Canada
    '54': 'AR',  # Argentina
    '61': 'AU',  # Australia
    '43': 'AT',  # Austria
    '32': 'BE',  # Belgium
    '267': 'BW',  # Botswana
    '55': 'BR',  # Brazil
    '359': 'BG',  # Bulgaria
    '57': 'CO',  # Colombia
    '506': 'CR',  # Costa Rica
    '385': 'HR',  # Croatia
    '420': 'CZ',  # Czech Republic
    '45': 'DK',  # Denmark
    '1829': 'DO',  # Dominican Republic
    '20': 'EG',  # Egypt
    '358': 'FI',  # Finland
    '30': 'GR',  # Greece
    '852': 'HK',  # Hong Kong
    '62': 'ID',  # Indonesia
    '353': 'IE',  # Ireland
    '972': 'IL',  # Israel
    '39': 'IT',  # Italy
    '81': 'JP',  # Japan
    '94': 'LK',  # Sri Lanka
    '352': 'LU',  # Luxembourg
    '60': 'MY',  # Malaysia
    '52': 'MX',  # Mexico
    '64': 'NZ',  # New Zealand
    '47': 'NO',  # Norway
    '51': 'PE',  # Peru
    '63': 'PH',  # Philippines
    '48': 'PL',  # Poland
    '974': 'QA',  # Qatar
    '40': 'RO',  # Romania
    '421': 'SK',  # Slovakia
    '82': 'KR',  # South Korea
    '34': 'ES',  # Spain
    '886': 'TW',  # Taiwan
    '66': 'TH',  # Thailand
    '256': 'UG',  # Uganda
    '598': 'UY',  # Uruguay
    '971': 'AE',  # UAE
    '58': 'VE',  # Venezuela
    '84': 'VN',  # Vietnam
}

def clean_pattern(pattern):
    """Remove whitespace and newlines from XML patterns."""
    if pattern is None:
        return None
    return re.sub(r'\s+', '', pattern.strip())

def parse_libphonenumber(xml_path):
    """Parse libphonenumber and extract patterns for Zendesk countries."""
    tree = ET.parse(xml_path)
    root = tree.getroot()

    results = {}

    for territory in root.findall('.//territory'):
        country_code = territory.get('countryCode')
        iso_code = territory.get('id')

        if country_code not in ZENDESK_TOLL_FREE_COUNTRIES:
            continue

        # Extract patterns
        toll_free_elem = territory.find('.//tollFree/nationalNumberPattern')
        premium_elem = territory.find('.//premiumRate/nationalNumberPattern')

        toll_free = clean_pattern(toll_free_elem.text) if toll_free_elem is not None else None
        premium = clean_pattern(premium_elem.text) if premium_elem is not None else None

        if toll_free or premium:
            if country_code not in results:
                results[country_code] = []

            results[country_code].append({
                'iso': iso_code,
                'toll_free': toll_free,
                'premium': premium
            })

    return results

def load_phony_definitions(countries_file):
    """Load existing phony definitions to see what's already there."""
    with open(countries_file, 'r') as f:
        content = f.read()

    definitions = {}
    current_code = None
    current_content = []

    for line in content.split('\n'):
        # Find country definition start
        match = re.match(r"\s*country\s+'(\d+)'", line)
        if match:
            # Save previous country
            if current_code:
                definitions[current_code] = '\n'.join(current_content)

            current_code = match.group(1)
            current_content = [line]
        elif current_code:
            current_content.append(line)
            # Check for end of country definition
            if re.match(r'\s*country\s+', line) or line.strip().startswith('#'):
                break

    return definitions

def main():
    patterns = parse_libphonenumber('resources/PhoneNumberMetadata.xml')

    print("="*80)
    print("ZENDESK TOLL-FREE COUNTRIES - LIBPHONENUMBER PATTERNS")
    print("="*80)
    print()

    for code in sorted(patterns.keys(), key=lambda x: int(x) if x.isdigit() else 9999):
        for entry in patterns[code]:
            zendesk_name = ZENDESK_TOLL_FREE_COUNTRIES.get(code, '???')
            print(f"+{code:5s} ({entry['iso']:2s}) - {zendesk_name}")

            if entry['toll_free']:
                print(f"  Toll-free:")
                print(f"    Pattern: {entry['toll_free']}")
                print()

            if entry['premium']:
                print(f"  Premium:")
                print(f"    Pattern: {entry['premium']}")
                print()

            print()

if __name__ == '__main__':
    main()
