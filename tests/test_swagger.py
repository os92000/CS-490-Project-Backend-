import re


PATH_PARAM_RE = re.compile(r"<(?:(?P<converter>[^:<>]+):)?(?P<name>[^<>]+)>")


def to_swagger_path(flask_rule):
    return PATH_PARAM_RE.sub(lambda match: "{" + match.group("name") + "}", flask_rule)


def test_swagger_ui_is_available(client):
    response = client.get("/apidocs/")

    assert response.status_code == 200


def test_swagger_spec_includes_core_paths(client):
    response = client.get("/apispec_1.json")

    assert response.status_code == 200
    spec = response.get_json()

    assert spec["swagger"] == "2.0"
    assert "openapi" not in spec
    assert spec["info"]["title"] == "Fitness App API"
    assert "/api/auth/login" in spec["paths"]
    assert "/api/auth/signup" in spec["paths"]
    assert "BearerAuth" in spec["securityDefinitions"]


def test_swagger_spec_includes_all_registered_api_routes(app, client):
    response = client.get("/apispec_1.json")

    assert response.status_code == 200
    spec = response.get_json()

    for rule in app.url_map.iter_rules():
        if rule.endpoint.startswith("static") or rule.endpoint.startswith("flasgger."):
            continue
        if not (rule.rule == "/" or rule.rule == "/health" or rule.rule.startswith("/api/")):
            continue

        swagger_path = to_swagger_path(rule.rule)
        assert swagger_path in spec["paths"], rule.rule

        for method in rule.methods - {"HEAD", "OPTIONS"}:
            assert method.lower() in spec["paths"][swagger_path], f"{method} {rule.rule}"
