from pyrogram.types import Message

from base.module import BaseModule
from base.mod_ext import ModuleExtension
from typing import Type

from .extensions.cock import CockExtension
from .extensions.tictactoe import TicTacToeExtension

#from sqlalchemy import select
from .db import Base


class MiniGamesModule(BaseModule):
    @property
    def help_page(self):
        return self.S["help"]

    @property
    def module_extensions(self) -> list[Type[ModuleExtension]]:
        return [
            CockExtension,
            TicTacToeExtension
        ]
    
    @property
    def db_meta(self):
        return Base.metadata
