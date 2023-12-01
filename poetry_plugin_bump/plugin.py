import os
from typing import Any

import semver
from cleo.application import Application
from cleo.helpers import argument
from poetry.console.commands.env_command import EnvCommand
from poetry.plugins.application_plugin import ApplicationPlugin


class ExecCommand(EnvCommand):
    name = "bump"
    description = "poetry plugin to bump version"

    arguments = [
        argument(
            "target_version", "target version or patch/minor/major", multiple=False
        ),
    ]

    def exec(self, bin: str, *args: str) -> int:
        ret = self.env.execute(bin, *args)
        if ret:
            exit(ret)

    def handle(self) -> Any:
        pyproject_folder_path = self.poetry.pyproject.file.path.parent
        pyproject_data = self.poetry.pyproject.data

        target: str = self.argument("target_version")
        current_version = semver.version.Version.parse(
            pyproject_data["tool"]["poetry"]["version"]
        )

        if target == "major":
            target_version = str(current_version.bump_major())
        elif target == "minor":
            target_version = str(current_version.bump_minor())
        elif target == "patch":
            target_version = str(current_version.bump_patch())
        else:
            target_version = str(semver.Version.parse(target.lstrip("v")))

        print(target_version)
        self.line(f"bump version to {target_version}")

        os.chdir(pyproject_folder_path)

        self.exec("poetry", "version", target_version)
        self.exec("git", "add", "pyproject.toml")

        option = pyproject_data.get("tool", {}).get("poetry-plugin-bump", {})
        commit_message = option.get("commit_msg", "bump: v{version}")
        tag_name = option.get("tag_name", "v{version}")

        self.exec(
            "git",
            "commit",
            "-m",
            commit_message.format(version=target_version),
        )

        self.exec(
            "git",
            "tag",
            tag_name.format(version=target_version),
            "-m",
            tag_name.format(version=target_version),
        )

        return


def factory() -> ExecCommand:
    return ExecCommand()


class ExecPlugin(ApplicationPlugin):
    def activate(self, application: Application, *args: Any, **kwargs: Any) -> None:
        application.add(factory())
