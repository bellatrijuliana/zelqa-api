from flask import Flask
from flask_cors import CORS
from supabase import create_client
from .config import Config

supabase_client = None

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=['http://localhost:5173'])  # Vite dev server

    # Init Supabase
    global supabase_client
    supabase_client = create_client(
        Config.SUPABASE_URL,
        Config.SUPABASE_SERVICE_KEY
    )

    # Register blueprints
    from .routes.projects import projects_bp
    from .routes.features import features_bp
    from .routes.test_cases import test_cases_bp
    from .routes.execution import execution_bp
    from .routes.defects import defects_bp
    from .routes.rtm import rtm_bp
    from .routes.reports import reports_bp
    from .routes.test_plans import test_plans_bp

    app.register_blueprint(projects_bp, url_prefix='/api/projects')
    app.register_blueprint(features_bp, url_prefix='/api/features')
    app.register_blueprint(test_cases_bp, url_prefix='/api/test-cases')
    app.register_blueprint(execution_bp, url_prefix='/api/execution')
    app.register_blueprint(defects_bp, url_prefix='/api/defects')
    app.register_blueprint(rtm_bp, url_prefix='/api/rtm')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(test_plans_bp, url_prefix='/api/test-plans')

    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'Zelqa API is running'}

    return app

def get_supabase():
    return supabase_client