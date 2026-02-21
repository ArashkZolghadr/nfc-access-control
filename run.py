"""
Main Entry Point for NFC Access Control System
Path: /run.py
"""

import os
import threading
import logging
from flask import Flask, render_template
from dotenv import load_dotenv

# --- Database Imports ---
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.database.corefiles.base import Base
# Ensure all models are imported so SQLAlchemy registers their tables
from core.database.modelsfiles.access_log import AccessLog  # noqa: F401
from core.database.modelsfiles.access_policy import AccessPolicy  # noqa: F401
from core.database.modelsfiles.card import Card  # noqa: F401
from core.database.modelsfiles.user import User  # noqa: F401
from core.database.modelsfiles.zone import Zone  # noqa: F401

# --- Application Imports ---

from core.settings.configs import Config 

from web.api.routes import api_bp

# --- NFC Core & Logic Imports ---
from core.NFC.nfc_core import NFCReader
from core.NFC.nfc_handler import NFCHandler


logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


load_dotenv()


DB_URI = os.getenv("DATABASE_URL", "sqlite:///nfc_access.db")

engine_kwargs = {"check_same_thread": False} if "sqlite" in DB_URI else {}
engine = create_engine(DB_URI, connect_args=engine_kwargs)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def ensure_default_zone():
    zone_id = int(os.getenv("DEFAULT_ZONE_ID", 1))
    zone_name = os.getenv("DEFAULT_ZONE_NAME", "Main Entrance")
    session = SessionLocal()
    try:
        existing = session.query(Zone).filter(Zone.id == zone_id).first()
        if existing:
            return
        # Avoid name collision on unique constraint
        name = zone_name
        if session.query(Zone).filter(Zone.name == name).first():
            name = f"{zone_name} #{zone_id}"
        zone = Zone(
            id=zone_id,
            name=name,
            description="Auto-created default zone",
            is_active=True,
        )
        session.add(zone)
        session.commit()
    finally:
        session.close()

def create_app() -> Flask:
    
    app = Flask(__name__)
    app.config.from_object(Config)
    
    
    app.register_blueprint(api_bp, url_prefix='/api')
    
    @app.route('/')
    def index():
        return render_template('index.html')
        
    return app

def nfc_background_task():
   
    logger.info("Initializing NFC Background Task...")
    
  
    db_session = SessionLocal()
    
    try:
      
        use_mock = os.getenv("USE_MOCK_NFC", "True").lower() == "true"
        reader = NFCReader(use_mock=use_mock) 
        
     
        handler = NFCHandler(db_session)

       
        def on_card_tap(uid: str):
          
            default_zone_id = int(os.getenv("DEFAULT_ZONE_ID", 1))
            device_id = os.getenv("DEVICE_ID", "MAIN_ENTRANCE_READER")
            
            logger.info(f"Card tap detected! UID: {uid}")
            
         
            result = handler.process_tap(raw_uid=uid, zone_id=default_zone_id, device_id=device_id)
            
            if result.get("success"):
                logger.info(f"✅ Access Granted for User: {result.get('user')}")
                # TODO
            else:
                logger.warning(f"❌ Access Denied: {result.get('message')}")

       
        reader.start_listening(callback=on_card_tap, interval=0.5)
        
    except Exception as e:
        logger.error(f"NFC Background Task encountered an error: {e}")
    finally:
        db_session.close()
        logger.info("NFC Background Task stopped and DB session closed.")

if __name__ == '__main__':
  
    logger.info("Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    ensure_default_zone()
    
    
    app = create_app()
    
    
    nfc_thread = threading.Thread(target=nfc_background_task, daemon=True)
    nfc_thread.start()
    

    port = int(os.getenv("PORT", 5000))
    host = os.getenv("HOST", "0.0.0.0")
    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    
    logger.info(f"Starting Flask API Server on {host}:{port}...")
    
    
    app.run(host=host, port=port, debug=debug_mode, use_reloader=False)
