"""Serper Google Maps (fork de El Faro): locales con web, no artículos."""
import json

import httpx
import pytest

from harvey.collectors import discover as D


def _client(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def _page(n, start=1):
    return {"places": [
        {"position": start + i, "title": f"Local {start + i}",
         "website": f"https://local{start + i}.example/",
         "address": "Calle Mayor 1, Alicante", "category": "Hamburguesa",
         "rating": 4.5, "ratingCount": 100, "cid": str(1000 + start + i)}
        for i in range(n)
    ]}


@pytest.mark.asyncio
async def test_serper_maps_reads_places():
    seen = []
    payload = {"places": [
        {"position": 1, "title": "Burger Ejemplo", "website": "http://www.burgerejemplo.example/",
         "address": "Calle Mayor 1, Alicante", "category": "Hamburguesa",
         "rating": 4.7, "ratingCount": 812, "phoneNumber": "965 00 00 00", "cid": "123"},
        {"position": 2, "title": "Solo Instagram", "website": "https://instagram.com/soloinstagram",
         "category": "Americana", "cid": "456"},
        {"position": 3, "title": "Sin Web", "category": "Hamburguesa"},
    ]}

    def handler(request):
        seen.append((str(request.url), request.headers.get("x-api-key"),
                     json.loads(request.content)))
        return httpx.Response(200, json=payload)

    async with _client(handler) as client:
        out = await D.SerperMaps().fetch(client, {"serper_api_key": "k"}, D.DiscoveryQuery(
            term="Hamburgueserías", location="Alicante, España"))

    url, key, body = seen[0]
    assert url == "https://google.serper.dev/places"
    assert key == "k"
    assert body == {"q": "Hamburgueserías Alicante, España", "page": 1}
    assert len(seen) == 1, "una página corta es la última"

    burger, insta, sin_web = out
    assert burger.domain == "burgerejemplo.example" and burger.has_website is True
    assert burger.rating == 4.7 and burger.review_count == 812
    assert burger.phone == "965 00 00 00"
    assert burger.external_id == "gmaps_cid:123"
    # La posición en Maps no es un rango orgánico.
    assert burger.rank is None and burger.maps_rank == 1
    # Una red social no es una web: el local se queda, sin web.
    assert insta.domain == "" and insta.has_website is False
    assert sin_web.domain == "" and sin_web.external_id == ""


@pytest.mark.asyncio
async def test_serper_maps_pages_up_to_the_limit():
    pages = []

    def handler(request):
        page = json.loads(request.content)["page"]
        pages.append(page)
        return httpx.Response(200, json=_page(10, start=(page - 1) * 10 + 1))

    async with _client(handler) as client:
        out = await D.SerperMaps().fetch(client, {"serper_api_key": "k"}, D.DiscoveryQuery(
            term="Cafeterías", location="Alicante, España", limit=25))

    assert pages == [1, 2, 3]
    assert len(out) == 25


def test_serper_maps_is_registered_and_estimated():
    assert "serper_maps" in D.PROVIDERS
    q = [D.DiscoveryQuery(term="Cafeterías", location="Alicante, España", limit=30)]
    assert D.estimate_cost("serper_maps", q) == pytest.approx(0.003)
