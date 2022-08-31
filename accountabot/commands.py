from discord.ext import commands  # type: ignore

from .data import User
from .data import Recurrence
from .data import Repetition
from .data import Weekday
from .data import timezone_to_utc_offset
from .data import users
from .data import parse_recurrence


timezone_parameter = commands.parameter(
    converter=str,
    description="Your timezone code (e.g. PST, PDT, EDT, etc.)",
    default="PST",
    displayed_default="PST",
)

name_parameter = commands.parameter(
    converter=str, description="What you want to commit to"
)

description_parameter = commands.parameter(
    converter=str,
    description="A more detailed description",
)

recurrence_parameter = commands.parameter(
    converter=str,
    description="How often your commitment repeats",
    default="daily",
    displayed_default="Daily",
)


class Accountability(commands.Cog):
    """Commands to manage your accountability commitments"""

    @commands.command()
    async def register(self, ctx: commands.Context, timezone: str = timezone_parameter):
        """Register yourself as a new user"""

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

    @commands.command()
    async def commit(
        self,
        ctx: commands.Context,
        name: str = name_parameter,
        description: str = description_parameter,
        recurrence: str = recurrence_parameter,
    ):
        """
        Create a new accountability commitment

        Enclose each argument in quotes

        For the recurrence, either indicate "weekly" and specify the days of the week as a three-letter
        abbreviation (e.g. Sun, Mon, Tue, etc.), or indicate "daily"

        Examples:
            &commit "Read" "Read for 30 min. before bed" "daily"
            &commit "Workout" "PPL program + flexibility routine" "Weekly Mon,Wed,Fri"
            &commit "Golden hour" "Do a golden hour at work" "Weekly Mon,Tue,Wed,Thu,Fri"
        """
        try:
            recurrence_obj = parse_recurrence(recurrence)
        except ValueError as ex:
            await ctx.send(str(ex))
