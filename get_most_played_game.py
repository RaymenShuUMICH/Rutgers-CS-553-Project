import argparse
from rich.console import Console
from rich.table import Table
from rich.progress import track
from src.steam_client import SteamAPIClient
from src.spark_processor import find_most_played, generate_full_report
from pyspark.sql import SparkSession

console = Console()

def display_results(steam_id, game_name, playtime):
    if not playtime:
        playtime = 0
    # Convert minutes to hours
    hours = playtime // 60
    minutes = playtime % 60
    
    table = Table(title=f"Steam Gaming Stats for {steam_id}", show_header=False)
    table.add_row(":video_game: Most Played Game", f"[bold]{game_name}[/]")
    table.add_row(":hourglass_flowing_sand: Total Playtime", f"{hours}h {minutes}m")
    table.add_row(":link: Profile", f"https://steamcommunity.com/profiles/{steam_id}")
    
    console.print(table)

def main():
    parser = argparse.ArgumentParser(
        description="Get Steam gaming statistics",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("steam_id", help="SteamID64 (17-digit number)")
    parser.add_argument("--full-report", action="store_true", 
                      help="Generate detailed PDF report")
    
    args = parser.parse_args()

    client = SteamAPIClient()
    
    with console.status("[bold green]Fetching Steam data...") as status:
        games_data = client.get_owned_games(args.steam_id)
    
    if games_data and games_data.get('response'):
        with console.status("[bold cyan]Analyzing data..."):
            spark = SparkSession.builder \
                .appName("SteamAnalytics") \
                .getOrCreate()
            
            if args.full_report:
                generate_full_report(spark, args.steam_id)
                console.print(f"[green]✓ Report saved to reports/{steam_id}_report.pdf[/]")
            else:
                game_name, playtime = find_most_played(spark, args.steam_id)
                display_results(args.steam_id, game_name, playtime)
            
            spark.stop()
    else:
        console.print("[red]× No game data found[/]", style="bold")

if __name__ == "__main__":
    main()
