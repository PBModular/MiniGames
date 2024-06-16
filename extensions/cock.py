from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from base.module import BaseModule, command, allowed_for, callback_query
from base.mod_ext import ModuleExtension
from ..db import Base, ChatState
from sqlalchemy import select, update
import asyncio
import random

class CockExtension(ModuleExtension):
    @property
    def db_meta(self):
        return Base.metadata  
    
    async def set_participation(self, chat_id, user_id, is_participating):
        async with self.db.session_maker() as session:
            chat_state = await session.execute(select(ChatState).where(ChatState.chat_id == chat_id, ChatState.user_id == user_id))
            chat_state = chat_state.scalar_one_or_none()
            
            if chat_state is None:
                chat_state = ChatState(chat_id=chat_id, user_id=user_id, is_participating=is_participating)
                session.add(chat_state)
            else:
                chat_state.is_participating = is_participating
            
            await session.commit()

    async def get_participants(self, chat_id):
        async with self.db.session_maker() as session:
            participants = await session.execute(select(ChatState.user_id).where(ChatState.chat_id == chat_id, ChatState.is_participating == True))
            participants = [participant[0] for participant in participants]
            return participants

    async def set_cock_length(self, chat_id, user_id, change):
        async with self.db.session_maker() as session:
            chat_state = await session.scalar(select(ChatState).where(ChatState.chat_id == chat_id, ChatState.user_id == user_id))
            if chat_state.cock_size is None:
                chat_state.cock_size = 10
            chat_state.cock_size += change

            session.add(chat_state)
            await session.commit()

    async def get_cock_length(self, chat_id, user_id):
        async with self.db.session_maker() as session:
            chat_state = await session.scalar(select(ChatState).where(ChatState.chat_id == chat_id, ChatState.user_id == user_id))
            if chat_state.cock_size is None:
                chat_state.cock_size = 10
            return chat_state.cock_size
        
    @command("cockjoin")
    async def join_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        participants = await self.get_participants(chat_id)

        if user_id in participants:
            await message.reply("Вы уже присоединились к игре!")
        else:
            await self.set_participation(chat_id, user_id, True)
            await message.reply("Вы присоединились к игре!")

    @command("cockleave")
    async def leave_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        participants = await self.get_participants(chat_id)

        if user_id in participants:
            await self.set_participation(chat_id, user_id, False)
            await message.reply("Вы покинули игру!")
        else:
            await message.reply("Вы не состоите в игре!")

    @command("cock")
    async def cock_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        participants = await self.get_participants(chat_id)

        if not participants:
            await message.reply("Нет участников игры.")
            return

        user_id = random.choice(participants)
        change = random.randint(-5, 5)

        await self.set_cock_length(chat_id, user_id, change)
        current_length = await self.get_cock_length(chat_id, user_id)

        user = await bot.get_users(user_id)
        result_message = f"{user.first_name} теперь имеет член длиной {current_length} см (изменение: {change} см)."
        await message.reply(result_message)
