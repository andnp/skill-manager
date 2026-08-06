import httpx

from skill_manager.github import discover, install


def test_discover_and_install_skill_package(tmp_path):
    (tmp_path / "skill-manager.toml").write_text('[project]\nsource_dir = "catalog"\n', encoding="utf-8")

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url.endswith("/repos/acme/demo"):
            return httpx.Response(200, json={"default_branch": "main"}, request=request)
        if "/git/trees/main" in url:
            return httpx.Response(
                200,
                json={"tree": [
                    {"path": "demo/SKILL.md", "type": "blob"},
                    {"path": "demo/reference.md", "type": "blob"},
                ]},
                request=request,
            )
        if url.endswith("/demo/SKILL.md"):
            return httpx.Response(200, text="---\ndescription: Demo skill\n---\nBody\n", request=request)
        if url.endswith("/demo/reference.md"):
            return httpx.Response(200, text="Reference", request=request)
        return httpx.Response(404, request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    found = discover("https://github.com/acme/demo", client)
    destination = install(found[0], tmp_path, client)
    client.close()

    assert found[0].summary == "Demo skill"
    assert destination == tmp_path / "catalog" / "demo"
    assert (destination / "reference.md").read_text() == "Reference"
