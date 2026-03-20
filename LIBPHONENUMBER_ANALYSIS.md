# LibPhoneNumber Analysis for Phony

## Summary

Comparison between [Google's libphonenumber](https://github.com/google/libphonenumber) metadata and Phony's current country definitions.

**Analysis Date:** 2026-03-20

## Key Findings

### Country Coverage

- **Phony has**: 301 country code definitions (including many `todo` placeholders)
- **LibPhoneNumber has**: 215 fully-defined territories with validation patterns
- **Truly missing in Phony**: 0 countries
  - Cambodia (+855) exists in special file `lib/phony/countries/cambodia.rb`
  - +888 is marked as `reserved` (International Disaster Relief)

### Countries with Toll-Free and Premium Rate Data

**192 countries in libphonenumber have toll-free or premium rate patterns**

Phony already has basic definitions for almost all of these, but many lack comprehensive toll-free and premium rate patterns.

## Specific Pattern Gaps

### New Zealand (+64)
**Current in Phony:**
- Toll-free: 800 (6-7 digits), 508 (6-7 digits)
- Premium: 900 (5-6 digits)

**LibPhoneNumber has:**
```
Toll-free: 508\d{6,7}|80\d{6,8}
Premium: (1[13-57-9]\d{5}|50(0[08]|30|66|77|88))\d{3}|90\d{6,8}
```

**Gap:** Missing 80\d{7,8} (8-9 digit toll-free) and more complex premium patterns

### Brazil (+55)
**Current in Phony:**
- Special numbers: 0800 (3+4 split)
- Service numbers: 3003, 4003, 4004, 4020

**LibPhoneNumber has:**
```
Toll-free: 800\d{6,7}
Premium: [59]00\d{6,7}
```

**Gap:** Premium rate patterns (500, 900) not explicitly defined

### South Africa (+27)
**Current in Phony:**
- Basic fixed(2) >> split(3, 4)

**LibPhoneNumber has:**
```
Toll-free: 80\d{7}
Premium: (86[2-9]|9[0-2]\d)\d{6}
```

**Gap:** No toll-free or premium patterns defined

### International Toll-Free (+800)
**LibPhoneNumber has:**
```
Pattern: (00|[1-9]\d)\d{6}
```

Phony has basic support but may need verification.

## Recommendations

### 1. Priority: Add Missing Toll-Free/Premium Patterns

Focus on countries from the `zendesk_voice_core` COUNTRIES list (70+ supported countries):

**High Priority:**
- New Zealand (+64) - known issues with toll-free validation
- Brazil (+55) - premium rate patterns missing
- South Africa (+27) - toll-free and premium missing
- Countries with active support tickets

### 2. Use LibPhoneNumber Patterns as Reference

The XML file at `resources/PhoneNumberMetadata.xml` contains authoritative regex patterns for:
- `<tollFree>` numbers
- `<premiumRate>` numbers
- `<sharedCost>` numbers
- `<voip>` numbers
- `<personalNumber>` numbers

### 3. Implementation Approach

**Option A:** Add patterns directly to `lib/phony/countries.rb`
```ruby
country '64',
        trunk('0') |
        match(/^(80)\d{7,8}$/) >> split(2, 3, 3) | # Toll-free 80
        match(/^(800)\d{6,7}$/) >> split(3, 4) |   # Toll-free 800
        match(/^(508)\d{6,7}$/) >> split(3, 4) |   # Toll-free 508
        match(/^(90)\d{6,8}$/) >> split(2, 3, 3) | # Premium 90
        # ... other patterns
```

**Option B:** Add to `zendesk_voice_core` PhonyRules (recommended for Zendesk)
```ruby
# lib/zendesk_voice_core/phony_rules.rb
Phony.define do
  country '64',
    trunk('0') |
    match(/^(80)\d{7,8}$/) >> split(2, 3, 3) # Additional toll-free
end
```

## Completed Work

### Phase 1: New Zealand (+64) and Brazil (+55)

**New Zealand - Added Missing Patterns:**
- ✅ Toll-free 080: `80\d{6,8}` (6-8 digits after 80)
  - `match(/^(80)\d{6}$/) >> split(3, 3)`
  - `match(/^(80)\d{7}$/) >> split(3, 4)`
  - `match(/^(80)\d{8}$/) >> split(4, 4)`
- ✅ Premium 090: `90\d{6,8}` (6-8 digits after 90)
  - `match(/^(90)\d{6}$/) >> split(3, 3)`
  - `match(/^(90)\d{7}$/) >> split(3, 4)`
  - `match(/^(90)\d{8}$/) >> split(4, 4)`
- ✅ Extended 0900 premium to support 7-8 digits

**Brazil - Added Missing Patterns:**
- ✅ Premium 500: `500\d{6,7}` (6-7 digits after 500)
  - `match(/^([59]00)\d{6}$/) >> split(3, 3)`
  - `match(/^([59]00)\d{7}$/) >> split(3, 4)`
- ✅ Premium 900: `900\d{6,7}` (6-7 digits after 900)

**Tests:**
- ✅ New Zealand: 15 examples, 0 failures
- ✅ Brazil: 88 examples, 0 failures

## Next Steps

1. ✅ Downloaded LibPhoneNumber metadata to `resources/PhoneNumberMetadata.xml`
2. ✅ Analyzed country coverage - no missing countries
3. ✅ Extract toll-free/premium patterns for Zendesk-supported countries
4. ✅ Convert libphonenumber regex to Phony DSL (NZ, BR)
5. ✅ Test patterns against known problematic numbers (NZ, BR)
6. 🔲 Add patterns for remaining Zendesk-supported countries (see zendesk_patterns.txt)
7. 🔲 Submit PR to phony upstream (or use in PhonyRules internally)

## Resources

- LibPhoneNumber XML: `resources/PhoneNumberMetadata.xml`
- LibPhoneNumber GitHub: https://github.com/google/libphonenumber
- Phony countries: `lib/phony/countries.rb`
- Phony special files: `lib/phony/countries/`
- Zendesk supported countries: See `zendesk_voice_core/app/models/voice/core/number_support.rb`
