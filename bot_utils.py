import discord
from datetime import datetime
import logging
import asyncio


async def ensure_roles_exist(guild, role_assignments):
    """
    Ensures that all roles specified in role_assignments exist in the guild.
    Creates the roles if they do not exist.

    Args:
        guild (discord.Guild): The guild to check.
        role_assignments (list): List of role assignments with days and role names.
    """
    logging.debug(f"Ensuring roles exist in guild {guild.name}")
    for assignment in role_assignments:
        try:
            role = discord.utils.get(guild.roles, name=assignment["role_name"])
            if role is None:
                role = await guild.create_role(name=assignment["role_name"])
                logging.info(f"Created role {role.name} in guild {guild.name}")
            assignment["role_id"] = role.id
        except Exception as e:
            logging.error(
                f"Error creating role {assignment['role_name']} in guild {guild.name}: {e}"
            )


async def assign_roles_to_members(guild, role_assignments):
    """
    Assigns roles to members based on how long they have been in the server.
    Members will only keep the most recent role corresponding to their time in the server.

    Args:
        guild (discord.Guild): The guild to assign roles in.
        role_assignments (list): List of role assignments with days and role names.
    """
    logging.debug(f"Assigning roles to members in guild {guild.name}")
    members = guild.members

    batch = []
    batch_size = 10
    last_batch_time = datetime.utcnow()

    for member in members:
        needs_update, new_role = await process_member(member, guild, role_assignments)
        if needs_update:
            batch.append((member, new_role))

        current_time = datetime.utcnow()
        time_elapsed = (current_time - last_batch_time).total_seconds()

        if len(batch) >= batch_size or (batch and time_elapsed >= 600):
            if batch:
                await update_member_roles(batch, guild, role_assignments)
                batch.clear()
            last_batch_time = datetime.utcnow()
            await asyncio.sleep(60)  # Wait 1 minute before processing the next batch

    if batch:
        await update_member_roles(batch, guild, role_assignments)
        batch.clear()

    logging.info(f"Completed assigning roles for all members in guild {guild.name}")


async def process_member(member, guild, role_assignments):
    """
    Processes a single member to determine if they need a role update based on their join date.

    Args:
        member (discord.Member): The member to process.
        guild (discord.Guild): The guild the member belongs to.
        role_assignments (list): List of role assignments with days and role names.

    Returns:
        (bool, discord.Role): Tuple indicating whether the member needs an update and the new role.
    """
    join_date = member.joined_at
    if join_date:
        try:
            join_date = join_date.replace(tzinfo=None)
            days_in_server = (datetime.utcnow() - join_date).days
            new_role = None
            for assignment in role_assignments:
                if days_in_server >= assignment["days"]:
                    new_role = guild.get_role(assignment["role_id"])

            if new_role and new_role not in member.roles:
                return True, new_role
            else:
                logging.info(
                    f"Member {member.name} already has the role {new_role.name if new_role else 'None'}. No changes made."
                )
                return False, None
        except Exception as e:
            logging.error(
                f"Error processing member {member.name} in guild {guild.name}: {e}"
            )
    return False, None


async def update_member_roles(batch, guild, role_assignments):
    """
    Updates roles for a batch of members.

    Args:
        batch (list): List of members and roles to update.
        guild (discord.Guild): The guild the members belong to.
        role_assignments (list): List of role assignments with days and role names.
    """
    for member, new_role in batch:
        try:
            await remove_old_roles(member, role_assignments)
            await add_role_with_retry(member, new_role)
            logging.info(f"Assigned role {new_role.name} to {member.name}.")
            await asyncio.sleep(
                1
            )  # Adding a small delay between individual role updates
        except Exception as e:
            logging.error(
                f"Error updating role for member {member.name} in guild {guild.name}: {e}"
            )


async def remove_old_roles(member, role_assignments):
    """
    Removes all roles specified in role_assignments from the member that are not the correct role.

    Args:
        member (discord.Member): The member to remove roles from.
        role_assignments (list): List of role assignments with days and role names.
    """
    try:
        correct_role = [
            discord.utils.get(member.guild.roles, id=assignment["role_id"])
            for assignment in role_assignments
            if assignment["role_id"] in [role.id for role in member.roles]
        ]
        roles_to_remove = [role for role in member.roles if role in correct_role]
        for role in roles_to_remove:
            await remove_role_with_retry(member, role)
            logging.info(f"Removed role {role.name} from {member.name}")
            await asyncio.sleep(
                1
            )  # Adding a small delay between individual role removals
    except Exception as e:
        logging.error(f"Error removing old roles from member {member.name}: {e}")


async def add_role_with_retry(member, role, retries=5):
    """
    Adds a role to a member with retry logic to handle rate limits.

    Args:
        member (discord.Member): The member to add the role to.
        role (discord.Role): The role to add.
        retries (int): Number of retries allowed for rate limits.
    """
    for attempt in range(retries):
        try:
            await member.add_roles(role)
            return
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_after = (
                    e.retry_after if hasattr(e, "retry_after") else (attempt + 1) * 2
                )
                logging.warning(
                    f"Rate limited while adding role {role.name} to {member.name}. Retrying in {retry_after} seconds."
                )
                await asyncio.sleep(retry_after)
            else:
                logging.error(f"Error adding role {role.name} to {member.name}: {e}")
                return


async def remove_role_with_retry(member, role, retries=5):
    """
    Removes a role from a member with retry logic to handle rate limits.

    Args:
        member (discord.Member): The member to remove the role from.
        role (discord.Role): The role to remove.
        retries (int): Number of retries allowed for rate limits.
    """
    for attempt in range(retries):
        try:
            await member.remove_roles(role)
            return
        except discord.HTTPException as e:
            if e.status == 429:  # Rate limited
                retry_after = (
                    e.retry_after if hasattr(e, "retry_after") else (attempt + 1) * 2
                )
                logging.warning(
                    f"Rate limited while removing role {role.name} from {member.name}. Retrying in {retry_after} seconds."
                )
                await asyncio.sleep(retry_after)
            else:
                logging.error(
                    f"Error removing role {role.name} from {member.name}: {e}"
                )
                return


def get_days_in_server(member):
    """
    Calculates the number of days a member has been in the server.

    Args:
        member (discord.Member): The member to calculate the days for.

    Returns:
        int: The number of days the member has been in the server, or None if an error occurs.
    """
    join_date = member.joined_at
    if join_date:
        try:
            join_date = join_date.replace(tzinfo=None)
            return (datetime.utcnow() - join_date).days
        except Exception as e:
            logging.error(
                f"Error calculating days in server for member {member.name}: {e}"
            )
    return None
