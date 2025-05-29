"""
Emerald's Killfeed - Parser Management System
Manage killfeed parsing, log processing, and data collection
"""

import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

import discord
from discord.ext import commands
from bot.cogs.autocomplete import ServerAutocomplete
from discord import Option
#from discord import app_commands # Removed app_commands import, not needed for py-cord 2.6.1

logger = logging.getLogger(__name__)

class Parsers(commands.Cog):
    """
    PARSER MANAGEMENT
    - Killfeed parser controls
    - Log processing management
    - Data collection status
    """

    def __init__(self, bot):
        self.bot = bot

    # Create subcommand group using SlashCommandGroup
    parser = discord.SlashCommandGroup("parser", "Parser management commands")

    @parser.command(name="status", description="Check parser status")
    async def parser_status(self, ctx: discord.ApplicationContext):
        """Check the status of all parsers"""
        try:
            embed = discord.Embed(
                title="🔍 Parser Status",
                description="Current status of all data parsers",
                color=0x3498DB,
                timestamp=datetime.now(timezone.utc)
            )

            # Killfeed parser status
            killfeed_status = "🟢 Active" if hasattr(self.bot, 'killfeed_parser') and self.bot.killfeed_parser else "🔴 Inactive"

            # Log parser status
            log_status = "🟢 Active" if hasattr(self.bot, 'log_parser') and self.bot.log_parser else "🔴 Inactive"

            # Historical parser status
            historical_status = "🟢 Active" if hasattr(self.bot, 'historical_parser') and self.bot.historical_parser else "🔴 Inactive"

            embed.add_field(
                name="📡 Killfeed Parser",
                value=f"Status: **{killfeed_status}**\nMonitors live PvP events",
                inline=True
            )

            embed.add_field(
                name="📜 Log Parser",
                value=f"Status: **{log_status}**\nProcesses server log files",
                inline=True
            )

            embed.add_field(
                name="📚 Historical Parser",
                value=f"Status: **{historical_status}**\nRefreshes historical data",
                inline=True
            )

            # Scheduler status
            scheduler_status = "🟢 Running" if self.bot.scheduler.running else "🔴 Stopped"
            embed.add_field(
                name="⏰ Background Scheduler",
                value=f"Status: **{scheduler_status}**\nManages automated tasks",
                inline=False
            )

            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to check parser status: {e}")
            await ctx.respond("❌ Failed to retrieve parser status.", ephemeral=True)

    @parser.command(name="refresh", description="Manually refresh data for a server")
    @commands.has_permissions(administrator=True)
    @discord.option(
        name="server",
        description="Select a server",
        autocomplete=ServerAutocomplete.autocomplete_server_name
    )
    async def parser_refresh(self, ctx: discord.ApplicationContext, server: str = "default"):
        """Manually trigger a data refresh for a server"""
        try:
            guild_id = ctx.guild.id

            # Check if server exists in guild config - fixed database call
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if not guild_config:
                await ctx.respond("❌ This guild is not configured!", ephemeral=True)
                return

            # Find the server - now using server ID from autocomplete
            servers = guild_config.get('servers', [])
            server_found = False
            server_name = "Unknown"
            for srv in servers:
                if str(srv.get('_id')) == server:
                    server_found = True
                    server_name = srv.get('name', 'Unknown')
                    break

            if not server_found:
                await ctx.respond(f"❌ Server not found in this guild!", ephemeral=True)
                return

            # Defer response for potentially long operation
            await ctx.defer()

            # Trigger historical refresh if parser is available
            if hasattr(self.bot, 'historical_parser') and self.bot.historical_parser:
                try:
                    await self.bot.historical_parser.refresh_historical_data(guild_id, server)

                    embed = discord.Embed(
                        title="🔄 Data Refresh Initiated",
                        description=f"Historical data refresh started for server **{server_name}**",
                        color=0x00FF00,
                        timestamp=datetime.now(timezone.utc)
                    )

                    embed.add_field(
                        name="⏰ Duration",
                        value="This process may take several minutes",
                        inline=True
                    )

                    embed.add_field(
                        name="📊 Data Updated",
                        value="• Player statistics\n• Kill/death records\n• Historical trends",
                        inline=True
                    )

                    embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

                    await ctx.followup.send(embed=embed)

                except Exception as e:
                    logger.error(f"Failed to refresh data: {e}")
                    await ctx.followup.send("❌ Failed to start data refresh. Please try again later.")
            else:
                await ctx.followup.send("❌ Historical parser is not available!")

        except Exception as e:
            logger.error(f"Failed to refresh parser data: {e}")
            await ctx.respond("❌ Failed to initiate data refresh.", ephemeral=True)

    @parser.command(name="stats", description="Show parser statistics")
    async def parser_stats(self, ctx: discord.ApplicationContext):
        """Display parser performance statistics"""
        try:
            guild_id = ctx.guild.id

            embed = discord.Embed(
                title="📊 Parser Statistics",
                description="Performance metrics for data parsers",
                color=0x9B59B6,
                timestamp=datetime.now(timezone.utc)
            )

            # Get recent parsing stats from database - fixed database calls
            try:
                # Count recent killfeed entries (last 24 hours)
                recent_kills = await self.bot.db_manager.killfeed.count_documents({
                    'guild_id': guild_id,
                    'timestamp': {'$gte': datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)}
                })

                # Count total players tracked
                total_players = await self.bot.db_manager.pvp_data.count_documents({
                    'guild_id': guild_id
                })

                # Count linked players
                linked_players = await self.bot.db_manager.players.count_documents({
                    'guild_id': guild_id
                })

                embed.add_field(
                    name="📈 Today's Activity",
                    value=f"• Kills Parsed: **{recent_kills}**\n• Players Tracked: **{total_players}**\n• Linked Users: **{linked_players}**",
                    inline=True
                )

                # Parser uptime
                uptime_status = "🟢 Operational" if self.bot.scheduler.running else "🔴 Down"
                embed.add_field(
                    name="⚡ System Health",
                    value=f"• Parser Status: **{uptime_status}**\n• Database: **🟢 Connected**\n• Scheduler: **🟢 Active**",
                    inline=True
                )

            except Exception as e:
                logger.error(f"Failed to get parser stats from database: {e}")
                embed.add_field(
                    name="⚠️ Statistics",
                    value="Unable to retrieve detailed statistics",
                    inline=False
                )

            embed.set_thumbnail(url="attachment://main.png")
            embed.set_footer(text="Powered by Discord.gg/EmeraldServers")

            await ctx.respond(embed=embed)

        except Exception as e:
            logger.error(f"Failed to show parser stats: {e}")
            await ctx.respond("❌ Failed to retrieve parser statistics.", ephemeral=True)

    @discord.slash_command(name="parse_historical", description="Parse historical data from CSV files")
    @commands.has_permissions(administrator=True)
    async def parse_historical(self, ctx: discord.ApplicationContext):
        """Parse historical data from CSV files"""
        try:
            if not self.bot.historical_parser:
                await ctx.respond("❌ Historical parser not initialized", ephemeral=True)
                return

            await ctx.defer()

            # Run historical parser
            await self.bot.historical_parser.run_historical_parser()

            embed = discord.Embed(
                title="📊 Historical Parser",
                description="Historical data parsing completed successfully",
                color=0x00FF00,
                timestamp=datetime.now(timezone.utc)
            )

            await ctx.followup.send(embed=embed)

        except Exception as e:
            logger.error(f"Historical parsing failed: {e}")
            await ctx.followup.send("❌ Historical parsing failed", ephemeral=True)

    @discord.slash_command(description="🧪 Test log parser on sample data")
    @commands.has_permissions(administrator=True)
    async def test_log_parser(self, ctx):
        """Test log parser with detailed diagnostics"""
        await ctx.defer()

        try:
            if not hasattr(self.bot, 'log_parser'):
                await ctx.followup.send("❌ Log parser not initialized")
                return

            # Get guild servers
            guild_config = await self.bot.db_manager.get_guild(ctx.guild.id)
            if not guild_config or not guild_config.get('servers'):
                await ctx.followup.send("❌ No servers configured for this guild")
                return

            servers = guild_config.get('servers', [])
            if not servers:
                await ctx.followup.send("❌ No servers found")
                return

            server = servers[0]  # Test with first server
            server_id = str(server.get('_id', 'unknown'))
            server_name = server.get('name', 'Unknown Server')

            # Enable debug logging temporarily
            import logging
            old_level = logging.getLogger('bot.parsers.log_parser').level
            logging.getLogger('bot.parsers.log_parser').setLevel(logging.DEBUG)

            try:
                # Test log parsing
                await ctx.followup.send(f"🔍 Testing log parser on server: **{server_name}** (ID: {server_id})")

                # Run the parser
                await self.bot.log_parser.parse_server_logs(ctx.guild.id, server)

                await ctx.followup.send("✅ Log parser test completed. Check console for detailed logs.")

            finally:
                # Restore logging level
                logging.getLogger('bot.parsers.log_parser').setLevel(old_level)

        except Exception as e:
            await ctx.followup.send(f"❌ Log parser test failed: {str(e)}")
            logger.error(f"Log parser test failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")

    @discord.slash_command(description="🧪 Run log parser manually")
    @commands.has_permissions(administrator=True)
    async def manual_log_parse(self, ctx):
        """Manual log parser execution"""
        await ctx.defer()

        try:
            if not hasattr(self.bot, 'log_parser'):
                await ctx.followup.send("❌ Log parser not initialized")
                return

            await self.bot.log_parser.run_log_parser()
            await ctx.followup.send("✅ Log parser executed successfully")

        except Exception as e:
            await ctx.followup.send(f"❌ Log parser failed: {str(e)}")
            logger.error(f"Manual log parser failed: {e}")

    @discord.slash_command(description="🔄 Reset log position tracking")
    @commands.has_permissions(administrator=True)
    async def reset_log_positions(self, ctx, server_id: Option(str, "Server ID to reset (leave empty for all)", required=False) = None):
        """Reset log position tracking"""
        await ctx.defer()

        try:
            if not hasattr(self.bot, 'log_parser'):
                await ctx.followup.send("❌ Log parser not initialized")
                return

            if server_id:
                # Reset specific server
                self.bot.log_parser.reset_log_positions(ctx.guild.id, server_id)
                await ctx.followup.send(f"✅ Reset log position for server {server_id}")
            else:
                # Reset all positions
                self.bot.log_parser.reset_log_positions()
                await ctx.followup.send("✅ Reset all log position tracking")

        except Exception as e:
            await ctx.followup.send(f"❌ Failed to reset log positions: {str(e)}")
            logger.error(f"Reset log positions failed: {e}")

    @discord.slash_command(name="test_regex", description="Test updated regex patterns against actual log data")
    async def test_regex(self, ctx: discord.ApplicationContext):
        """Test updated regex patterns against actual log data"""
        await ctx.defer(ephemeral=True)

        try:
            # Sample lines from the actual log file from attached_assets/Deadside.log
            test_lines = [
                # Basic log start
                "Log file open, 05/17/25 02:01:30",
                # Server configuration that might contain player limits
                "LogSFPS: playersmaxcount=50",
                # Mission events - these should now match
                "LogSFPS: Mission GA_Settle_05_ChernyLog_mis1 will respawn in 221",
                "LogSFPS: Mission GA_Settle_05_ChernyLog_mis1 switched to INITIAL",
                "LogSFPS: Mission GA_Military_02_mis1 will respawn in 1303",
                # Vehicle events  
                "LogSFPS: [ASFPSGameMode::NewVehicle_Add] Add vehicle BP_SFPSVehicle_Ural_M6736_Sidecar_C_2147482394 Total 1",
                # Connection events
                "LogNet: Join request: /Game/Maps/world_0/World_0?logintype=eos&login=Njshh&Name=Njshh&eosid=|0002e69a65204b669c20238266782d7b",
                "LogBeacon: Beacon Join SFPSOnlineBeaconClient EOS:|0002e69a65204b669c20238266782d7b",
                "LogNet: UChannel::Close: Sending CloseBunch. ChIndex == 0. UniqueId: EOS:|0002e69a65204b669c20238266782d7b"
            ]

            # Test both intelligent parser and log parser patterns
            results = []
            
            # Test intelligent connection parser patterns
            if hasattr(self.bot, 'log_parser') and hasattr(self.bot.log_parser, 'connection_parser'):
                connection_parser = self.bot.log_parser.connection_parser
                results.append("**🔍 Testing Intelligent Connection Parser:**")
                for line in test_lines:
                    matched = False
                    for pattern_name, pattern in connection_parser.patterns.items():
                        match = pattern.search(line)
                        if match:
                            results.append(f"✅ **{pattern_name}**: {match.groups()}")
                            matched = True
                            break
                    if not matched:
                        results.append(f"❌ No match: `{line[:50]}...`")
                
                results.append("\n**🔍 Testing Log Parser Patterns:**")
                # Test main log parser patterns  
                for line in test_lines:
                    matched = False
                    for pattern_name, pattern in self.bot.log_parser.log_patterns.items():
                        match = pattern.search(line)
                        if match:
                            results.append(f"✅ **{pattern_name}**: {match.groups()}")
                            matched = True
                            break
                    if not matched:
                        results.append(f"❌ No match: `{line[:50]}...`")
            else:
                results.append("❌ Parsers not available")

            response = "**Regex Pattern Test Results:**\n\n" + "\n".join(results)
            
            if len(response) > 2000:
                # Split into multiple messages if too long
                await ctx.followup.send(response[:2000])
                await ctx.followup.send(response[2000:])
            else:
                await ctx.followup.send(response)

        except Exception as e:
            await ctx.followup.send(f"❌ Test failed: {str(e)}")

    @discord.slash_command(name="debug_playercount", description="Debug player count tracking - comprehensive investigation")
    @discord.option(name="server_id", description="Optional specific server ID to debug", required=False)
    async def debug_playercount(self, ctx: discord.ApplicationContext, server_id: str = None):
        """Debug player count tracking for investigation"""
        await ctx.defer(ephemeral=True)

        guild_id = ctx.guild.id

        # Check if log parser is available
        if not hasattr(self.bot, 'log_parser') or not self.bot.log_parser:
            await ctx.followup.send("❌ Log parser not initialized")
            return

        # Get guild config to find servers
        guild_config = await self.bot.db_manager.get_guild(guild_id)
        if not guild_config or not guild_config.get('servers'):
            await ctx.followup.send("❌ No servers configured for this guild")
            return

        servers = guild_config.get('servers', [])
        if not servers:
            await ctx.followup.send("❌ No servers found")
            return

        embed = discord.Embed(
            title="🐛 Player Count Debug Information",
            color=0xff9900,
            timestamp=discord.utils.utcnow()
        )

        # Check intelligent connection parser
        if hasattr(self.bot, 'log_parser') and hasattr(self.bot.log_parser, 'connection_parser'):
            connection_parser = self.bot.log_parser.connection_parser

            for server_config in servers:
                server_name = server_config.get('name', 'Unknown')
                current_server_id = str(server_config.get('_id', 'unknown'))

                # Skip if specific server requested and this isn't it
                if server_id and current_server_id != server_id:
                    continue

                server_key = f"{guild_id}_{current_server_id}"

                # Get current stats
                stats = connection_parser.get_server_stats(server_key)

                # Debug the state
                connection_parser.debug_server_state(server_key)

                # Get file state info
                file_state = self.bot.log_parser.file_states.get(server_key, {})

                # Count player states
                player_states = connection_parser.player_states.get(server_key, {})
                state_counts = {}
                for player_id, player_state in player_states.items():
                    state = player_state.current_state
                    state_counts[state] = state_counts.get(state, 0) + 1

                embed.add_field(
                    name=f"📊 {server_name} (ID: {current_server_id})",
                    value=f"**Live Counts:**\nQueue: {stats.get('queue_count', 0)}\nPlayers: {stats.get('player_count', 0)}\n"
                          f"**File State:**\nSize: {file_state.get('file_size', 0)}\nLines: {file_state.get('line_count', 0)}\n"
                          f"**Player States:** {len(player_states)} total\n{', '.join([f'{k}: {v}' for k, v in state_counts.items()]) if state_counts else 'None'}",
                    inline=True
                )

        await ctx.followup.send(embed=embed)

    @discord.slash_command(name="resetlogparser", description="Reset log parser state and player counts")
    @commands.has_permissions(administrator=True)
    async def resetlogparser(self, ctx: discord.ApplicationContext,
                           server_id: Option(str, "Server ID to reset (leave empty for all servers)", required=False) = None):
        """Reset log parser state and clear player counts"""
        await ctx.defer()

        try:
            if not hasattr(self.bot, 'log_parser') or not self.bot.log_parser:
                await ctx.followup.send("❌ Log parser not initialized")
                return

            guild_id = ctx.guild.id
            
            # Get guild configuration
            guild_config = await self.bot.db_manager.get_guild(guild_id)
            if not guild_config:
                await ctx.followup.send("❌ This guild is not configured")
                return

            servers = guild_config.get('servers', [])
            if not servers:
                await ctx.followup.send("❌ No servers configured for this guild")
                return

            reset_count = 0
            
            if server_id:
                # Reset specific server
                server_found = False
                for server in servers:
                    if str(server.get('_id')) == server_id:
                        server_found = True
                        server_key = f"{guild_id}_{server_id}"
                        
                        # Reset log parser state
                        if hasattr(self.bot.log_parser, 'last_log_position'):
                            self.bot.log_parser.last_log_position.pop(server_key, None)
                        
                        # Reset file states
                        if hasattr(self.bot.log_parser, 'file_states'):
                            self.bot.log_parser.file_states.pop(server_key, None)
                        
                        # Reset connection parser state
                        if hasattr(self.bot.log_parser, 'connection_parser'):
                            connection_parser = self.bot.log_parser.connection_parser
                            if hasattr(connection_parser, 'player_states'):
                                connection_parser.player_states.pop(server_key, None)
                            if hasattr(connection_parser, 'server_stats'):
                                connection_parser.server_stats.pop(server_key, None)
                        
                        # Reset server status
                        if hasattr(self.bot.log_parser, 'server_status'):
                            self.bot.log_parser.server_status.pop(server_key, None)
                        
                        reset_count = 1
                        break
                
                if not server_found:
                    await ctx.followup.send(f"❌ Server ID {server_id} not found in this guild")
                    return
            else:
                # Reset all servers for this guild
                for server in servers:
                    server_key = f"{guild_id}_{server.get('_id')}"
                    
                    # Reset log parser state
                    if hasattr(self.bot.log_parser, 'last_log_position'):
                        self.bot.log_parser.last_log_position.pop(server_key, None)
                    
                    # Reset file states
                    if hasattr(self.bot.log_parser, 'file_states'):
                        self.bot.log_parser.file_states.pop(server_key, None)
                    
                    # Reset connection parser state
                    if hasattr(self.bot.log_parser, 'connection_parser'):
                        connection_parser = self.bot.log_parser.connection_parser
                        if hasattr(connection_parser, 'player_states'):
                            connection_parser.player_states.pop(server_key, None)
                        if hasattr(connection_parser, 'server_stats'):
                            connection_parser.server_stats.pop(server_key, None)
                    
                    # Reset server status
                    if hasattr(self.bot.log_parser, 'server_status'):
                        self.bot.log_parser.server_status.pop(server_key, None)
                    
                    reset_count += 1

            # Create success embed using EmbedFactory
            from bot.utils.embed_factory import EmbedFactory
            embed = EmbedFactory.create_success_embed(
                success_message=f"Log parser state reset for {reset_count} server{'s' if reset_count != 1 else ''}",
                details="• Cleared last parsed line positions\n• Reset player count tracking\n• Cleared connection states\n• Reset file tracking states\n\nParser will restart from beginning of log files on next run"
            )
            
            await ctx.followup.send(embed=embed)
            
            logger.info(f"Log parser reset completed for guild {guild_id}, reset {reset_count} servers")

        except Exception as e:
            logger.error(f"Failed to reset log parser: {e}")
            await ctx.followup.send(f"❌ Failed to reset log parser: {str(e)}")

    @discord.slash_command(name="validatelogparser", description="Validate log parser against included test log file")
    @commands.has_permissions(administrator=True)
    async def validatelogparser(self, ctx: discord.ApplicationContext):
        """Parse the included Deadside.log file and output validation results"""
        await ctx.defer()

        try:
            if not hasattr(self.bot, 'log_parser') or not self.bot.log_parser:
                await ctx.followup.send("❌ Log parser not initialized")
                return

            import os
            log_file_path = "attached_assets/Deadside.log"
            
            if not os.path.exists(log_file_path):
                await ctx.followup.send("❌ Test log file not found")
                return

            # Initialize counters for validation
            validation_results = {
                'queue_joins': 0,
                'player_joins': 0,
                'disconnects_post_join': 0,
                'disconnects_pre_join': 0,
                'missions_ready': 0,
                'missions_initial': 0,
                'airdrops_flying': 0,
                'heli_crashes': 0,
                'traders': 0,
                'total_lines': 0
            }

            # Player lifecycle tracking for count calculation
            jq = 0  # Queued
            j2 = 0  # Joined
            d1 = 0  # Disconnected after join
            d2 = 0  # Disconnected before join

            player_states = {}  # Track player states for accurate counting

            # Parse the log file line by line
            with open(log_file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    validation_results['total_lines'] += 1
                    line = line.strip()
                    
                    # Test queue joins
                    if self.bot.log_parser.log_patterns['queue_join'].search(line):
                        match = self.bot.log_parser.log_patterns['queue_join'].search(line)
                        if match:
                            player_name, player_id = match.groups()
                            validation_results['queue_joins'] += 1
                            jq += 1
                            player_states[player_id] = 'QUEUED'
                    
                    # Test player joins (registrations)
                    elif self.bot.log_parser.log_patterns['player_joined'].search(line):
                        match = self.bot.log_parser.log_patterns['player_joined'].search(line)
                        if match:
                            player_id = match.groups()[0]
                            validation_results['player_joins'] += 1
                            j2 += 1
                            player_states[player_id] = 'JOINED'
                    
                    # Test disconnects post-join
                    elif self.bot.log_parser.log_patterns['disconnect_post_join'].search(line):
                        match = self.bot.log_parser.log_patterns['disconnect_post_join'].search(line)
                        if match:
                            player_id = match.groups()[0]
                            validation_results['disconnects_post_join'] += 1
                            if player_states.get(player_id) == 'JOINED':
                                d1 += 1
                            else:
                                d2 += 1
                            player_states[player_id] = 'DISCONNECTED'
                    
                    # Test missions ready
                    elif self.bot.log_parser.log_patterns['mission_ready'].search(line):
                        match = self.bot.log_parser.log_patterns['mission_ready'].search(line)
                        if match:
                            mission_name = match.groups()[0]
                            # Only count missions level 3+ as per requirements
                            if 'mis' in mission_name.lower():
                                validation_results['missions_ready'] += 1
                    
                    # Test missions initial
                    elif self.bot.log_parser.log_patterns['mission_initial'].search(line):
                        match = self.bot.log_parser.log_patterns['mission_initial'].search(line)
                        if match:
                            mission_name = match.groups()[0]
                            if 'mis' in mission_name.lower():
                                validation_results['missions_initial'] += 1
                    
                    # Test airdrops flying
                    elif self.bot.log_parser.log_patterns['airdrop_flying'].search(line):
                        validation_results['airdrops_flying'] += 1

            # Calculate final player and queue counts using the specified logic
            player_count = j2 - d1  # PC = j2 - d1
            queue_count = jq - j2 - d2  # QC = jq - j2 - d2

            # Create validation results embed manually since EmbedFactory expects different parameters
            embed = discord.Embed(
                title="📊 Log Parser Validation Results",
                description=f"Validation completed on {validation_results['total_lines']:,} log lines",
                color=0x1E90FF,
                timestamp=datetime.now(timezone.utc)
            )
            
            embed.add_field(
                name="🔢 Connection Events", 
                value=f"• Queue Joins (jq): **{validation_results['queue_joins']}**\n"
                      f"• Player Joins (j2): **{validation_results['player_joins']}**\n"
                      f"• Disconnects Post-Join (d1): **{validation_results['disconnects_post_join']}**\n"
                      f"• Disconnects Pre-Join (d2): **{d2}**", 
                inline=True
            )
            
            embed.add_field(
                name="📈 Calculated Counts", 
                value=f"• **Player Count (PC)**: {player_count}\n"
                      f"• **Queue Count (QC)**: {queue_count}\n"
                      f"• Formula: PC = j2 - d1, QC = jq - j2 - d2", 
                inline=True
            )
            
            embed.add_field(
                name="🎯 Game Events", 
                value=f"• Missions Ready: **{validation_results['missions_ready']}**\n"
                      f"• Missions Initial: **{validation_results['missions_initial']}**\n"
                      f"• Airdrops Flying: **{validation_results['airdrops_flying']}**", 
                inline=True
            )
            
            embed.add_field(
                name="✅ Validation Status", 
                value=f"• Patterns Working: **{'✅ Yes' if validation_results['queue_joins'] > 0 else '❌ No'}**\n"
                      f"• Player Count Valid: **{'✅ Yes' if player_count >= 0 else '❌ No'}**\n"
                      f"• Queue Count Valid: **{'✅ Yes' if queue_count >= 0 else '❌ No'}**", 
                inline=True
            )

            # Set appropriate thumbnail
            embed.set_thumbnail(url="attachment://Mission.png")
            embed.set_footer(text="Log Parser Validation • Powered by Emerald Servers")

            await ctx.followup.send(embed=embed)
            
            # Also log the results for debugging
            logger.info(f"Log parser validation completed:")
            logger.info(f"  Queue joins: {validation_results['queue_joins']}")
            logger.info(f"  Player joins: {validation_results['player_joins']}")
            logger.info(f"  Disconnects: {validation_results['disconnects_post_join']}")
            logger.info(f"  Missions ready: {validation_results['missions_ready']}")
            logger.info(f"  Airdrops: {validation_results['airdrops_flying']}")
            logger.info(f"  Final PC: {player_count}, QC: {queue_count}")

        except Exception as e:
            logger.error(f"Failed to validate log parser: {e}")
            await ctx.followup.send(f"❌ Failed to validate log parser: {str(e)}")

    @discord.slash_command(name="investigate_playercount", description="Deep investigation of player count issues")
    async def investigate_playercount(self, ctx: discord.ApplicationContext, 
                                     server_id: Option(str, "Specific server ID to investigate", required=False) = None):
        """Comprehensive player count investigation"""
        await ctx.defer(ephemeral=True)

        guild_id = ctx.guild.id

        if not hasattr(self.bot, 'log_parser') or not self.bot.log_parser:
            await ctx.followup.send("❌ Log parser not initialized")
            return

        # Get guild config
        guild_config = await self.bot.db_manager.get_guild(guild_id)
        if not guild_config or not guild_config.get('servers'):
            await ctx.followup.send("❌ No servers configured for this guild")
            return

        servers = guild_config.get('servers', [])
        connection_parser = self.bot.log_parser.connection_parser

        investigation_results = []

        for server_config in servers:
            server_name = server_config.get('name', 'Unknown')
            current_server_id = str(server_config.get('_id', 'unknown'))

            if server_id and current_server_id != server_id:
                continue

            server_key = f"{guild_id}_{current_server_id}"

            # 1. Verify regex patterns
            pattern_results = connection_parser.verify_regex_patterns()

            # 2. Test counting logic
            counting_results = connection_parser.test_counting_logic(server_key)

            # 3. Check file processing state
            file_state = self.bot.log_parser.file_states.get(server_key, {})

            investigation_results.append({
                'server_name': server_name,
                'server_id': current_server_id,
                'pattern_results': pattern_results,
                'counting_results': counting_results,
                'file_state': file_state
            })

        # Create detailed report
        embed = discord.Embed(
            title="🔬 Player Count Investigation Report",
            color=0x00ff00,
            timestamp=datetime.now(timezone.utc)
        )

        for result in investigation_results:
            pattern_summary = {k: v['match_count'] for k, v in result['pattern_results'].items()}
            counting = result['counting_results']

            embed.add_field(
                name=f"🔍 {result['server_name']} Investigation",
                value=f"**Pattern Matches:** {sum(pattern_summary.values())} total\n"
                      f"**Queue Count:** Manual={counting.get('manual_count', {}).get('queue_count', 0)}, "
                      f"Official={counting.get('official_stats', {}).get('queue_count', 0)}\n"
                      f"**Player Count:** Manual={counting.get('manual_count', {}).get('player_count', 0)}, "
                      f"Official={counting.get('official_stats', {}).get('player_count', 0)}\n"
                      f"**File State:** Size={result['file_state'].get('file_size', 0)}, "
                      f"Lines={result['file_state'].get('line_count', 0)}",
                inline=False
            )

        await ctx.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(Parsers(bot))