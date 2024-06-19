@staticmethod
async def fetch_user(bot, user_id, with_link=False):
    user = await bot.get_users(user_id)
    
    if user.username:
        if with_link:
            return f"@{user.username}"
        else:
            return user.username
    else:
        first_name = user.first_name if user.first_name else ""
        last_name = user.last_name if user.last_name else ""
        if with_link:
            profile_link = f"[{first_name} {last_name}](tg://user?id={user_id})"
        else:
            profile_link = f"{first_name} {last_name}"
        return profile_link