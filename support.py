from urllib.parse import quote_plus


def _maps_url(query):
    return 'https://www.google.com/maps/search/?api=1&query=' + quote_plus(f'{query} near me')


def _maps(label, query, description):
    return {
        'kind': 'maps',
        'label': label,
        'description': description,
        'maps_query': query,
        'url': _maps_url(query)
    }


def _phone(label, number, description):
    return {
        'kind': 'phone',
        'label': label,
        'description': description,
        'phone': number,
        'url': f'tel:{number}'
    }


def _link(label, url, description):
    return {
        'kind': 'link',
        'label': label,
        'description': description,
        'url': url
    }


EMERGENCY_INDIA = _phone(
    'Call 112 for emergency help',
    '112',
    "India's all-in-one emergency number for police, fire and health services."
)
TELE_MANAS = _phone(
    'Call Tele-MANAS',
    '14416',
    'Free, confidential, 24/7 mental health support in multiple Indian languages.'
)
FIND_A_HELPLINE = _link(
    'Find a helpline outside India',
    'https://findahelpline.com/',
    'Verified crisis and emotional-support lines in more than 175 countries.'
)

NEARBY_EMERGENCY = _maps(
    'Nearby emergency hospital',
    'emergency hospital',
    'Open a map search for the closest emergency department or hospital.'
)
NEARBY_GYNAECOLOGIST = _maps(
    'Nearby gynaecologist',
    'gynaecologist',
    'A doctor for period, bleeding, pain and reproductive health concerns.'
)
NEARBY_GOVT_GYNAECOLOGY = _maps(
    'Government hospital gynaecology',
    'government hospital gynaecology',
    'Low-cost gynaecology care at a government hospital.'
)
NEARBY_GP = _maps(
    'Nearby general doctor',
    'general physician',
    'A GP can assess your symptoms and refer you to the right specialist.'
)
NEARBY_COUNSELLOR = _maps(
    'Nearby counsellor or therapist',
    'counselling psychologist',
    'Talking support for stress, low mood, anxiety or overwhelming feelings.'
)
NEARBY_PSYCHIATRIST = _maps(
    'Nearby psychiatrist',
    'psychiatrist',
    'A doctor who can assess mental health and discuss treatment options.'
)
NEARBY_PHARMACY = _maps(
    'Nearby pharmacy',
    'pharmacy',
    'A pharmacist can advise on minor cold, cough or over-the-counter care.'
)
NEARBY_ADOLESCENT_CLINIC = _maps(
    'Adolescent-friendly health clinic',
    'adolescent health clinic',
    'A clinic experienced with teenagers and confidential health questions.'
)
NEARBY_ADOLESCENT_COUNSELLOR = _maps(
    'Counsellor for teenagers',
    'child and adolescent counsellor',
    'A counsellor who works with teenagers and their families.'
)

LOCATION_NOTE = (
    'Use “Use my location” to improve map results. '
    'Your location stays in your browser and is not sent to recHERsion.'
)


def _unique(options):
    seen = set()
    out = []
    for option in options:
        key = (option.get('kind'), option.get('label'), option.get('url'))
        if key in seen:
            continue
        seen.add(key)
        out.append(option)
    return out


def build_support(theme, res=None):
    res = res or {}
    extracted = ((res.get('extraction') or {}).get('extracted') or {})
    age = extracted.get('age')
    is_minor = isinstance(age, (int, float)) and age < 18

    if theme == 'urgent':
        title = 'Get urgent help now'
        note = (
            'Call 112 now if this is an emergency. In India, 112 connects police, fire and health services. '
            'Outside India, call your local emergency number.'
        )
        options = [EMERGENCY_INDIA, NEARBY_EMERGENCY, NEARBY_GYNAECOLOGIST]
    elif theme == 'distress':
        title = 'Talk to someone now'
        note = (
            'You deserve support right now. If you might act on these thoughts or feel unsafe, call 112 '
            'or go to the nearest emergency department. Outside India, call your local emergency number.'
        )
        options = [TELE_MANAS, NEARBY_COUNSELLOR, NEARBY_PSYCHIATRIST, FIND_A_HELPLINE]
    elif theme == 'discuss':
        title = 'Find a doctor nearby'
        note = 'A doctor can assess what you shared and decide whether tests or a referral are needed.'
        options = [NEARBY_GYNAECOLOGIST, NEARBY_GP, NEARBY_GOVT_GYNAECOLOGY]
    elif theme == 'low':
        title = 'Find someone to talk to'
        note = 'You do not have to manage this alone. Counselling or medical support can help.'
        options = [TELE_MANAS, NEARBY_COUNSELLOR, NEARBY_PSYCHIATRIST, FIND_A_HELPLINE]
    elif theme == 'mild':
        title = 'Find nearby care'
        note = 'For mild symptoms, a GP or pharmacist can advise on next steps.'
        options = [NEARBY_GP, NEARBY_PHARMACY]
    else:
        title = 'Find nearby care'
        note = 'Choose the kind of support that fits what you need right now.'
        options = [NEARBY_GP, NEARBY_GYNAECOLOGIST, NEARBY_COUNSELLOR]

    if is_minor:
        options = options + [NEARBY_ADOLESCENT_CLINIC, NEARBY_ADOLESCENT_COUNSELLOR]

    options = _unique(options)
    return {
        'title': title,
        'note': note,
        'location_note': LOCATION_NOTE,
        'options': options
    }
