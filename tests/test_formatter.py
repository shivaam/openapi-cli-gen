from openapi_cli_gen.output.formatter import format_output


def test_format_json():
    data = {"name": "John", "age": 30}
    result = format_output(data, "json")
    assert '"name": "John"' in result
    assert '"age": 30' in result


def test_format_yaml():
    data = {"name": "John", "age": 30}
    result = format_output(data, "yaml")
    assert "name: John" in result
    assert "age: 30" in result


def test_format_raw():
    data = {"name": "John"}
    result = format_output(data, "raw")
    assert "name" in result


def test_format_table_single(capsys):
    data = {"name": "John", "age": 30}
    format_output(data, "table", print_output=True)
    captured = capsys.readouterr()
    assert "John" in captured.out


def test_format_table_list(capsys):
    data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
    format_output(data, "table", print_output=True)
    captured = capsys.readouterr()
    assert "A" in captured.out
    assert "B" in captured.out


def test_format_table_wrapped_list(capsys):
    data = {"items": [{"id": 1}, {"id": 2}], "total": 2}
    format_output(data, "table", print_output=True)
    captured = capsys.readouterr()
    assert "1" in captured.out
