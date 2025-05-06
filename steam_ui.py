# steam_ui.py
from src.spark_processor import analyze_play_habits, recommend_top_games  # For analytics functions
from pyspark.sql.functions import sum, avg, max  # Spark functions
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress
from rich.prompt import Prompt, IntPrompt
import matplotlib.pyplot as plt
try:
    import seaborn as sns
except ImportError:
    pass

console = Console()

class SteamInterface:
    def __init__(self, client, spark):
        self.client = client
        self.spark = spark
        # cache data so you don't make new requests for no reason.
        self.cached_data = {
            'current_steam_id': None,
            'profiles': {}
        }
    def _get_steam_id(self):
        """Always get fresh SteamID input"""
        return Prompt.ask(
            "Enter SteamID64", 
            default="76561197960265731"
        )
        return self.cached_data['current_steam_id']
    def _display_and_wait(self, panel):
        """Show output and wait for user confirmation"""
        console.print(panel)
        Prompt.ask("\nPress Enter to continue...", default="")
        
    def profile_summary(self):
        """Display basic user profile information"""
        steam_id = self._get_steam_id()
        self._reset_cache_for_new_id(steam_id)
        try:
            profile_data = self._get_user_profile(steam_id)
            players = profile_data.get('response', {}).get('players', [{}])
            
            if not players:
                raise ValueError("No profile data found in API response")
                
            profile = players[0]
            
            # Create the table
            table = Table(show_header=False, box=None)
            table.add_row(":bust_in_silhouette: Name", profile.get('personaname', 'Unknown'))
            table.add_row(":id_button: SteamID", steam_id)
            table.add_row(":earth_americas: Location", f"{profile.get('loccountrycode', '?')}")
            
            # Convert timestamp
            created = profile.get('timecreated')
            if created:
                from datetime import datetime
                created = datetime.utcfromtimestamp(int(created)).strftime('%Y-%m-%d')
            else:
                created = "Unknown"
            
            table.add_row(":cake: Account Created", created)

            # Create the panel
            profile_panel = Panel(
                table, 
                title=f"Profile Summary for {profile.get('personaname', 'Unknown User')}",
                border_style="blue"
            )
            
            # Display and wait
            console.print(profile_panel)
            console.print(Panel.fit(
                f"[link=https://steamcommunity.com/profiles/{steam_id}]View Full Profile[/link]",
                title="Quick Links"
            ))
            Prompt.ask("\nPress Enter to continue...", default="")
        except Exception as e:
            error_panel = Panel(
                f"[red]Error: {str(e)}[/]",
                title="Profile Error",
                border_style="red"
            )
            console.print(error_panel)
            Prompt.ask("\nPress Enter to continue...", default="")
    def _show_playtime_heatmap(self, data):
        """Generate heatmap of top game playtime"""
        try:
            import seaborn as sns
            import numpy as np

            plt.figure(figsize=(10,6))
            pivoted = data.set_index("name")[["total_playtime"]]
            pivoted["total_playtime"] = pivoted["total_playtime"] // 60  # Convert to hours
            sns.heatmap(
                pivoted,
                annot=True,
                fmt=".0f",
                cmap="Blues"
            )
            plt.title("Top Games by Total Playtime (in Hours)")
            plt.tight_layout()
            plt.savefig("playtime_heatmap.png")
            console.print("[green]✓ Saved heatmap to playtime_heatmap.png[/]")
        except ImportError:
            console.print("[red]⚠️ Install seaborn for visualizations: pip install seaborn[/]")
    def gaming_habits(self):
        """Display top X most played games"""
        steam_id = self._get_steam_id()
        
        try:
            with console.status("[bold]Loading game data...") as status:
                games_data = self.client.get_owned_games(steam_id)
                if not games_data or not games_data.get('response'):
                    raise ValueError("No game data found")

                # Use Spark to load and process total playtime
                df = self.spark.read.json(f"data/raw/games/games_{steam_id}.json")
                habits_df = df.selectExpr("explode(response.games) as game").selectExpr(
                    "game.name", "game.playtime_forever"
                ).toPandas()

                if habits_df.empty:
                    raise ValueError("No playtime data available")

                habits_df = habits_df.rename(columns={"playtime_forever": "total_playtime"})
                habits_df = habits_df[habits_df["total_playtime"] > 0]  # filter 0-play games
                habits_df = habits_df.nlargest(15, "total_playtime")  # show top 15 games

                self._render_habits_table(habits_df)
                self._show_playtime_heatmap(habits_df)
        except Exception as e:
            error_panel = Panel(
                f"[red]Error: {str(e)}[/]",
                title="Analysis Error",
                border_style="red"
            )
            console.print(error_panel)
        finally:
            Prompt.ask("\nPress Enter to continue...", default="")
    def _render_habits_table(self, habits):
        """Display top games by playtime"""
        table = Table(title="Top Games by Total Playtime")
        table.add_column("Game", style="cyan", no_wrap=True)
        table.add_column("Playtime (hrs)", justify="right")

        for _, row in habits.iterrows():
            hours = row['total_playtime'] // 60
            table.add_row(row['name'], f"{hours:,} hrs")

        console.print(Panel(table, title="Playtime Breakdown"))
    def main_menu(self):
        while True:
            #console.clear()
            console.print(Panel("[bold cyan]Steam Analytics Suite[/]", subtitle="By Vivek B. and Raymen Shu"))
            
            choice = Prompt.ask(
                "\nChoose an option:",
                choices=["1", "2", "3", "4", "5", "q"],
                show_choices=True
            )
            
            if choice == "1": self.profile_summary()
            elif choice == "2": self.gaming_habits()
            elif choice == "3": self.friend_network()
            elif choice == "4": self.game_recommendations()
            elif choice == "5": self.export_data()
            #elif choice == "q'": break
            if choice != "q":
                # Only clear after user has viewed the output
                console.clear()  # Move this from top of loop to here
            else:
                break
    def _get_user_profile(self, steam_id):
        """Cache profiles per SteamID"""
        if steam_id not in self.cached_data['profiles']:
            with Progress() as progress:
                task = progress.add_task(f"Fetching profile {steam_id}...", total=1) #fix time
                self.cached_data['profiles'][steam_id] = self.client.get_user_data(steam_id)
                progress.update(task, advance=1)
        return self.cached_data['profiles'][steam_id]
    def _reset_cache_for_new_id(self, new_id):
        """Clear cache when ID changes"""
        current_id = self.cached_data['current_steam_id']
        if current_id and current_id != new_id:
            self.cached_data['profiles'] = {}
        self.cached_data['current_steam_id'] = new_id
    def friend_network(self):
        """Fetch and display the user's Steam friends"""
        steam_id = self._get_steam_id()

        try:
            with console.status("[bold]Fetching friends list...") as status:
                friend_data = self.client.get_friend_list(steam_id)
                if not friend_data or 'friendslist' not in friend_data:
                    raise ValueError("No friend data available.")

                friend_ids = [f['steamid'] for f in friend_data['friendslist']['friends']]

                if not friend_ids:
                    raise ValueError("This user has no public friends.")

                # Limit number of profiles to avoid API rate limits
                friend_ids = friend_ids[:10]  # You can increase this later

                friends_info = []
                for fid in friend_ids:
                    profile = self.client.get_user_data(fid)
                    player = profile.get("response", {}).get("players", [{}])[0]
                    friends_info.append({
                        "name": player.get("personaname", "Unknown"),
                        "steamid": fid,
                        "country": player.get("loccountrycode", "—")
                    })
                console.print(f"[green]✓ Showing {len(friend_ids)} friends[/]")
                self._render_friends_table(friends_info)

        except Exception as e:
            error_panel = Panel(
                f"[red]Error: {str(e)}[/]",
                title="Friend Network Error",
                border_style="red"
            )
            console.print(error_panel)
        finally:
            Prompt.ask("\nPress Enter to continue...", default="")
    def _render_friends_table(self, friends_info):
        table = Table(title="Friend Network", show_lines=True)
        table.add_column("Persona Name", style="cyan")
        table.add_column("Steam ID")
        table.add_column("Country")

        for friend in friends_info:
            table.add_row(friend["name"], friend["steamid"], friend["country"])

        console.print(Panel(table, title="Friends Overview"))
    def game_recommendations(self):
        """Recommend games based on friends' most played titles"""
        steam_id = self._get_steam_id()

        try:
            with console.status("[bold]Building recommendations from friend network...") as status:
                friend_data = self.client.get_friend_list(steam_id)
                if not friend_data or 'friendslist' not in friend_data:
                    raise ValueError("No friend data available.")
                
                friend_ids = [f['steamid'] for f in friend_data['friendslist']['friends']][:10]
                all_games = []
                friend_names = []

                for fid in friend_ids:
                    try:
                        # Fetch friend profile
                        profile = self.client.get_user_data(fid)
                        name = profile.get('response', {}).get('players', [{}])[0].get('personaname', 'Unknown')
                        friend_names.append(name)

                        # Fetch their games
                        game_data = self.client.get_owned_games(fid)
                        if not game_data or 'response' not in game_data:
                            continue

                        # Take top 10 games by playtime
                        games = sorted(game_data['response'].get('games', []), key=lambda g: g.get('playtime_forever', 0), reverse=True)[:10]
                        for game in games:
                            all_games.append((
                                game.get('appid'),
                                game.get('name', f"Unknown ({game.get('appid')})"),
                                game.get('playtime_forever', 0)
                            ))
                    except Exception as inner_err:
                        console.print(f"[yellow]Skipping friend {fid} due to error: {inner_err}[/]")

                if not all_games:
                    raise ValueError("No valid game data found from friends.")
                user_game_data = self.client.get_owned_games(steam_id)
                user_owned_appids = set()
                if user_game_data and 'response' in user_game_data:
                    user_owned_appids = {
                        game.get("appid")
                        for game in user_game_data['response'].get("games", [])
                    }
                top_games = recommend_top_games(self.spark, all_games, user_owned_appids)
                self._render_recommendations_table(top_games, friend_names)

        except Exception as e:
            error_panel = Panel(f"[red]Error: {str(e)}[/]", title="Recommendation Error", border_style="red")
            console.print(error_panel)
        finally:
            Prompt.ask("\nPress Enter to continue...", default="")
    def _render_recommendations_table(self, recs_df, friend_names):
        table = Table(title="Top Game Recommendations", show_lines=True)
        table.add_column("Game", style="cyan")
        table.add_column("Friend Playtime (hrs)", justify="right")

        for _, row in recs_df.iterrows():
            hours = round(row["total_playtime"] / 60.0, 1)
            table.add_row(row["name"], f"{hours} hrs")

        console.print(Panel(table, title="Recommended Based on Friends"))
        console.print(Panel("\n".join(friend_names), title="Friends Used for Recommendations", border_style="green"))
