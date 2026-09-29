"""Tests for reading WMTS layer parameters from a capabilities document (no QGIS needed)."""

import pytest

from nin_qgis_plugin.wmts_capabilities import (
    WmtsCapabilitiesError,
    select_wmts_layer_parameters,
)

# Esri-style capabilities as served for Norge i bilder: RESTful ResourceURL,
# 'default028mm' tile matrix set, jpgpng first in the format list.
ESRI_CAPS = b'''<?xml version="1.0" encoding="UTF-8"?>
<Capabilities xmlns="http://www.opengis.net/wmts/1.0" xmlns:ows="http://www.opengis.net/ows/1.1"
  xmlns:xlink="http://www.w3.org/1999/xlink" version="1.0.0">
  <Contents>
    <Layer>
      <ows:Title>Nibcache_UTM32_EUREF89_v2</ows:Title>
      <ows:Identifier>Nibcache_UTM32_EUREF89_v2</ows:Identifier>
      <Style isDefault="true"><ows:Identifier>default</ows:Identifier></Style>
      <Format>image/jpgpng</Format>
      <Format>image/png</Format>
      <TileMatrixSetLink><TileMatrixSet>default028mm</TileMatrixSet></TileMatrixSetLink>
      <TileMatrixSetLink><TileMatrixSet>GoogleMapsCompatible</TileMatrixSet></TileMatrixSetLink>
      <ResourceURL format="image/jpgpng" resourceType="tile"
        template="https://tilecache.norgeibilder.no/wmts/utm32_euref89/tile/1.0.0/Nibcache_UTM32_EUREF89_v2/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.jpgpng"/>
    </Layer>
    <TileMatrixSet>
      <ows:Identifier>default028mm</ows:Identifier>
      <ows:SupportedCRS>urn:ogc:def:crs:EPSG::25832</ows:SupportedCRS>
    </TileMatrixSet>
    <TileMatrixSet>
      <ows:Identifier>GoogleMapsCompatible</ows:Identifier>
      <ows:SupportedCRS>urn:ogc:def:crs:EPSG:6.18:3:3857</ows:SupportedCRS>
    </TileMatrixSet>
  </Contents>
</Capabilities>'''


def test_picks_tile_matrix_set_matching_the_crs_and_preferred_format():
    params = select_wmts_layer_parameters(ESRI_CAPS, 'Nibcache_UTM32_EUREF89_v2', 'EPSG:25832')
    assert params == {
        'layer': 'Nibcache_UTM32_EUREF89_v2',
        'style': 'default',
        'format': 'image/png',
        'tile_matrix_set': 'default028mm',
        'tile_matrix_set_crs': 'urn:ogc:def:crs:EPSG::25832',
    }


def test_web_mercator_crs_selects_the_other_set():
    params = select_wmts_layer_parameters(ESRI_CAPS, 'Nibcache_UTM32_EUREF89_v2', 'EPSG:3857')
    assert params['tile_matrix_set'] == 'GoogleMapsCompatible'


def test_unsupported_crs_is_reported_with_available_sets():
    with pytest.raises(WmtsCapabilitiesError) as excinfo:
        select_wmts_layer_parameters(ESRI_CAPS, 'Nibcache_UTM32_EUREF89_v2', 'EPSG:25833')
    assert 'default028mm' in str(excinfo.value)
    assert 'EPSG:25833' in str(excinfo.value)


def test_single_layer_is_used_when_identifier_differs():
    params = select_wmts_layer_parameters(ESRI_CAPS, 'Nibcache_UTM32_EUREF89', 'EPSG:25832')
    assert params['layer'] == 'Nibcache_UTM32_EUREF89_v2'


def test_unknown_layer_among_several_is_reported():
    two_layers = ESRI_CAPS.replace(
        b'<TileMatrixSet>\n      <ows:Identifier>default028mm',
        b'<Layer><ows:Identifier>other</ows:Identifier></Layer>\n    <TileMatrixSet>\n      <ows:Identifier>default028mm',
    )
    with pytest.raises(WmtsCapabilitiesError) as excinfo:
        select_wmts_layer_parameters(two_layers, 'nope', 'EPSG:25832')
    assert 'Nibcache_UTM32_EUREF89_v2' in str(excinfo.value)


def test_unparseable_document_is_reported():
    with pytest.raises(WmtsCapabilitiesError):
        select_wmts_layer_parameters(b'<html>not xml capabilities', 'x', 'EPSG:25832')


def test_documents_with_entity_declarations_are_refused():
    hostile = b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY a "aaaa">]>' + ESRI_CAPS.split(b'?>', 1)[1]
    with pytest.raises(WmtsCapabilitiesError):
        select_wmts_layer_parameters(hostile, 'Nibcache_UTM32_EUREF89_v2', 'EPSG:25832')
