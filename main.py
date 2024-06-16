from pyrogram.types import Message

from base.module import BaseModule
from base.mod_ext import ModuleExtension
from typing import Type

from .extensions.cock import CockExtension

#from sqlalchemy import select
from .db import Base


class MiniGamesModule(BaseModule):
    @property
    def module_extensions(self) -> list[Type[ModuleExtension]]:
        return [
            CockExtension
        ]
    
    @property
    def db_meta(self):
        return Base.metadata
