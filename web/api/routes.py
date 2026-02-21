"""
API Routes
Path: web/api/routes.py

Defines the REST API endpoints for the web interface.
"""

import os
from flask import Blueprint, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Importing Models and Logic ---
from core.database.modelsfiles.user import User
from core.database.modelsfiles.access_log import AccessLog
from core.database.modelsfiles.zone import Zone


api_bp = Blueprint('api_bp', __name__)


DB_URI = os.getenv("DATABASE_URL", "sqlite:///nfc_access.db")
engine_kwargs = {"check_same_thread": False} if "sqlite" in DB_URI else {}
engine = create_engine(DB_URI, connect_args=engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@api_bp.route('/zones', methods=['GET'])
def get_zones():
    session = SessionLocal()
    try:
        zones = session.query(Zone).all()
        zones_data = [zone.to_dict() for zone in zones]
        
        return jsonify({
            "success": True,
            "count": len(zones_data),
            "data": zones_data
        }), 200
    finally:
        session.close()

@api_bp.route('/status', methods=['GET'])
def get_status():

    return jsonify({
        "status": "online",
        "service": "NFC Access Control API",
        "version": "1.0.0"
    }), 200

@api_bp.route('/logs', methods=['GET'])
def get_recent_logs():
   
    limit = request.args.get('limit', default=10, type=int)
    session = SessionLocal()
    
    try:
      
        logs = session.query(AccessLog).order_by(AccessLog.timestamp.desc()).limit(limit).all()
        
        
        logs_data = [log.to_dict(include_details=True) for log in logs]
        
        return jsonify({
            "success": True,
            "count": len(logs_data),
            "data": logs_data
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        session.close()

@api_bp.route('/users', methods=['GET'])
def get_users():
   
    session = SessionLocal()
    try:
        users = session.query(User).all()
        users_data = [user.to_dict() for user in users]
        
        return jsonify({
            "success": True,
            "count": len(users_data),
            "data": users_data
        }), 200
    finally:
        session.close()

@api_bp.route('/simulate-tap', methods=['POST'])
def simulate_nfc_tap():
    
    data = request.get_json()
    if not data or 'uid' not in data:
        return jsonify({"success": False, "message": "UID is required"}), 400
        
    uid = data['uid']
    zone_id = data.get('zone_id', 1) 
    device_id = "API_SIMULATOR"
    
    session = SessionLocal()
    handler = NFCHandler(session)
    
    try:
       
        result = handler.process_tap(raw_uid=uid, zone_id=zone_id, device_id=device_id)
        
        return jsonify(result), 200 if result['success'] else 403
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        session.close()
