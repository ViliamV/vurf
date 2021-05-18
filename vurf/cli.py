import click
from vurf.parser import parse
from pathlib import Path
from vurf.transformer import Package, Comment

FILE = Path(__file__).parent / "test.vurf"



@click.command()
@click.argument("section")
@click.argument("pkg")
def main(section, pkg):
    with open(FILE) as f:
        root = parse(f)
    args = pkg.split(maxsplit=1)
    comment = Comment(args[1].strip()) if len(args) > 1 else None
    package = Package(args[0].strip(), comment)
    root.add(package, section)
    with open(FILE, 'w') as f:
        f.write(root.to_string())


if __name__ == "__main__":
    main()
