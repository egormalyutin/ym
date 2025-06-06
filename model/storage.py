import json
import os
from uuid import uuid4
from pydantic import BaseModel


class FileMeta(BaseModel):
    id: str
    uuid: str
    commited: bool


class FileStorageMeta(BaseModel):
    version: int
    files: dict[str, FileMeta]


class FileStorage:
    meta: FileStorageMeta

    def __init__(self, dir):
        self.meta_path = os.path.join(dir, "meta.json")
        self.data_dir = os.path.join(dir, "data")

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir, exist_ok=True)

        if not os.path.exists(self.meta_path):
            self.meta = FileStorageMeta(
                version=0,
                files={}
            )
        else:
            with open(self.meta_path, "r") as file:
                meta = json.load(file)
                self.meta = FileStorageMeta(**meta)

    def save_meta(self):
        with open(self.meta_path, "w") as file:
            file.write(self.meta.model_dump_json())

    def create(self, id) -> str:
        self.remove(id)

        uuid = str(uuid4())
        self.meta.files[id] = FileMeta(
            id=id,
            uuid=uuid,
            commited=False
        )
        self.save_meta()
        return os.path.join(self.data_dir, uuid)

    def has(self, id) -> bool:
        return id in self.meta.files

    def get_path(self, id) -> str:
        file = self.meta.files[id]
        return os.path.join(self.data_dir, file.uuid)

    def commit(self, id):
        self.meta.files[id].commited = True
        self.save_meta()

    def uncommit(self, id):
        self.meta.files[id].commited = False
        self.save_meta()

    def is_commited(self, id) -> bool:
        return self.meta.files[id].commited

    def has_commited(self, id) -> bool:
        return self.has(id) and self.is_commited(id)

    def remove(self, id):
        if id not in self.meta.files:
            return

        path = self.get_path(id)

        del self.meta.files[id]
        self.save_meta()

        if os.path.exists(path):
            os.unlink(path)
