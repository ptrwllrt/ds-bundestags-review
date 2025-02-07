import click
from utils.download import download_protocols
from utils.clean import process_csv_files

@click.group()
def cli():
    """Bundestag Protocol Processing Tool"""
    pass

@cli.command()
def download():
    """Download protocols from Bundestag API"""
    click.echo("Downloading protocols...")
    download_protocols()

@cli.command()
def clean():
    """Clean and process downloaded protocols"""
    click.echo("Processing CSV files...")
    process_csv_files()

if __name__ == "__main__":
    cli()