import os
import shutil
import tempfile

import pytest


@pytest.fixture(scope="function")
def project(request):
    from lektor.project import Project

    return Project.from_path(os.path.join(os.path.dirname(__file__), "demo-project"))


@pytest.fixture(scope="function")
def env(request, project):
    from lektor.environment import Environment

    return Environment(project)


@pytest.fixture(scope="function")
def pad(request, env):
    from lektor.db import Database

    return Database(env).new_pad()


def make_builder(request, pad):
    from lektor.builder import Builder

    out = tempfile.mkdtemp()
    b = Builder(pad, out)

    def cleanup():
        try:
            shutil.rmtree(out)
        except (OSError, IOError):
            pass

    request.addfinalizer(cleanup)
    return b


@pytest.fixture(scope="function")
def builder(request, pad):
    return make_builder(request, pad)


@pytest.fixture(scope="function")
def F():
    from lektor.db import F

    return F


@pytest.fixture(scope="function")
def webui(request, env):
    from lektor.admin.webui import WebUI

    output_path = tempfile.mkdtemp()

    def cleanup():
        try:
            shutil.rmtree(output_path)
        except (OSError, IOError):
            pass

    request.addfinalizer(cleanup)

    return WebUI(env, output_path=output_path)
