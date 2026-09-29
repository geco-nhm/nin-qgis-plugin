"""
Norge i bilder (NiB) access helpers without QGIS dependencies, so the
response classification can be unit-tested with plain Python. The network
request itself lives in project_setup.check_nib_access().
"""

from typing import Optional, Union

# Web page where users generate their NiB token (a public address, not a
# credential), and the plugin guide section about it
NIB_AUTH_PAGE_URL = 'https://services.norgeibilder.no/token'  # nosec B105
NIB_HELP_URL = (
    'https://geco-nhm.github.io/nin-qgis-plugin/'
    'oppsett-og-tilrettelegging.html#nib-token'
)

NIB_HINT = (
    'Kontroller brukernavn og token, og at tokenet ikke er utløpt. '
    f'Nytt token lages på {NIB_AUTH_PAGE_URL}.'
)


def classify_nib_capabilities_response(
    status_code: Optional[int],
    body: Union[bytes, str, None],
    network_error: str = '',
) -> Optional[str]:
    '''
    Returns a Norwegian error message when a WMTS GetCapabilities response
    from Norge i bilder does not look like a successful, authenticated
    answer, or None when it does.

    status_code: HTTP status, or None when no HTTP response was received.
    body: response body.
    network_error: error text when the request itself failed.
    '''

    if status_code is None:
        detail = network_error or 'ukjent nettverksfeil'
        return f'Fikk ikke kontakt med Norge i bilder ({detail}).'

    if status_code in (401, 403):
        return (
            f'Norge i bilder avviste innloggingen (HTTP {status_code}). {NIB_HINT}'
        )

    if status_code >= 400:
        return f'Norge i bilder svarte med feil (HTTP {status_code}).'

    text = body.decode('utf-8', 'replace') if isinstance(body, bytes) else (body or '')
    if 'Capabilities' in text:
        return None

    lowered = text.lower()
    if any(word in lowered for word in ('token', 'unauthorized', 'invalid', 'login')):
        # Esri-style services often answer HTTP 200 with an error document
        return f'Norge i bilder godtok ikke brukernavn/token. {NIB_HINT}'

    return (
        'Norge i bilder returnerte ikke en gyldig WMTS-tjenestebeskrivelse '
        '(uventet svar).'
    )
