import sqlite3
import discord
from discord.ext import commands
from discord.ui import Button, View, Modal, TextInput
from utils.emoji import *
from utils.config import *
import asyncio
DB_PATH = "./database/creator.db"

class PanelView(View):
    def __init__(self):
        super().__init__(timeout=None)

        lock_button = Button(label="", emoji="<:lock:1280773605202067517>", style=discord.ButtonStyle.grey, custom_id="lock", row=0)
        unlock_button = Button(label="", emoji="<:unlock:1280773607882096674>", style=discord.ButtonStyle.grey, custom_id="unlock", row=0)
        hide_button = Button(label="", emoji="<:hide:1280773602228310058>", style=discord.ButtonStyle.grey, custom_id="hide", row=0)
        unhide_button = Button(label="", emoji="<:unhide:1280773599355207743>", style=discord.ButtonStyle.grey, custom_id="unhide", row=0)
        limit_button = Button(label="", emoji="<:limite:1280773596138049607>", style=discord.ButtonStyle.grey, custom_id="limit", row=1)
        invite_button = Button(label="", emoji="<:invite:1280773592488869941>", style=discord.ButtonStyle.grey, custom_id="invite", row=1)
        ban_button = Button(label="", emoji="<:ban:1280773589485748226>", style=discord.ButtonStyle.grey, custom_id="ban", row=1)
        permit_button = Button(label="", emoji="<:permit:1280773585941565491>", style=discord.ButtonStyle.grey, custom_id="permit", row=1)
        rename_button = Button(label="", emoji="<:rename:1280773582330265663>", style=discord.ButtonStyle.grey, custom_id="rename", row=2)

        lock_button.callback = self.lock_callback
        unlock_button.callback = self.unlock_callback
        hide_button.callback = self.hide_callback
        unhide_button.callback = self.unhide_callback
        limit_button.callback = self.limit_callback
        invite_button.callback = self.invite_callback
        ban_button.callback = self.ban_callback
        permit_button.callback = self.permit_callback
        rename_button.callback = self.rename_callback

        self.add_item(lock_button)
        self.add_item(unlock_button)
        self.add_item(hide_button)
        self.add_item(unhide_button)
        self.add_item(limit_button)
        self.add_item(invite_button)
        self.add_item(ban_button)
        self.add_item(permit_button)
        self.add_item(rename_button)


    async def lock_callback(self, interaction):
        await vccreator.lock_vc(interaction)

    async def unlock_callback(self, interaction):
        await vccreator.unlock_vc(interaction)

    async def hide_callback(self, interaction):
        await vccreator.hide_vc(interaction)

    async def unhide_callback(self, interaction):
        await vccreator.unhide_vc(interaction)

    async def limit_callback(self, interaction):
        await vccreator.limit_vc(interaction)

    async def invite_callback(self, interaction):
        await vccreator.invite_to_vc(interaction)

    async def ban_callback(self, interaction):
        await vccreator.ban_from_vc(interaction)

    async def permit_callback(self, interaction):
        await vccreator.permit_in_vc(interaction)

    async def rename_callback(self, interaction):
        await vccreator.rename_vc(interaction)

class vccreator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db_path = './database/creator.db'
        self.setup_database()

    def setup_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS setups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                setup_name TEXT,
                category_id INTEGER,
                channel_id INTEGER,
                max_users INTEGER,
                UNIQUE(guild_id, setup_name)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS panels (
                guild_id INTEGER,
                channel_id INTEGER,
                PRIMARY KEY (guild_id)
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                channel_id INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    async def cog_load(self):
        self.bot.add_view(PanelView())

    @commands.group(invoke_without_command=True)
    async def vccreator(self, ctx):
        if ctx.subcommand_passed is None:
            await ctx.send_help(ctx.command)
            ctx.command.reset_cooldown(ctx)

    @vccreator.command(name='setup')
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def setup(self, ctx, setup_name: str, mode: str):
        """Sets up voice channels based on the setup name and mode (solo, duo, trio, quad)."""
        modes = {'solo': 1, 'duo': 2, 'trio': 3, 'quad': 4}
        if mode not in modes:
            await ctx.send('Invalid mode. Choose from: solo, duo, trio, quad.')
            return

        max_users = modes[mode]
        guild = ctx.guild

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check if a setup already exists for this setup name in the guild
        c.execute('SELECT * FROM setups WHERE guild_id = ? AND setup_name = ?', (guild.id, setup_name))
        setup = c.fetchone()

        if setup:
            category = guild.get_channel(setup[3])
            if category is None:
                category = await guild.create_category(setup_name)
                c.execute('UPDATE setups SET category_id = ? WHERE guild_id = ? AND setup_name = ?', (category.id, guild.id, setup_name))
                conn.commit()

            channel_name = f'Join to Create - {mode}'
            existing_channel = discord.utils.get(category.voice_channels, name=channel_name)

            if not existing_channel:
                channel = await guild.create_voice_channel(channel_name, category=category)
                c.execute('INSERT INTO setups (guild_id, setup_name, category_id, channel_id, max_users) VALUES (?, ?, ?, ?, ?)',
                          (guild.id, setup_name, category.id, channel.id, max_users))
                conn.commit()
            await ctx.send(f'Setup complete for setup name: {setup_name}, mode: {mode}')
        else:
            # Create category
            category = await guild.create_category(setup_name)

            # Create voice channel
            channel_name = f'Join to Create - {mode}'
            channel = await guild.create_voice_channel(channel_name, category=category)

            # Save to database
            c.execute('INSERT INTO setups (guild_id, setup_name, category_id, channel_id, max_users) VALUES (?, ?, ?, ?, ?)',
                      (guild.id, setup_name, category.id, channel.id, max_users))
            conn.commit()
            await ctx.send(f'Setup complete for setup name: {setup_name}, mode: {mode}')

        conn.close()

    @vccreator.command(name='set')
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def set(self, ctx, setup_name: str, category: discord.CategoryChannel, channel: discord.VoiceChannel, max_users: int):
        """Allows setting a custom category, channel, and max users for a setup."""
        guild = ctx.guild

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Check if the setup exists
        c.execute('SELECT * FROM setups WHERE guild_id = ? AND setup_name = ?', (guild.id, setup_name))
        setup = c.fetchone()

        if setup:
            # Update the existing setup with the custom values
            c.execute('UPDATE setups SET category_id = ?, channel_id = ?, max_users = ? WHERE guild_id = ? AND setup_name = ?',
                    (category.id, channel.id, max_users, guild.id, setup_name))
            await ctx.send(f'Setup `{setup_name}` updated with custom category `{category.name}`, channel `{channel.name}`, and max users set to {max_users}.')
        else:
            # Create a new setup with the provided custom values
            c.execute('INSERT INTO setups (guild_id, setup_name, category_id, channel_id, max_users) VALUES (?, ?, ?, ?, ?)',
                    (guild.id, setup_name, category.id, channel.id, max_users))
            await ctx.send(f'New setup `{setup_name}` created with custom category `{category.name}`, channel `{channel.name}`, and max users set to {max_users}.')
        
        conn.commit()
        conn.close()

    @vccreator.command(name='panel')
    @commands.guild_only()
    @commands.has_permissions(manage_channels=True)
    async def panel(self, ctx, channel: discord.TextChannel):
        """Sends an embed with control buttons to the specified channel."""
        
        embed = discord.Embed(
            title="Voice Channel Creator Panel",
            description="Control your private voice channel using the buttons below.",
            color=discord.Color.blue()
        )
        embed.set_image(url="https://cdn.discordapp.com/attachments/1266823752885469347/1280771318752481361/blue_panel_ez1.png")

        view = PanelView()

        await channel.send(embed=embed, view=view)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('INSERT OR REPLACE INTO panels (guild_id, channel_id) VALUES (?, ?)', (ctx.guild.id, channel.id))
        conn.commit()
        conn.close()


    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel is None or before.channel == after.channel:
            return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check if the user has joined a setup's voice channel
        c.execute('SELECT * FROM setups WHERE channel_id = ?', (after.channel.id,))
        setup = c.fetchone()
        conn.close()

        if setup:
            guild = member.guild
            category = guild.get_channel(setup[3])
            max_users = setup[5]

            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=False),
                member: discord.PermissionOverwrite(connect=True, manage_channels=True)
            }

            try:
                new_channel = await guild.create_voice_channel(f"{member.display_name}'s VC", category=category, user_limit=max_users, overwrites=overwrites)
                await member.move_to(new_channel)

                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('INSERT INTO user_channels (guild_id, channel_id) VALUES (?, ?)', (guild.id, new_channel.id))
                conn.commit()
                conn.close()

                await self.check_and_delete_empty_channel(new_channel)
            except:
                pass

    async def check_and_delete_empty_channel(self, channel):
        while True:
            await asyncio.sleep(30)
            if len(channel.members) == 0:
                try:
                    await channel.delete()
                except:
                    await asyncio.sleep(5)
                    return
                
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                c.execute('DELETE FROM user_channels WHERE channel_id = ?', (channel.id,))
                conn.commit()
                conn.close()
                
                break

    @staticmethod
    async def is_valid_channel(channel_id: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM user_channels WHERE channel_id = ?', (channel_id,))
        valid = c.fetchone() is not None
        conn.close()
        return valid

    @staticmethod
    async def lock_vc(interaction):
        try:
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                if await vccreator.is_valid_channel(channel.id):
                    overwrites = channel.overwrites_for(interaction.guild.default_role)
                    overwrites.connect = False
                    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
                    await interaction.response.send_message("Voice channel locked.", ephemeral=True)
                else:
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    @staticmethod
    async def unlock_vc(interaction):
        try:
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                if await vccreator.is_valid_channel(channel.id):
                    overwrites = channel.overwrites_for(interaction.guild.default_role)
                    overwrites.connect = True
                    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
                    await interaction.response.send_message("Voice channel unlocked.", ephemeral=True)
                else:
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    @staticmethod
    async def hide_vc(interaction):
        try:
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                if await vccreator.is_valid_channel(channel.id):
                    overwrites = channel.overwrites_for(interaction.guild.default_role)
                    overwrites.view_channel = False
                    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
                    await interaction.response.send_message("Voice channel hidden.", ephemeral=True)
                else:
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    @staticmethod
    async def unhide_vc(interaction):
        try:
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                if await vccreator.is_valid_channel(channel.id):
                    overwrites = channel.overwrites_for(interaction.guild.default_role)
                    overwrites.view_channel = True
                    await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
                    await interaction.response.send_message("Voice channel unhidden.", ephemeral=True)
                else:
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    @staticmethod
    async def limit_vc(interaction):
        try:
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                if await vccreator.is_valid_channel(channel.id):
                    class LimitModal(Modal):
                        def __init__(self):
                            super().__init__(title="Set User Limit")
                            self.add_item(TextInput(label="User Limit", placeholder="Enter the number of users"))

                        async def on_submit(self, modal_interaction):
                            limit = self.children[0].value
                            try:
                                if channel:
                                    await channel.edit(user_limit=int(limit))
                                    await modal_interaction.response.send_message(f"User limit set to {limit}.", ephemeral=True)
                                else:
                                    
                                    await modal_interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
                            except Exception as e:
                                
                                await modal_interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
                    
                    modal = LimitModal()
                    await interaction.response.send_modal(modal)
                else:
                    
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    @staticmethod
    async def invite_to_vc(interaction):
        try:
            
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                
                if await vccreator.is_valid_channel(channel.id):
                    class InviteModal(Modal):
                        def __init__(self):
                            super().__init__(title="Invite User")
                            self.add_item(TextInput(label="User ID", placeholder="Enter the user ID"))

                        async def on_submit(self, modal_interaction):
                            user_id = self.children[0].value
                            
                            try:
                                user = interaction.guild.get_member(int(user_id))
                            except Exception as e:
                                
                                user = None
                            
                            if user:
                                
                                try:
                                    if channel:
                                        await channel.set_permissions(user, connect=True)
                                        await modal_interaction.response.send_message(f"{user.display_name} invited to the channel.", ephemeral=True)
                                        try:
                                            await user.send(f"{modal_interaction.user.mention} invited you to join their VC: {channel.jump_url}")
                                        except:
                                            pass
                                    else:
                                        await modal_interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
                                except Exception as e:
                                    
                                    await modal_interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
                            else:
                                
                                await modal_interaction.response.send_message("User not found.", ephemeral=True)
                    
                    modal = InviteModal()
                    await interaction.response.send_modal(modal)
                else:
                    
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    @staticmethod
    async def ban_from_vc(interaction):
        try:
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                if await vccreator.is_valid_channel(channel.id):
                    class BanModal(Modal):
                        def __init__(self):
                            super().__init__(title="Ban User")
                            self.add_item(TextInput(label="User ID", placeholder="Enter the user ID"))

                        async def on_submit(self, modal_interaction):
                            user_id = self.children[0].value
                            
                            try:
                                user = interaction.guild.get_member(int(user_id))
                            except Exception as e:
                                
                                user = None

                            if user:
                                try:
                                    if channel:
                                        await channel.set_permissions(user, connect=False)
                                        await modal_interaction.response.send_message(f"{user.display_name} banned from the channel.", ephemeral=True)
                                    else:
                                        
                                        await modal_interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
                                except Exception as e:
                                    
                                    await modal_interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
                            else:
                                
                                await modal_interaction.response.send_message("User not found.", ephemeral=True)
                    
                    modal = BanModal()
                    await interaction.response.send_modal(modal)
                else:
                    
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    @staticmethod
    async def permit_in_vc(interaction):
        try:
            
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                
                if await vccreator.is_valid_channel(channel.id):
                    class PermitModal(Modal):
                        def __init__(self):
                            super().__init__(title="Permit User")
                            self.add_item(TextInput(label="User ID", placeholder="Enter the user ID"))

                        async def on_submit(self, modal_interaction):
                            user_id = self.children[0].value
                            
                            try:
                                user = interaction.guild.get_member(int(user_id))
                            except Exception as e:
                                
                                user = None

                            if user:
                                
                                try:
                                    if channel:
                                        await channel.set_permissions(user, connect=True, speak=True)
                                        await modal_interaction.response.send_message(f"{user.display_name} permitted to connect and speak.", ephemeral=True)
                                    else:
                                        
                                        await modal_interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
                                except Exception as e:
                                    
                                    await modal_interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
                            else:
                                
                                await modal_interaction.response.send_message("User not found.", ephemeral=True)
                    
                    modal = PermitModal()
                    await interaction.response.send_modal(modal)
                else:
                    
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

    @staticmethod
    async def rename_vc(interaction):
        try:
            
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
                
                if await vccreator.is_valid_channel(channel.id):
                    class RenameModal(Modal):
                        def __init__(self):
                            super().__init__(title="Rename Channel")
                            self.add_item(TextInput(label="New Name", placeholder="Enter the new channel name"))

                        async def on_submit(self, modal_interaction):
                            new_name = self.children[0].value
                            
                            try:
                                if channel:
                                    await channel.edit(name=new_name)
                                    await modal_interaction.response.send_message(f"Channel renamed to {new_name}.", ephemeral=True)
                                else:
                                    
                                    await modal_interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
                            except Exception as e:
                                
                                await modal_interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)
                    
                    modal = RenameModal()
                    await interaction.response.send_modal(modal)
                else:
                    
                    await interaction.response.send_message("This action is not allowed in this channel.", ephemeral=True)
            else:
                
                await interaction.response.send_message("You are not in a voice channel.", ephemeral=True)
        except Exception as e:
            
            await interaction.response.send_message("Something went wrong. Please try again.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(vccreator(bot))
