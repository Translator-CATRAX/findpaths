import pytest
import findpaths


def pytest_addoption(parser):
    parser.addoption("--lang", action="store", default='python')


@pytest.fixture(scope='session')
def lang(request):
    lang = request.config.getoption('--lang')
    print(f"setting language: {lang}")
    findpaths.set_language(lang)
    return lang
