from pyrogram import Client, filters
from pyrogram.types import Message
from base.module import BaseModule, command
from base.mod_ext import ModuleExtension
from ..db import Base, CockState
from ..utils import fetch_user
from sqlalchemy import select, delete, func
from datetime import datetime, timedelta
import random

class CockExtension(ModuleExtension):
    @property
    def db_meta(self):
        return Base.metadata  

    async def set_participation(self, chat_id, user_id, is_participating):
        async with self.db.session_maker() as session:
            cock_state = await session.execute(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            cock_state = cock_state.scalar_one_or_none()
            
            if cock_state is None:
                cock_state = CockState(chat_id=chat_id, user_id=user_id, is_participating=is_participating)
                if cock_state.cock_size is None:
                    cock_state.cock_size = 5
                session.add(cock_state)
            else:
                cock_state.is_participating = is_participating
            
            await session.commit()

    async def get_participants(self, chat_id):
        async with self.db.session_maker() as session:
            participants = await session.execute(
                select(CockState.user_id).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            participants = [participant[0] for participant in participants]
            return participants

    async def set_cock_length(self, chat_id, user_id, change):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            if cock_state.active_event == "rubber":
                cock_state.cock_size = change
            else:
                cock_state.cock_size += change

            cock_state.cock_size = round(cock_state.cock_size, 1)

            if cock_state.event_duration > 0:
                cock_state.event_duration -= 1
                if cock_state.event_duration == 0:
                    cock_state.active_event = None

            session.add(cock_state)
            await session.commit()

    async def get_cock_length(self, chat_id, user_id):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            if cock_state.cock_size is None:
                cock_state.cock_size = 5
                session.add(cock_state)
                await session.commit()
            return cock_state.cock_size

    async def get_all_participants(self, chat_id):
        async with self.db.session_maker() as session:
            participants = await session.execute(
                select(CockState.user_id, CockState.cock_size).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            participants = participants.all()
            return participants

    async def get_average_length(self, chat_id):
        async with self.db.session_maker() as session:
            avg_length = await session.execute(
                select(func.avg(CockState.cock_size)).where(CockState.chat_id == chat_id, CockState.is_participating == True)
            )
            avg_length = avg_length.scalar()
            return avg_length if avg_length is not None else 0

    def calculate_change(self, current_length):
        increase_probability = max(0.35, 0.95 - (current_length / 60) * 0.60)
        rand_num = random.random()

        if (rand_num <= increase_probability):
            change = random.randint(1, min(5, 60 - int(current_length)))
        else:
            max_decrease = max(1, (current_length * 0.25))
            change = -random.randint(1, int(max_decrease))

        return change

    async def check_special_events(self, chat_id, user_id, current_length):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            if cock_state.active_event:
                return None

            possible_events = []

            if current_length > 35 and random.random() < 0.03:
                possible_events.append(self.event_micro)

            if random.random() < 0.02:
                possible_events.append(self.event_rubber)

            if random.random() < 0.02:
                possible_events.append(self.event_teleport)

            if random.random() < 0.04:
                possible_events.append(self.event_aging)

            if random.random() < 0.01:
                possible_events.append(self.event_rocket)

            if possible_events:
                chosen_event = random.choice(possible_events)
                special_event_message = await chosen_event(chat_id, user_id, current_length)
                return special_event_message
        
            return None

    async def event_micro(self, chat_id, user_id, current_length):
        await self.set_cock_length(chat_id, user_id, -current_length + 0.1)
        return self.S["cock"]["event"]["micro"]

    async def event_rubber(self, chat_id, user_id, current_length):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            cock_state.active_event = "rubber"
            cock_state.event_duration = 4
            session.add(cock_state)
            await session.commit()

        return self.S["cock"]["event"]["rubber"]["message"]

    async def event_teleport(bot: Client, self, chat_id, user_id, current_length):
        participants = await self.get_all_participants(chat_id)
        if len(participants) < 2:
            return None

        other_user_id, other_user_length = random.choice([p for p in participants if p[0] != user_id])
        fetch_user = fetch_user(bot, user_id, with_link=True)

        async with self.db.session_maker() as session:
            user_cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            other_cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == other_user_id)
            )

            user_cock_state.cock_size, other_cock_state.cock_size = other_cock_state.cock_size, user_cock_state.cock_size

            session.add(user_cock_state)
            session.add(other_cock_state)
            await session.commit()

        return self.S["cock"]["event"]["teleport"].format(fetch_user=fetch_user, other_user_length=other_user_length)

    async def event_aging(self, chat_id, user_id, current_length):
        new_length = round(current_length * 0.8, 1)
        await self.set_cock_length(chat_id, user_id, new_length - current_length)
        return self.S["cock"]["event"]["aging"].format(new_length=new_length)

    async def event_rocket(self, chat_id, user_id, current_length):
        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )
            cock_state.active_event = "rocket"
            cock_state.event_duration = random.randint(2, 5)
            session.add(cock_state)
            await session.commit()

        return self.S["cock"]["event"]["rocket"]["message"]

    @command("cockjoin")
    async def join_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        participants = await self.get_participants(chat_id)

        if user_id in participants:
            await message.reply(self.S["cock"]["join"]["already"])
        else:
            await self.set_participation(chat_id, user_id, True)
            await message.reply(self.S["cock"]["join"]["ok"])

    @command("cockleave")
    async def leave_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        participants = await self.get_participants(chat_id)

        if user_id in participants:
            async with self.db.session_maker() as session:
                await session.execute(
                    delete(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
                )
                await session.commit()
            await message.reply(self.S["cock"]["leave"]["ok"])
        else:
            await message.reply(self.S["cock"]["leave"]["not_participant"])

    @command("cock")
    async def cock_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        user_id = message.from_user.id
        participants = await self.get_participants(chat_id)

        if user_id not in participants:
            await message.reply(self.S["cock"]["not_participant"])
            return

        async with self.db.session_maker() as session:
            cock_state = await session.scalar(
                select(CockState).where(CockState.chat_id == chat_id, CockState.user_id == user_id)
            )

            now = datetime.utcnow()
            if cock_state.cooldown and now - cock_state.cooldown < timedelta(hours=24):
                time_remaining = timedelta(hours=24) - (now - cock_state.cooldown)
                hours, remainder = divmod(time_remaining.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                await message.reply(self.S["cock"]["cooldown"].format(hours=hours, minutes=minutes))
                return

            current_length = await self.get_cock_length(chat_id, user_id)
            special_event_message = await self.check_special_events(chat_id, user_id, current_length)

            if special_event_message:
                await message.reply(special_event_message)
            else:
                if cock_state.active_event == "rubber" and cock_state.event_duration > 0:
                    change = random.randint(1, 60)
                    await self.set_cock_length(chat_id, user_id, change)
                    return self.S["cock"]["event"]["rubber"]["change"].format(change=change, remain=(cock_state.event_duration - 1))
                elif cock_state.active_event == "rocket" and cock_state.event_duration > 0:
                    if random.random() < 0.5:
                        cock_state.event_duration =- 1
                        change = int(current_length) + 20
                        await self.set_cock_length(chat_id, user_id, change)
                        result_message = self.S["cock"]["event"]["rocket"]["no_change"].format(change=change)
                    else:
                        cock_state.event_duration = 0
                        change = int(current_length) / 4
                        await self.set_cock_length(chat_id, user_id, change)
                        result_message = self.S["cock"]["event"]["rocket"]["change"].format(change=change)
                else:
                    change = self.calculate_change(current_length)
                    await self.set_cock_length(chat_id, user_id, change)
                    new_length = await self.get_cock_length(chat_id, user_id)
                    result_message = self.S["cock"]["change"].format(new_length=new_length, change=change)

                cock_state.cooldown = now
                session.add(cock_state)
                await session.commit()

                await message.reply(result_message)

    @command("cockstat")
    async def cockstat_cmd(self, bot: Client, message: Message):
        chat_id = message.chat.id
        participants = await self.get_all_participants(chat_id)
        average_length = await self.get_average_length(chat_id)

        if not participants:
            await message.reply(self.S["cock"]["stat"]["no_participants"])
            return

        sorted_participants = sorted(participants, key=lambda x: x[1], reverse=True)

        stats_message = self.S["cock"]["stat"]["list_header"]
        for place, (user_id, cock_length) in enumerate(sorted_participants, start=1):
            profile_link = await fetch_user(bot, user_id, with_link=False)
            stats_message += self.S["cock"]["stat"]["list"].format(place=place, profile_link=profile_link, cock_length=cock_length)

        stats_message += self.S["cock"]["stat"]["average"].format(average=round(average_length, 2))

        await message.reply(stats_message)
    