# api_routes.py - Module séparé pour les routes API

from flask import jsonify, request, Response
from datetime import datetime, timedelta
import json
import csv
from io import StringIO
from sqlalchemy import and_, or_, func

def register_api_routes(app, db, AlertAcknowledgment, SystemMetrics):
    """Enregistrer toutes les routes API"""
    
    # ===============================================
    # API ROUTES - DASHBOARD PRINCIPAL
    # ===============================================
    
    @app.route('/api/stats')
    def api_stats():
        """API : Statistiques générales"""
        try:
            # Statistiques des dernières 24h
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            total_acks_24h = AlertAcknowledgment.query.filter(
                AlertAcknowledgment.acknowledged_at >= yesterday
            ).count()
            
            successful_acks_24h = AlertAcknowledgment.query.filter(
                AlertAcknowledgment.acknowledged_at >= yesterday,
                AlertAcknowledgment.success == True
            ).count()
            
            failed_acks_24h = total_acks_24h - successful_acks_24h
            
            # Taux de succès
            success_rate = (successful_acks_24h / total_acks_24h * 100) if total_acks_24h > 0 else 0
            
            # Statistiques globales
            total_all_time = AlertAcknowledgment.query.count()
            
            # Temps de réponse moyen
            avg_response_time = db.session.query(
                db.func.avg(AlertAcknowledgment.response_time)
            ).filter(
                AlertAcknowledgment.acknowledged_at >= yesterday,
                AlertAcknowledgment.response_time.isnot(None)
            ).scalar() or 0
            
            return jsonify({
                'last_24h': {
                    'total_acks': total_acks_24h,
                    'successful_acks': successful_acks_24h,
                    'failed_acks': failed_acks_24h,
                    'success_rate': round(success_rate, 2)
                },
                'all_time': {
                    'total_acks': total_all_time
                },
                'performance': {
                    'avg_response_time': round(avg_response_time, 3) if avg_response_time else 0
                }
            })
        except Exception as e:
            app.logger.error(f"Erreur lors de la récupération des stats: {e}")
            return jsonify({'error': 'Erreur serveur'}), 500
    
    @app.route('/api/charts/hourly')
    def api_charts_hourly():
        """API : Données pour graphique horaire"""
        try:
            # Dernières 24 heures, regroupées par heure
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            # Requête pour compter les acquittements par heure
            results = db.session.query(
                db.func.strftime('%H', AlertAcknowledgment.acknowledged_at).label('hour'),
                db.func.count(AlertAcknowledgment.id).label('total'),
                db.func.sum(db.case([(AlertAcknowledgment.success == True, 1)], else_=0)).label('success'),
                db.func.sum(db.case([(AlertAcknowledgment.success == False, 1)], else_=0)).label('failed')
            ).filter(
                AlertAcknowledgment.acknowledged_at >= yesterday
            ).group_by(
                db.func.strftime('%H', AlertAcknowledgment.acknowledged_at)
            ).all()
            
            # Préparer les données pour Chart.js
            hours = [f"{i:02d}:00" for i in range(24)]
            totals = [0] * 24
            successes = [0] * 24
            failures = [0] * 24
            
            for result in results:
                hour_index = int(result.hour)
                totals[hour_index] = result.total or 0
                successes[hour_index] = result.success or 0
                failures[hour_index] = result.failed or 0
            
            return jsonify({
                'labels': hours,
                'datasets': [
                    {
                        'label': 'Acquittements réussis',
                        'data': successes,
                        'backgroundColor': 'rgba(40, 167, 69, 0.8)',
                        'borderColor': 'rgba(40, 167, 69, 1)',
                        'borderWidth': 1
                    },
                    {
                        'label': 'Acquittements échoués',
                        'data': failures,
                        'backgroundColor': 'rgba(220, 53, 69, 0.8)',
                        'borderColor': 'rgba(220, 53, 69, 1)',
                        'borderWidth': 1
                    }
                ]
            })
        except Exception as e:
            app.logger.error(f"Erreur lors de la récupération des données horaires: {e}")
            return jsonify({'error': 'Erreur serveur'}), 500
    
    # ... [Autres routes API] ...
    
    # ===============================================
    # API ROUTES - HISTORIQUE
    # ===============================================
    
    @app.route('/api/history')
    def api_history():
        """API : Données d'historique avec filtres et pagination"""
        # [Code complet de la fonction api_history...]
        pass
    
    # ===============================================
    # FONCTIONS UTILITAIRES
    # ===============================================
    
    def generate_charts_data(base_query, start_date, end_date):
        """Génère les données pour les graphiques"""
        # [Code complet de la fonction...]
        pass
