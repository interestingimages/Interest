from pathlib import Path


class Config:
    def __init__(
        self, config_file: Path, default: dict, encoding: str = "utf-8"
    ) -> None:
        import tomlkit

        self.tomlkit = tomlkit

        if not isinstance(config_file, Path):
            config_file = Path(config_file)

        if not config_file.is_file():
            self.file = open(config_file, "w", encoding=encoding)

            # Make new config file
            self.data = self.tomlkit.document()

            for key, value in default.items():
                self.data[key] = value

            # Cleanup
            self.file.write(self.tomlkit.dumps(self.data))
            self.file.flush()

        else:
            self.file = open(config_file, "r+", encoding=encoding)
            self.data = tomlkit.loads(self.file.read())

            # Add unadded tables
            for table in [t for t in default.keys() if t not in self.data.keys()]:
                print(
                    f'{config_file.stem}: Appending non-present table "{table}" not '
                    f"present in {config_file.name}."
                )
                self.data.update({table: default[table]})

            # Add unadded keys to existing tables
            for table, contents in self.data.items():
                if table in default:
                    if contents.keys() != default[table].keys():
                        for key in [
                            k for k in default[table].keys() if k not in contents.keys()
                        ]:
                            print(
                                f"{config_file.stem}: Appending non-present key "
                                f'value pair "{key}" not present in '
                                f"{config_file.name}:{table}"
                            )
                            self.data[table][key] = default[table][key]

            # Cleanup
            self.file.seek(0)
            self.file.write(self.tomlkit.dumps(self.data))
            self.file.flush()

    def __getitem__(self, item):
        return self.data[item]

    def get(self, item, default=None):
        return self.data.get(item, default=default)

    def write(self) -> None:
        self.file.seek(0)
        self.write(self.tomlkit.dumps(self.data))
        self.file.flush()

    def close(self) -> None:
        self.file.close()
