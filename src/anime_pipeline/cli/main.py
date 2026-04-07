import typer

from anime_pipeline.cli.audio import app as audio_app
from anime_pipeline.cli.export import app as export_app
from anime_pipeline.cli.project import app as project_app
from anime_pipeline.cli.preview import app as preview_app
from anime_pipeline.cli.shot import app as shot_app
from anime_pipeline.cli.subtitle import app as subtitle_app

app = typer.Typer(help="Local AI anime production pipeline CLI.")
app.add_typer(audio_app, name="audio")
app.add_typer(export_app, name="export")
app.add_typer(project_app, name="project")
app.add_typer(shot_app, name="shot")
app.add_typer(subtitle_app, name="subtitle")
app.add_typer(preview_app, name="preview")
