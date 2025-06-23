# src/table_modifier/cli.py
import click
from src.table_modifier.localization import String
from src.table_modifier.file_interface.factory import load, save

@click.command(help=String("cli_help"))
@click.option('--lang', '-l', default='en', help="Language code for messages")
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
def main(lang, input_path, output_path):
  """Load, process and save a table file."""
  String.set_language(lang)
  click.echo(String("processing_file", file=input_path))
  table = load(input_path)

  save(table, output_path)
  click.echo(String("done", file=output_path))

if __name__ == "__main__":
    main()