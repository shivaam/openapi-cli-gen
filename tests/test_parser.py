from openapi_cli_gen.spec.parser import parse_spec, EndpointInfo, extract_security_schemes, SecuritySchemeInfo


def test_parse_returns_endpoints(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    assert len(endpoints) > 0
    assert all(isinstance(ep, EndpointInfo) for ep in endpoints)


def test_parse_groups_by_tag(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    tags = {ep.tag for ep in endpoints}
    assert "users" in tags
    assert "orders" in tags
    assert "tags" in tags


def test_parse_extracts_operation_id(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    op_ids = {ep.operation_id for ep in endpoints}
    assert "list_users" in op_ids
    assert "create_user" in op_ids
    assert "get_user" in op_ids


def test_parse_extracts_method_and_path(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    create_user = next(ep for ep in endpoints if ep.operation_id == "create_user")
    assert create_user.method == "post"
    assert create_user.path == "/users"


def test_parse_classifies_params(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    get_user = next(ep for ep in endpoints if ep.operation_id == "get_user")
    assert "user_id" in [p.name for p in get_user.path_params]

    list_users = next(ep for ep in endpoints if ep.operation_id == "list_users")
    query_names = [p.name for p in list_users.query_params]
    assert "limit" in query_names
    assert "offset" in query_names


def test_parse_extracts_body_schema(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    create_user = next(ep for ep in endpoints if ep.operation_id == "create_user")
    assert create_user.body_schema is not None
    assert "name" in create_user.body_schema.get("properties", {})


def test_parse_no_body_for_get(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    list_users = next(ep for ep in endpoints if ep.operation_id == "list_users")
    assert list_users.body_schema is None


def test_parse_extracts_summary(resolved_spec):
    endpoints = parse_spec(resolved_spec)
    create_user = next(ep for ep in endpoints if ep.operation_id == "create_user")
    assert create_user.summary == "Create a new user"


def test_parse_extracts_security_schemes(resolved_spec):
    schemes = extract_security_schemes(resolved_spec)
    assert len(schemes) > 0
    names = {s.name for s in schemes}
    assert "bearerAuth" in names
