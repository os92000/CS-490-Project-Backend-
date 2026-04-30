import json
import re

from flasgger import Swagger


PATH_PARAM_RE = re.compile(r"<(?:(?P<converter>[^:<>]+):)?(?P<name>[^<>]+)>")
PUBLIC_PATH_PREFIXES = (
    "/api/auth/login",
    "/api/auth/signup",
    "/api/coaches/public",
    "/api/workouts/public",
)
PUBLIC_PATHS = {"/", "/health", "/api/coaches/specializations"}


def init_swagger(app):
    """Configure Swagger UI and OpenAPI generation for the Flask app."""
    template = {
        "swagger": "2.0",
        "info": {
            "title": "Fitness App API",
            "description": "API documentation for the Fitness App backend.",
            "version": "1.0.0",
        },
        "basePath": "/",
        "schemes": ["http"],
        "securityDefinitions": {
            "BearerAuth": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT authorization header using the Bearer scheme. Example: Bearer {token}",
            },
        },
        "definitions": {
            "ApiSuccess": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "data": {"type": "object"},
                    "message": {"type": "string"},
                    "error": {"type": "object"},
                },
            },
            "ApiError": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": False},
                    "data": {"type": "object", "example": None},
                    "message": {"type": "string"},
                    "error": {"type": "object"},
                },
            },
            "AuthTokens": {
                "type": "object",
                "properties": {
                    "access_token": {"type": "string"},
                    "refresh_token": {"type": "string"},
                },
            },
            "User": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "email": {"type": "string", "format": "email"},
                    "role": {"type": "string"},
                    "status": {"type": "string"},
                },
            },
        },
    }

    config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/",
    }

    swagger = Swagger(app, template=template, config=config)

    @app.after_request
    def complete_swagger_spec(response):
        if response.status_code != 200 or response.mimetype != "application/json":
            return response

        if getattr(response, "_swagger_completed", False):
            return response

        try:
            spec = response.get_json()
        except Exception:
            return response

        if not isinstance(spec, dict) or spec.get("swagger") != "2.0":
            return response

        completed_spec = _add_registered_routes_to_spec(app, spec)
        response.set_data(json.dumps(completed_spec))
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Length"] = str(len(response.get_data()))
        response._swagger_completed = True
        return response

    return swagger


def _add_registered_routes_to_spec(app, spec):
    paths = spec.setdefault("paths", {})

    for rule in app.url_map.iter_rules():
        if not _should_document_rule(rule):
            continue

        swagger_path = _to_swagger_path(rule.rule)
        path_item = paths.setdefault(swagger_path, {})
        path_parameters = _path_parameters_for_rule(rule)

        for method in sorted(rule.methods - {"HEAD", "OPTIONS"}):
            method_key = method.lower()
            if method_key in path_item:
                _ensure_operation_defaults(path_item[method_key], rule, method, path_parameters)
                continue

            path_item[method_key] = _build_operation(rule, method, path_parameters)

    return spec


def _should_document_rule(rule):
    if rule.endpoint.startswith("static") or rule.endpoint.startswith("flasgger."):
        return False
    return rule.rule == "/" or rule.rule == "/health" or rule.rule.startswith("/api/")


def _to_swagger_path(flask_rule):
    return PATH_PARAM_RE.sub(lambda match: "{" + match.group("name") + "}", flask_rule)


def _path_parameters_for_rule(rule):
    parameters = []
    for match in PATH_PARAM_RE.finditer(rule.rule):
        converter = match.group("converter")
        parameters.append(
            {
                "name": match.group("name"),
                "in": "path",
                "required": True,
                "type": _swagger_type_for_converter(converter),
            }
        )
    return parameters


def _swagger_type_for_converter(converter):
    if converter == "int":
        return "integer"
    if converter == "float":
        return "number"
    return "string"


def _build_operation(rule, method, path_parameters):
    operation = {
        "tags": [_tag_for_rule(rule.rule)],
        "summary": _summary_for_rule(rule),
        "operationId": f"{rule.endpoint.replace('.', '_')}_{method.lower()}",
        "responses": _responses_for_method(method),
    }

    parameters = list(path_parameters)
    if method in {"POST", "PUT", "PATCH"}:
        parameters.append(
            {
                "name": "body",
                "in": "body",
                "required": method in {"POST", "PUT"},
                "schema": {"type": "object"},
            }
        )

    if parameters:
        operation["parameters"] = parameters

    if _requires_auth(rule.rule):
        operation["security"] = [{"BearerAuth": []}]

    return operation


def _ensure_operation_defaults(operation, rule, method, path_parameters):
    operation.setdefault("tags", [_tag_for_rule(rule.rule)])
    operation.setdefault("summary", _summary_for_rule(rule))
    operation.setdefault("operationId", f"{rule.endpoint.replace('.', '_')}_{method.lower()}")
    operation.setdefault("responses", _responses_for_method(method))

    existing_parameters = operation.setdefault("parameters", [])
    existing_names = {
        (parameter.get("in"), parameter.get("name"))
        for parameter in existing_parameters
    }

    for parameter in path_parameters:
        key = (parameter["in"], parameter["name"])
        if key not in existing_names:
            existing_parameters.append(parameter)

    if _requires_auth(rule.rule):
        operation.setdefault("security", [{"BearerAuth": []}])


def _tag_for_rule(rule):
    if rule == "/":
        return "Root"
    if rule == "/health":
        return "Health"

    parts = [part for part in rule.split("/") if part]
    if len(parts) >= 2 and parts[0] == "api":
        return parts[1].replace("-", " ").title()
    return "Default"


def _summary_for_rule(rule):
    view_func = rule.endpoint
    return view_func.split(".")[-1].replace("_", " ").title()


def _responses_for_method(method):
    responses = {
        "200": {"description": "Successful response."},
        "400": {"description": "Bad request."},
        "500": {"description": "Internal server error."},
    }

    if method == "POST":
        responses["201"] = {"description": "Created successfully."}
    if method in {"GET", "PUT", "PATCH", "DELETE"}:
        responses["404"] = {"description": "Resource not found."}

    return responses


def _requires_auth(rule):
    if rule in PUBLIC_PATHS:
        return False
    return rule.startswith("/api/") and not rule.startswith(PUBLIC_PATH_PREFIXES)
