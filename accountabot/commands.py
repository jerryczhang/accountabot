from discord.ext import commands  # type: ignore

from .data import User
from .data import timezone_to_utc_offset
from .data import accountability_members


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
        members_dict = accountability_members.members
        if member_id in members_dict:
            members_dict[member_id].timezone = timezone
            await ctx.send(f"User successfully updated:\n{members_dict[member_id]}")
        else:
            new_member = User(
                user_id=member_id, commitments=[], is_active=True, timezone=timezone
            )
            members_dict[member_id] = new_member
            accountability_members.save()
            await ctx.send(f"Registration successful!\n{new_member}")
