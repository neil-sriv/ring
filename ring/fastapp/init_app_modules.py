from __future__ import annotations


def init_app_modules() -> None:
    """Initialize all app modules.

    This function is called when the app is initialized. It calls all functions in
    the entrypoint.initialize files.
    """
    from ring.fastapp._gen.all_sqla_models import import_all_sqla_models

    import_all_sqla_models()
