"""Tests for the Norge i bilder response classification (no QGIS needed)."""

from nin_qgis_plugin.nib_access import (
    NIB_HELP_URL,
    NIB_AUTH_PAGE_URL,
    classify_nib_capabilities_response,
)

WMTS_OK = b'<?xml version="1.0"?><Capabilities xmlns="http://www.opengis.net/wmts/1.0"></Capabilities>'


def test_valid_capabilities_pass():
    assert classify_nib_capabilities_response(200, WMTS_OK) is None


def test_http_401_and_403_are_reported_as_login_failures():
    for status in (401, 403):
        message = classify_nib_capabilities_response(status, b'')
        assert 'avviste innloggingen' in message
        assert str(status) in message
        assert NIB_AUTH_PAGE_URL in message


def test_other_http_errors_are_reported():
    message = classify_nib_capabilities_response(500, b'Internal error')
    assert 'HTTP 500' in message


def test_no_response_reports_network_error():
    message = classify_nib_capabilities_response(None, None, 'Host not found')
    assert 'Fikk ikke kontakt' in message
    assert 'Host not found' in message


def test_http_200_with_token_error_document_is_a_login_failure():
    esri_error = b'{"error":{"code":498,"message":"Invalid token."}}'
    message = classify_nib_capabilities_response(200, esri_error)
    assert 'godtok ikke brukernavn/token' in message


def test_http_200_without_capabilities_is_reported():
    message = classify_nib_capabilities_response(200, b'<html>Welcome</html>')
    assert 'uventet svar' in message


def test_help_url_points_to_the_guide_section():
    assert NIB_HELP_URL.startswith('https://geco-nhm.github.io/nin-qgis-plugin/')
    assert NIB_HELP_URL.endswith('#nib-token')
