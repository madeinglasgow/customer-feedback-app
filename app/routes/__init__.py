def register_blueprints(app) -> None:
    from app.routes.dashboard import dashboard_bp
    from app.routes.public import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(dashboard_bp)
