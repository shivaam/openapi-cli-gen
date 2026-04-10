from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ParamInfo:
    name: str
    type: str  # "string", "integer", "number", "boolean"
    required: bool = False
    default: object = None
    enum: list[str] | None = None


@dataclass
class SecuritySchemeInfo:
    name: str
    type: str  # "http", "apiKey", "oauth2", "openIdConnect"
    scheme: str | None = None  # "bearer", "basic" (for http type)
    header_name: str | None = None  # for apiKey type
    location: str | None = None  # "header", "query", "cookie" (for apiKey)


@dataclass
class EndpointInfo:
    operation_id: str
    tag: str
    method: str  # "get", "post", "put", "patch", "delete"
    path: str
    summary: str = ""
    path_params: list[ParamInfo] = field(default_factory=list)
    query_params: list[ParamInfo] = field(default_factory=list)
    body_schema: dict | None = None
    body_ref_name: str | None = None  # Original $ref name (e.g., "CreateChatCompletionRequest")
    body_content_type: str = "application/json"  # "application/json" or "multipart/form-data"
    body_file_fields: set[str] = field(default_factory=set)  # field names with format: binary


HTTP_METHODS = ("get", "post", "put", "patch", "delete")


def parse_spec(
    resolved_spec: dict,
    body_ref_names: dict[tuple[str, str], str] | None = None,
) -> list[EndpointInfo]:
    """Parse a resolved OpenAPI spec into a list of EndpointInfo.

    Args:
        resolved_spec: Spec with $ref resolved.
        body_ref_names: Optional {(path, method): schema_name} from raw spec.
    """
    endpoints = []
    body_ref_names = body_ref_names or {}

    for path, path_item in resolved_spec.get("paths", {}).items():
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not operation:
                continue

            tag = (operation.get("tags") or ["default"])[0]
            op_id = operation.get("operationId", f"{method}_{path.strip('/').replace('/', '_')}")

            path_params = []
            query_params = []
            for p in operation.get("parameters", []):
                schema = p.get("schema", {})
                # Object-typed query params with properties (OpenAPI style=form, explode=true)
                # flatten into individual query params. Typesense's `searchParameters` is the
                # canonical case: spec declares one object-typed query param with 72 properties,
                # wire format is `?q=matrix&query_by=title&...` — each property as its own param.
                if (
                    p.get("in") == "query"
                    and schema.get("type") == "object"
                    and schema.get("properties")
                ):
                    for sub_name, sub_schema in schema.get("properties", {}).items():
                        if not isinstance(sub_schema, dict):
                            continue
                        query_params.append(
                            ParamInfo(
                                name=sub_name,
                                type=sub_schema.get("type", "string"),
                                required=False,  # always optional; server decides at runtime
                                default=sub_schema.get("default"),
                                enum=sub_schema.get("enum"),
                            )
                        )
                    continue

                param = ParamInfo(
                    name=p["name"],
                    type=schema.get("type", "string"),
                    required=p.get("required", False),
                    default=schema.get("default"),
                    enum=schema.get("enum"),
                )
                if p["in"] == "path":
                    path_params.append(param)
                elif p["in"] == "query":
                    query_params.append(param)

            body_schema = None
            body_content_type = "application/json"
            body_file_fields: set[str] = set()
            rb = operation.get("requestBody")
            if rb:
                content = rb.get("content", {})
                # Prefer JSON; fall back to multipart/form-data for file upload endpoints
                if "application/json" in content:
                    body_schema = content["application/json"].get("schema")
                elif "multipart/form-data" in content:
                    body_schema = content["multipart/form-data"].get("schema")
                    body_content_type = "multipart/form-data"
                    # Detect file fields: properties with format: binary
                    for fname, prop in (body_schema or {}).get("properties", {}).items():
                        if isinstance(prop, dict) and prop.get("format") == "binary":
                            body_file_fields.add(fname)

            endpoints.append(EndpointInfo(
                operation_id=op_id,
                tag=tag,
                method=method,
                path=path,
                summary=operation.get("summary", ""),
                path_params=path_params,
                query_params=query_params,
                body_schema=body_schema,
                body_ref_name=body_ref_names.get((path, method)),
                body_content_type=body_content_type,
                body_file_fields=body_file_fields,
            ))

    return endpoints


def extract_security_schemes(resolved_spec: dict) -> list[SecuritySchemeInfo]:
    """Extract security scheme info from spec."""
    schemes = []
    components = resolved_spec.get("components", {})
    security_schemes = components.get("securitySchemes", {})

    for name, scheme in security_schemes.items():
        schemes.append(SecuritySchemeInfo(
            name=name,
            type=scheme.get("type", ""),
            scheme=scheme.get("scheme"),
            header_name=scheme.get("name"),
            location=scheme.get("in"),
        ))

    return schemes
