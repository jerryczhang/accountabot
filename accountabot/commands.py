from discord.ext import commands  # type: ignore

from .data import User
from .data import timezone_to_utc_offset
from .data import users


timezone_parameter = commands.parameter(
    converter=str,
    default="PST",
    description="Your timezone code (e.g. PST, PDT, EDT, etc.)",
    displayed_default="PST",
)


class Accountability(commands.Cog):
    """Commands to manage your accountability commitments"""

    @commands.command()
    async def register(self, ctx: commands.Context, timezone: str = timezone_parameter):
        """
        Register yourself as a new user
        """

        timezone = timezone.upper()
        if timezone not in timezone_to_utc_offset:
            invalid_timezone_message = (
                f"Timezone '{timezone}' isn't valid\n"
                f"Supported timezones: {', '.join(list(timezone_to_utc_offset.keys()))}"
            )
            await ctx.send(invalid_timezone_message)
            return

        member_id = ctx.author.id
        if member_id in users.member_id_to_user:
            user = users.member_id_to_user[member_id]
            user.timezone = timezone
            await ctx.send(f"User successfully updated:\n{user}")
        else:
            new_user = User(
                member_id=member_id, commitments=[], is_active=True, timezone=timezone
            )
            users.member_id_to_user[member_id] = new_user
            users.save()
            await ctx.send(f"Registration successful!\n{new_user}")
