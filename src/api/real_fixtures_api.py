import requests
import json
from datetime import datetime, timedelta
import time
import os

class RealFixturesAPI:
    """API para obtener partidos reales de fútbol usando únicamente datos reales"""
    
    def __init__(self):
        # Usar API gratuita de Football-Data.org (tier gratuito: 10 requests/min)
        self.api_key = os.environ.get('FOOTBALL_API_KEY', '')  # Configurar en Railway
        self.base_url = "https://api.football-data.org/v4"
        self.headers = {
            'X-Auth-Token': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # IDs de las principales ligas europeas
        self.league_ids = {
            'E0': 2021,  # Premier League
            'SP1': 2014, # La Liga
            'D1': 2002,  # Bundesliga
            'I1': 2019,  # Serie A
            'F1': 2015   # Ligue 1
        }
        
    def get_upcoming_matches(self, days_ahead=7):
        """Obtener partidos próximos reales de APIs gratuitas"""
        try:
            if self.api_key:
                return self._get_football_data_matches(days_ahead)
            else:
                # Usar API completamente gratuita sin key
                return self._get_free_api_matches(days_ahead)
        except Exception as e:
            print(f"Error obteniendo datos reales: {e}")
            # Fallback a API gratuita sin key
            return self._get_free_api_matches(days_ahead)
    
    def _get_football_data_matches(self, days_ahead):
        """Obtener partidos reales usando Football-Data.org API"""
        fixtures = []
        today = datetime.now().date()
        date_to = today + timedelta(days=days_ahead)
        
        for league_code, league_id in self.league_ids.items():
            try:
                url = f"{self.base_url}/competitions/{league_id}/matches"
                params = {
                    'dateFrom': today.isoformat(),
                    'dateTo': date_to.isoformat(),
                    'status': 'SCHEDULED'
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for match in data.get('matches', []):
                        if match['status'] == 'SCHEDULED':
                            match_date = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
                            fixtures.append({
                                'HomeTeam': match['homeTeam']['name'],
                                'AwayTeam': match['awayTeam']['name'],
                                'Date': match_date.strftime('%Y-%m-%d'),
                                'Time': match_date.strftime('%H:%M'),
                                'League': league_code,
                                'Competition': match['competition']['name'],
                                'Status': match['status']
                            })
                    print(f"✅ Obtenidos {len(data.get('matches', []))} partidos reales para {league_code}")
                else:
                    print(f"⚠️ Error API {league_code}: {response.status_code}")
                
                time.sleep(1)  # Respetar límite de rate
                
            except Exception as e:
                print(f"Error obteniendo partidos de {league_code}: {e}")
                continue
        
        return fixtures
    
    def _get_free_api_matches(self, days_ahead):
        """Usar API completamente gratuita sin key"""
        try:
            # Usar API gratuita de RapidAPI
            return self._get_rapidapi_matches(days_ahead)
        except Exception as e:
            print(f"Error con API gratuita: {e}")
            # Último recurso: usar datos de calendario oficial
            return self._get_official_calendar_matches(days_ahead)
    
    def _get_rapidapi_matches(self, days_ahead):
        """Usar RapidAPI gratuita para obtener partidos reales"""
        fixtures = []
        today = datetime.now().date()
        
        # Headers para RapidAPI (sin key requerida para tier gratuito)
        headers = {
            'X-RapidAPI-Key': '',  # Vacío para tier gratuito
            'X-RapidAPI-Host': 'api-football-v1.p.rapidapi.com'
        }
        
        # IDs de ligas para RapidAPI
        rapidapi_leagues = {
            'E0': 39,   # Premier League
            'SP1': 140, # La Liga
            'D1': 78,   # Bundesliga
            'I1': 135,  # Serie A
            'F1': 61    # Ligue 1
        }
        
        for league_code, league_id in rapidapi_leagues.items():
            try:
                url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
                params = {
                    'league': league_id,
                    'season': 2024,
                    'next': 10  # Próximos 10 partidos
                }
                
                response = requests.get(url, headers=headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    for fixture in data.get('response', []):
                        if fixture['fixture']['status']['short'] == 'NS':  # Not Started
                            match_date = datetime.fromisoformat(fixture['fixture']['date'].replace('Z', '+00:00'))
                            fixtures.append({
                                'HomeTeam': fixture['teams']['home']['name'],
                                'AwayTeam': fixture['teams']['away']['name'],
                                'Date': match_date.strftime('%Y-%m-%d'),
                                'Time': match_date.strftime('%H:%M'),
                                'League': league_code,
                                'Competition': self._get_competition_name(league_code),
                                'Status': 'SCHEDULED'
                            })
                    print(f"✅ Obtenidos {len(data.get('response', []))} partidos reales para {league_code}")
                
                time.sleep(2)  # Respetar límites de API gratuita
                
            except Exception as e:
                print(f"Error RapidAPI {league_code}: {e}")
                continue
        
        return fixtures
    
    def _get_official_calendar_matches(self, days_ahead):
        """Obtener partidos del calendario oficial de las ligas (web scraping)"""
        fixtures = []
        today = datetime.now().date()
        
        try:
            # Scraping del calendario oficial de Premier League
            premier_matches = self._scrape_premier_league_calendar()
            fixtures.extend(premier_matches)
            
            # Scraping del calendario oficial de La Liga
            laliga_matches = self._scrape_laliga_calendar()
            fixtures.extend(laliga_matches)
            
            print(f"✅ Obtenidos {len(fixtures)} partidos del calendario oficial")
            
        except Exception as e:
            print(f"Error scraping calendarios oficiales: {e}")
        
        return fixtures
    
    def _scrape_premier_league_calendar(self):
        """Scraping del calendario oficial de Premier League"""
        fixtures = []
        try:
            from bs4 import BeautifulSoup
            
            url = "https://www.premierleague.com/fixtures"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar elementos de partidos próximos
                match_elements = soup.find_all('div', class_='matchList')
                
                for match in match_elements[:10]:  # Limitar a 10 partidos
                    try:
                        home_team = match.find('span', class_='teamName').text.strip()
                        away_team = match.find_all('span', class_='teamName')[1].text.strip()
                        date_elem = match.find('time')
                        
                        if date_elem:
                            date_str = date_elem.get('datetime')
                            if date_str:
                                match_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                fixtures.append({
                                    'HomeTeam': home_team,
                                    'AwayTeam': away_team,
                                    'Date': match_date.strftime('%Y-%m-%d'),
                                    'Time': match_date.strftime('%H:%M'),
                                    'League': 'E0',
                                    'Competition': 'Premier League',
                                    'Status': 'SCHEDULED'
                                })
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error scraping Premier League: {e}")
        
        return fixtures
    
    def _scrape_laliga_calendar(self):
        """Scraping del calendario oficial de La Liga"""
        fixtures = []
        try:
            from bs4 import BeautifulSoup
            
            url = "https://www.laliga.com/en-GB/fixture"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Buscar elementos de partidos próximos
                match_elements = soup.find_all('div', class_='match-item')
                
                for match in match_elements[:10]:  # Limitar a 10 partidos
                    try:
                        teams = match.find_all('span', class_='team-name')
                        if len(teams) >= 2:
                            home_team = teams[0].text.strip()
                            away_team = teams[1].text.strip()
                            
                            date_elem = match.find('time')
                            if date_elem:
                                date_str = date_elem.get('datetime')
                                if date_str:
                                    match_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                                    fixtures.append({
                                        'HomeTeam': home_team,
                                        'AwayTeam': away_team,
                                        'Date': match_date.strftime('%Y-%m-%d'),
                                        'Time': match_date.strftime('%H:%M'),
                                        'League': 'SP1',
                                        'Competition': 'La Liga',
                                        'Status': 'SCHEDULED'
                                    })
                    except Exception as e:
                        continue
                        
        except Exception as e:
            print(f"Error scraping La Liga: {e}")
        
        return fixtures
    
    def _get_competition_name(self, league_code):
        """Obtener nombre de la competición"""
        competition_names = {
            'E0': 'Premier League',
            'SP1': 'La Liga',
            'D1': 'Bundesliga',
            'I1': 'Serie A',
            'F1': 'Ligue 1'
        }
        return competition_names.get(league_code, 'Unknown League')
    
    def get_team_stats(self, team_name):
        """Obtener estadísticas reales del equipo desde API"""
        try:
            # Implementar obtención de estadísticas reales
            # Por ahora retornar None para forzar uso de datos reales
            return None
        except Exception as e:
            print(f"Error obteniendo estadísticas de {team_name}: {e}")
            return None
    
    def get_head_to_head(self, team1, team2):
        """Obtener historial de enfrentamientos desde API"""
        try:
            # Implementar obtención de H2H reales
            # Por ahora retornar None para forzar uso de datos reales
            return None
        except Exception as e:
            print(f"Error obteniendo H2H {team1} vs {team2}: {e}")
            return None