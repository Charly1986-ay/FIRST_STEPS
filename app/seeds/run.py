import typer

from app.seeds.services import run_users, run_categories, run_tags, run_all

app = typer.Typer(help='Seeds: users, categories, tags')

@app.command('all')
def all_():
    run_all()
    typer.echo('Todos los seeds creadoss')


@app.command('users')
def users():
    run_users()
    typer.echo('Usuarios cargados')


@app.command('categories')
def categories():
    run_categories()
    typer.echo('Categorías cargadas')


@app.command('tags')
def tags():
    run_tags()
    typer.echo('Etiquetas cargadas')